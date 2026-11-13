# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

D1-D6 are the owner's standing answers, injected into this one-shot run. Per-game override (`rom/overrides.md`): use
`../time-bokan-series-bokan-desu-yo-en` as reference. Rows marked **agent default** follow that project's rulings and
are not owner rulings for this game; `docs/status.md` lists them under "Waiting on the user".

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-13 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western name order (given name first). Owner's standing answer. |
| D2 | 2026-11-13 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist, else an earlier fan patch, else Hepburn without macrons. Owner's standing answer. No earlier patch found (search 2026-11-13). |
| D3 | 2026-11-13 | Credits | stay Japanese, translate | English. Owner's standing answer. |
| D4 | 2026-11-13 | Abbreviations | engine work first (default), abbreviate | Engine work first; abbreviate only as a flagged last resort. Skill default, not overridden. |
| D5 | 2026-11-13 | Graphics text left in Japanese | none (default), list | Translate all of it (titles, menus, banners, cards). The Japanese logo stays only if it has no official English version; none is known for ボカンと一発!ドロンボー, so it stays (with its small タイムボカンシリーズ), as desu-yo's did. Owner's standing answer. |
| D6 | 2026-11-13 | Specs and plans | need approval, pre-approved | Pre-approved. Owner's standing answer. |
| D7 | 2026-11-13 | Saves, memory cards, savestates | owner supplies; none | None provided; build the debug tool as usual. Owner's standing answer. |
| D8 | 2026-11-13 | FMV dialogue (6 movies, spoken, no subtitles) | leave untranslated; burn English subtitles | Burn in subtitles if re-encoding fits each file's sector count, with desu-yo's tools and its subtitle style (Liberation Serif Bold 13 px on a soft halo, its D15; size replaced by D11: 15 px on the 320-wide canvas). **Agent default** from desu-yo D7, which the owner left standing. |
| D9 | 2026-11-13 | Names that differ between the voice and Tatsunoko's English site | Hepburn of the voice; official English | Official English, as desu-yo D11: Doronbow, Boyacky, Tonzra, Dokurobey, Zenderman, Rescueman; Yattodetaman stays. **Agent default** following the reference project. |
| D10 | 2026-11-13 | Memory card title (Shift-JIS in `BOKAN.EXE`, shown by the console's card manager) | leave Japanese; full-width English | Full-width English in the same 34 bytes, since it is text the player sees. **Agent default.** |
| D11 | 2026-11-14 | Fonts, per label class | one font throughout; a font per class | Desu-yo's set (its D9, D15): Liberation Sans Bold 14 with a 1 px outline for menu labels on bars and panels (title menu, options; Bangers 16 was muddy there in the spike, as desu-yo found on its title bars); Bangers for display labels (card messages, ship names, banners, stamps, stage cards); Jersey 10 at its native 18.67 px for the song and voice lists, at 10 px for tags and badges; Jersey 15 for the staff roll; Liberation Sans Bold 12 for signs and the boss plates; Liberation Serif Bold for FMV subtitles, 15 px on a 320-wide canvas stretched 2x (the movies are 640x240). All OFL. Table: `CLASSES` in `tools/gfx.py`. **Agent default** following the reference project, so the two games look alike. |
| D12 | 2026-11-14 | Sound-test song list: Jersey 10 at 18.67 px (D11) with 「」 as quotes, or another style | keep D11 and abbreviate the longest title; Jersey 15 without quotes | Jersey 15, no quotes, for all 20 songs: "Yattodetaman Boogie-Woogie Lady" is 226 px in Jersey 10 even unquoted and the plate holds 206; Jersey 15 gives 200, so no title is cut (D4). Replaces D11 for the song list only. **Agent default.** |
| D13 | 2026-11-14 | Title calls in MOVE01 (ボカンと一発! / ドロンボー!) | translate the title; romanize | Romanized, "Bokan to Ippatsu!" / "Doronbow!": it is the game's name and the logo stays Japanese (D5). **Agent default.** |
| D14 | 2026-11-14 | Memory card title (34 bytes, full-width only) | 「ＢＯＫＡＮ！　ＤＯＲＯＮＢＯＷ」; other short forms | 「ＢＯＫＡＮ！　ＤＯＲＯＮＢＯＷ」: the full romanized title needs 26 characters and the slot holds 17; capitals, as the BIOS card font draws them for sure. **Agent default.** |
| D15 | 2026-11-14 | Staff roll English style | credit class with a 1 px outline (D11); flat | Flat Jersey 15 in each line's own ink (roles red, names white), as the Japanese glyphs, which have no outline. With the outline the English needs 99% of END_STF0 and does not pack. A line too wide for its page (u8 x, ends by 276) closes its part gap to 8 px. **Agent default.** |
| D16 | 2026-11-14 | FMV subtitle timing (owner: subtitles showed a bit before the voice) | Whisper times as is; constant delay; per-row onset from audio energy | Constant 0.3 s delay, `fmv_burn.DELAY`: speech after a pause starts 0.34 s after Whisper's start at the median (47 rows, IQR 0.23-0.42). Per-row energy onset rejected: music under the voice gives false onsets of 1-2.5 s. Owner request; value **agent default**. |
