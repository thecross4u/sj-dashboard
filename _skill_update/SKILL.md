---
name: sj-dashboard
description: Build or refresh "SJ's Dashboard" — Seongjun Kim's personal Obsidian pastoral-ministry dashboard (sermon prep tracker, to-dos, prayer tracker, Korean/US news, church-ministry trends, clippings, Des Moines weather, USD/KRW trend, Google Calendar, and a Daily Note writer that saves back into the vault). Use this skill whenever the user asks to make, update, refresh, or add a section to their dashboard, mentions "대시보드", "SJ's Dashboard", or asks for a fresh snapshot of their Obsidian vault, sermon schedule, or daily notes as a visual page — even if they don't say the word "dashboard" and even if they only want one section changed. Also use it before reading their Obsidian vault for any summary or tracker, since it documents the vault's layout and the shell commands that don't time out.
---

# SJ's Dashboard

This skill rebuilds a single self-contained HTML dashboard from Seongjun Kim's
Obsidian vault plus live web and connector data. The dashboard is a **snapshot**,
not a live app: every number and headline is baked in at build time, so
"refresh the dashboard" means re-running this whole process and re-delivering
the file.

The one exception is the Daily Note writer, which is genuinely interactive —
it writes back into the vault from the browser. See
`references/daily-note-writer.md`.

## Before anything else

Read the memory file `/areas/obsidian-dashboard.md`. It carries the user's
current preferences — which news sources they've accepted or rejected, which
sections they've asked to remove, what's already built. Those decisions override
the defaults below, because they were made after this skill was written.

The vault reaches this session through the Cowork device bridge, mounted at
`$HOME/mnt/SJKim` for `device_bash`. In an interactive session, if the bridge
tools are missing or the folder isn't connected, ask the user to connect the
vault folder in the desktop app rather than guessing at the data.

**Unattended runs (the scheduled task) are different — the bridge often isn't
there and there's no one to ask.** A cloud session only reaches the vault if
the desktop app happens to be open and connected at that exact moment, which
it usually isn't during an automatic hourly firing. Don't render vault-derived
sections as empty or "연결 안됨" in that case — that reads as broken and was a
real complaint. Instead: after every successful vault-connected scan, save the
scanner's JSON output to the Claude Project "대시보드" as `vault-snapshot.json`
(`Projects` tool, `project_write`). When the bridge is unreachable, `project_read`
that file instead and render the vault-derived sections from it, with a visible
note giving its `scanned_at` timestamp so the user knows it's cached, not live.
A stale-but-labeled number beats a blank card.

## The build sequence

Work in this order. Gathering before rendering matters here — the layout
depends on how much data actually came back, and several sources fail in ways
you can't predict.

**1. Scan the vault.** Run the bundled scanner:

```bash
python3 scripts/vault_scan.py            # on device_bash, from the vault root
```

It emits one JSON blob with note counts, open tasks, the sermon pipeline,
prayer items, recent clippings, and Readwise books. Read
`references/vault-map.md` before writing any of your own shell commands against
the vault — it documents the folder layout and, more importantly, the commands
that time out. A naive `grep -r` across the vault root will hang: two folders
hold ~13,000 files between them.

**2. Fetch the live data.** News, church-ministry trends, and USD/KRW.
`references/data-sources.md` lists the exact URLs, which ones are reliably
fetchable, and which are blocked at the proxy so you don't burn attempts
rediscovering that. Fetch these in parallel — they're independent, and a few
will fail regardless of what you do.

Weather is **not** part of this build-time fetch anymore. The user needs
temperature to update at least every 30 minutes, more often than any rebuild
can realistically run, so the weather widget is live client-side JavaScript
(Open-Meteo, no key needed) that fetches on page load and re-polls every 30
minutes in the browser. When rebuilding, just make sure that script block is
still intact — see `references/data-sources.md` for the exact endpoint and
coordinates. Don't reintroduce a baked-in `wxHourly` snapshot as the primary
source; it's kept only as an offline fallback inside that same script.

**3. Pull the calendar.** `mcp__Google_Calendar__list_events` for the next two
weeks, `America/Chicago`. The user has this connector plus Gmail connected.

**4. Render.** Read the `dataviz` skill before writing chart code, and use its
palette — the existing dashboard is built on it, so ignoring it will make a new
section look foreign. Layout conventions are in `references/layout.md`.

**5. Deliver.** The two files are named `index.html` (main dashboard) and
`daily_note.html` (Daily Note writer) — not `sjkim_dashboard.html` /
`sjkim_daily_note.html` anymore. That rename happened 2026-08-16 when the
dashboard moved from "download and open as a local file" to a real hosted
page, because iOS Safari/Chrome can't run a local file's JavaScript (Quick
Look preview strips it), so iPad viewing was broken. `index.html` is also
what GitHub Pages serves by default at the bare repo URL, which is the whole
point of the rename. Both files carry a passphrase lock screen (session's
current passphrase: `1108`, in a `#lockScreen` overlay at the top of
`<body>` and an unlock `<script>` block at the very end) — never strip that
out when rebuilding; it's the only thing standing between this personal
ministry data and the public internet, since the hosting repo has to be
public on GitHub's free tier.

