# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator next (phase 7 insert/fit/check done 2026-11-14).
- **Phase 7 (done 2026-11-14):** phase 6 review had 0 Critical/Important; Minors 1, 4, 5, 6 applied, the rest in
  `docs/polish.md`. `tools/build.py` (no flag) builds the English disc: `gfx.english_items` (rects widened inside the
  drawn box, CLUT row from budgets; song rects take the whole plate, white on each row's own plate colour),
  `gfx.no_card` (one 128x40 canvas cut over the two TITLE4 quads), `credits.english` (staff roll repacked, page table
  rewritten in place, D15, `docs/re/credits.md`), card title via `script_text.encode`, movies via
  `fmv_burn.burn_all(tl_check.subs)`. Gate `tools/build_check.py`: **0 findings** (51253 sectors in 37 files + 6
  movies; EXE changes only in the page table and card title, romdiff). `check.py` 41 passed (new: credit pack test,
  English build passes build_check). Smoke ok. Build sha1 (Track 01) `41e4acc0d409ab3b76d8d195943814b439640434`.
  Warp on build/ 8/8 ok (title, menu, options, sound, memcard_nocard, card1, staff, movie01; `work/qa/warp_en`):
  English shows on the title menu, options, stage card, a movie subtitle and the staff roll.
- **Phase 8 must look at (seen on row_sheet crops / first shots, not fixed):**
  - Movies: requant on most subtitled frames, qscale +6 to +12 (MOVE04 1390 of 1472). Check blockiness; if bad,
    re-quantise only macroblocks off the text, as phase 5 planned.
  - Inks: title menu and options rows come out striped/low contrast (fill per row off a gradient); `hud.gameover`
    stripes (desu-yo used `Inks(15, 10)`); ship names (e.g. `ship.rakuda`) pale on pale. Add `gfx.ROW_INKS`.
  - `st5.stop`: the clear leaves a flat band on the steel texture (inpaint, desu-yo `gfx.inpainted`).
  - `build_check.INK_NEAR_RECT` lists rows whose leftover hits were read as art (title panel frame, rnk skull, voice
    side marks, song bevels, st5 steel, ship art): confirm in game. Staff roll page 15 head is drawn in blue (game CLUT).
  - Sound scene final shot shows "It's under repair!" on the options list: check which row that is.
- **Done:**
  - Step 0: dump pinned (`rom.sha1`, 23 files), pre-commit hook in `tools/hooks` (a failing test blocked a commit), guard blocks `sed -i`, `tools/skill.py` prints the skill path, smoke boots the original disc on `tools/pcsx` and a scripted Start skips the opening FMV to the title. Not tested: GUI keyboard input (headless run). Tools copied from desu-yo: `disc.py`, `tim.py` (+ `best_clut`, `png ... auto`), `tim_sheets.py`, `tim_survey.py`, `str_frames.py`, `strings_scan.py`, `vram.py`, `tbl.py`, `bps.py`, `romdiff.py`. New: `sjis_scan.py`.
  - Phase 1: `docs/re/disc.md` (22 tracks, 188 TIMs, 7 stage overlays, 6 STR movies, DA = CD audio), `text.md` (no encoding; only Shift-JIS is the memory card title at EXE 0x8FA60, byte-swapped words), `graphics.md` (every Japanese TIM element by screen, read zoomed). FMVs sampled every 3 s: spoken dialogue, no captions. `tests/test_recon.py` holds the layout and the single-string finding.
  - Phase 2: `tools/debug/warp_all.py` runs 54 scenes from cold boot, **54/54 ok** (2026-11-13), shots in `work/qa/warp/<scene>`, every final shot read on one sheet. Scenes: logo, movies, title, menu, demo, ranking table, options (rows, every value `optvals`, sound test = 20 songs + voice lines), every memory card message but the corrupt-save pair (`tools/mcd.py` blank/full/unformatted cards, `NOCARD=1`), continue prompt + taking it, 2P join (`P2=1` plugs pad 2), game over, cards/stages/clears/selects 1-7, `tour1-7` (GOD + shot held through each stage to its boss arena; stage 3's boss dies and MOVE03 plays; clear7 runs ending, staff roll, MOVE06). God mode = HP 0x800D7D4C pinned (`--god`). Map: `docs/re/state.md`. Tests: `tests/test_debug.py` (families, card/var scenes, card checksums).
  - Phase 3: `tools/build.py --identity` rewrites every Form 1 file through `disc.write_file` and every TIM (188) through `tim.pixels/with_pixels`; Track 01 and the cue match `rom.sha1`, audio tracks hard-linked (`tests/test_build.py`, also guards write_file touches only its own sectors). Identity build passes `emu.py --smoke`.
  - Phase 4: no script bytes beyond the card title, so "roundtrip" is `tests/test_script.py`: all 188 TIMs roundtrip through `pixels`/`with_pixels`; each is in `script/graphics.tsv` (154 rows over 37 TIMs, every rect non-blank) or `script/no_text.txt` (151), never both; `script/text.tsv` card title decodes from and re-encodes to the EXE's 34 bytes (`tools/script_text.py`); `script/fmv/MOVE01-06.tsv` timed dialogue with speakers for all 6 movies. Rects measured with `tools/ink_boxes.py` + `tim_ruler.py`, every row checked on `gfx_script.py sheet` crops (3 sheets, fixes re-checked).
  - Phase 5: marker disc (`build.py --marker`) boots and passes **55/55** warp scenes (2026-11-14); zoomed reads of title, options, sound test (song and voice rows), memory card, ship select, stage card, staff roll and a movie frame: every rect shows its row number, the movies show the numbered test line, no unmarked Japanese seen on those screens outside the kept logo. STR here is **version 3** (DC coded by difference): `tools/mdec.py` now parses and re-encodes v3 bit-exact (`tests/test_mdec.py`); movies are 640x240, so `fmv_burn.py` draws on a 320-wide canvas stretched 2x. Font spike (`build.py --spike`, `script/spike.tsv`, test lines, not translations) shown in game: title menu, options, ship name, card menu, stage 5 card; classes decided (D11, `gfx.CLASSES`). Width gate: `gfx.typeset` raises on overflow; `script/budgets.tsv` holds per-row drawn boxes and CLUT rows from GPU dumps of all 54 original scenes (122 quad, 13 sibling, 15 none; `docs/re/credits.md`). Staff roll mapped: page table at `BOKAN.EXE` 0x91854 (45 groups), 93 lines with Japanese and pieces in `script/credits.tsv`, both held to each other by `tests/test_gfx.py`. New tools: `gfx.py`, `prims.py` (+ ordering-table walk `live()`), `budgets.py`, `credits.py`, `fmv_burn.py`, `mdec.py`, `fmv_sheet.py`, `debug/primdump.lua`; scenes `staff` (shot every 60 frames) and a 16-shot burst on `card1-7`.
  - Phase 6: all English in `script/en/`: `graphics.tsv` (124 rows, every non-keep, non-credit row; 3 `canvas:` parts drawn by `card.p_memory`),
    `credits.tsv` (93 lines by `script/credits.tsv` n, `|` between parts; 8 icons empty), `fmv.tsv` (all 131 rows of
    6 movies, ` || ` splits a long row's time by length, 9 such), `text.tsv` (card title 「ＢＯＫＡＮ！　ＤＯＲＯＮＢＯＷ」,
    D14). Gate `tools/tl_check.py` prints OK (`tests/test_translation.py`, 4 tests; `check.py` 39 passed): ids,
    ASCII, glossary terms and Avoid list, -sama for 様, pixel widths per class against `budgets()` (rect start to the
    drawn quads' right edge, rect height; overrides for the no-card canvas, `hud.wait`, `rnk.*`, song plates 206 px),
    credit rows <= 296 px, subtitles <= 296 px and 3 lines (0 at 3 lines now), <= 30 chars/s. Songs moved to Jersey 15
    without quotes so all 20 titles fit whole (D12); title calls romanized (D13). Glossary gained 三悪 trio,
    おしおき, Akudaman, Ojamaman, Bicycle, Banpre Kikaku. New docs: `synopsis.md`, `style-reference.md`,
    `translator-brief.md`, `reviewer-brief.md`, `polish.md`; `tools/pairs.py` writes `work/qa/story/chapters/`
    (story, labels, credits) for review and the phase 9 story pass.
  - Review: **independent**, `codex exec` (codex-cli 0.167.1, read-only) on the three chapter files. Round 1: 0
    Critical, 14 Important (voice flattened in 8 movie lines, "Key Config"/"Launch Prep" abbreviations, ポチっとな
    shortened, voice.11/12, credit 43), all fixed except voice.12 (no width; to polish) and credit 43 kept as "Color
    Design" (usual credit term; "Paint Check" added). Round 2 on the fixed files: 0 Critical, 0 Important, all three
    Approved. Reports in gitignored `work/qa/review/`. Minors in `docs/polish.md`.
- **Phase 6 limits:**
  - Translated by one agent (Orca refuses nested workers), not in batches; 124 + 93 + 131 rows.
  - No English seen in game yet: fit is by measurement only. 15 rows have rect-only budgets (never drawn), voice rows
    are held to their own uv quads (a table phase 7 could widen), and stage-card rows to their rects.
  - Nobody listened to the movies; `?` rows are listed in `docs/polish.md`.
- **Next (phase 8):** follow desu-yo's phase 8 (`qa_sheets.py`, `row_cover.py`, `rect_spill.py`, `qa_gate.py`):
  full warp tour on build/ (all 54 scenes + `--prims` for text coverage), contact sheets per chunk, verdicts by a
  fresh read-only pass or `codex exec` (no nested workers), every graphics row zoomed in a cold-boot shot (options
  rows in both CLUT rows), `inkbox.py` on menus, fix the list above. Subtitle times are still Whisper's (not exact
  frames); MOVE04.2's split should land on the voice change.
- **Phase 5 limits:**
  - Review was by the implementer in a separate read pass, not independent (no codex run). Screens read zoomed: about 12; the other scenes only passed their state checks.
  - Burning the 3-line marker forced a qscale rise on every subtitled frame (+7 to +15; base q 4-8), so the frames go blocky. Real subtitles are shorter; phase 7 must measure the cost and, if needed, re-quantise only the macroblocks off the text or cap at 2 lines (`fmv_sheet.py --slack`: median 736-1332 bytes free per frame).
  - 15 rows were never drawn in a dump (`source` none in budgets.tsv): their limit is the rect, a guess. Ship names and tags of the six ships the select scenes never offer use `sibling` boxes.
  - Inks: `typeset` takes the CLUT row the game draws a row with (budgets `clut`), but rows drawn with two rows (options: normal and highlighted) need checking in both; the card menu's LOAD came out dark and thin in the spike: phase 7 needs per-row inks (desu-yo `ROW_INKS`).
  - `sel.join_ok`'s rect stops before the English "K" of 参加OK; phase 7 grows it or keeps "OK" and replaces 参加 only.
  - The no-card message is two 64x40 quads side by side (canvas); title menu is one 144x80 quad; options rows are 240x32 quads: English can use those boxes, not only the rects (`docs/re/credits.md`).
- **Phase 4 limits (carry into 6-7):**
  - Rects are by eye/ink scan; `card.p_*` pieces (TITLE4 top-left and row y102) and `hud.wait` split by eye. Staff roll rows `end0.r*`/`end1.r*` are glyph-sheet strips, not credit lines: translate by line from `script/credits.tsv` (phase 5). Readings of name kanji 小(?) in `end1.r04` and `st5.sign_small` 人命尊重(?) unsure. `wep.sfx` is ボ ー | カ ン in two columns; how they combine is phase 5.
  - FMV text not ear-checked: faster-whisper large-v3 (CPU) drafts in `work/fmv/`, corrected from franchise knowledge (三悪 was heard as 山岳, hero names, アラホラサッサー), raw reading kept as `was:`; rows with `?` are guesses, speakers inferred from speech style. Second pass (`tools/fmv_clip.py`) on MOVE04 103-140 s and MOVE06 5-30 s. MOVE06 (Dokurobey, logprob -1.0) is weakest. Hallucinated "ご視聴ありがとうございました" tails dropped. Times are Whisper's; phase 7 takes exact frames.
  - Review: same-agent read-only re-pass of crops, not independent (no codex run).
- **Not reached yet (phase 7/8 coverage, not blocking):** `KIHON` ポチっとな badge and ◀メカをえらんで, `sel.gameover`, `wep.sfx`, `st5.safety`, boss 5 plates and 怒 (no dump drew them); card messages カードがこわれてます / ロードに失敗しました (need a card with a damaged save); 体験版 stamp (likely unused); six ship names and seven tags (ships the select scenes never offer). ちょっと待ってね! (`hud.wait`) was drawn. Details in `docs/re/state.md` §Not settled, `docs/re/credits.md`.
- **Open bugs:** none.
- **Waiting on the user:** all non-blocking, each an agent default carried over from desu-yo:
  - D8: burn English subtitles into the 6 FMVs. D9: official Tatsunoko names (Tonzra, Dokurobey, Doronbow...). D10: memory card title in full-width English.
  - D5: the ボカンと一発!ドロンボー logo stays Japanese (no official English logo known).
  - D12: song list in Jersey 15 without quotes. D13: title calls romanized. D14: card title 「ＢＯＫＡＮ！　ＤＯＲＯＮＢＯＷ」.
  - Song titles and credit readings in `docs/polish.md` have no official source; say if you know better ones.
  - Earlier patch search: one web search, nothing found; romhacking.net not checked.
