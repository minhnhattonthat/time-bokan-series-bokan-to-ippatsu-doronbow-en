# Time Bokan Series: Bokan to Ippatsu! Doronbow English translation

Unofficial English fan translation of **Time Bokan Series: Bokan to Ippatsu! Doronbow** (PlayStation, Banpresto, 1996):
the source text and tools that build the patch. Progress and open bugs are in `docs/status.md`.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Movie dialogue | English subtitles burned into all 6 movies; voices stay Japanese |
| Title and options menus, memory card messages | Translated |
| Ship select, stage cards, banners, HUD, signs | Translated |
| Sound test (song titles, voice captions) | Translated |
| Credits roll | Translated |
| Memory card save name | Full-width English (BOKAN! DORONBOW) |
| Title logo | Left in Japanese, as no official English logo is known |
| Songs and voice samples | Left in Japanese (audio) |

Known issues: nobody checked the subtitles by ear, as they come from machine transcription with corrections; song titles
and some credit name readings have no official source; 23 labels the game never drew in testing are translated from
their images only. Tested on PCSX-Redux only, by scripted warps to every scene rather than a full playthrough. See also
[Issues](../../issues).

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/time-bokan-series-bokan-to-ippatsu-doronbow-en
cd time-bokan-series-bokan-to-ippatsu-doronbow-en
# copy your dump (.cue and all 22 tracks) to rom/, for example:
#   rom/Time Bokan Series - Bokan to Ippatsu! Doronbow (Japan) (Track 01).bin
#   (209718432 bytes, CRC32 acaef1f8, MD5 7eba4fea10de196ecb4e1edd4b0bada5,
#    SHA-1 4e6fcf5c2a35226c2d381f65aa7ad87162b9fe49; the build refuses any other dump, see rom.sha1)
# Redump: http://redump.org/discs/quicksearch/SLPS-00609/
python -X utf8 tools/build.py                          # -> build/ (about 4 min with the movies)
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Banpresto's and is included only so
the translation can be checked against it. Time Bokan Series: Bokan to Ippatsu! Doronbow is (c) Banpresto and Tatsunoko
Production; this project is not affiliated with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
