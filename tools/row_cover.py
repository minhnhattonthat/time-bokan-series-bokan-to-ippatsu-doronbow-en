"""Text coverage for a game with no strings: a graphics row counts as shown when a dumped frame drew a quad over it.

usage: row_cover.py PRIMS_ROWS.tsv [...] [--out work/qa/cover]
Reads tools/prims.py rows output (id, ..., scenes) and writes OUT/strings.tsv and OUT/log.txt in the form the skill's
textcover.py takes, so the release gate is its usual call:
    textcover.py work/qa/cover work/qa/cover/strings.tsv --waive docs/text_unshown.tsv
A row is its line number in script/graphics.tsv; a row the build doesn't letter (keep, logo) isn't listed."""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import tl_check


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rows", nargs="+")
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "cover"))
    a = ap.parse_args()
    ids = [r["id"] for r in tl_check.table(ROOT / "script" / "en" / "graphics.tsv")]
    shown = set()
    for path in a.rows:
        with open(path, encoding="utf-8", newline="") as f:
            shown |= {r["id"] for r in csv.DictReader(f, delimiter="\t") if r["quad_uv"] != "NOT DRAWN"}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "strings.tsv").write_text("".join(f"{rid}\t{n:x}\n" for n, rid in enumerate(ids, 1)), encoding="utf-8")
    (out / "log.txt").write_text("".join(f"TEXT {n:x}\n" for n, rid in enumerate(ids, 1) if rid in shown), encoding="utf-8")
    print(f"{sum(i in shown for i in ids)}/{len(ids)} rows drawn")
    for i in ids:
        if i not in shown:
            print(i)


if __name__ == "__main__":
    main()
