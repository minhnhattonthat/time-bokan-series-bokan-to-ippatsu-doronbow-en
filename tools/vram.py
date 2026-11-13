"""Crop a VRAM dump (tools/debug/primdump.lua) to PNG, and name the TIM file holding those pixels.

usage: vram.py png VRAM.bin X Y W H BPP CLUT OUT.png    X, W in VRAM units; CLUT is the GPU word in hex, e.g. 7CC3
       vram.py find VRAM.bin X Y W H [X_DIR]            which TIMs under work/x contain this rectangle's bytes"""
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import tim


def row(vram, x, y, w):
    o = (y * 1024 + x) * 2
    return vram[o:o + w * 2]


def png(vram, x, y, w, h, bpp, clut, out):
    from PIL import Image
    cy, cx = clut >> 6, (clut & 0x3F) * 16
    n = 16 if bpp == 4 else 256
    pal = [tim.rgba(c, True) for c in struct.unpack(f"<{n}H", row(vram, cx, cy, n))]
    vals = []
    for r in range(h):
        px = row(vram, x, y + r, w)
        vals += [v for b in px for v in (b & 15, b >> 4)] if bpp == 4 else list(px)
    img = Image.new("RGBA", (w * (4 if bpp == 4 else 2), h))
    img.putdata([pal[v] for v in vals])
    img.save(out)


def find(vram, x, y, w, h, root):
    needle = [row(vram, x, y + r, w) for r in range(h)]
    busy = max(range(h), key=lambda r: len(set(needle[r])))
    for r, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(r, f)
            b = open(p, "rb").read()
            t = tim.parse(b)
            if not t:
                continue
            i = b.find(needle[busy], t.px_off)
            if i >= 0:
                tw = t.px_wh[0]
                off = (i - t.px_off) // 2
                print(os.path.relpath(p, root), f"at VRAM-unit x {off % tw}, y {off // tw - busy}, {t.bpp}bpp, header slot {t.px_xy}")


if __name__ == "__main__":
    a = sys.argv
    vram = open(a[2], "rb").read()
    x, y, w, h = map(int, a[3:7])
    if a[1] == "png":
        png(vram, x, y, w, h, int(a[7]), int(a[8], 16), a[9])
    else:
        find(vram, x, y, w, h, a[7] if len(a) > 7 else str(ROOT / "work" / "x"))