Delivery itself branches on where this skill is running:

- **Cowork (cloud session, this environment):** This sandbox's outbound
  network proxy blocks `git push` to arbitrary GitHub repos even with a
  valid token (confirmed 2026-08-16 — `git clone`/read works, `push` gets
  rejected with "access denied by the git proxy... not in this session's
  authorized repository set", and there's no tool here to lift that). So:
  `SendUserFile` both files, then tell the user to upload them at
  `https://github.com/thecross4u/sj-dashboard/upload/main` (drag-and-drop +
  Commit changes) — that's the whole manual step, repeated each refresh.
  Still also try `mcp__remote-devices__update_artifact` on the dashboard
  (id: `sjkim-obsidian-dashboard`) as a same-session preview convenience,
  but the GitHub Pages URL is what he actually bookmarks and opens day to
  day now, not the Cowork artifact gallery.
- **Claude Code (local, on his Mac):** No proxy restriction here — write
  both files straight into `~/sj-dashboard-repo/`, then:

  ```bash
  cd ~/sj-dashboard-repo
  git add -A
  git commit -m "dashboard refresh $(date +%Y-%m-%d)"
  git push
  ```

  The remote's push URL already has his token embedded
  (`git remote -v` will confirm), so plain `git push` needs no credential
  prompt. GitHub Pages picks up the new commit and serves it within
  seconds — no separate "enable Pages" step needed, that's already on.

Either way, the live site is `https://thecross4u.github.io/sj-dashboard/`
(dashboard) and `https://thecross4u.github.io/sj-dashboard/daily_note.html`
(writer) — that's what to tell him to check, not "download the file."

## Sections

Default set, in display order. The user adds and removes these freely — check
memory first, and when they ask for something new, put it where it reads
naturally rather than appending to the bottom.

Page order (since 2026-08-15, the user asked for this specific sequence — don't
revert to appending new sections at the bottom):

| Order | Section | Source |
|---|---|---|
| 1 | KPI row | totals from the scan + live weather (client-side) + FX |
| 2 | 날씨 + 환율 (side by side) | live weather (client-side) + FX web fetch |
| 3 | 할 일 트래커 + 구글 일정 트래커 (side by side) | scan's open priorities + Calendar connector |
| 4 | 설교·목회 준비 트래커 + 기도 트래커 (side by side, since 2026-08-15) | scan's sermon pipeline (5 items only) + scan's prayer notes |
| 5 | 뉴스 트래커 | web fetch |
| 6 | 교계·목회 동향 트래커 | web fetch |
| 7 | 스크랩 트래커 + 독서 트래커 (side by side, since 2026-08-15) | scan's recent clippings + Readwise |

**노트 현황 (note-distribution bar chart) was removed entirely on 2026-08-15** —
don't rebuild it. The user still wants the total note count, but that already
lives in the KPI row's "전체 노트" tile, so nothing else needed to change
there. Drop the `folders`/`bigCollections` data arrays and their render code
if you find them lingering from an older copy of this file.

**Daily Note 작성 is no longer inline on this page.** It's a separate file,
`daily_note.html`, linked from a button in the top-right of the header
(next to 🌓). See `references/daily-note-writer.md` for how to build and
deliver it alongside the main dashboard.

**Daily Devotion (added 2026-08-16)** — a third file, `daily_devotion.html`,
linked from a button next to the Daily Note button (📖 Daily Devotion). It
lists that day's Bible readings from two lectionaries and lets him tap a
reference to open it in 개역개정 (Korean) or ESV (English) in a new tab.
This is a **snapshot page like the rest of the dashboard, not a live app** —
it must be rebuilt with that day's actual readings every time the dashboard
refreshes, or it'll silently show yesterday's (or last week's) passages.

Sources, fetched fresh each rebuild:
- **RCL (Protestant/Reformed):** `https://lectionary.library.vanderbilt.edu/`
  doesn't expose a clean per-date URL — the daily-readings page with a `#`
  date fragment is a client-side app WebFetch can't render. Instead
  `WebSearch` for `"Revised Common Lectionary readings <month> <day> <year>"`,
  which reliably surfaces a direct post URL like
  `.../2026/08/august-16-2026-proper-15-20/` — fetch that. Sundays give two
  tracks (Track 1 continuous OT, Track 2 tied to the Gospel) plus one epistle
  and one Gospel reading; weekdays are a single set. Show whatever the page
  actually has, don't force a Track 1/2 split on weekdays.
- **USCCB (Catholic daily Mass):** `https://bible.usccb.org/bible/readings/MMDDYY.cfm`
  is a clean predictable URL — no search needed, just format today's date.

Link construction (verified working 2026-08-16 — don't re-derive from
scratch, these exact patterns work):
```js
function krLink(book, chap, startVerse){
  return `https://www.bskorea.or.kr/bible/korbibReadpage.php?version=GAE&book=${book}&chap=${chap}&sec=${startVerse}&cVersion=SAENEW%5E&fontSize=15px&fontWeight=normal`;
}
function esvLink(query){
  return `https://www.biblegateway.com/passage/?search=${encodeURIComponent(query)}&version=ESV`;
}
```
- **개역개정** has to come from `bskorea.or.kr` (대한성서공회's own reader,
  `version=GAE`) — Bible Gateway and YouVersion (bible.com) both dropped
  개역개정 for licensing reasons; YouVersion's Korean catalog only has
  개역한글/새번역/KLB/등, not 개역개정. Don't waste a round-trip rediscovering
  this. The `sec=` param only takes a single starting verse (no end-verse
  parameter), so the Korean link jumps to the right verse but keeps
  scrolling; that's fine, don't try to fake a range.
- **ESV** comes from Bible Gateway, `version=ESV`, `search=` takes a full
  citation string including a verse range (`Genesis+45:1-15`) — this one
  does render the exact bounded range.
- Book codes confirmed for `bskorea.or.kr`: `gen`, `psa`, `isa`, `rom`,
  `mat` (English 3-letter abbreviations, lowercase). Others weren't tested;
  assume the same family (`exo`, `luk`, `joh`, `act`, etc.) but verify a new
  one with a quick `WebFetch` before trusting it silently.

Same lock-screen requirement as the other two pages (see Deliver below) —
copy the `#lockScreen` markup and unlock script verbatim, this page holds
the same public-repo exposure as the rest of the site.

Rules the user has already corrected at least once, so they're worth holding
onto on every rebuild:

- Sermon tracker shows **only upcoming** services, and only the **nearest 5**
  (2026-08-15: trimmed from "all upcoming" to a hard cap of 5 — completed ones
  were already excluded, but even the upcoming list got too long).
- Sermon status has a fourth value, **준비완료** (prep done, service still
  ahead) — added 2026-08-15, distinct from 완료 (the service already
  happened, `d < today`). The criterion is specifically whether the
  service's review/복습 **HTML** file exists (`vault_scan.py`'s `has_review`,
  now `.html`-extension-checked), *not* whether md+pptx+guide all exist —
  the user corrected this the same day it was first built, because a
  finished manuscript/slides/guide can still be sitting mid-edit, while the
  review HTML is written last, after everything else is actually done. Style
  it the same green `status-done` badge as 완료 (both mean "done", just a
  different kind), keep 준비중/미시작 as before.
