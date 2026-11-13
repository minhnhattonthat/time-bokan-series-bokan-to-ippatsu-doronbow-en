"""Find ink boxes in a TIM (runs of opaque pixels split by blank rows, then by column gaps) and draw them numbered.

usage: ink_boxes.py FILE [--crop x,y,w,h] [--gap N] [--clut N|auto] [--out OUT.png] [--zoom N]
Prints one box per line: n x y w h. A box is a starting point for a script/graphics.tsv rect, read by eye after."""
import argparse
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import tim


def boxes(img, x0, y0, w, h, gap):
    """Ink = any pixel that differs from the crop's most common colour (pages here fill with 0 or with a flat colour)."""
    a = img.load()
    from collections import Counter
    bg = Counter(a[x, y] for x in range(x0, x0 + w) for y in range(y0, y0 + h)).most_common(1)[0][0]
    ink = lambda x, y: a[x, y] != bg
    out, y = [], y0
    while y < y0 + h:
        if not any(ink(x, y) for x in range(x0, x0 + w)):
            y += 1
            continue
        y1 = y
        while y1 < y0 + h and any(ink(x, y1) for x in range(x0, x0 + w)):
            y1 += 1
        cols = [any(ink(x, yy) for yy in range(y, y1)) for x in range(x0, x0 + w)]
        x, run = 0, None
        while x <= w:
            on = x < w and cols[x]
            if on and run is None:
                run, last = x, x
            elif on:
                last = x
            elif run is not None and (x == w or x - last > gap):
                # trim the band to this run's own ink rows
                rows = [yy for yy in range(y, y1) if any(ink(x0 + xx, yy) for xx in range(run, last + 1))]
                out.append((x0 + run, rows[0], last - run + 1, rows[-1] - rows[0] + 1))
                run = None
            x += 1
        y = y1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--crop")
    ap.add_argument("--gap", type=int, default=6)
    ap.add_argument("--clut", default="auto")
    ap.add_argument("--out")
    ap.add_argument("--zoom", type=int, default=3)
    a = ap.parse_args()
    b = open(a.file, "rb").read()
    t = tim.parse(b)
    img = tim.to_image(t, b, tim.best_clut(t) if a.clut == "auto" else int(a.clut))
    x0, y0, w, h = map(int, a.crop.split(",")) if a.crop else (0, 0, *img.size)
    bs = boxes(img, x0, y0, w, h, a.gap)
    for n, (x, y, bw, bh) in enumerate(bs):
        print(n, x, y, bw, bh)
    if a.out:
        z = a.zoom
        big = img.crop((x0, y0, x0 + w, y0 + h)).resize((w * z, h * z), Image.NEAREST)
        out = Image.new("RGB", big.size, (72, 0, 72))
        out.paste(big, (0, 0), big)
        d = ImageDraw.Draw(out)
        for n, (x, y, bw, bh) in enumerate(bs):
            r = ((x - x0) * z, (y - y0) * z, (x - x0 + bw) * z - 1, (y - y0 + bh) * z - 1)
            d.rectangle(r, outline=(0, 255, 0))
            d.text((r[0] + 1, r[1] + 1), str(n), fill=(255, 255, 0), stroke_width=1, stroke_fill=(0, 0, 0))
        out.save(a.out)


if __name__ == "__main__":
    main()
