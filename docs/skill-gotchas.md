# Skill gotchas

One line per gotcha: the reference file it belongs in, then the fact.

- scripts/sheet.py: `--out DIR/x.png` fails with FileNotFoundError when DIR does not exist; it does not create it.
- references/graphics.md (survey): PS1 TIMs here keep a one-colour placeholder in CLUT row 0, so CLUT-0 sheets show text as solid shapes; pick the first multi-colour row (`tools/tim.py png FILE OUT auto`) to read it.
- scripts/jpscan.py: misses Shift-JIS stored as byte-swapped 16-bit words (this game's memory card title); `tools/sjis_scan.py --swap` finds it.
