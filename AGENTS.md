# Time Bokan Series: Bokan to Ippatsu! Doronbow (PS1) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `python tools/skill.py` prints its folder; `$SKILL` = that folder). Read its SKILL.md before ROM, text or QA work.
Reference project: `../time-bokan-series-bokan-desu-yo-en` (sequel, finished; same no-encoding setup). Reuse its tools and rulings before writing new ones.

## Commands (run from repo root)
- Hooks:    `git config core.hooksPath tools/hooks` (once per clone)
- Check:    `python -X utf8 tools/check.py` (tests + lint; the pre-commit hook runs this)
- Dump:     `python -X utf8 tools/check_rom.py` (checks the dump against `rom.sha1`)
- Extract:  `python -X utf8 tools/disc.py x "rom/Time Bokan Series - Bokan to Ippatsu! Doronbow (Japan) (Track 01).bin" work/x` (Form 1 files; STR stays on disc)
- Survey:   `python -X utf8 tools/tim_sheets.py work/x work/recon/tims`; `tools/tim.py png FILE OUT.png auto` (first real CLUT row); `tools/str_frames.py BIN work/recon/str --every 3`; `tools/sjis_scan.py [--swap] FILE..`
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py "rom/Time Bokan Series - Bokan to Ippatsu! Doronbow (Japan).cue" --out work/qa/smoke --route tools/routes/boot.txt --smoke` (build output once phase 3 exists)
- Build, Warp, Release: not written yet (phases 2, 3, 9); follow desu-yo's `tools/build.py`, `tools/debug/warp_all.py`, `tools/release.py`.
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original disc: `rom/` (gitignored; 22 .bin tracks plus .cue, SHA-1s in `rom.sha1`). Only Track 01 changes. Emulator: this repo's own PCSX-Redux in `tools/pcsx/` (version.json: 30282.20261104.5; gitignored). BIOS: `tools/bios/scph5500.bin`. Savestates: `work/states/`.
- Text: no text encoding exists except the memory card title; every string is a TIM region or spoken FMV audio. RE notes: `docs/re/README.md`. Glossary: `glossary.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the plugin types (translator, reviewer, visual-qa, playtester, graphics), never general-purpose. In an Orca one-shot run nested workers are refused: do reviews yourself in a fresh read-only pass, or with `codex exec`.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Gotchas: Japanese games confirm with circle. Start at frame 1200 skips the opening FMV to the title. Many TIMs keep a magenta placeholder in CLUT row 0. `disc.py verify` reports "bad 1" on the clean dump (LBA 89165, in no file). `/DA/*.DA` point into the CD audio tracks. `disc.py write_file` keeps LBAs, so a replacement must keep each file's exact size.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
