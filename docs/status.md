# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool next (phase 1 recon done 2026-11-13). No build yet.
- **Done:**
  - Step 0: dump pinned (`rom.sha1`, 23 files), pre-commit hook in `tools/hooks` (a failing test blocked a commit), guard blocks `sed -i`, `tools/skill.py` prints the skill path, smoke boots the original disc on `tools/pcsx` and a scripted Start skips the opening FMV to the title. Not tested: GUI keyboard input (headless run). Tools copied from desu-yo: `disc.py`, `tim.py` (+ `best_clut`, `png ... auto`), `tim_sheets.py`, `tim_survey.py`, `str_frames.py`, `strings_scan.py`, `vram.py`, `tbl.py`, `bps.py`, `romdiff.py`. New: `sjis_scan.py`.
  - Phase 1: `docs/re/disc.md` (22 tracks, 188 TIMs, 7 stage overlays, 6 STR movies, DA = CD audio), `text.md` (no encoding; only Shift-JIS is the memory card title at EXE 0x8FA60, byte-swapped words), `graphics.md` (every Japanese TIM element by screen, read zoomed). FMVs sampled every 3 s: spoken dialogue, no captions. `tests/test_recon.py` holds the layout and the single-string finding.
- **Next (phase 2):** warp tool to every screen from a cold boot: title, options (levels, credit, sound test songs + voice test, key config), memory card screens, ship select (all 9 ships, 整備中), each stage card, stage, boss, game over, ranking, continue, the 6 movies, ending and staff roll. Start from the EXE debug strings at 0x2D30 (`STAGE NO`, `DIFFICULT`) to find the stage variables; copy desu-yo's `tools/debug/warp.lua`, `warp_all.py`, `scenes.lua`, `primdump.lua` and adapt. Phase 2 must also settle which "guess" rows in `graphics.md` show at all (trial advert `TK_00/01`, 体験版 stamp, ship-sheet name tags).
- **Open bugs:** none.
- **Waiting on the user:** all non-blocking, each an agent default carried over from desu-yo:
  - D8: burn English subtitles into the 6 FMVs. D9: official Tatsunoko names (Tonzra, Dokurobey, Doronbow...). D10: memory card title in full-width English.
  - D5: the ボカンと一発!ドロンボー logo stays Japanese (no official English logo known).
  - Earlier patch search: one web search, nothing found; romhacking.net not checked.
