# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release. Classes: `CLASSES` in `tools/gfx.py` (D11).

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| fonts/Bangers-Regular.ttf | github.com/google/fonts `ofl/bangers` (copied from desu-yo, fetched there 2026-11-06) | OFL 1.1 (`fonts/bangers.OFL.txt`) | yes, as rendered pixels | message, piece, name, label, stamp, banner, sfx, card classes | none |
| fonts/Jersey10-Regular.ttf | github.com/google/fonts `ofl/jersey10` (copied from desu-yo) | OFL 1.1 (`fonts/jersey10.OFL.txt`) | yes, as rendered pixels | list (songs), voice, badge, tag classes | none |
| fonts/Jersey15-Regular.ttf | github.com/google/fonts `ofl/jersey15` (copied from desu-yo) | OFL 1.1 (`fonts/jersey15.OFL.txt`) | yes, as rendered pixels | credit class (staff roll) | none |
| fonts/LiberationSans-Bold.ttf | Liberation Fonts 2.1.5 (github.com/liberationfonts/liberation-fonts), copied from desu-yo | OFL 1.1 (`fonts/LICENSE-Liberation.txt`) | yes, as rendered pixels | menu class (title menu, options), sign class (stage 5 signs, boss plates) | none |
| fonts/LiberationSerif-Bold.ttf | Liberation Fonts 2.1.5, copied from desu-yo | OFL 1.1 (`fonts/LICENSE-Liberation.txt`) | yes, as rendered pixels | FMV subtitles (`tools/fmv_burn.py`) | none |
