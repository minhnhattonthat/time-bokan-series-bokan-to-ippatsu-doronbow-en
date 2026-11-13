"""Dump each /STR/*.STR movie as raw 2352-byte sectors, and sample frames with ffmpeg's psxstr demuxer.

usage: str_frames.py BIN OUT_DIR [--every SECONDS]
Writes OUT_DIR/MOVIExx.raw and OUT_DIR/MOVIExx/fNNNN.png, one PNG every SECONDS (default 4) plus OUT_DIR/durations.tsv.
The .raw dump is a Form 2 sector copy; no re-encode happens here, this only samples for the survey."""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from disc import SECTOR, Disc


def dump(d, e, path):
    n = -(-e.size // 2048)
    with open(path, "wb") as f:
        for i in range(n):
            f.write(d.raw(e.lba + i))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bin")
    ap.add_argument("out")
    ap.add_argument("--every", type=float, default=4)
    a = ap.parse_args()
    d = Disc(a.bin)
    os.makedirs(a.out, exist_ok=True)
    tsv = open(os.path.join(a.out, "durations.tsv"), "w", encoding="utf-8")
    tsv.write("movie\tsectors\tframes_sampled\n")
    for p, e in sorted(d.files.items()):
        if not p.startswith("/STR/"):
            continue
        name = os.path.basename(p).split(".")[0]
        raw = os.path.join(a.out, name + ".raw")
        n = dump(d, e, raw)
        out = os.path.join(a.out, name)
        os.makedirs(out, exist_ok=True)
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "psxstr", "-i", raw, "-vf",
                            f"fps=1/{a.every}", os.path.join(out, "f%04d.png")], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"{name}: ffmpeg failed: {r.stderr[:400]}")
        tsv.write(f"{name}\t{n}\t{len(os.listdir(out))}\n")
        print(name, n, "sectors", len(os.listdir(out)), "frames", r.stderr[:80])
    assert SECTOR == 2352


if __name__ == "__main__":
    main()
