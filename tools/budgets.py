"""Pixel budgets for script/graphics.tsv rows: what the game actually samples and where it draws it.

usage: budgets.py [--prims work/recon/prims_rows.tsv] [--out script/budgets.tsv]
Sources: quad = seen in a GPU dump (tools/prims.py, `warp_all.py --prims`); sibling = not drawn, box taken from the
slot grid of measured rows of the same kind (sibling()); none = not drawn in any dump, so the row's own rect is only a
guess. Quads overlapping under half of a row (or of the quad) are not counted; a row split over
several quads lists each. English must fit the `uv` boxes, and `screen` says where they land (x,y on the 320-wide screen).
Desu-yo also read sprite cell tables; this game has none in that format (no group found in the EXE or overlays)."""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx_script
import tim


def overlap(r, u, v, w, h):
    ox = min(r.x + r.w, u + w) - max(r.x, u)
    oy = min(r.y + r.h, v + h) - max(r.y, v)
    return max(ox, 0) * max(oy, 0)


def read_quads(path):
    q = defaultdict(set)
    for ln in Path(path).read_text(encoding="utf-8").splitlines()[1:]:
        c = ln.split("\t")
        if c[3] == "NOT DRAWN":
            continue
        q[c[0]].add((tuple(map(int, c[3].split(","))), tuple(map(int, c[4].split(","))), int(c[5], 16)))
    return q


def clut_row(file, clut):
    """The TIM's CLUT row a GPU clut word selects, or None when it points outside the file's CLUT."""
    b = (ROOT / "work" / "x" / (file + ".BIN")).read_bytes()
    t = tim.parse(b)
    row = (clut >> 6) - t.clut_xy[1]
    return row if (clut & 0x3F) * 16 == t.clut_xy[0] and 0 <= row < t.clut_wh[1] else None


def sibling(r):
    """A box for a row no dump drew, from the slot grid its measured siblings show, or None. Ship names sit in 32-row
    slots of SELNAME's right column (seen: 152,0 and 152,96, 103x31); every ship sheet's tag is drawn as 0,240,80,16."""
    if r.id.startswith("ship.") and r.x >= 152:
        return 152, round(r.y / 32) * 32, 103, 31
    if r.id.startswith("tag."):
        return 0, 240, 80, 16
    return None


def table(quads):
    """Columns: uv = drawn texel boxes (x,y,w,h in TIM pixels); screen = where they land; clut = TIM CLUT rows drawn
    with (more than one: a highlight state, so English must read in each)."""
    lines = ["id\tfile\trect\tsource\tuv\tscreen\tclut"]
    count = defaultdict(int)
    for r in gfx_script.rows():
        if r.form == "keep":
            continue
        area = r.w * r.h
        seen = [(uv, sc, c) for uv, sc, c in quads.get(r.id, ()) if overlap(r, *uv) * 2 >= min(area, uv[2] * uv[3])]
        uvs = sorted({uv for uv, _, _ in seen})
        screens = sorted({(sc[0], sc[1] % 240) for _, sc, _ in seen})[:4]  # y + 240: the other display buffer
        rows = sorted({row for row in (clut_row(r.file, c) for _, _, c in seen) if row is not None})
        source = "quad" if seen else "none"
        if not seen and sibling(r):
            uvs, source = [sibling(r)], "sibling"
        count[source] += 1
        lines.append("\t".join([r.id, r.file, f"{r.x},{r.y},{r.w},{r.h}", source,
                                ";".join(",".join(map(str, u)) for u in uvs), ";".join(f"{x},{y}" for x, y in screens),
                                ",".join(map(str, rows))]))
    return lines, dict(count)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prims", default=str(ROOT / "work" / "recon" / "prims_rows.tsv"))
    ap.add_argument("--out", default=str(ROOT / "script" / "budgets.tsv"))
    a = ap.parse_args()
    lines, count = table(read_quads(a.prims))
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(count, a.out)


if __name__ == "__main__":
    main()
