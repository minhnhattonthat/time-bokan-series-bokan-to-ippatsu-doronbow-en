"""Graphics rows whose rect doesn't cover the original's Japanese: a stroke runs past the rect, so the build leaves it
behind as stray pixels (title bar dakuten, 2026-11-08). Uses rectcover.spill (copied from the skill) on each TIM.

usage: rect_spill.py [--all]     rows that need to grow; --all also lists ok rows and art joins
Library: spills() -> [(row id, file, rect, (left, right, top, bottom, joins_art))] for every row with English."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx
import rectcover
import tim

# Rows checked by eye whose spill is not Japanese text (joins art, or a neighbour's ink): id -> why.
NEIGHBOUR = "the row above's shadow touches the rect; English crop shows no Japanese left (2026-11-14)"
WAIVED = {"voice.06": "the list's white side marks at x 240; " + NEIGHBOUR,
          **{k: NEIGHBOUR for k in ("voice.11", "voice.14", "voice.27")},
          "ship.rakuda": "y 95, the glyph's last outline row, is below the drawn quad (y 64-94): never on screen"}


def spills(x_dir=ROOT / "work" / "x"):
    by_file = {}
    out = []
    for row_id, file, row in gfx.english_items():
        if not row[1]:  # a clear-only rect (gfx.CLEARS)
            continue
        if file not in by_file:
            data = (Path(x_dir) / f"{file}.BIN").read_bytes() if (Path(x_dir) / f"{file}.BIN").exists() \
                else (Path(x_dir) / file).read_bytes()
            t = tim.parse(data)
            by_file[file] = gfx.tim_px(t, data).tolist()
        rect = row[0]  # the rect the build clears, after any widening for English
        out.append((row_id, file, rect, rectcover.spill(by_file[file], rect)))
    return out


def main():
    bad = 0
    for row_id, file, rect, (l, rt, t, b, art) in spills():
        need = (l or rt or t or b) and not art and row_id not in WAIVED
        bad += bool(need)
        if need or "--all" in sys.argv:
            tag = "GROW" if need else "art " if art else "ok  "
            print(f"{tag} {row_id:18} {file:22} {rect} past l{l} r{rt} t{t} b{b}")
    print(f"{bad} rows need a bigger rect")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
