# Skill gotchas

One line per gotcha: the reference file it belongs in, then the fact.

- scripts/sheet.py: `--out DIR/x.png` fails with FileNotFoundError when DIR does not exist; it does not create it.
- references/graphics.md (survey): PS1 TIMs here keep a one-colour placeholder in CLUT row 0, so CLUT-0 sheets show text as solid shapes; pick the first multi-colour row (`tools/tim.py png FILE OUT auto`) to read it.
- references/emulator-qa.md (Hooks): a `--var SHOTS=...` collides with emu.py's own `SHOTS` global in `_run.lua`; PCSX-Redux then exits -1 with an empty log. Name scene vars something else (NSHOTS).
- references/emulator-qa.md (Hooks): PCSX-Redux Lua is LuaJIT 5.1: no `//` operator (parse error, exit 2).
- references/platform-ps1.md: emu.py drives pad 1 only; `PCSX.SIO0.slots[2].pads[1].setOverride(b)` reaches pad 2 (this game's 2P join did not react; unconfirmed whether the override works).
- references/emulator-qa.md (Debug tool): to call a game function from Lua without the debugger, write a small MIPS stub into dead RAM and start it as a task (it kills its slot, then `j fn`); use a fresh stub address per call since the dynarec caches compiled code.
- scripts/jpscan.py: misses Shift-JIS stored as byte-swapped 16-bit words (this game's memory card title); `tools/sjis_scan.py --swap` finds it.
