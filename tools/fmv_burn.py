"""Burn subtitles into STR movies on a built disc, in place: only macroblocks under the text are repainted, each frame
keeps its sectors, and audio sectors stay untouched (see tools/mdec.py). A frame that no longer fits its sectors is
re-quantised whole, one step at a time up to mdec.MAX_Q: here most subtitled frames (MOVE04 1390 of 1472), +6 to +12
steps per movie at most (phase 7 build).

Library: burn_all(track_path, subs_of) where subs_of(movie) gives [(start s, end s, text)]."""
import concurrent.futures as cf
import os
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import disc
import mdec

FONT = ROOT / "fonts" / "LiberationSerif-Bold.ttf"
# The movies are 640x240: each pixel is half as wide as tall, so text is drawn on a 320-wide square-pixel canvas and
# stretched 2x across. Sizes below are in canvas pixels.
XSCALE = 2
SIZE = 15
LINE = 17
BLACK, WHITE = -112.0, 107.0  # luma of the halo and the ink
MAX_W = 296        # canvas is 320 wide, keep 12 px each side
MAX_LINES = 3
BOTTOM = 226       # last text row of the 240-line picture, clear of TV overscan
SECTORS_PER_SEC = 150
WORDS_MAX = 16416  # largest MDEC size in the original movies (MOVE03), so the one player's buffer is known to hold it
MARKER = "The quick brown fox jumps over the lazy dog, again and again and again"


def wrap(text, font, width=MAX_W):
    """Greedy word wrap by pixel width."""
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if font.getlength(t) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur] if cur else lines


def balance(lines, font):
    """lines with words moved down while that narrows the wider of each pair, so a greedy wrap leaves no lone last word."""
    lines = [ln.split() for ln in lines]
    width = lambda words: font.getlength(" ".join(words))  # noqa: E731
    for i in range(len(lines) - 1, 0, -1):
        while len(lines[i - 1]) > 1:
            up, down = lines[i - 1][:-1], [lines[i - 1][-1]] + lines[i]
            if width(down) > MAX_W or max(width(up), width(down)) >= max(width(lines[i - 1]), width(lines[i])):
                break
            lines[i - 1], lines[i] = up, down
    return [" ".join(ln) for ln in lines]


def text_masks(lines, w, h):
    """(ink, halo) 0-1 float masks of the subtitle: antialiased, centred, descenders ending on BOTTOM, with a soft dark
    halo so it reads on any picture and a smooth edge costs few bits."""
    font = ImageFont.truetype(str(FONT), SIZE)
    cw = w // XSCALE
    im = Image.new("L", (cw, h))
    d = ImageDraw.Draw(im)
    baseline = BOTTOM - font.getmetrics()[1]
    for n, ln in enumerate(reversed(lines)):
        d.text(((cw - int(font.getlength(ln))) // 2, baseline - n * LINE), ln, font=font, fill=255, anchor="ls")
    spread = im.point(lambda v: 255 if v > 51 else 0).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.5))
    im, spread = (x.resize((w, h), Image.BILINEAR) for x in (im, spread))
    return np.array(im) / 255.0, np.clip(np.array(spread) / 255.0 * 1.3, 0, 1)


def burn_frame(p, ink, halo):
    """Blend onto Picture p: the picture fades to black and grey under the halo, then white ink goes on top."""
    rows = np.flatnonzero(halo.any(axis=1))
    if not len(rows):
        return
    for r in range(rows[0] // 16, rows[-1] // 16 + 1):
        for c in range(p.cols):
            h = halo[r * 16:r * 16 + 16, c * 16:c * 16 + 16]
            if not h.any():
                continue
            i = ink[r * 16:r * 16 + 16, c * 16:c * 16 + 16]
            y, cb, cr = p.get_mb(c, r)
            y = (y - BLACK) * (1 - h) + BLACK + i * (WHITE - BLACK)
            keep = 1 - h.reshape(8, 2, 8, 2).mean(axis=(1, 3))
            p.set_mb(c, r, y, cb * keep, cr * keep)


def burn_movie(track, entry, movie, subs):
    """New raw sectors {lba: bytes} for one movie. subs = [(start, end, text)]; times in seconds."""
    d = disc.Disc(track)
    n = -(-entry.size // 2048)
    raw = {i: d.raw(entry.lba + i) for i in range(n)}
    font = ImageFont.truetype(str(FONT), SIZE)
    frames = mdec.frames(raw.items())
    masks = {}
    out = {}
    stats = dict(frames=0, requant=0, max_q_step=0, frames_total=len(frames))
    for f in frames:
        t = f.sectors[0] / SECTORS_PER_SEC
        sub = next((s for s in subs if s[0] <= t < s[1]), None)
        if not sub:
            continue
        if sub[2] not in masks:
            lines = balance(wrap(sub[2], font), font)
            assert len(lines) <= MAX_LINES, f"{movie}: subtitle over {MAX_LINES} lines: {sub[2]!r}"
            masks[sub[2]] = text_masks(lines, f.w, f.h)
        bs = mdec.frame_bytes(f, raw.__getitem__)
        p = mdec.Picture(bs, f.w, f.h)
        burn_frame(p, *masks[sub[2]])
        cap = f.chunks * mdec.CHUNK
        new = p.tobytes()
        q = p.q
        while len(new) > cap or struct.unpack_from("<H", new)[0] > WORDS_MAX:
            q += 1
            assert q <= mdec.MAX_Q, f"{movie} frame {f.no}: no qscale fits {cap} bytes, {WORDS_MAX} words"
            new = p.tobytes_at(q)
        stats["requant"] += q != p.q
        stats["max_q_step"] = max(stats["max_q_step"], q - p.q)
        for idx, i in enumerate(f.sectors):
            sec = bytearray(raw[i])
            struct.pack_into("<I", sec, 36, len(new))
            sec[44:52] = new[:8]
            sec[56:56 + mdec.CHUNK] = new[idx * mdec.CHUNK:(idx + 1) * mdec.CHUNK].ljust(mdec.CHUNK, b"\0")
            disc.form1_seal(sec)
            out[entry.lba + i] = bytes(sec)
        stats["frames"] += 1
    return movie, out, stats


def read_rows(movie):
    path = ROOT / "script" / "fmv" / f"{movie}.tsv"
    rows = []
    for ln in path.read_text(encoding="utf-8").splitlines()[1:]:
        c = ln.split("\t")
        rows.append((float(c[0]), float(c[1]), c[2], c[3], c[4]))
    return rows


def burn_all(track, subs_of, jobs=None):
    """Writes every movie's new sectors into track. subs_of(movie) -> [(start, end, text)]. Returns stats by movie."""
    d = disc.Disc(track)
    entries = {os.path.basename(p).split(".")[0]: e for p, e in d.files.items() if p.startswith("/STR/")}
    d.f.close()
    jobs_list = [(track, e, movie, subs_of(movie)) for movie, e in sorted(entries.items())]
    report = {}
    with cf.ProcessPoolExecutor(jobs or min(8, os.cpu_count())) as ex:
        results = list(ex.map(burn_movie, *zip(*jobs_list)))
    with open(track, "r+b") as f:
        for movie, out, stats in results:
            for lba, sec in out.items():
                f.seek(lba * disc.SECTOR)
                f.write(sec)
            report[movie] = stats
    return report


def marker_subs(movie):
    """Marker build: the row's id on every spoken or captioned row, then a line that fills the width."""
    return [(row[0], row[1], f"{movie[4:]}.{n} {MARKER}") for n, row in enumerate(read_rows(movie), 1)
            if row[2] in ("dlg", "caption", "form")]
