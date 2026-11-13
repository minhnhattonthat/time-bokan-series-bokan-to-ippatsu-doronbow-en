"""GPU primitives of a dumped frame (tools/debug/primdump.lua), matched to the TIM files in VRAM and to script/graphics.tsv.

usage: prims.py list RAM.bin                  every textured packet with a non-empty quad
       prims.py rows DIR [DIR ...] [--out F]  for each row of graphics.tsv, the quads that sample it, over all dumps
A packet counts only when its link word points into RAM or is the end marker. Stale packets from an earlier frame can
pass that test, so a row's list may hold extra quads; a quad whose texels are not in VRAM's current TIMs is dropped."""
import argparse
import glob
import os
import struct
import sys
from collections import defaultdict, namedtuple
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx_script
import tim

Prim = namedtuple("Prim", "addr code x y sw sh u v tw th vx vy bpp clut")
RAM = 0x200000
BPPS = {0: 4, 1: 8, 2: 16, 3: 16}


def s11(v):
    v &= 0x7FF
    return v - 0x800 if v & 0x400 else v


def decode(ram, a):
    """The FT3/FT4 packet at RAM offset a, or the game's sprite packet (n=5: E1 draw mode then SPRT; desu-yo's n=7 had
    two zero words between). None for anything else."""
    n, code = ram[a + 3], ram[a + 7]
    w = struct.unpack_from("<9I", ram, a + 4)
    if 0x24 <= code <= 0x27 and n == 7:
        vs = (1, 3, 5)
    elif 0x2C <= code <= 0x2F and n == 9:
        vs = (1, 3, 5, 7)
    elif code == 0xE1 and n in (5, 7) and 0x64 <= w[n - 4] >> 24 <= 0x67:
        s = n - 4  # the SPRT command word
        sw, sh = w[s + 3] & 0xFFFF, w[s + 3] >> 16
        if not (0 < sw <= 256 and 0 < sh <= 256):
            return None
        tp = w[0] & 0xFFFF
        bpp = BPPS[(tp >> 7) & 3]
        u, v = w[s + 2] & 0xFF, (w[s + 2] >> 8) & 0xFF
        vx, vy = (tp & 15) * 64 + u * bpp // 16, ((tp >> 4) & 1) * 256 + v
        return Prim(a, 0x64, s11(w[s + 1]), s11(w[s + 1] >> 16), sw, sh, u, v, sw, sh, vx, vy, bpp, w[s + 2] >> 16)
    else:
        return None
    xy = [(s11(w[i]), s11(w[i] >> 16)) for i in vs]
    uv = [(w[i + 1] & 0xFF, (w[i + 1] >> 8) & 0xFF) for i in vs]
    xs, ys, us, vvs = [p[0] for p in xy], [p[1] for p in xy], [p[0] for p in uv], [p[1] for p in uv]
    sw, sh, tw, th = max(xs) - min(xs), max(ys) - min(ys), max(us) - min(us), max(vvs) - min(vvs)
    if not (sw and sh and tw and th):
        return None
    tp = w[4] >> 16
    bpp = BPPS[(tp >> 7) & 3]
    u, v = min(us), min(vvs)
    vx, vy = (tp & 15) * 64 + u * bpp // 16, ((tp >> 4) & 1) * 256 + v
    return Prim(a, code, min(xs), min(ys), sw, sh, u, v, tw, th, vx, vy, bpp, w[2] >> 16)


def scan(ram):
    out = []
    for a in range(0, RAM - 72, 4):
        if ram[a + 3] not in (5, 7, 9) or not (0x24 <= ram[a + 7] <= 0x2F or ram[a + 7] == 0xE1):
            continue
        link = struct.unpack_from("<I", ram, a)[0] & 0xFFFFFF
        if link != 0xFFFFFF and (link >= RAM or link & 3):
            continue
        p = decode(ram, a)
        if p:
            out.append(p)
    return out


def ordering_tables(ram, min_len=256):
    """(first, last) RAM offsets of each ordering table: a run of words where an empty entry links to the one before it
    (ClearOTagR), its first entry being the end marker. This game keeps two (double buffer), 4096 entries each."""
    w = struct.unpack(f"<{len(ram) // 4}I", ram)
    out, start, end = [], None, None
    for i in range(1, len(w)):
        if w[i] == 4 * (i - 1):  # an empty entry: length 0, link to the previous word
            if start is None:
                start = i
            end = i
        elif start is not None and i - end > 64:
            if end - start >= min_len:
                out.append((4 * (start - 1), 4 * end))
            start = None
    if start is not None and end - start >= min_len:
        out.append((4 * (start - 1), 4 * end))
    return out


def live(ram):
    """[set of packet offsets] per ordering table: the packets one frame's chain reaches, walked from the table's last
    entry (where DrawOTag starts) to the end marker. Packets left in RAM from earlier frames are in no chain."""
    chains = []
    for first, last in ordering_tables(ram):
        seen, a = set(), last
        for _ in range(200000):
            if a == 0xFFFFFF or a >= RAM:
                break
            if not first <= a <= last:
                seen.add(a)
            a = struct.unpack_from("<I", ram, a)[0] & 0xFFFFFF
        chains.append(seen)
    return chains


