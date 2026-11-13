"""Sweep helpers: find TIMs embedded inside binaries, and TIMs whose CLUT 0 hides pixels.

usage: tim_survey.py embedded DIR   (TIM headers at any 4-byte offset of every non-TIM file, and past the first TIM)
       tim_survey.py hidden DIR     (share of non-zero-index pixels CLUT 0 draws as transparent or flat black)"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import tim


def walk(top):
    for r, _, fs in os.walk(top):
        for f in sorted(fs):
            p = os.path.join(r, f)
            yield os.path.relpath(p, top).replace(os.sep, "/"), open(p, "rb").read()


def embedded(top):
    for rel, b in walk(top):
        if rel.startswith("SE/"):
            continue
        first = tim.parse(b)
        start = first.size if first else 0
        for off in range(start, len(b) - 16, 4):
            if b[off:off + 4] == b"\x10\0\0\0":
                t = tim.parse(b, off)
                if t and t.px_wh[0] and t.px_wh[1]:
                    print(f"{rel} +{off:#x} bpp{t.bpp} {t.px_wh} cluts {t.clut_wh} size {t.size}")


def hidden(top):
    rows = []
    for rel, b in walk(top):
        t = tim.parse(b)
        if not t or t.bpp not in (4, 8) or not t.clut:
            continue
        w, h = t.px_wh
        px = b[t.px_off:t.px_off + w * h * 2]
        vals = [v for x in px for v in (x & 15, x >> 4)] if t.bpp == 4 else list(px)
        pal = t.clut[:t.clut_wh[0]]
        nz = [v for v in vals if v]
        if not nz:
            continue
        hide = sum(1 for v in nz if v < len(pal) and pal[v] in (0, 0x8000))
        rows.append((hide / len(nz), rel, t.clut_wh[1]))
    for share, rel, n in sorted(rows, reverse=True)[:40]:
        print(f"{share:6.1%} {rel} cluts={n}")


if __name__ == "__main__":
    {"embedded": embedded, "hidden": hidden}[sys.argv[1]](sys.argv[2])
