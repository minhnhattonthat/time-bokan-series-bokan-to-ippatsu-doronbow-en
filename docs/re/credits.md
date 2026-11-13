# Staff roll and drawn-quad budgets (phase 5)

## How the roll is built (verified)

The ending (task 80031020, `docs/re/state.md`) draws the staff roll in the lower band as sprites (GPU packet: E1 draw
mode then SPRT, 6 words, `tools/prims.py`) cut from the glyph sheets `CHRPLY2/END_STF0` (anime staff, cast) and
`END_STF1` (game staff, copyrights). Role names are whole strips (`総監督・絵コンテ` is one 144x16 piece); personal names
are mostly 16-32 px cells, some shared between names (e.g. 吉田 in 吉田義樹 and 吉田文恵).

**Page table:** `BOKAN.EXE` 0x91854-0x91FA0 (RAM 0x800A1054-), 45 groups, each a u32 count then count 8-byte entries
`u8 u, v, x, y; u16 w, h` (x, y: the piece's place on the page; read by `credits.pages()`). Groups 0-23 are the credit
pages in roll order (0-14 sample END_STF0, 15-23 END_STF1), 24 the copyright page (END_STF1), 25 the four face icons
(END_STF0), 26-44 one-piece ending art frames (no text). Which sheet a page samples is not in the table; the code picks
it (not traced). After the table, 0x91FA0: thirteen 20-byte records (`12, 496..499, 0, pointer 0x800A0CC4.., 2` then
pointers into 0x800A17C8..): **guess** page timing / sprite animation scripts, not decoded.

**Lines:** `script/credits.tsv`, 93 lines in order of first appearance (n, kind, jp, screen y, pieces
`SHEET:u,v,w,h@dx`). Taken from the `staff` warp scene (a shot every 60 frames, `warp_all.py --prims staff`) by
`tools/credits.py lines`: per frame, only packets on an ordering-table chain (`prims.live`), grouped by y and colour,
split at gaps over 48 px. Japanese read by eye from `credits.py sheet` (each line composed from its pieces, read zoomed);
`八郎．N` is as drawn. `tests/test_gfx.py` holds the table and the lines to each other: every page line is a
credits.tsv line and every credits.tsv line is on a page; nothing unmatched but the 19 art frames.

**For phase 7:** English credit lines need new strips in END_STF0/1 (space freed by the Japanese cells) and page entries rewritten in place (each page keeps its entry count, so a line with more
pieces than its page has must be drawn as fewer, wider pieces). Six lines join a role and its first names on one row
(`role+name` kind); they sit at one y in the table.

**English (phase 7, `credits.english`):** both sheets cleared but the icons (face icons, seahorse), each line's parts
lettered flat (D15) in the commonest ink of its Japanese cells, shelf-packed (`credits.pack`) into the sheet its page
samples (pages 0-14 END_STF0, 15-24 END_STF1), and the page entries rewritten in place: a line with spare entries
repeats its last part, one with too few joins its tail into one strip. Screen x = page x + 32 (staff dumps), so a line
must end by page x 276; two lines at one y slide apart (right one right, then left one left). The page pointers sit in
12-byte records at RAM 0x800A1C68 (`ptr, 2, 0`); the per-page sheet choice is not there and was not traced.

## Drawn-quad budgets

`warp_all.py --prims` dumps RAM and VRAM at every shot; `tools/prims.py rows` matches every textured packet to the
TIM in VRAM (by pixel content, so a file loaded elsewhere is still found) and to `script/graphics.tsv` rows;
`tools/budgets.py` writes `script/budgets.tsv`: per row the drawn texel boxes (`uv`, TIM pixels), screen place, and the
CLUT rows drawn with. All 54 scenes on the original disc (2026-11-14): 122 of 150 non-keep rows drawn (`quad`), 13
inferred from sibling slots (`sibling`: ship names in SELNAME's 32-row slots, tags at 0,240,80,16 in every ship sheet),
15 never drawn (`none`): `logo.trial`, the damaged-card pieces `card.p_broken/temasu/save/load/failed`,
`sel.gameover`, `hud.pochitto`, `hud.pick_mecha`, `wep.sfx`, `st5.safety`, the boss 5 plates and 怒, `end1.r09`.

Findings the budgets show:
- The title menu (スタート/オプション/メモリーカード) is one 144x80 quad (TITLE3 112,176): English may use the whole box.
- Options rows are 240x32 quads, each drawn with two CLUT rows (normal and highlighted, 1 and 2): English must read
  in both.
- The no-card message is two 64x40 quads side by side (TITLE4 32,0 and 40,40): line 1 ・メモリー + カードが, line 2
  差されて + (い)ません. English is one 128x40 canvas cut in two, as desu-yo's GAME OVER banner.
- Only three ships (Sharekobe Mecha, Sharekobe Buggy, Gaikottsu) are offered in the select scenes, so the other six
  ship names and seven tags were never drawn; `sibling` boxes stand in.
- No sprite cell table in desu-yo's format (`u32 n`, 12-byte parts) exists in this game's EXE or overlays.
