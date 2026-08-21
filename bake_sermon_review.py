#!/usr/bin/env python3
"""
Bake the upcoming Sunday's 6 sermon materials (요약/복습/5일묵상 x 한글/영어)
into sermon_review.html's SR_STATIC JSON blob.

Intended to run ONLY on Saturdays (the wrapper script, refresh-dashboard.sh,
gates the call to this script on day-of-week) — per the user's decision
(2026-08-21), sermon materials are finalized on Saturday and don't change
again until the following Saturday, so a static snapshot only needs
refreshing once a week, not on every daily rebuild.

This is a deterministic, stdlib-only script (no LLM call, no external
dependencies) so it's reliable to run unattended. It mirrors the exact
same folder-picking / file-classification / docx-paragraph-extraction
logic as the live client-side JS in sermon_review.html (srFindTargetFolder,
srClassify, srLangOf, srDocxToParagraphs) so the two stay in sync.

Usage: python3 bake_sermon_review.py
  (run from anywhere; paths below are absolute / relative to this file)
"""
import os
import re
import sys
import json
import zipfile
import datetime
import unicodedata

VAULT_SERMON_DIR = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/SJKim/"
    "200. CBB Ministry/210. Ministry of the Word/2026 기본"
)
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
SERMON_REVIEW_PATH = os.path.join(REPO_DIR, "sermon_review.html")

SLOTS = [
    ("summaryK", "K", lambda n: re.search(r"(summary|요약)", n, re.I) and re.search(r"\.docx?$", n, re.I)),
    ("summaryE", "E", lambda n: re.search(r"(summary|요약)", n, re.I) and re.search(r"\.docx?$", n, re.I)),
    ("reviewK",  "K", lambda n: re.search(r"(review|복습)", n, re.I) and re.search(r"\.html?$", n, re.I)),
    ("reviewE",  "E", lambda n: re.search(r"(review|복습)", n, re.I) and re.search(r"\.html?$", n, re.I)),
    ("devotionK","K", lambda n: re.search(r"(devotion|5\s*day|5일\s*묵상)", n, re.I) and re.search(r"\.html?$", n, re.I)),
    ("devotionE","E", lambda n: re.search(r"(devotion|5\s*day|5일\s*묵상)", n, re.I) and re.search(r"\.html?$", n, re.I)),
]


def lang_of(name):
    if re.search(r"(?:^|[-_])E(?=[-_.]|$)", name):
        return "E"
    if re.search(r"(?:^|[-_])K(?=[-_.]|$)", name):
        return "K"
    if re.search(r"영어|english", name, re.I):
        return "E"
    if re.search(r"한글|korean", name, re.I):
        return "K"
    return None


def find_target_folder():
    if not os.path.isdir(VAULT_SERMON_DIR):
        print(f"ERROR: vault sermon folder not found: {VAULT_SERMON_DIR}", file=sys.stderr)
        return None
    dated = []
    for name in os.listdir(VAULT_SERMON_DIR):
        full = os.path.join(VAULT_SERMON_DIR, name)
        if not os.path.isdir(full):
            continue
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})[ _]", name)
        if not m:
            continue
        dated.append((f"{m.group(1)}-{m.group(2)}-{m.group(3)}", name))
    dated.sort(key=lambda x: x[0])
    if not dated:
        return None
    today = datetime.date.today()
    today_str = today.isoformat()
    is_saturday = today.weekday() == 5  # Mon=0 ... Sat=5, Sun=6 (matches JS getDay()===6)
    if is_saturday:
        upcoming = [d for d in dated if d[0] > today_str]
        return upcoming[0] if upcoming else dated[-1]
    else:
        past = [d for d in dated if d[0] <= today_str]
        return past[-1] if past else dated[0]


def classify(folder_path):
    files = {}
    for raw_name in os.listdir(folder_path):
        full = os.path.join(folder_path, raw_name)
        if not os.path.isfile(full):
            continue
        name = unicodedata.normalize("NFC", raw_name)
        if re.match(r"^(prayer|invitation)", name, re.I):
            continue
        lang = lang_of(name)
        if not lang:
            continue
        for key, slot_lang, matcher in SLOTS:
            if slot_lang != lang:
                continue
            if matcher(name):
                if key not in files:
                    files[key] = full
                break
    return files


def extract_docx_paragraphs(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    para_re = re.compile(r"<w:p[ >].*?</w:p>", re.S)
    style_re = re.compile(r'<w:pStyle[^>]*w:val="(Heading|Title)', re.I)
    t_re = re.compile(r"<w:t[^>]*>(.*?)</w:t>", re.S)
    paragraphs = []
    for m in para_re.finditer(xml):
        p_xml = m.group(0)
        is_heading = bool(style_re.search(p_xml))
        text = "".join(t_re.findall(p_xml))
        text = (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                    .replace("&quot;", '"').replace("&apos;", "'"))
        if text.strip():
            paragraphs.append({"heading": is_heading, "text": text})
    return paragraphs


def build_static_data(week_date, week_folder_name, classified_files):
    out_files = {}
    for key, path in classified_files.items():
        name = os.path.basename(path)
        if path.lower().endswith((".docx", ".doc")):
            out_files[key] = {"kind": "docx", "name": name, "paragraphs": extract_docx_paragraphs(path)}
        else:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                out_files[key] = {"kind": "html", "name": name, "html": f.read()}
    return {
        "weekFolder": week_folder_name,
        "generatedAt": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": out_files,
    }


def splice_into_html(html_text, data):
    json_str = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    pattern = re.compile(
        r'(<script type="application/json" id="srStaticData">).*?(</script>)', re.S
    )
    new_html, n = pattern.subn(lambda m: m.group(1) + json_str + m.group(2), html_text, count=1)
    if n != 1:
        raise RuntimeError(
            "Could not find the <script type=\"application/json\" id=\"srStaticData\"> "
            "block in sermon_review.html — has the page structure changed?"
        )
    return new_html


def main():
    target = find_target_folder()
    if not target:
        print("No dated sermon folder found — nothing to bake.", file=sys.stderr)
        return 1
    week_date, week_folder_name = target
    folder_path = os.path.join(VAULT_SERMON_DIR, week_folder_name)
    classified = classify(folder_path)

    missing = [key for key, _, _ in SLOTS if key not in classified]
    if missing:
        print(f"Note: {week_folder_name} is missing materials for: {', '.join(missing)}", file=sys.stderr)
    if not classified:
        print(f"ERROR: no sermon materials matched in {week_folder_name} — leaving sermon_review.html untouched.", file=sys.stderr)
        return 1

    data = build_static_data(week_date, week_folder_name, classified)

    if not os.path.isfile(SERMON_REVIEW_PATH):
        print(f"ERROR: {SERMON_REVIEW_PATH} not found.", file=sys.stderr)
        return 1
    with open(SERMON_REVIEW_PATH, "r", encoding="utf-8") as f:
        html_text = f.read()

    new_html = splice_into_html(html_text, data)
    with open(SERMON_REVIEW_PATH, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"Baked sermon_review.html from '{week_folder_name}' — "
          f"{len(classified)}/6 materials found ({', '.join(sorted(classified))}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
