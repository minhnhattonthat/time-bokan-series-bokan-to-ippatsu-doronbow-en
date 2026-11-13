# Visual-QA reviewer brief - Time Bokan Series: Bokan to Ippatsu! Doronbow (PS1)

You review contact sheets from the English build's QA tour and give each one a verdict. Read-only: no edits to the
repo, no git, no subagents. The controller writes your verdict lines to `work/qa/verdicts/<chunk>.tsv`.

## Inputs
- The sheets attached to the prompt, each named by its id. Read every one; none may be skipped.
- The original disc's sheets for the same scene, when attached (`work/qa/tsheets_jp/<id>.png`), and `glossary.md`.

## How to look
- Read each sheet whole first, then the small text closely: menu rows, labels, banners, signs, subtitles.
- When something looks wrong, compare with the original's sheet for the same id. If the original shows the same
  thing, it is the game's own behaviour: `ok`, with a note.

## Judge
An `issue` is any of:
- Japanese still visible (outside the standing exceptions below);
- text overflowing a box, clipped by a frame, or running off screen;
- text off-centre where the original centres it: a menu row, a label, a banner;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters, leftover pieces of Japanese glyphs;
- text so low in contrast (striped, pale on pale) that it is hard to read;
- broken subtitle line breaks: a word split mid-line, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok`:
- the logo ボカンと一発!ドロンボー with its small タイムボカンシリーズ stays Japanese (decision D5); so does the
  Banpresto/Tatsunoko logo art that has no Japanese text;
- the console's own memory card screens and the BIOS boot logo;
- a screen mid-fade, mid-scroll or still loading after a warp; a cursor mid-blink;
- stage tours (god mode) show sprites and HUD only; enemies and bullets overlapping text are gameplay;
- movies are re-encoded under the subtitles, so frames are slightly softer than the original: an issue only if
  blocks are plainly visible;
- anything identical in the original's sheet.

## Verdicts
Answer with one line per sheet id and nothing else:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which shot, which text, what is wrong).
