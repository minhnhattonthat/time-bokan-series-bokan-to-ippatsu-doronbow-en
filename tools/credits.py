"""The staff roll by line, from the GPU dumps of the `staff` warp scene (`warp_all.py --prims staff`).

usage: credits.py lines [DIR]            every distinct line, in roll order, with its pieces -> work/recon/credit_lines.tsv
       credits.py sheet [DIR] OUT.png    each line composed from its pieces, numbered, to read the Japanese by eye
The roll draws each line from pieces (sprites) of the END_STF0/1 glyph sheets, so a line = the pieces drawn at one screen
y in one frame, ordered by x, with their x offsets. A line scrolling across the band keeps its pieces and offsets, so it
is the same line in every frame it shows in. Pieces: FILE:u,v,w,h@dx (dx from the line's first piece)."""
import argparse
import glob
import os
import struct
import sys
from collections import defaultdict, namedtuple
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import prims
import tim

SHEETS = ("CHRPLY2/END_STF0", "CHRPLY2/END_STF1")
DEFAULT = ROOT / "work" / "qa" / "prim" / "staff"


def sheets():
    return {f: (tim.parse(b), b) for f in SHEETS for b in [(ROOT / "work" / "x" / (f + ".BIN")).read_bytes()]}


GAP = 48  # px between pieces that splits a row into two blocks (blocks on screen at once sit 200+ px apart)


def frame_lines(packets, vram, tims):
    """[(y, [(x, file, u, v, w, h, clut)])] of one frame's lines from the glyph sheets: pieces of one colour at one y,
    split where a gap exceeds GAP. packets = one ordering-table chain (prims.live), so no stale packet gets in."""
    at = {f: prims.loaded(vram, *tb) for f, tb in tims.items()}
    rows = defaultdict(set)
    for p in packets:
        p = p._replace(y=p.y % 240)  # the second display buffer draws 240 lines lower
        if p.bpp != 4:
            continue
        for f, xy in at.items():
            if not xy:
                continue
            t = tims[f][0]
            if xy[0] <= p.vx < xy[0] + t.px_wh[0] and xy[1] <= p.vy < xy[1] + t.px_wh[1]:
                rows[(p.y, p.clut)].add((p.x, f, (p.vx - xy[0]) * 4, p.vy - xy[1], p.tw, p.th, p.clut))
    out = []
    for (y, _), pieces in sorted(rows.items()):
        kept = sorted(pieces)
        group = [kept[0]]
        for pc in kept[1:]:
            if pc[0] - (group[-1][0] + group[-1][4]) > GAP:
                out.append((y, group))
                group = []
            group.append(pc)
        out.append((y, group))
    return out


def key(pieces):
    """A line's identity: its pieces and their x offsets from the first."""
    pieces = sorted(pieces)
    x0 = pieces[0][0]
    return tuple((f, u, v, w, h, x - x0) for x, f, u, v, w, h, _ in pieces)


def lines(d=DEFAULT):
    """[(key, first shot, screen y, clut)] of every distinct line, in order of first appearance."""
    tims = sheets()
    seen = {}
    for ram_path in sorted(glob.glob(os.path.join(d, "*.ram.bin"))):
        name = os.path.basename(ram_path)[:-8]
        ram = open(ram_path, "rb").read()
        vram = open(os.path.join(d, name + ".vram.bin"), "rb").read()
        packets = prims.scan(ram)
        for chain in prims.live(ram):
            for y, pieces in frame_lines([p for p in packets if p.addr in chain], vram, tims):
                k = key(pieces)
                if k not in seen:
                    seen[k] = (k, name, y, sorted({p[6] for p in pieces}))
    # A line that enters or leaves the screen shows only part of its pieces: keep the fullest copy only.
    out = list(seen.values())
    full = [ln for ln in out if not any(o is not ln and set(ln[0]) < set(o[0]) for o in out
                                        if _shifted_subset(ln[0], o[0]))]
    return full


def _shifted_subset(a, b):
    """Whether a's pieces appear in b with the same offsets between them."""
    if len(a) >= len(b):
        return False
    for i in range(len(b)):
        base = b[i][5] - a[0][5]
        bs = {(f, u, v, w, h, dx - base) for f, u, v, w, h, dx in b}
        if all(p in bs for p in a):
            return True
    return False


