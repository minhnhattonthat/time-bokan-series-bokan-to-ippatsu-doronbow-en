"""Contact sheets of a warp tour for visual QA, grouped so a reviewer reads each screen once. Names end in _sheet so
qa_gate.py init finds them.

usage: qa_sheets.py TOUR_DIR OUT_DIR
Scenes sharing a prefix go on one sheet at full size. A stage tour (god mode, one shot per 170 frames) keeps every third
shot at half size: it only shows HUD and sprites, and rows on those have their own zoomed crops in the row sheets."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL

SHEET = str(Path(SKILL) / "scripts" / "sheet.py")
GROUPS = ("memcard", "card", "stage", "clear", "select")  # movies get fmv_sheet.py --subs sheets instead


def shots(d):
    return sorted(p for p in d.glob("*.png"))


def make(paths, out, *args):
    if paths:
        subprocess.run([sys.executable, "-X", "utf8", SHEET, *map(str, paths), "--out", str(out), *args], check=True,
                       stdout=subprocess.DEVNULL)


def main():
    tour, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    grouped = {}
    for d in sorted(p for p in tour.iterdir() if p.is_dir()):
        key = next((g for g in GROUPS if d.name.startswith(g)), None)
        if key:
            grouped.setdefault(key, []).extend(shots(d))
        elif d.name.startswith("tour"):
            make(shots(d)[::3], out / f"{d.name}_sheet.png", "--div", "2", "--cols", "6", "--max", "36")
        else:
            make(shots(d), out / f"{d.name}_sheet.png", "--div", "1", "--cols", "4", "--max", "12", "--changed", "0.01")
    for key, paths in grouped.items():
        make(paths, out / f"{key.rstrip('_')}_sheet.png", "--div", "1", "--cols", "4", "--max", "16")


if __name__ == "__main__":
    main()
