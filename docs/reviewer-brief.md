# Translation reviewer brief - Time Bokan Series: Bokan to Ippatsu! Doronbow

You review one file of a JP->English fan translation. Read-only: no edits, no git, no subagents.
Mechanical validity (ids, encodable characters, width, glossary spellings) is already enforced by
`tools/tl_check.py` - judge translation quality. Return the report as your final message.

## Inputs
- A chapter file from `work/qa/story/chapters/` (`tools/pairs.py`): `>> id | speaker or form | JP` then the English.
  ` / ` in the English is a line break or a split subtitle. Read ALL of it.
- `glossary.md` (rulings at the top), `docs/style-reference.md`, `docs/synopsis.md`.
- Movie Japanese is a Whisper transcription corrected by hand; rows whose note or JP has `?` are guesses.

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly; honorifics (-sama) kept; voice matches the style reference.
- Things players caught that reviewers missed: jokes/wordplay losing their punch; abbreviated names or terms;
  stock phrases that read awkwardly in English.
- Voice: Doronjo bossy, Boyacky fawning, Tonzra Kansai-rough ("I tell ya"), Dokurobey rustic (", y'hear"). A line any
  speaker could have said is a finding.
- Labels: menu and sound-test text must read as a game UI; voice-sample rows are short cries.

## Report
### Issues
#### Critical (meaning reversed, wrong speaker)
#### Important (clear mistranslation, glossary inconsistency, abbreviation, a character's voice flattened, joke dead)
#### Minor (style - deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
Approved | Needs fixes - one sentence why.