PAGES = (0x91854, 0x91FA0)  # BOKAN.EXE file offsets of the page table (docs/re/credits.md)
Entry = namedtuple("Entry", "off u v x y w h")


def pages(exe=None):
    """[(offset, [Entry])] of the roll's page table: u32 count, then count 8-byte entries u8 u, v, x, y; u16 w, h.
    x, y place the piece on the page; which glyph sheet a page samples is not in the table (code picks it)."""
    d = exe or (ROOT / "work" / "x" / "BOKAN.EXE").read_bytes()
    out, o = [], PAGES[0]
    while o < PAGES[1]:
        n = struct.unpack_from("<I", d, o)[0]
        assert 1 <= n <= 40, f"page at {o:X}: count {n}"
        es = [Entry(o + 4 + 8 * i, *struct.unpack_from("<4B2H", d, o + 4 + 8 * i)) for i in range(n)]
        assert all(0 < e.w and e.u + e.w <= 256 and e.v + e.h <= 256 for e in es), f"page at {o:X}"
        out.append((o, es))
        o += 4 + 8 * n
    assert o == PAGES[1]
    return out


def page_lines(es):
    """A page's entries as lines: same y, ordered by x, split at gaps over GAP (as frame_lines splits the screen)."""
    rows = defaultdict(list)
    for e in es:
        rows[e.y].append(e)
    out = []
    for y in sorted(rows):
        group = []
        for e in sorted(rows[y], key=lambda e: e.x):
            if group and e.x - (group[-1].x + group[-1].w) > GAP:
                out.append(group)
                group = []
            group.append(e)
        out.append(group)
    return out


def table_lines(path=ROOT / "script" / "credits.tsv"):
    """[(n, kind, jp, pieces)] of script/credits.tsv; pieces = [(sheet, u, v, w, h, dx)]."""
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines()[1:]:
        n, kind, jp, _y, pieces = ln.split("\t")
        ps = []
        for p in pieces.split():
            sheet, rest = p.split(":")
            box, dx = rest.split("@")
            ps.append((sheet, *map(int, box.split(",")), int(dx)))
        out.append((int(n), kind, jp, ps))
    return out


def fmt(k):
    return " ".join(f"{f[-4:]}:{u},{v},{w},{h}@{dx}" for f, u, v, w, h, dx in k)


def compose(k, tims, clut_row=None):
    """RGBA image of one line from its pieces."""
    from PIL import Image
    width = max(dx + w for *_, w, h, dx in [(p[0], p[1], p[2], p[3], p[4], p[5]) for p in k])
    height = max(p[4] for p in k)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    for f, u, v, w, h, dx in k:
        t, b = tims[f]
        src = tim.to_image(t, b, clut_row if clut_row is not None else tim.best_clut(t))
        img.alpha_composite(src.crop((u, v, u + w, v + h)), (dx, 0))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["lines", "sheet"])
    ap.add_argument("dir", nargs="?", default=str(DEFAULT))
    ap.add_argument("out", nargs="?")
    a = ap.parse_args()
    ls = lines(a.dir)
    if a.cmd == "lines":
        out = Path(a.out or ROOT / "work" / "recon" / "credit_lines.tsv")
        rows = ["n\tshot\ty\tclut\tpieces"] + [f"{i}\t{s}\t{y}\t{','.join(f'{c:04X}' for c in cl)}\t{fmt(k)}"
                                               for i, (k, s, y, cl) in enumerate(ls)]
        out.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        print(len(ls), "lines,", out)
    else:
        from PIL import Image, ImageDraw
        tims = sheets()
        imgs = [compose(k, tims) for k, *_ in ls]
        z = 2
        h = sum(im.height * z + 4 for im in imgs)
        w = max(im.width for im in imgs) * z + 40
        sheet = Image.new("RGB", (w, h), (64, 0, 64))
        d = ImageDraw.Draw(sheet)
        y = 0
        for i, im in enumerate(imgs):
            d.text((2, y + 2), str(i), fill=(255, 255, 0))
            sheet.paste(im.resize((im.width * z, im.height * z), Image.NEAREST), (36, y))
            y += im.height * z + 4
        sheet.save(a.out)
        print(len(imgs), "lines,", a.out)


if __name__ == "__main__":
    main()
