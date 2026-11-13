"""Render every TIM on the extracted disc tree (work/x) to PNGs plus contact sheets, for the graphics-text sweep.

usage: tim_sheets.py SRC_DIR OUT_DIR [--per-sheet N]
Writes OUT_DIR/png/<path>.png, OUT_DIR/sheet_NN.png, and OUT_DIR/index.tsv (sheet, cell, file, bpp, size, cluts, tail).
Prints every file it skipped and why, so nothing drops out of the survey silently."""
import argparse
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import tim

CELL_W, CELL_H, LABEL = 320, 256, 12


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--per-sheet", type=int, default=12)
    a = ap.parse_args()
    items = []
    for r, _, fs in os.walk(a.src):
        for f in sorted(fs):
            p = os.path.join(r, f)
            b = open(p, "rb").read()
            t = tim.parse(b)
            rel = os.path.relpath(p, a.src).replace(os.sep, "/")
            if not t:
                print("skip (not a TIM at offset 0):", rel)
                continue
            img = tim.to_image(t, b)
            out = os.path.join(a.out, "png", rel + ".png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            img.save(out)
            ncl = t.clut_wh[1] if t.clut else 0
            items.append((rel, t, img, ncl, len(b) - t.size))
    with open(os.path.join(a.out, "index.tsv"), "w", encoding="utf-8") as idx:
        idx.write("sheet\tcell\tfile\tbpp\tsize\tcluts\ttail\n")
        for s in range(math.ceil(len(items) / a.per_sheet)):
            chunk = items[s * a.per_sheet:(s + 1) * a.per_sheet]
            cols = 4
            sheet = Image.new("RGB", (cols * CELL_W, math.ceil(len(chunk) / cols) * (CELL_H + LABEL)), (72, 0, 72))
            d = ImageDraw.Draw(sheet)
            for i, (rel, t, img, ncl, tail) in enumerate(chunk):
                x, y = (i % cols) * CELL_W, (i // cols) * (CELL_H + LABEL)
                d.text((x + 2, y), f"{i} {rel}", fill=(255, 255, 0))
                th = img.copy()
                th.thumbnail((CELL_W - 2, CELL_H - 2))
                sheet.paste(th, (x + 1, y + LABEL), th)
                idx.write(f"{s:02d}\t{i}\t{rel}\t{t.bpp}\t{img.size[0]}x{img.size[1]}\t{ncl}\t{tail}\n")
            sheet.save(os.path.join(a.out, f"sheet_{s:02d}.png"))
    print(len(items), "TIMs rendered")


if __name__ == "__main__":
    main()
