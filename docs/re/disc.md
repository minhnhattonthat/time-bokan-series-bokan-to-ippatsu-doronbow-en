# Disc layout

Game: Time Bokan Series: Bokan to Ippatsu! Doronbow (SLPS-00609). Banpresto (Eleven credited in the staff roll),
PlayStation, 1996-11-29, 1-2 players, vertical-scrolling shooter: the Doronbow gang against the Time Bokan heroes.
Prequel to Bokan desu yo (`../time-bokan-series-bokan-desu-yo-en`, finished; its tools and rulings are this repo's
reference). A Saturn "Complete Version" (1997) exists; no English release of either.

**Verified** by `tools/disc.py list`, `tools/tim.py scan work/x` and `tests/test_recon.py` unless marked.

- 22 tracks: Track 01 MODE2/2352 data (89,166 sectors), Tracks 02-22 CD audio.
- `/DA/*.DA` (21 entries: SELECT, MBOSS1-3, STAGE1-7, BOSS1-5, BOSS61, BOSS62, LASBOSS, ENDING, DAMMY) point past
  Track 01's end into the audio tracks: music, never rewritten. **Guess:** no speech in them (names are BGM slots).
- `disc.py` (from the desu-yo repo) reads the ISO9660 tree and rewrites form 1 files in place with fresh EDC/ECC.
  Files keep their LBA. `disc.py verify` reports "bad 1" on the clean dump (LBA 89165, the track's last sector,
  past every file): that is the baseline, as in desu-yo.
- Boot: `SYSTEM.CNF` -> `SLPS_006.09` (4 KB loader) -> `BOKAN.EXE` (772,096 bytes). Memory card save name
  `BISLPS-00609BOKAN` (EXE 0x1CB8).

| Path | Count | What it is |
|---|---|---|
| `BOKAN.EXE` | 1 | main program; SDK and debug strings, one Japanese string (card title, `text.md`) |
| `BOKAN1-7.BIN` | 7 | one overlay per stage; starts with a pointer table and the stage's file names (`\ST3\BG\...`) |
| `MOVIE1.BIN` | 1 | movie player overlay (names `\STR\MOVE0n`) |
| `RECDATA1-3.DAT` | 3 | 21,600 bytes of zeros each. **Guess:** demo input records, empty on this disc |
| `CHRPLY/` | 26 | title, menus, ship select, HUD (`KIHON`), ranking, ships; all TIMs |
| `CHRPLY2/` | 28 | ending art and staff roll, options, sound test, stage title cards (`TI_ST1-7`), stage intro silhouettes (`TAI_1-7`) |
| `ST1-7/BG, ST1-7/ENM` | 134 | stage backgrounds, enemies, bosses, hero cut-ins |
| `SOUND/SE1, SE2` | 40 | VAB banks (`VOICEA/B` = in-game voice samples, `BOSS_*`, `SAB_*`, `TIME_SE`) |
| `STR/MOVE01-06.STR` | 6 | MDEC video with XA audio, form 2, 83,074 sectors in all |

188 TIMs: 185 4 bpp (16 CLUT rows each), 2 8 bpp (`TITLE1B`, `TITLE2`), 1 16 bpp (`BPMARK`, Banpresto logo). Every one
is a plain TIM at offset 0, 33,312 bytes for a 256x256 4 bpp page, no trailing bytes.

## Compression

None on the images (all parse as TIMs with no tail). The overlays and EXE were not checked for embedded TIMs.

## Free space

None needed so far: graphics are replaced at the same TIM size, so no file moves. Re-encoded FMV must fit each
STR file's sector count, as in desu-yo.

## Movies

| File | Sectors | Content (3 s samples, `tools/str_frames.py`) |
|---|---|---|
| MOVE01 | 15,551 | opening: "The Time Bokan!" (English), the gang in silhouette, heroes, title logo. Spoken |
| MOVE02 | 12,919 | Doronbow and Dokurobey (skull) briefing, mecha line-up. Spoken |
| MOVE03 | 13,111 | the gang at the base, Boyacky's plan. Spoken |
| MOVE04 | 21,159 | the gang in the cockpit during a battle. Spoken |
| MOVE05 | 12,663 | the gang in the desert, sunset. Spoken |
| MOVE06 | 7,671 | ending: the gang flies off, skull explosion, "THE END" (English) |

No burned-in Japanese captions in any sampled frame; the only drawn text is the English "The Time Bokan!", the title
logo and "THE END". The story is in the spoken Japanese, as in desu-yo (its D7: burned-in English subtitles).

## Debug leftovers (phase 2)

`BOKAN.EXE` 0x2D30-0x2E7C: a debug display (`V SYNC TIME`, `PLY1 BUL NUM`, `ENM NUM`, `SCROLL Y`, `PLY0 CND`,
`STAGE NO : < %d >`, `DIFFICULT: < %d >`). **Guess:** its readers name the stage and difficulty variables; find
them first for the warp tool.
