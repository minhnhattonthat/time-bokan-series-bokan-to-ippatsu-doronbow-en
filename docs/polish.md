# Polish list

Minors deferred to one pass before release. Tick each `[x]`, fixed or `waived: reason`; the release script refuses to
run while a line is unticked.

- [ ] Movie rows on unclear audio (marked `?` in `script/fmv/`): MOVE01.18, .19, .22; MOVE02.11, .18, .19, .21;
  MOVE03.9, .11, .15, .18; MOVE04.6, .7, .9, .15, .23, .31, .33, .34; MOVE05.4, .5, .7, .13, .15; MOVE06.1-.4.
  Nobody has listened against the English; speakers of MOVE01.22, MOVE03.11, MOVE04.31, .34 are unknown, and
  MOVE03.18, MOVE04.18, .24 are guessed.
- [ ] Credit readings with no source: 35 斎藤直征 (Naoyuki), 42 スタジオ・キリー (Studio Kiri), 45 山本公 (Ko),
  78 錦織有亭 (Yutei). 85 大山誉展 comes from desu-yo's MobyGames reading.
- [ ] Credit 19 演出 "Episode Director" (codex: "Direction"); kept to match desu-yo's roll.
- [ ] `voice.12` 今週のやまばぁ "Big scene time!" drops "this week's" (codex); "This week's big moment!" is 30 px over
  its quad. Phase 7 may widen the voice quads (the uv table) and restore it. Codex round 2 offered "Weekly climax!".
- [ ] `voice.03` 爆弾用意 "Bombs up!" reads oddly (codex); "Ready the bombs!" is over its 72 px quad, as above.
- [ ] Song titles are our own English (no official ones); `song.17` Zorozoro and `song.18` Patoru! de SHOW keep
  their sound. Reading of ぱとる unchecked.
- [ ] `st5.sign_small` reading 人命尊重 unsure (phase 4); "Life First" follows that reading.
- [ ] `wep.sfx` "KA-|BOOM" and `hud.wait`, `hud.pick_mecha`, `boss5.*`, `st5.safety`, `card.p_broken`-`p_failed`,
  `logo.trial` were never drawn in any dump: their layout is a guess until phase 8 sees them.
