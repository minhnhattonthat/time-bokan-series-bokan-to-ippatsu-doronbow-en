# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 3. Identity build next (phase 2 debug tool done 2026-11-13). No build yet.
- **Done:**
  - Step 0: dump pinned (`rom.sha1`, 23 files), pre-commit hook in `tools/hooks` (a failing test blocked a commit), guard blocks `sed -i`, `tools/skill.py` prints the skill path, smoke boots the original disc on `tools/pcsx` and a scripted Start skips the opening FMV to the title. Not tested: GUI keyboard input (headless run). Tools copied from desu-yo: `disc.py`, `tim.py` (+ `best_clut`, `png ... auto`), `tim_sheets.py`, `tim_survey.py`, `str_frames.py`, `strings_scan.py`, `vram.py`, `tbl.py`, `bps.py`, `romdiff.py`. New: `sjis_scan.py`.
  - Phase 1: `docs/re/disc.md` (22 tracks, 188 TIMs, 7 stage overlays, 6 STR movies, DA = CD audio), `text.md` (no encoding; only Shift-JIS is the memory card title at EXE 0x8FA60, byte-swapped words), `graphics.md` (every Japanese TIM element by screen, read zoomed). FMVs sampled every 3 s: spoken dialogue, no captions. `tests/test_recon.py` holds the layout and the single-string finding.
  - Phase 2: `tools/debug/warp_all.py` runs 54 scenes from cold boot, **54/54 ok** (2026-11-13), shots in `work/qa/warp/<scene>`, every final shot read on one sheet. Scenes: logo, movies, title, menu, demo, ranking table, options (rows, every value `optvals`, sound test = 20 songs + voice lines), every memory card message but the corrupt-save pair (`tools/mcd.py` blank/full/unformatted cards, `NOCARD=1`), continue prompt + taking it, 2P join (`P2=1` plugs pad 2), game over, cards/stages/clears/selects 1-7, `tour1-7` (GOD + shot held through each stage to its boss arena; stage 3's boss dies and MOVE03 plays; clear7 runs ending, staff roll, MOVE06). God mode = HP 0x800D7D4C pinned (`--god`). Map: `docs/re/state.md`. Tests: `tests/test_debug.py` (families, card/var scenes, card checksums).
- **Next (phase 3):** identity build: unpack Track 01 and rebuild it byte-identical, as a test (follow desu-yo's `tools/build.py`; `disc.py write_file` keeps LBAs). Then phase 4 extract (memory card title; FMV transcripts; staff-roll cells as in desu-yo `docs/re/cells.md`).
- **Not reached yet (phase 5/8 coverage, not blocking):** `KIHON` ポチっとな badge, ちょっと待ってね!, ◀メカをえらんで (no screen found that draws them); card messages カードがこわれてます / ロードに失敗しました (need a card with a damaged save); 体験版 stamp and ship-sheet name tags (likely unused). Details in `docs/re/state.md` §Not settled.
- **Open bugs:** none.
- **Waiting on the user:** all non-blocking, each an agent default carried over from desu-yo:
  - D8: burn English subtitles into the 6 FMVs. D9: official Tatsunoko names (Tonzra, Dokurobey, Doronbow...). D10: memory card title in full-width English.
  - D5: the ボカンと一発!ドロンボー logo stays Japanese (no official English logo known).
  - Earlier patch search: one web search, nothing found; romhacking.net not checked.
