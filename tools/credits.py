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


ROOM = 276  # page x + 32 = screen x (staff dumps); keep 12 px at the right, as the movies
LINE_GAP = 8  # px kept between two lines at one y of a page
SHEET_OF_PAGE = ["CHRPLY2/END_STF0"] * 15 + ["CHRPLY2/END_STF1"] * 10  # pages 0-14, 15-24 (docs/re/credits.md)


def pack(strips, keep):
    """{key: (u, v)} for each (key, w, h) strip in a 256x256 sheet, clear of the keep rects (x, y, w, h). Shelf packing,
    tallest then widest first, each strip in the first shelf with room. ValueError when the sheet is full."""
    shelves, top, at = [], 0, {}
    for key, w, h in sorted(strips, key=lambda s: (-s[2], -s[1], s[0])):
        spot = next(((sh, i) for sh in shelves if sh[1] >= h for i, (a, b) in enumerate(sh[2]) if b - a >= w), None)
        if not spot:
            if top + h > 256:
                raise ValueError(f"credit sheet full at {key!r}")
            free, a = [], 0
            for c0, c1 in sorted((kx, kx + kw) for kx, ky, kw, kh in keep if ky < top + h and top < ky + kh):
                free.append((a, c0))
                a = max(a, c1)
            free.append((a, 256))
            shelves.append((top, h, free))
            top += h
            i = next((i for i, (a, b) in enumerate(free) if b - a >= w), None)
            if i is None:
                raise ValueError(f"credit strip {key!r} is {w} px, wider than a shelf")
            spot = (shelves[-1], i)
        sh, i = spot
        a, b = sh[2][i]
        sh[2][i] = (a + w, b)
        at[key] = (a, sh[0])
    return at


