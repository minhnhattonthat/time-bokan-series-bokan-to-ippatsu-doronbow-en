# Style reference

Copied from desu-yo's (the sequel, same cast and voices), trimmed to who speaks here. Subtitles carry no speaker
names, so each voice must show in the line itself.

| Speaker | JP markers | English devices | Example |
|---|---|---|---|
| Doronjo | だよ, じゃないか, お前たち, かい, おくれ | bossy, sharp; "you two", "boys", "Let's...!" | お前たち、出動だよ → Boys, move out! |
| Boyacky | ですよ, ございます, ドロンジョ様ったら, ポチッとな | fawning and smug; "yes indeed", "if you please", "ma'am", "Annnd... click!"; "little ol' me" only for ボクちゃん | 今さら止めるわけにはいかないんですよ → We can't back out now, yes indeed. |
| Tonzra | わい, まんねん, でっせ, や, へん (Kansai) | rough, dropped g; "I tell ya", "ya", "'em" | 100倍にして返しまっせ → A hundred times over, I tell ya! |
| Dokurobey | わし, だべ, スカポンタン | rustic and pompous; ", y'hear", "you numbskulls" | わしはドクロベェだべ → I'm Dokurobey, y'hear. |

Rules:
- One idea per subtitle, 2 lines at most where it can be, 296 px each (`tools/tl_check.py` is the gate). A long
  Whisper row is split with ` || ` (time shared by length) rather than run to 3 lines.
- A sentence split across rows reads across them with "..." at both ends.
- Catchphrases never change: "Arahora-sassa!", "Annnd... click!", "Let 'em have it!", "punishment".
- Stage cards end on the announcer's tic: Omotchama "Koron!", Perasuke "Peccha!".
- Title calls stay romanized: "Bokan to Ippatsu!" / "Doronbow!" (the logo stays Japanese, D5).
- Corrected example: MOVE04.10 都合の悪いことは全部私にさせる uses 私, not ボクちゃん, so it is "you always make me do
  the dirty work", not "little ol' me".