def tims():
    """(file, Tim, data) of every TIM named by graphics.tsv."""
    seen = {}
    for r in gfx_script.rows():
        if r.file not in seen:
            b = open(ROOT / "work" / "x" / (r.file + ".BIN"), "rb").read()
            seen[r.file] = (tim.parse(b), b)
    return seen


def loaded(vram, t, b):
    """(x, y) of the TIM's pixel block in this VRAM dump, or None: tried at the header's slot, then anywhere, since code
    can load a file elsewhere (name tags and stage cards do). Needs 90% of bytes equal; the game may rewrite some."""
    (hx, hy), (w, h) = t.px_xy, t.px_wh
    px = b[t.px_off:t.px_off + w * h * 2]

    def match(x, y):
        same = n = 0
        for row in range(0, h, 8):
            if y + row >= 512:
                return False
            o = ((y + row) * 1024 + x) * 2
            a, c = vram[o:o + w * 2], px[row * w * 2:(row + 1) * w * 2]
            same += sum(p == q for p, q in zip(a, c))
            n += len(c)
        return n and same >= n * 0.9

    if hx + w <= 1024 and match(hx, hy):
        return hx, hy
    # search on the busiest sampled row, whole width
    row = max(range(0, h, 8), key=lambda r: len(set(px[r * w * 2:(r + 1) * w * 2])))
    needle = px[row * w * 2:(row + 1) * w * 2]
    if len(set(needle)) < 4:
        return None
    for y in range(512 - h + 1):
        o = (y + row) * 2048
        i = vram[o:o + 2048].find(needle)
        if i >= 0 and i % 2 == 0 and match(i // 2, y):
            return i // 2, y
    return None


def rows_report(dirs, out):
    all_tims = tims()
    hits = defaultdict(set)
    seen_files = defaultdict(set)
    for d in dirs:
        for ram_path in glob.glob(os.path.join(d, "*.ram.bin")):
            name = os.path.basename(ram_path)[:-8]
            vp = os.path.join(d, name + ".vram.bin")
            if not os.path.exists(vp):
                continue
            ram, vram = open(ram_path, "rb").read(), open(vp, "rb").read()
            here = {}
            for f, tb in all_tims.items():
                at = loaded(vram, *tb)
                if at:
                    here[f] = (tb[0], at)
            ps = {(p.x, p.y, p.sw, p.sh, p.vx, p.vy, p.tw, p.th, p.bpp, p.clut) for p in scan(ram)}
            scene = os.path.basename(d)
            for f in here:
                seen_files[f].add(scene)
            for r in gfx_script.rows():
                if r.file not in here:
                    continue
                t, at = here[r.file]
                scale = t.bpp / 16
                rx0, ry0 = at[0] + r.x * scale, at[1] + r.y
                rx1, ry1 = rx0 + r.w * scale, ry0 + r.h
                for x, y, sw, sh, vx, vy, tw, th, bpp, clut in ps:
                    if bpp != t.bpp:
                        continue
                    if vx < rx1 and vx + tw * scale > rx0 and vy < ry1 and vy + th > ry0:
                        # texel rect in TIM coordinates
                        tx, ty = round((vx - at[0]) / scale), vy - at[1]
                        hits[r.id].add((tx, ty, tw, th, x, y, sw, sh, clut, scene))
    lines = ["id\tfile\trect\tquad_uv\tscreen\tclut\tscenes"]
    missing = 0
    for r in gfx_script.rows():
        by = defaultdict(set)
        for tx, ty, tw, th, x, y, sw, sh, clut, scene in hits[r.id]:
            by[(tx, ty, tw, th, x, y, sw, sh, clut)].add(scene)
        if not by:
            missing += 1
            lines.append(f"{r.id}\t{r.file}\t{r.x},{r.y},{r.w},{r.h}\tNOT DRAWN\t\t\t{','.join(sorted(seen_files[r.file]))}")
        for (tx, ty, tw, th, x, y, sw, sh, clut), scenes in sorted(by.items()):
            lines.append(f"{r.id}\t{r.file}\t{r.x},{r.y},{r.w},{r.h}\t{tx},{ty},{tw},{th}\t{x},{y},{sw},{sh}\t{clut:04X}\t{','.join(sorted(scenes))[:60]}")
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(lines) - 1} lines, {missing} rows with no quad, {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "rows"])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out", default=str(ROOT / "work" / "recon" / "prims_rows.tsv"))
    a = ap.parse_args()
    if a.cmd == "list":
        for p in scan(open(a.paths[0], "rb").read()):
            print(f"{0x80000000 + p.addr:08X} {p.code:02X} screen {p.x:4},{p.y:4} {p.sw:3}x{p.sh:3} uv {p.u:3},{p.v:3} "
                  f"{p.tw:3}x{p.th:3} vram {p.vx:4},{p.vy:3} {p.bpp}bpp clut {p.clut:04X}")
    else:
        rows_report(a.paths, a.out)


if __name__ == "__main__":
    main()
