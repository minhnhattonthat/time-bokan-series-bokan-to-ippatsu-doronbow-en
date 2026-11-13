# Translator brief - Time Bokan Series: Bokan to Ippatsu! Doronbow (PS1, 1996)

For any later translation fix. A vertical shooter parody: the Doronbow trio against every Time Bokan hero, slapstick
throughout. No encoded script exists: the English lives in `script/en/` (formats at the top of `tools/tl_check.py`).

## Read first
1. `docs/style-reference.md` - voices and approved examples. 2. `glossary.md` - binding names and terms.
3. `docs/synopsis.md` - story order and the late turn (MOVE04's victory undone).

## Edit
Only the `en` (and `note`) columns of `script/en/*.tsv`, with the file-edit tool. Keep ids. Plain ASCII except the
full-width card title. `|` breaks a graphics or credit line; ` || ` splits a movie row's time.

## Validate
`python -X utf8 tools/tl_check.py` until it prints OK (widths are pixels in the row's class, `gfx.CLASSES`).
`python -X utf8 tools/pairs.py` regenerates the review files in `work/qa/story/chapters/`.

## Style
- Faithful; adapt idiom and jokes, never meaning. Keep each speaker audible (style reference).
- Names and terms exactly as the glossary; never abbreviate to fit: report `LONG: id` instead.
- Honorifics kept (-sama), Western name order. 「」 -> "...", ・・・ -> `...`.
- Boyacky's ボクちゃん only is "little ol' me"; 私 is plain "me".
