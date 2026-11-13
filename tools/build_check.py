"""Phase 7 gate: compare a built Track 01 with the dump, so an edit can't land outside where it is meant to go.

usage: build_check.py [BUILD_DIR]     default build/; exit 1 on any finding
Fails on a changed sector outside the allowed files, a changed TIM header or CLUT, a TIM pixel changed outside its rows'
rects, original text ink left beside a rect, a movie sector changed in anything but its video data or badly sealed, or
a BOKAN.EXE byte changed outside the staff roll page table and the card title (romdiff.check). Ported from desu-yo."""
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import credits
import disc
import gfx
import gfx_script
import mdec
import romdiff
import script_text
import tim
import tl_check

RING = 6  # px around a rect searched for leftover ink
# Rows whose fill index is also art beside the rect, read zoomed on row_sheet.py crops (2026-11-14): title panel frame,
# HUD art, the ranking skull, the voice list's side marks, the steel of the STOP sign, ship art round the name.
INK_NEAR_RECT = {"title.start", "title.card", "ship.rakuda", "rnk.ranking", "rnk.score", "hud.gameover", "voice.06",
                 "voice.21", "st5.stop"} | {f"song.{i:02}" for i in range(1, 21)}  # song plates' bevel and bolts


def allowed_rects():
    """{TIM file: [rect, ...]} the English may change; the credit sheets are cleared and relaid whole, so have none."""
    out = {f: [r[0] for r in rows] for f, rows in gfx.english_rows().items()}
    by_id = {r.id: r for r in gfx_script.rows()}
    out.setdefault("CHRPLY/TITLE4", []).extend([(u, v, w, h) for u, v, w, h, _ in gfx.CANVAS_PIECES]
                                               + [(by_id[i].x, by_id[i].y, by_id[i].w, by_id[i].h) for i in gfx.CANVAS_ROWS])
    return out


def exe_ranges():
    ok = set(range(*credits.PAGES))
    for r in script_text.rows():
        ok |= set(range(r.offset, r.offset + r.size))
    return ok


def leftovers(name, old, new, t, items, by_id, budgets):
    """Original text ink left beside a row's rect, inside the box the game draws: a rect that missed part of a glyph."""
    errs = []
    taken = [r[0] for _, r in items] + [(o.x, o.y, o.w, o.h) for o in by_id.values() if o.file == name and o.form != "keep"]
    for rid, row in items:
        if rid in INK_NEAR_RECT:
            continue
        o = by_id[rid]
        (x, y, w, h), box = row[0], gfx.uv_box(budgets[rid], row[0]) if rid in budgets else row[0]
        near = np.zeros(old.shape, bool)
        near[max(y - RING, box[1], 0):min(y + h + RING, box[1] + box[3]), max(x - RING, box[0], 0):min(x + w + RING, box[0] + box[2])] = True
        for rx, ry, rw, rh in taken:
            near[ry:ry + rh, rx:rx + rw] = False
        _, fill, _ = gfx.sampled_inks(old[o.y:o.y + o.h, o.x:o.x + o.w], t.clut)
        hits = near & (old == new) & np.isin(old, np.unique(fill))
        if hits.any():
            ys, xs = np.nonzero(hits)
            errs.append(f"{rid}: {len(ys)} px of original ink beside the rect, first at {xs[0]},{ys[0]}")
    return errs


def movie_sector(lba, old, new):
    """Only a video sector's frame size, bitstream header and data may change, and its EDC/ECC must be right."""
    if struct.unpack_from("<I", old, 24)[0] != mdec.MAGIC:
        return [f"LBA {lba}: a movie sector that isn't video changed"]
    if old[:36] != new[:36] or old[40:44] != new[40:44] or old[52:56] != new[52:56]:
        return [f"LBA {lba}: movie sector header changed"]
    sealed = bytearray(new)
    disc.form1_seal(sealed)
    return [] if sealed == new else [f"LBA {lba}: bad EDC/ECC on a movie sector"]


def check(build_dir):
    """(findings, one-line summary)."""
    a, b = disc.Disc(str(ROOT / "rom" / build.TRACK1)), disc.Disc(str(Path(build_dir) / build.TRACK1))
    errs = []
    rects = allowed_rects()
    allowed = set(rects) | set(credits.SHEETS) | {build.EXE}
    x = np.memmap(str(ROOT / "rom" / build.TRACK1), dtype=np.uint8, mode="r")
    y = np.memmap(str(Path(build_dir) / build.TRACK1), dtype=np.uint8, mode="r")
    if len(x) != len(y):
        return [f"track size {len(x)} became {len(y)}"], ""
    n = len(x) // disc.SECTOR
    moved = np.flatnonzero((x[:n * disc.SECTOR].reshape(n, -1) != y[:n * disc.SECTOR].reshape(n, -1)).any(axis=1))
    owner = {}
    for path, e in a.files.items():
        for i in range(-(-e.size // 2048)):
            owner[e.lba + i] = path
    touched = {}
    for lba in moved.tolist():
        path = owner.get(lba)
        name = path.strip("/").removesuffix(".BIN") if path else None
        if path is None or not (name in allowed or path.startswith("/STR/")):
            errs.append(f"LBA {lba} changed, in {path or 'no file'}")
        else:
            touched[path] = touched.get(path, 0) + 1
            if path.startswith("/STR/"):
                errs += movie_sector(lba, x[lba * disc.SECTOR:(lba + 1) * disc.SECTOR].tobytes(),
                                     y[lba * disc.SECTOR:(lba + 1) * disc.SECTOR].tobytes())
    budgets = {r["id"]: r for r in tl_check.table(ROOT / "script" / "budgets.tsv")}
    by_id = {r.id: r for r in gfx_script.rows()}
    items = {}
    for rid, file, row in gfx.english_items():
        items.setdefault(file, []).append((rid, row))
    files = 0
    for path in touched:
        name = path.strip("/").removesuffix(".BIN")
        if path.startswith("/STR/"):
            continue
        old, new = a.read(path), b.read(path)
        files += 1
        if name == build.EXE:
            errs += [f"{build.EXE}: {e}" for e in romdiff.check(old, new, exe_ranges(), [])[0]]
            continue
        t = tim.parse(old)
        if old[:t.px_off] != new[:t.px_off]:
            errs.append(f"{path}: TIM header or CLUT changed")
        if name in credits.SHEETS:
            continue
        p, q = gfx.tim_px(t, old), gfx.tim_px(t, new)
        errs += leftovers(name, p, q, t, items.get(name, []), by_id, budgets)
        mask = p != q
        for rx, ry, rw, rh in rects[name]:
            mask[ry:ry + rh, rx:rx + rw] = False
        if mask.any():
            ys, xs = np.nonzero(mask)
            errs.append(f"{path}: {len(ys)} pixels outside rects, first at {xs[0]},{ys[0]}")
    return errs, f"{len(moved)} sectors changed in {files} files and {sum(p.startswith('/STR/') for p in touched)} movies"


if __name__ == "__main__":
    findings, summary = check(sys.argv[1] if len(sys.argv) > 1 else ROOT / "build")
    for f in findings:
        print(f)
    print(f"{len(findings)} findings; {summary}")
    sys.exit(1 if findings else 0)
