"""script/graphics.tsv reader, and a contact sheet of each row's pixels to check the JP reading and rectangle by eye.

usage: gfx_script.py sheet X_DIR OUT.png [--form credit] [--from N] [--to M]
Rows keep their columns: id file x y w h form jp note; a trailing empty note may be absent."""
import argparse
import os
import sys
from collections import namedtuple
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import tim

Row = namedtuple("Row", "id file x y w h form jp note")


def rows(path=ROOT / "script" / "graphics.tsv"):
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines()[1:]:
        c = ln.split("\t")
        assert len(c) in (8, 9), f"bad row: {ln}"
        out.append(Row(c[0], c[1], *map(int, c[2:6]), c[6], c[7], c[8] if len(c) == 9 else ""))
    return out


def sheet(x_dir, out, form, lo, hi, ids=None):
    from PIL import Image, ImageDraw
    rs = [r for r in rows() if (not form or r.form == form) and (not ids or r.id in ids)][lo:hi]
    cols, cell_w, cell_h = 6, 200, 66
    img = Image.new("RGB", (cols * cell_w, (len(rs) + cols - 1) // cols * cell_h), (72, 0, 72))
    d = ImageDraw.Draw(img)
    for i, r in enumerate(rs):
        b = open(os.path.join(x_dir, r.file + ".BIN"), "rb").read()
        t = tim.parse(b)
        # CLUT row 0 is often a one-colour placeholder here
        crop = tim.to_image(t, b, tim.best_clut(t)).crop((r.x, r.y, r.x + r.w, r.y + r.h))
        z = max(1, min(cell_w // max(r.w, 1), (cell_h - 12) // max(r.h, 1)))
        crop = crop.resize((r.w * z, r.h * z), Image.NEAREST)
        x, y = i % cols * cell_w, i // cols * cell_h
        d.text((x + 2, y), r.id[:32], fill=(255, 255, 0))
        img.paste(crop, (x + 2, y + 12), crop)
    img.save(out)
    print(len(rs), "rows")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sheet"])
    ap.add_argument("x_dir")
    ap.add_argument("out")
    ap.add_argument("--form")
    ap.add_argument("--from", dest="lo", type=int)
    ap.add_argument("--to", dest="hi", type=int)
    ap.add_argument("--ids", help="file of row ids, one a line")
    a = ap.parse_args()
    sheet(a.x_dir, a.out, a.form, a.lo, a.hi, open(a.ids).read().split() if a.ids else None)
