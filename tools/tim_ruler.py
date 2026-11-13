"""Zoom a TIM (or a crop of it) on a labelled pixel grid, to read text and measure its rectangle.

usage: tim_ruler.py FILE OUT.png [--clut N] [--crop x,y,w,h] [--zoom N] [--grid N] [--bg r,g,b]"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import tim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("out")
    ap.add_argument("--clut", type=int, default=0)
    ap.add_argument("--crop")
    ap.add_argument("--zoom", type=int, default=4)
    ap.add_argument("--grid", type=int, default=16)
    ap.add_argument("--bg", default="72,0,72")
    a = ap.parse_args()
    b = open(a.file, "rb").read()
    t = tim.parse(b)
    assert t, "not a TIM at offset 0"
    img = tim.to_image(t, b, a.clut)
    x0, y0, w, h = map(int, a.crop.split(",")) if a.crop else (0, 0, *img.size)
    crop = img.crop((x0, y0, x0 + w, y0 + h)).resize((w * a.zoom, h * a.zoom), Image.NEAREST)
    pad = 26
    out = Image.new("RGB", (crop.width + pad, crop.height + pad), tuple(map(int, a.bg.split(","))))
    out.paste(crop, (pad, pad), crop)
    d = ImageDraw.Draw(out)
    for x in range(x0 - x0 % a.grid + (a.grid if x0 % a.grid else 0), x0 + w, a.grid):
        px = pad + (x - x0) * a.zoom
        d.line([(px, pad - 4), (px, out.height)], fill=(0, 255, 255))
        d.text((px + 2, 2), str(x), fill=(255, 255, 0))
    for y in range(y0 - y0 % a.grid + (a.grid if y0 % a.grid else 0), y0 + h, a.grid):
        py = pad + (y - y0) * a.zoom
        d.line([(pad - 4, py), (out.width, py)], fill=(0, 255, 255))
        d.text((1, py + 1), str(y), fill=(255, 255, 0))
    out.save(a.out)


if __name__ == "__main__":
    main()
