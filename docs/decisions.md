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
| D8 | 2026-11-13 | FMV dialogue (6 movies, spoken, no subtitles) | leave untranslated; burn English subtitles | Burn in subtitles if re-encoding fits each file's sector count, with desu-yo's tools and its subtitle style (Liberation Serif Bold 13 px on a soft halo, its D15). **Agent default** from desu-yo D7, which the owner left standing. |
| D9 | 2026-11-13 | Names that differ between the voice and Tatsunoko's English site | Hepburn of the voice; official English | Official English, as desu-yo D11: Doronbow, Boyacky, Tonzra, Dokurobey, Zenderman, Rescueman; Yattodetaman stays. **Agent default** following the reference project. |
| D10 | 2026-11-13 | Memory card title (Shift-JIS in `BOKAN.EXE`, shown by the console's card manager) | leave Japanese; full-width English | Full-width English in the same 34 bytes, since it is text the player sees. **Agent default.** |
| D11 | 2026-11-14 | Fonts, per label class | one font throughout; a font per class | Desu-yo's set (its D9, D15): Liberation Sans Bold 14 with a 1 px outline for menu labels on bars and panels (title menu, options; Bangers 16 was muddy there in the spike, as desu-yo found on its title bars); Bangers for display labels (card messages, ship names, banners, stamps, stage cards); Jersey 10 at its native 18.67 px for the song and voice lists, at 10 px for tags and badges; Jersey 15 for the staff roll; Liberation Sans Bold 12 for signs and the boss plates; Liberation Serif Bold for FMV subtitles, 15 px on a 320-wide canvas stretched 2x (the movies are 640x240). All OFL. Table: `CLASSES` in `tools/gfx.py`. **Agent default** following the reference project, so the two games look alike. |
