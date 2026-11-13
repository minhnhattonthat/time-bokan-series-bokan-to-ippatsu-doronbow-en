# Game state and flow

Addresses are RAM. `BOKAN.EXE` loads at 0x80010000 (file offset = addr - 0x8000F800). Stage overlays `BOKAN1-7.BIN`
and `MOVIE1.BIN` load at 0x80158904 (file offset = addr - 0x80158904; found in a stage-3 RAM dump).
**Verified** = read in the disassembly and seen at run time by `tools/debug/` (warp.lua, scenes.lua, tasklog.lua).

## Tasks (verified)

No single main-state variable: a task runner (8002EFB4, called every frame) runs 3 groups x 6 slots from 0x8010CBB4,
group stride 0xF4, slot stride 0x28: +0 u16 delay, +2 u16, +4 function (0 = free; kill = 8002ECE8 writes 0), +8 the
task's own state word (handlers get a0 = slot+8), +0xC argument. Create = 8002ED18(a0 group, a1 function, a2 delay).
0x800CBD80 holds the slot being run. `tools/task_spawns.py` lists every create call; `tools/debug/tasklog.lua` logs
slot changes. The screen is group 0 slot 0 (`W.TASK` 0x8010CBB8, its state `W.SUB` 0x8010CBBC):

| Function | Screen | Notes |
|---|---|---|
| 80016F1C | Banpresto logo | then movie id 0 |
| 80019D20 | movie (MOVIE1 overlay) | arg = id; Start ends it once playing (ignored while the stream starts). After it: id 0 MOVE01 -> title; 1 MOVE02 -> 8002DB78 -> ship select; 2 MOVE03 -> 80021918 -> ship select; 3 MOVE04 then MOVE05 -> ending; 4 -> ending; else (5, MOVE06) -> 8002B344 |
| 8001751C | title | state 0-9 logo build, 0xA press start (900-frame idle -> 0x15 demo), 0xB menu, 0x14 start chosen. Start in 0xA works only after the press-start object is up (flag 0x40000000 in 0x800D7C64); it then sets 0x00F00000 and the task goes to 0xB |
| 8001A0D8 | options | state 0x14 = menu up. Cursor 0x800D7C70, rows 1-7 (1 level, 2 credit, 3 sound test, 5 shot key, 6 bomb key, 7 EXIT; down skips 4, the キーコンフィグ label). Sound value 0x800D7C74 (right steps it; code bounds 0x33 and 0xA). 0x800D7C80 also changes per row |
| 8001D50C | memory card | menu セーブ/ロード/EXIT (`TITLE4`); state 0xB menu. No card attached in emu.py: circle on セーブ showed no message in 60 frames (not yet read) |
| 80020C4C | ship select | 0x13 choosing (right moves; 5 distinct ships seen over 9 rights on stage 1), circle -> 0x14 -> 0x1E -> card. 参加OK panel for 2P; pad-2 Start/circle via `W.tap2` changed nothing (not solved) |
| 80027850 | stage card (`TI_ST<n>`, `TAI_<n>`) | follows `STAGE` |
| 8002DDFC | stage play | |
| 8002E28C | attract demo | cycles stages 1-3 (8002E0FC); RECDATA files hold zeros |
| 800286BC | attract ranking (`RNK`) | after the demo |
| 8002BBB0 | game over / end of game | `OVERLOG` GAME OVER, ranking; after MOVE06 too |
| 80031020 | ending + staff roll (`END_*`) | about 12,700 frames, then movie id 5 |
| 8007F058/8007F160/8007F594 | debug print and debug stage select (R1/L1 stage, L2/R2 difficulty) | never spawned in retail (no caller) |

## Variables