- A habit-completion trend chart was explicitly removed and should not come
  back unless asked.
- Prayer tracker only shows 응답됨 (answered) prayers answered **this
  calendar month** — drop older answered ones from the list entirely rather
  than just de-emphasizing them. Re-derive the cutoff each rebuild (it moves
  every month).
- Weather hourly row shows ~8 hours ahead, not 12 — keep the live Open-Meteo
  fetch loop and the static offline-fallback array the same length.
- Church/ministry trend tracker: 뉴스앤조이 (Korea) and 미주뉴스앤조이 (US
  Korean immigrant church) were removed as source cards — don't re-add them.
  기독신문/한국기독공보 (Korea) and KCMUSA/아멘넷 (US Korean immigrant church)
  stay.
- Scrap/clippings tracker shows 8 items, not more.

## When a source fails

Some fetches will fail. Don't let a failure silently become an empty card:
render the section with a short, honest line about what happened and a link to
the source, the way the existing dashboard does for the Korean newspaper RSS
feeds. Then tell the user in your reply — they have opinions about which
sources are worth the trouble, and they can often confirm from their own
browser whether a feed works, which is information you can't get yourself.

Resist the urge to route around a block with a scraper or an alternate mirror.
When the fetch tools refuse a domain, that refusal is the answer; offer the
user a different source instead.

## If the user says scheduled refreshes have stopped

Check with `mcp__claude-code-remote__list_triggers` (or `update_trigger` on the
known id, which errors "not found" if it's gone) before assuming the vault
connection is the problem — the trigger itself can disappear silently (this
has happened once already), and a missing trigger looks identical to a stale
gallery artifact from its last run. If it's gone, recreate it with
`create_trigger` rather than just re-explaining the vault-connection
limitation; check memory for the last known cron schedule and prompt shape
first so the recreated one matches what the user asked for.

## Reference files

- `references/vault-map.md` — folder layout, parsing recipes, the commands that time out
- `references/data-sources.md` — every URL, what works, what's blocked
- `references/daily-note-writer.md` — the write-back form: template, insertion logic, platform limits
- `references/layout.md` — palette, card patterns, Korean-language conventions
- `scripts/vault_scan.py` — one-shot vault scanner, emits JSON
