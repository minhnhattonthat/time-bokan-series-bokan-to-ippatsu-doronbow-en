"""Decode chosen frames of a movie on a built disc (or the dump) to PNGs, and report how full each frame's sectors are.

usage: fmv_sheet.py TRACK.bin MOVE01 OUTDIR [--at SECONDS ...]     frames at those times -> OUTDIR/MOVE01_<s>.png
       fmv_sheet.py TRACK.bin MOVE01 --slack                       bytes free in each frame's sectors (min/median/max)
       fmv_sheet.py TRACK.bin MOVE01 OUTDIR --subs                 the middle of every subtitle -> move01_NN_sheet.png
Decoding is tools/mdec.py's own (versions 2 and 3), so it shows exactly what fmv_burn.py wrote."""
import argparse
import os
import statistics
import struct
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import disc
import fmv_burn
import mdec


def movie(track, name):
    d = disc.Disc(track)
    e = d.files[f"/STR/{name}.STR"]
    n = -(-e.size // 2048)
    raw = {i: d.raw(e.lba + i) for i in range(n)}
    return mdec.frames(raw.items()), raw.__getitem__


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("track")
    ap.add_argument("movie")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--at", type=float, nargs="*", default=[])
    ap.add_argument("--slack", action="store_true")
    ap.add_argument("--subs", action="store_true")
    a = ap.parse_args()
    frames, sec = movie(a.track, a.movie)
    if a.slack:
        free = [f.chunks * mdec.CHUNK - f.size for f in frames]
        qs = [struct.unpack_from("<H", mdec.frame_bytes(f, sec), 4)[0] for f in frames]
        print(f"{a.movie}: {len(frames)} frames, free bytes min {min(free)} median {statistics.median(free)} "
              f"max {max(free)}; qscale min {min(qs)} median {statistics.median(qs)} max {max(qs)}")
        return
    os.makedirs(a.out, exist_ok=True)
    if a.subs:  # the middle of every subtitle, 8 frames a sheet, for visual QA (names end in _sheet for qa_gate.py)
        import tl_check
        from PIL import ImageDraw
        subs = tl_check.subs(a.movie)
        for page in range(0, len(subs), 8):
            tiles = []
            for n, (s, e, _) in enumerate(subs[page:page + 8], page + 1):
                f = min(frames, key=lambda f: abs(f.sectors[0] / fmv_burn.SECTORS_PER_SEC - (s + e) / 2))
                tiles.append((f"{a.movie} #{n} {(s + e) / 2:.2f}s", mdec.Picture(mdec.frame_bytes(f, sec), f.w, f.h).rgb()))
            h, w = tiles[0][1].shape[:2]
            img = Image.new("RGB", (2 * (w + 2), -(-len(tiles) // 2) * (h + 14)), (30, 30, 30))
            draw = ImageDraw.Draw(img)
            for i, (label, px) in enumerate(tiles):
                x, y = (i % 2) * (w + 2), (i // 2) * (h + 14)
                draw.text((x + 2, y + 1), label, fill=(255, 255, 0))
                img.paste(Image.fromarray(px), (x, y + 14))
            img.save(os.path.join(a.out, f"{a.movie.lower()}_{page // 8:02d}_sheet.png"))
        return
    for t in a.at:
        f = min(frames, key=lambda f: abs(f.sectors[0] / fmv_burn.SECTORS_PER_SEC - t))
        p = mdec.Picture(mdec.frame_bytes(f, sec), f.w, f.h)
        out = os.path.join(a.out, f"{a.movie}_{t:g}.png")
        Image.fromarray(p.rgb()).save(out)
        print(out, "q", p.q)


if __name__ == "__main__":
    main()
