# Graphics-text survey

**Method (verified):** `tools/tim_sheets.py work/x work/recon/tims` rendered all 188 TIMs with CLUT 0 to 16 contact
sheets, and every sheet was read. Many files keep a one-colour placeholder (magenta 0x7C3F) in CLUT row 0, which still
shows every non-zero pixel; `tools/tim.py png FILE OUT auto` picks the first real row. `tools/tim_survey.py hidden`
finds CLUT 0 hiding pixels only in `ST7/BG/ST7_SA1` (34%); read with row 1: no text. `tim_survey.py embedded`: no TIM
inside the EXE, overlays or past any TIM. Text-bearing files below were read zoomed (`work/recon/z/`).

FMVs: `tools/str_frames.py --every 3` sampled 185 frames over the 6 movies (`disc.md`): no Japanese captions. A caption
shorter than 3 s can be missed; phase 4 transcribes each movie in full.

Readings are by eye; kanji marked (?) need a second look in phase 4. "Where shown" is a guess until phase 2 reaches it.

## Title, menus, memory card

| File | Japanese elements |
|---|---|
| `CHRPLY/TITLE1B` (8 bpp) | logo ドローボー (ドロンボー), ボカンと一発!, タイムボカンシリーズ; stamp 体験版 (trial edition: **guess** unused in retail). Logo: see D5 |
| `CHRPLY/TITLE2` (8 bpp) | skull emblem, no text |
| `CHRPLY/TITLE3` | menu スタート, オプション, メモリーカード; ©タツノコプロ, ©バンプレ企画 1996 (English: PUSH START BUTTON, ©BANPRESTO 1996, DORONBOO tiles) |
| `CHRPLY/TITLE4` | memory card: menu セーブ, ロード (EXIT English); NO/YES (English); アクセス中, セーブOK!, ロードOK!; messages このメモリーカードは / フォーマットされてません / フォーマットしますか? / 空き容量が足りません / データがありません; fragments ・メモリー, 差されて, カードが, (い)ません, カードがこわれてます, セーブ, ロードに失敗しました (assembled from pieces at run time: **guess**) |
| `CHRPLY/TK_00, TK_01` | trial-edition advert: タイムボカンシリーズ ボカンと一発!ドロンボー '96 11月発売予定!! 請う、ご期待だべぇ 定価5800円(税別). **Verified unused:** no file name for them in `BOKAN.EXE` or any overlay (`tools/file_refs.py`), so retail never loads them; leave Japanese |
| `CHRPLY2/OPTI_01` | options: ゲームレベル 1(やさしい), 2(ふつう), 3(むずい), 4(げきむず); クレジット; サウンドテスト; キーコンフィグ; ショット; ボム |
| `CHRPLY2/OPTI_02` | OPTION, EXIT, digits (English) |
| `CHRPLY2/OPTI_03-05` | sound test song titles, 「」-bracketed: タイムボカン, それゆけガイコッツ, ヤッターマンの歌, 天才ドロンボー, ヤッターキング, ドロンボーのシラーケッ(?), ゼンダマンの歌, これまたアクダマン, オタスケマンの歌, アーウー・オジャママン, ヤットデタマンの歌, ヤットデタマン・ブギウギ・レディ, 逆転イッパツマン, シビビーン・ラプソディ, いただきマンボ, 正義のハイライト, ゾロゾロマーチ, ぱとる!でSHOW, ストライク・ドロンボー, 夕日のドロンボー (20 rows) |
| `CHRPLY2/OPTI_06` | voice test, 27 lines: エッホ! あれ~っ! 爆弾用意! きゅ~っ! やっておしまい! なんてことだい! スカポンタン! やられたまんねん! これでイチコロや! しまったぁ~! あ、どないしよ! 今週のやまば(?) あ痛ぁ~~ メカ戦だぁ! スタート! いくわよ~ん あ~ん、くやしい~! アラホラサッサ! しゅっぱ~つ! なぬう~! どれを使おうかねぇ? しっかりおしよ! オプションよぉ! ポチっとな! メカを選んでください いったぁ~い! それは整備中なの! (and character face icons) |

## Ship select, HUD, ranking