| Address | Size | Meaning | |
|---|---|---|---|
| 800CBE7C | u32 | stage 1-7 (debug print `STAGE NO`; stage table 8009D390, 0x24 per stage) | verified: written during ship select, the card and stage follow it |
| 800CBF88 | u32 | difficulty 0-3 (`DIFFICULT`) | verified (1 after options default, 2 in demo) |
| 800CBDB0 / 800CBDB8 | u16 x2 | pad held / edge, 1P then 2P: 0x800 Start, 0x20 circle, 0x40 cross, 0x4000 down, 0x1000 up | verified |
| 800D7C64 | u32 | title/menu event bits (0x40000000 press start up, 0x00F00000 menu open) | verified |
| 800D7C68 | u32 | copy of the title/options task state | verified |
| 800D7C70 | u32 | title menu cursor 0 start, 1 options, 2 memory card; options row 1-7 | verified |
| 801490FC | s32 16.16 | scroll Y (`SCROLL Y`): counts down from ~64900 on stage 1, holds still at a mid-boss | verified |
| 800D7D28 | u8 | `PLY0 CND` (debug print) | not used yet |
| 800D421D | u8 | 3 at stage start, falls with hits: a HUD copy, the death check never reads it | verified |
| 800D7D28 | struct x2 | player structs, stride 0x80 (debug print PLY0 CND/CNDO/ACTCND/TYPE INF1): +0 CND, +1 CNDO, +2 ACTCND (3 bomb, 4 dying/dead), +6 TYPE INF1 (1 after a bomb: any hit kills), +0x24 s32 HP (0x2000 full, -1366 a hit) | verified: hit code 80046AC0 kills when TYPE == 1 or HP <= 0; `GOD` pins HP and the stage tours survive |
| 800CBDE4 | s16 | PLY NUM: ships in play (1 -> 0 at death) | verified |
| 800CBEA0 | u32 x2 | PLY0 STAT (15 alive, 0 dead) | read at run time |
| 800CBE90 / 800CBF98 | u8 | options level (0-3) / credit setting; game start (8002DB78) copies credits to 800CBE98 | verified (RAM search on the options screen) |
| 800CBE98 | u8 | credits left: the CONTINUE? prompt (8003EEA4) takes Start from pad edge 800CBF30 + 2*player and decrements it | verified (`continue` scene) |
| 801490FC boss values | | scroll Y where each stage's boss arena holds (tours): 1 59599, 2 61586, 3 16904, 4 61336, 5 62197, 6 62884, 7 61336 (fixed scroll, looping clouds) | verified |

## Stage clear (verified)

A stage's clear object (in its overlay) runs when the boss dies:
- stages 1, 2, 4, 5, 6: `STAGE` + 1, then 80021918 (ship select for the next stage);
- stage 3: `STAGE` = 4, byte 0x800CBF70 = 0xFF, movie id 2 (MOVE03, then ship select);
- stage 7: movie id 3 (MOVE04, MOVE05, ending, staff roll, MOVE06, game-end screen).

`W.call(fn, a0)` (warp.lua) runs a game function from task context: it writes an 8-instruction stub into the dead
debug-print strings at 0x80012530 and starts it in a free group-0 slot; the stub kills its slot and tail-jumps to fn.
`scenes.lua` `clear(n)` replays the clear object's writes and call. Verified from cold boot for stages 1, 3 and 7.

## Controls and hardware (verified)

Circle shoots, cross is the bomb (ACTCND 3, then TYPE INF1 = 1: one hit kills, so GOD does not cover it), L1/R1
spin the ship, Start pauses (2P too). Stage scroll holds while a mid-boss lives (under 2000 frames with circle held)
and for good at the boss. PCSX-Redux leaves pad 2 unplugged (`PCSX.settings.pads[2].Connected`): warp.lua's `P2=1`
plugs it in; `NOCARD=1` pulls card 1 (`PCSX.settings.emulator.Mcd1Inserted`). `L.press` queues: a long hold delays
every later press, so scenes hold in short chunks when they press again after.

Options rows (verified, cursor forced to 4 by poke): 4 is the キーコンフィグ label, which the cursor code (8001A42C)
always skips. The sound test row runs 0x00-0x13 songs (`OPTI_03-05`) and 0x14 up the voice lines with face icons
(`OPTI_06`): the `sound` scene shoots them all.

Memory card screen (`TITLE4` messages), by card (`tools/mcd.py`): blank: save アクセス中 -> セーブOK!, load ->
データがありません; save then load -> ロードOK!; full (15 dummy blocks) -> 空き容量が足りません; unformatted -> フォーマット
されてません, circle -> フォーマットしますか? YES/NO (right = YES, 0x800D7C74 = 0) -> format and セーブOK!; no card ->
差されてません. Sub-states: 0xB menu, 0xD access, 0xE/0x13 message, 0x10 format prompt.

## Not settled yet

- `KIHON` ポチっとな badge, ちょっと待ってね!, ◀メカをえらんで: not seen in any scene (continue respawns straight into the
  stage; 2P join mid-stage shows no prompt; L1/R1 only spin the ship). The 2P HUD's ゲームオーバー shows in every
  1P stage shot (it alternates with PUSH! START). Phase 5 marker build: find who draws those KIHON cells.
- Memory card: カードがこわれてます and ロードに失敗しました (corrupt save) not reached; needs a card with a damaged save.
- Graphics guesses: `TK_00/01` (trial advert) are referenced by no code: never shown. The 体験版 stamp and the
  ship-sheet name tags are still open.