def english(exe, sheet_data, log=None):
    """(exe, {sheet: TIM bytes}) with the English roll: every text cell cleared (icons kept), each line's parts
    (script/en/credits.tsv, "|") lettered flat in the line's own ink, as the Japanese glyphs (no outline), packed into
    the sheet its page samples, and the line's page entries pointed at them in place. A line with fewer parts than
    entries repeats its last part; one with more joins its last parts into one strip. log: a list that gets one
    romdiff write (offset, original bytes, new bytes, by) per page entry."""
    import numpy as np
    import gfx
    import tl_check
    en = {int(r["n"]): r["en"] for r in tl_check.table(tl_check.EN / "credits.tsv")}
    src = table_lines()
    by_shape = {tuple(p[1:] for p in ps): (n, kind) for n, kind, _, ps in src}
    tims = {f: tim.parse(b) for f, b in sheet_data.items()}
    px = {f: gfx.tim_px(t, sheet_data[f]) for f, t in tims.items()}
    full = SHEETS[0][:-4]
    keep = {f: [] for f in SHEETS}
    for n, kind, _, ps in src:
        if kind == "icon":
            keep[full + ps[0][0]] += [(u, v, w, h) for _, u, v, w, h, _ in ps]
    pgs = pages(exe)
    keep[SHEETS[0]] += [(e.u, e.v, e.w, e.h) for e in pgs[25][1]]  # the four face icons

    def ink(text):
        frame = gfx.raster(text, "credit")
        cols = np.flatnonzero(frame.any(axis=0))
        return frame[:, cols[0]:cols[-1] + 1]

    def outline(p, line):
        """(ink, halo) of p padded 1 px all round; the halo is empty when line is 0 (no outline)."""
        p = np.pad(p, 1)
        halo = np.zeros_like(p)
        if line:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    halo |= np.roll(np.roll(p, dy, 0), dx, 1)
        return p, halo & ~p

    texts = [p.strip() for e in en.values() if e for p in e.split("|")]
    rows = np.flatnonzero(np.logical_or.reduce([ink(t).any(axis=1) for t in texts]))
    band0, band = rows[0], rows[-1] - rows[0] + 1  # rows every line's ink falls in, so lines share one baseline
    jobs = []  # (page, line entries, n, kind)
    for pi in range(25):
        for g in page_lines(pgs[pi][1]):
            n, kind = by_shape[tuple((e.u, e.v, e.w, e.h, e.x - g[0].x) for e in g)]
            if kind != "icon" and en[n]:
                jobs.append((pi, g, n, kind))
    strips, placed = {}, []
    for pi, g, n, kind in jobs:
        f = SHEET_OF_PAGE[pi]
        old = np.concatenate([px[f][e.v:e.v + e.h, e.u:e.u + e.w].ravel() for e in g])
        vals, cnt = np.unique(old[old != 0], return_counts=True)
        fill = int(vals[cnt.argmax()])
        parts = [ink(p.strip()) for p in en[n].split("|")]
        # role and heading glyphs are bright (15) with a dark outline (11) in the page's CLUT row; names flat white (1)
        lined = len(parts) if kind in ("role", "head") else 1 if kind == "role+name" else 0
        two = {11, 15} <= set(vals.tolist())
        styles = [(15, 11) if i < lined and two else (1 if kind == "role+name" else fill, 0) for i in range(len(parts))]
        parts = [(np.dstack(outline(p, s[1])), s) for p, s in zip(parts, styles)]  # [h, w, (ink, halo)]
        if len(parts) > len(g):  # join the tail into the last entry's strip (one style: the tail's first)
            gap = np.zeros((parts[0][0].shape[0], tl_check.CREDIT_GAP, 2), bool)
            tail = parts[len(g) - 1:]
            parts = parts[:len(g) - 1] + [(np.hstack([a for p, _ in tail for a in (p, gap)][:-1]), tail[0][1])]
        inked = sum(p.shape[1] for p, _ in parts)
        gap = tl_check.CREDIT_GAP
        if len(parts) > 1 and inked + gap * (len(parts) - 1) > ROOM:  # page x can't go below 0 (u8)
            gap = max(8, (ROOM - inked) // (len(parts) - 1))
        # a copyright line split as its entries keeps their x (the Tatsunoko mark sits between (C) and the name)
        offs = [e.x - g[0].x for e in g] if kind == "copy" and len(parts) == len(g) else [0] * len(parts)
        pos, dx = [], 0
        for (p, _), o in zip(parts, offs):
            pos.append(max(dx, o))
            dx = pos[-1] + p.shape[1] + gap
        width = dx - gap
        x0, x1 = g[0].x, g[-1].x + g[-1].w
        x = (x0 + x1 - width) // 2 if kind == "head" or pi in (0, 15) else x0
        x = max(0, min(x, ROOM - width))
        if x + width > ROOM:
            raise ValueError(f"credit {n}: {width} px, room {ROOM}")
        y = g[0].y + (g[0].h - band) // 2 - band0
        ents = []
        for (p, (fill, line)), dx in zip(parts, pos):
            r = np.flatnonzero(p.any(axis=(1, 2)))
            key = (f, p[r[0]:r[-1] + 1].tobytes(), p.shape[1], fill, line)
            strips[key] = (p[r[0]:r[-1] + 1], fill, line)
            ents.append((key, dx, y - 1 + r[0]))  # -1: outline() pads a row above the ink
        placed.append([pi, g, n, x, width, ents])
    rows = {}
    for ln in placed:
        rows.setdefault((ln[0], ln[1][0].y), []).append(ln)
    for (pi, _), ls in rows.items():  # two lines at one y: slide the right one right, then the left one left
        ls.sort(key=lambda ln: ln[3])
        for a, b in zip(ls, ls[1:]):
            need = a[3] + a[4] + LINE_GAP - b[3]
            if need > 0:
                step = min(need, ROOM - b[4] - b[3])
                b[3] += step
                a[3] -= min(need - step, a[3])
            if b[3] < a[3] + a[4] + LINE_GAP:
                raise ValueError(f"credits {a[2]} and {b[2]} overlap on page {pi}")
    at = {}
    for f in SHEETS:
        mine = [(k, s.shape[1], s.shape[0]) for k, (s, *_) in strips.items() if k[0] == f]
        at.update(pack(mine, keep[f]))
        cleared = np.zeros_like(px[f])
        for kx, ky, kw, kh in keep[f]:
            cleared[ky:ky + kh, kx:kx + kw] = px[f][ky:ky + kh, kx:kx + kw]
        px[f] = cleared
    for k, (s, fill, line) in strips.items():
        u, v = at[k]
        cell = px[k[0]][v:v + s.shape[0], u:u + s.shape[1]]
        cell[s[..., 1]] = line
        cell[s[..., 0]] = fill
    out = bytearray(exe)
    for pi, g, n, x, _, ents in placed:
        for e, (key, dx, y) in zip(g, ents + [ents[-1]] * (len(g) - len(ents))):
            u, v = at[key]
            s = strips[key][0]
            struct.pack_into("<4B2H", out, e.off, u, v, x + dx, y, s.shape[1], s.shape[0])
            if log is not None:
                log.append((e.off, bytes(exe[e.off:e.off + 8]), bytes(out[e.off:e.off + 8]), f"page entry {pi}"))
    new = {f: tim.with_pixels(tims[f], sheet_data[f], px[f].reshape(-1).tolist()) for f in SHEETS}
    return bytes(out), new


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
