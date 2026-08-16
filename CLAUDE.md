# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A two-page static HTML dashboard ("SJ's Dashboard") for a single Obsidian pastoral-ministry vault (`iCloud/obsidian/SJKim`). There is no build system, package manager, linter, or test suite — each file is a self-contained `.html` document with inline `<style>` and `<script>`. "Running" the app means opening the file directly in a browser (Chrome or Edge specifically for `daily_note.html`, see below).

- `index.html` — the dashboard itself: KPI tiles, sermon/task/prayer trackers, news and ministry-trend feeds, weather, FX chart, reading list, clippings.
- `daily_note.html` — a form that writes directly into today's Obsidian daily note via the File System Access API.

This repo is typically regenerated/refreshed by the `sj-dashboard` Claude Code skill, which knows the vault's folder layout and the shell commands used to pull fresh data from it. Prefer invoking that skill over hand-rolling a vault scan when the user asks to "refresh the dashboard" or similar.

## Working with these files

- No install, build, lint, or test commands exist — don't go looking for `package.json`/CI config, there isn't any.
- To preview a change, just open the file in a browser (`open index.html` on macOS) or use the `run` skill.
- `daily_note.html`'s save/folder-connect features require `window.showDirectoryPicker` (Chrome/Edge only); they silently no-op elsewhere.
- Both files start with a client-side numeric PIN lock (`lockScreen` div, checked in the final `<script>` block, unlocked state kept in `sessionStorage`). This is UI obfuscation, not real security — don't treat it as an auth boundary, and don't weaken/remove it without being asked.

## Architecture notes

**The two files duplicate their entire `<style>` block and color-token system on purpose.** Both use the same `.viz-root` custom-property scheme (`--surface-1`, `--text-primary`, `--series-1..8`, etc.) with three variants: light (`:root`), dark via `prefers-color-scheme`, and an explicit `data-theme="dark"`/`"light"` override toggled by `toggleTheme()`. When changing shared visual style (colors, KPI tiles, card/section layout, list/badge styles), edit both files identically — they are meant to look like one app split across two pages, cross-linked via the header (`index.html` → `daily_note.html` and back).

**`index.html` data is a static snapshot, not a live query.** Sections like sermons, open tasks, prayers, books, calendar events, and all news/ministry-trend feeds are plain JS arrays (`const sermons = [...]`, `const openTasks = [...]`, etc.) defined inline in the final `<script>` block, then rendered into the DOM by small `render*`/`forEach` functions right below their data. To update this content you either edit the arrays directly or regenerate the file via the `sj-dashboard` skill — there is no API call backing these sections.

**Weather is the one genuinely live section.** `wxFetchLive()` calls the Open-Meteo API client-side on load and every 30 minutes (`setInterval`), populating both the KPI tile and the hourly row; `wxRenderStatic()` is the fallback that renders the baked-in `wxHourly` snapshot if the fetch fails. The FX chart (`fxRates`), by contrast, is a static array rendered once into inline SVG by hand-built path/line/circle elements (no charting library).

**`daily_note.html`'s save flow reads and rewrites the vault file directly:**
- `dnConnectFolder()` calls `showDirectoryPicker` to grant access to the vault's `110. Daily notes` folder; the resulting handle is persisted in IndexedDB (`dn-dashboard-db`) via `dnSaveHandle`/`dnLoadHandle` so the connection survives reloads (permission still needs a one-click reconfirm each session — see `dnTryAutoReconnect`).
- On connect, `dnLoadTodayNote()` reads today's `YYYY-MM-DD.md` if it exists and pre-fills the form from it (via `dnSectionBody`/`dnParsePriorities`/`dnParseHabitChecks`/`dnFillTextarea`), so re-opening the page doesn't blank out already-saved content.
- `dnSaveToDailyNote()` either creates today's file from `dnBuildTemplate()` (the canonical daily-note markdown template — section headers here must match the regexes used for parsing/inserting) or loads the existing file, then merges form input into the right sections via `dnInsertIntoSection` / `dnInsertPrioritiesSection` / `dnSetHabitChecks`, which locate a section by a header regex and fill empty `- ` / `- [ ]` bullets before appending overflow lines. If you add a new form field, you need to update: the form field itself, `dnBuildTemplate()`'s template section, the insert call in `dnSaveToDailyNote()`, and the matching parse/fill call in `dnLoadTodayNote()` — all four are keyed off the same header regex and must stay consistent.
