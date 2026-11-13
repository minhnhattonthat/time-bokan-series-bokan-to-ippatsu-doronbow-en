"""build.py: make the playable disc in build/ from rom/. Only Track 01 is rewritten; the audio tracks are hard links.

usage: build.py [OUTDIR] [--identity]
Every Form 1 file goes through disc.write_file, and every TIM through tim.pixels/with_pixels, so with --identity the
output must equal the dump: tests/test_build.py holds that. English edits arrive in later phases (follow desu-yo)."""
import os
import shutil
import sys
from pathlib import Path

import check_rom
import disc
import tim

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom"
CUE = "Time Bokan Series - Bokan to Ippatsu! Doronbow (Japan).cue"
TRACK1 = "Time Bokan Series - Bokan to Ippatsu! Doronbow (Japan) (Track 01).bin"


def rebuild(data):
    t = tim.parse(data)
    return tim.with_pixels(t, data, tim.pixels(t, data)) if t else data


def build(out=None, identity=False):
    """Returns the path of the new cue. identity: no edits (the only mode until phase 5)."""
    out = Path(out or ROOT / ("build/identity" if identity else "build"))
    check_rom.check()
    out.mkdir(parents=True, exist_ok=True)
    for p in ROM.iterdir():
        dst = out / p.name
        if p.name in (CUE, TRACK1):
            shutil.copyfile(p, dst)
        elif p.suffix == ".bin" and not dst.exists():
            try:
                os.link(p, dst)
            except OSError:  # out/ on another volume
                shutil.copyfile(p, dst)
    d = disc.Disc(str(out / TRACK1), write=True)
    for e in d.files.values():
        if not d.is_xa(e):
            d.write_file(e.path, rebuild(d.read(e.path)))
    d.f.close()
    return out / CUE


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    print(build(args[0] if args else None, "--identity" in sys.argv))
