# Text engine

**There is almost no text encoding to extract.** Every Japanese string the player sees in game is pixels: a region
of a TIM image. The movies carry spoken Japanese only. Same finding as desu-yo (`../time-bokan-series-bokan-desu-yo-en/docs/re/text.md`).

**Verified:**
- `tools/sjis_scan.py` (any byte alignment) and `--swap` (16-bit words byte-swapped) over `BOKAN.EXE`, `SLPS_006.09`,
  `BOKAN1-7.BIN`, `MOVIE1.BIN` and `RECDATA*.DAT` find one Japanese string, the rest noise (`拐跼棋瑩口`, mirrored
  pairs from lookup tables): `tests/test_recon.py`.
- That string is the memory card save title at `BOKAN.EXE` 0x8FA60, 34 bytes, Shift-JIS stored as little-endian
  16-bit words (each character's two bytes swapped): `「　ボカンと一発！　ドロンボー　」`. It shows only in the
  console's memory card manager. Just before it (0x8FA40) sits a 16-colour CLUT, so this is the save icon block.
  Row `card.title` in phase 4; English must be full-width Shift-JIS (the BIOS draws only those), same 34 bytes.
- `jpscan.py`'s hits are noise: misaligned pairs of that title and UTF-16 reads of pointer tables.
- ASCII strings are SDK messages, file names, a font order `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:?!.()=+-"%`
  (EXE 0x225C, for the English HUD/ranking fonts in `KIHON`/`RNK`) and debug labels (`disc.md`).

**Guess, to confirm in phase 5:** menus and labels are sprites drawn from fixed UV rectangles held in overlay data or
code, so each label's size is data. Fit English inside the existing rectangles first, as desu-yo did.

So for this game:
- **Pointers:** none for text; the card title has a fixed slot. **Text ranges:** the card title, plus the
  rectangles in `graphics.md`.
- **Control codes, table files:** none. `tbl/` stays empty; `jp_left.py --sjis` can only confirm the absence, and
  must show the card title gone after the build.
- **Script source for translators:** the Japanese read from the images (phase 4), and transcripts of the movies.
- **Roundtrip test (phase 4):** decoding a TIM and re-encoding it gives identical bytes.

## Voice (no on-screen text)

- The 6 FMVs carry spoken dialogue in XA audio with no subtitles (`disc.md`). English needs burned-in subtitles, as
  in desu-yo (its `tools/mdec.py`, `fmv_burn.py`, `fmv_transcribe.py`).
- In-game voice samples (`SOUND/SE1/VOICEA/B`) are the same lines the voice test lists in `CHRPLY2/OPTI_06`
  (Eh-ho!, Arahora-sassa!, Pochitto na!...). **Guess:** the gameplay voice needs no subtitles once that list is English.
