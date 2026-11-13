"""build.py: make the playable disc in build/ from rom/. Only Track 01 is rewritten; the audio tracks are hard links.

usage: build.py [OUTDIR] [--no-movies | --identity | --marker | --spike]
Default: the English disc from script/en/ (--no-movies skips the FMV burn, which takes minutes). Every Form 1 file goes
through disc.write_file, and every TIM through tim.pixels/with_pixels, so with --identity the output must equal the dump:
tests/test_build.py holds that. --marker paints each rect with its row number and burns a numbered test line into every
movie row (build/marker); --spike letters script/spike.tsv (build/spike). Follows desu-yo's build.py."""
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
EXE = "BOKAN.EXE"


def rebuild(data):
    t = tim.parse(data)
    return tim.with_pixels(t, data, tim.pixels(t, data)) if t else data


def english_files(d, log=None):
    """{file name: new bytes} of the files whose English isn't per TIM row: BOKAN.EXE (staff roll page table, card
    title) and the two staff roll glyph sheets. log: a list that gets the EXE's romdiff writes."""
    import credits
    import script_text
    import tl_check
    path = {e.path.strip("/").removesuffix(".BIN"): e.path for e in d.files.values()}
    exe, sheets = credits.english(d.read(path[EXE]), {f: d.read(path[f]) for f in credits.SHEETS}, log)
    exe = bytearray(exe)
    en = {r["id"]: r["en"] for r in tl_check.table(tl_check.EN / "text.tsv")}
    for r in script_text.rows():
        assert r.file == EXE and script_text.decode(exe[r.offset:r.offset + r.size]) == r.jp, r.id
        new = script_text.encode(en[r.id], r.size)
        if log is not None:
            log.append((r.offset, bytes(exe[r.offset:r.offset + r.size]), new, r.id))
        exe[r.offset:r.offset + r.size] = new
    return {EXE: bytes(exe), **sheets}


def build(out=None, identity=False, marker=False, spike=False, movies=True):
    """Returns the path of the new cue. identity: no edits. movies=False skips the English FMV burn."""
    mode = "identity" if identity else "marker" if marker else "spike" if spike else None
    out = Path(out or ROOT / ("build/" + mode if mode else "build"))
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
    rects, whole = {}, {}
    if mode in ("marker", "spike"):
        import gfx
        rects = gfx.marker_rects() if marker else gfx.spike_rows()
    elif mode is None:
        import gfx
        rects, whole = gfx.english_rows(), english_files(d)
    for e in d.files.values():
        if not d.is_xa(e):
            name = e.path.strip("/").removesuffix(".BIN")
            data = whole.pop(name) if name in whole else rebuild(d.read(e.path))
            if mode is None and name == "CHRPLY/SELNAME":
                data = gfx.stamp_x(data)
            if name in rects:
                data = (gfx.marked if marker else gfx.typeset)(data, rects.pop(name))
            if mode is None and name == "CHRPLY/TITLE4":
                data = gfx.no_card(data)
            d.write_file(e.path, data)
    d.f.close()
    assert not rects and not whole, f"no file for rows: {sorted(rects) + sorted(whole)}"
    if marker or (mode is None and movies):
        import fmv_burn
        import tl_check
        subs = fmv_burn.marker_subs if marker else tl_check.subs
        for movie, stats in fmv_burn.burn_all(str(out / TRACK1), subs).items():
            print(movie, stats)
    return out / CUE


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    print(build(args[0] if args else None, "--identity" in sys.argv, "--marker" in sys.argv, "--spike" in sys.argv,
                "--no-movies" not in sys.argv))
