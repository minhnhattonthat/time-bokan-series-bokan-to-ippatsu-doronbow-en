# Polish list

Minors deferred to one pass before release. Tick each `[x]`, fixed or `waived: reason`; the release script refuses to
run while a line is unticked.

- [x] Movie rows on unclear audio (marked `?` in `script/fmv/`): MOVE01.18, .19, .22; MOVE02.11, .18, .19, .21;
  MOVE03.9, .11, .15, .18; MOVE04.6, .7, .9, .15, .23, .31, .33, .34; MOVE05.4, .5, .7, .13, .15; MOVE06.1-.4.
  Nobody has listened against the English; speakers of MOVE01.22, MOVE03.11, MOVE04.31, .34 are unknown, and
  MOVE03.18, MOVE04.18, .24 are guessed. waived: no listener in this run; the phase 9 story pass read them in order and
  the release README lists the subtitles as not ear-checked, as desu-yo's did.
- [x] Credit readings with no source: 35 斎藤直征 (Naoyuki), 42 スタジオ・キリー (Studio Kiri), 45 山本公 (Ko),
  78 錦織有亭 (Yutei). 85 大山誉展 comes from desu-yo's MobyGames reading. waived: no source found; README known issues.
- [x] Credit 19 演出 "Episode Director" (codex: "Direction"); waived: kept to match desu-yo's roll.
- [x] `voice.12` 今週のやまばぁ now "Weekly climax!" (codex round 2; 91 of 112 px), restoring "this week's".
- [x] `voice.03` 爆弾用意 "Bombs up!" reads oddly (codex); waived: "Bombs ready!" (86 px) and "Ready the bombs!" are
  over the 72 px quad, and "Bombs up!" keeps the meaning (D4: no abbreviation).
- [x] Song titles are our own English (no official ones); `song.17` Zorozoro and `song.18` Patoru! de SHOW keep
  their sound. Reading of ぱとる unchecked. waived: no official titles exist to check against; README known issues.
- [x] `st5.sign_small` reading 人命尊重 unsure (phase 4): read zoomed in phase 8, it is 火器厳禁 (the 火's dots show); now "No Flames".
- [x] `wep.sfx` "KA-|BOOM", `hud.pick_mecha`, `boss5.*`, `st5.safety`, `card.p_broken`-`p_failed`, `logo.trial` were
  never drawn in any dump: phase 8 read them zoomed on TIM crops (`rows_unshown_sheet`, codex ok), not in game.
  `hud.wait` was drawn in tour4 (two pieces side by side, zooming in) and redone on its yellow plates. waived: no
  scene found that draws them (`docs/text_unshown.tsv`); README known issues.
- [x] Phase 6 review minor: `hud.pick_mecha` was "< Pick a mecha" in `badge`, 6 px tall, and its "<" doubled the
  plate's own ◀. Now "Pick|a mecha" in `tag` (outlined, two lines, 30x20 in the 56x20 rect), phase 9.
- [x] `boss5.anger` "MAD" now `stamp` class, outlined, fills the 32 px plate (phase 8).
- [x] Credit 81 協力 "Special Thanks" where desu-yo uses "Cooperation"; credit 37 drops the ♥ of スタジオ・ラブ♥ハンター
  (credit font is ASCII; restore if a heart glyph is added). waived: "Special Thanks" is the usual English credit for
  協力; the heart needs a glyph Jersey 15 lacks.
- [x] Tonzra ended 8 movie lines on ", I tell ya": now 3 (MOVE01.19, MOVE02.18, MOVE05.13); MOVE01.5 a question as the
  Japanese, MOVE03.18 "ain't it", MOVE04.23 and MOVE05.4 reworded. MOVE04.2 rebalanced so the ` || ` length split
  falls near the Boyacky/Tonzra change (JP 14:12 characters, English 33:33), phase 9.
- [x] Phase 9 visual QA (codex, clear_sheet): "READY TO LAUNCH" split mid-letter across the four 40 px tiles of
  出撃準備 while they fly in apart. Now one word per tile, `sel.banner1-4` "ALL SET TO GO!", as the Japanese has one
  kanji per tile.
- [x] Phase 9 rect audit (rects against their drawn quads): `hud.pick_mecha`, `ship.gaikotu`, `sel.join_ok` and the
  name tags erased edge rows of neighbouring sprites (HUD tops, START., a tag cap); `hud.gameover` had erased the winged
  pig behind its text; `st5.sign_small` ran into the next BG tile, which the stage draws at the screen's right edge
  ("es" on a grey box in stage 5). All fitted to their sprites; the cut-off 火の sign there is `st5.sign_edge` "Fire".
- [x] Stage 6 card header reads "VS IPPATUMAN" (the game's own English); glossary spells Ippatsuman. waived: it is
  the original's own English lettering (card 7's "VS GYAKUTEN IPPATUMAN" too), left as the game spells it; README
  known issues.
