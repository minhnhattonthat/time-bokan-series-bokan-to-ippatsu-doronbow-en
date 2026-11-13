"""PS1 TIM reader: parse headers, classify a file tree, render to PNG.

usage: tim.py scan DIR | tim.py png FILE OUT.png [clut]
Library: parse(data, off=0) -> Tim or None; to_image(tim, clut=0) -> PIL RGBA image."""
import os
import struct
import sys
from collections import Counter, namedtuple

Tim = namedtuple("Tim", "off bpp clut clut_xy clut_wh px_xy px_wh px_off size")
BPP = {0: 4, 1: 8, 2: 16, 3: 24}


def parse(b, off=0):
    """Header at off, or None when it isn't a TIM. Width in the header is in 16-bit VRAM units."""
    if len(b) < off + 16 or struct.unpack_from("<I", b, off)[0] != 0x10:
        return None
    flags = struct.unpack_from("<I", b, off + 4)[0]
    mode = flags & 7
    if flags & ~0xF or mode > 3:
        return None
    p = off + 8
    clut = None
    cxy = cwh = (0, 0)
    if flags & 8:
        n = struct.unpack_from("<I", b, p)[0]
        cx, cy, cw, ch = struct.unpack_from("<4H", b, p + 4)
        if n != 12 + cw * ch * 2 or p + n > len(b):
            return None
        clut, cxy, cwh = struct.unpack_from(f"<{cw * ch}H", b, p + 12), (cx, cy), (cw, ch)
        p += n
    n = struct.unpack_from("<I", b, p)[0]
    x, y, w, h = struct.unpack_from("<4H", b, p + 4)
    if n != 12 + w * h * 2 or p + n > len(b):
        return None
    return Tim(off, BPP[mode], clut, cxy, cwh, (x, y), (w, h), p + 12, p + n - off)


def rgba(c, opaque=False):
    r, g, b = c & 31, (c >> 5) & 31, (c >> 10) & 31
    a = 255 if opaque or c else 0
    return (r * 255 // 31, g * 255 // 31, b * 255 // 31, a)


def pixels(t, data):
    """Stored pixel values, row by row: CLUT indices at 4 and 8 bpp, raw words at 16 bpp, raw bytes at 24 bpp."""
    w, h = t.px_wh
    px = data[t.px_off:t.px_off + w * h * 2]
    if t.bpp == 4:
        return [v for byte in px for v in (byte & 15, byte >> 4)]
    return list(struct.unpack(f"<{w * h}H", px)) if t.bpp == 16 else list(px)


def with_pixels(t, data, vals):
    """data with its pixel block replaced by vals (as from pixels); header, CLUT and trailing bytes stay."""
    if t.bpp == 4:
        px = bytes(lo | hi << 4 for lo, hi in zip(vals[::2], vals[1::2]))
    else:
        px = struct.pack(f"<{len(vals)}H", *vals) if t.bpp == 16 else bytes(vals)
    assert len(px) == t.px_wh[0] * t.px_wh[1] * 2, "pixel count differs from the TIM's"
    return data[:t.px_off] + px + data[t.px_off + len(px):]


def best_clut(t):
    """First CLUT row with more than two colours: many files here keep a one-colour placeholder in row 0."""
    cw = t.clut_wh[0]
    for i in range(len(t.clut) // cw if t.clut else 0):
        if len(set(t.clut[i * cw:(i + 1) * cw])) > 2:
            return i
    return 0


def to_image(t, data, clut=0):
    from PIL import Image
    w, h = t.px_wh
    cw = t.clut_wh[0]
    pal = [rgba(c) for c in t.clut[clut * cw:(clut + 1) * cw]] if t.clut else None
    vals = pixels(t, data)
    if t.bpp == 4:
        size = (w * 4, h)
    elif t.bpp == 8:
        size = (w * 2, h)
    elif t.bpp == 16:
        pal, size = None, (w, h)
    else:
        return Image.frombytes("RGB", (w * 2 // 3, h), bytes(vals)).convert("RGBA")
    img = Image.new("RGBA", size)
    if pal is None and t.bpp in (4, 8):
        pal = [(v * 255 // (2 ** t.bpp - 1),) * 3 + (255,) for v in range(2 ** t.bpp)]  # no CLUT: greyscale
    img.putdata([pal[v] if v < len(pal) else (255, 0, 255, 255) for v in vals] if pal else [rgba(v) for v in vals])
    return img


if __name__ == "__main__":
    if sys.argv[1] == "scan":
        c = Counter()
        for r, _, fs in os.walk(sys.argv[2]):
            for f in fs:
                b = open(os.path.join(r, f), "rb").read()
                t = parse(b)
                folder = os.path.relpath(r, sys.argv[2]).split(os.sep)[0]
                if t:
                    tail = "" if t.size == len(b) else f" +{len(b) - t.size}b"
                    c[f"tim{t.bpp} {folder}{tail if len(tail) < 8 else ' +tail'}"] += 1
                else:
                    c[f"{b[:4].hex()} {folder} {os.path.splitext(f)[1]}"] += 1
        for k, v in sorted(c.items()):
            print(v, k)
    else:
        b = open(sys.argv[2], "rb").read()
        t = parse(b)
        assert t, "not a TIM"
        c = sys.argv[4] if len(sys.argv) > 4 else "0"
        to_image(t, b, best_clut(t) if c == "auto" else int(c)).save(sys.argv[3])