| File | Japanese elements |
|---|---|
| `CHRPLY/SELNAME` | ship names: シャレコーベメカ, アンドロメダマ号, タイムラクーダ, シャレコーベバギー, デンデンメカ, ドロンジョカー, ボヤッキーカー, ガイコッツ, トンズラーカー; ゲームオーバー; 参加OK; stamp 整備中 (English: 1P 2P OK, PUSH START!, PUSH! START., STAND BY OK!, NO CREDIT) |
| `CHRPLY/SEL_BG` | banner 出撃準備 (4 tiles); small ドロンボー logo on the wall (with English BOKAN TO IPPATSU) |
| `CHRPLY/SELECT` | ship sprites; English STAGE, CHANGE, LR, digits |
| `CHRPLY/KIHON` | HUD: ポチっとな (badge), ちょっと待ってね! (split across the page edge), ◀メカをえらんで, ゲームオーバー (English: fonts, DANGER, LEVEL UP/MAX/DOWN, SHIELD, TURBO, CREDIT +1, scores, DEMO(?), CHANGE) |
| `CHRPLY/RNK` | ランキング スコア banner (English font, RANK NAME SCORE) |
| `CHRPLY/ANDORO, BOYA, DENDEN, DORON, GAIKOTU1, RAKUDA, SYAREKO, SYA_BAGI, TONZR, TYARINKO` | each ship's sheet ends in a small name tag: アンドロメダ号, ボヤッキーカー, デンデンメカ, ドロンジョカー, ガイコッツ, タイムラクーダ, シャレコーベメカ, シャレコーベバギー, トンズラーカー, チャリンコ. **Guess:** tags may be unused (developer labels); phase 2/5 decides |
| `CHRPLY/D_WEPON` | sound-effect kana ボーン, カン (bomb) |

## Stage cards and stages

| File | Japanese elements |
|---|---|
| `CHRPLY2/TI_ST1-7` | stage titles (English STAGE n / VS hero lines already): 1 鷹は舞い下りた! だコロン; 2 南の島のヤッターキング! だコロン; 3 真昼の決闘! 崖っぷちだよ、ゼンダマン; 4 集結! 助っ人メカ 雪原の大バトル!; 5 怒れ! 正義の大巨神!; 6 灼熱のダブルヒーロー!; 7 飛べ!ドロンボー 空中大決戦 だペッチャ! |
| `ST5/BG/ST5_B2` | road signs 安全第一, small 人命尊重(?) |
| `ST5/BG/ST5_B3` | green two-kanji plate (?) on a building roof |
| `ST5/BG/ST5_SA0` | street sign とまれ (English billboard YATTO DETA / BEER, TATSUNOKO sign in `ST5_A6`) |
| `ST5/ENM/R5_BOSS2` | speech plates 罪を憎んで / 人を憎まず |
| `ST5/ENM/R5_BOSS4` | kanji 怒 on the robot |

## Ending

| File | Japanese elements |
|---|---|
| `CHRPLY2/END_STF0, END_STF1` | staff roll glyph sheets: headings 声の出演, アニメ制作スタッフ, ゲーム制作スタッフ, role names (総監督・絵コンテ, 演出, ゲスト(メカ)設定, プロデューサー, 制作進行, 作画監督, 原画, 動画, 色指定・検査, 仕上げ, 美術監督・背景, 特殊効果, 撮影, 編集, 録音監督, 効果, 調整, 録音スタジオ, 録音制作, 現像, 制作協力, 制作, プログラム, グラフィック, サウンド, 効果音, ディレクター, 協力プロデューサー, 総指揮, 企画・制作販売), character names (ドロンジョ ボヤッキー トンズラー ドクロベー), and staff/company names as kanji cells shared between names. **The roll composes lines from cells**, as desu-yo's did (`../time-bokan-series-bokan-desu-yo-en/docs/re/cells.md`): map lines in phase 4 |
| `CHRPLY2/END_0-4` | ending scenes, no text |

## Checked, no Japanese

`CHRPLY/BPMARK` (BANPRESTO logo), `OVERLOG` (English GAME OVER), `SFXSET`, `SYS`, `TITLE2`, `TK_00` (art only),
`CHRPLY2/OPTI_00`, `TAI_1-7` (stage intro silhouettes), `END_0-4`; every `ST1-7/BG` and `ST*/ENM` file except those
above (signs in `ST6/BG/ST6_A4` read EXIT and IN; `ST2/BG/SPR_2` flag and `ST3/ENM/R3_BOSS3` plate are English or
digits). Hero cut-ins `YTAMN_C`, `ZENDA_C`, `OTSKE_C`, `YATDETA`, `IPPATSU`, `ITADAKI`, `HERO`: art only.

## Logo

The title logo (ボカンと一発!ドロンボー in `TITLE1B`, and burned into MOVE01's last frames) has no known official
English version. Per the standing answer (D5) it stays Japanese, as desu-yo's did; small タイムボカンシリーズ with it.
