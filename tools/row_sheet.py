"""Before/after crops of graphics rows: the original TIM beside the built one, each row's drawn box plus a ring, zoomed.

usage: row_sheet.py OUT.png [ID ..] [--build DIR] [--zoom N]    no ids = every row with English
Crops use the CLUT row the game draws the row with (budgets.tsv), else the TIM's first real row. The English rect is
framed in yellow on the after crop."""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import disc
import gfx
import tim
import tl_check

RING = 6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--build", default=str(ROOT / "build"))
    ap.add_argument("--zoom", type=int, default=3)
    a = ap.parse_args()
    budgets = {r["id"]: r for r in tl_check.table(ROOT / "script" / "budgets.tsv")}
    cluts = gfx.drawn_cluts()
    old_d, new_d = disc.Disc(str(ROOT / "rom" / build.TRACK1)), disc.Disc(str(Path(a.build) / build.TRACK1))
    path = {e.path.strip("/").removesuffix(".BIN"): e.path for e in old_d.files.values()}
    tiles = []
    for rid, file, row in gfx.english_items():
        if a.ids and rid not in a.ids:
            continue
        x, y, w, h = row[0]
        bx, by, bw, bh = gfx.uv_box(budgets[rid], row[0]) if rid in budgets else row[0]
        x0, y0 = max(min(x, bx) - RING, 0), max(min(y, by) - RING, 0)
        x1, y1 = max(x + w, bx + bw) + RING, max(y + h, by + bh) + RING
        pair = []
        for d in (old_d, new_d):
            data = d.read(path[file])
            t = tim.parse(data)
            img = tim.to_image(t, data, cluts.get(rid, tim.best_clut(t))).crop((x0, y0, x1, y1))
            bg = Image.new("RGBA", img.size, (80, 0, 80, 255))
            bg.alpha_composite(img)
            pair.append(bg.convert("RGB").resize((img.width * a.zoom, img.height * a.zoom), Image.NEAREST))
        z = a.zoom
        ImageDraw.Draw(pair[1]).rectangle(((x - x0) * z, (y - y0) * z, (x - x0 + w) * z - 1, (y - y0 + h) * z - 1),
                                          outline=(255, 255, 0))
        tiles.append((rid, pair))
    width = max(p[0].width * 2 + 12 for _, p in tiles) + 4
    height = sum(p[0].height + 14 for _, p in tiles)
    sheet = Image.new("RGB", (width, height), (32, 32, 32))
    d = ImageDraw.Draw(sheet)
    yy = 0
    for rid, (b, c) in tiles:
        d.text((2, yy), rid, fill=(255, 255, 0))
        sheet.paste(b, (2, yy + 12))
        sheet.paste(c, (b.width + 12, yy + 12))
        yy += b.height + 14
    sheet.save(a.out)
    print(len(tiles), "rows,", a.out)


if __name__ == "__main__":
    main()
