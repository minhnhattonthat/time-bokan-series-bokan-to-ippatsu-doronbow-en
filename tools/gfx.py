"""Graphics-text edits on TIM pixels: the marker build paints each script/graphics.tsv rect with its row number, and
typeset() letters English into a rect (font spike now, the English build in phase 7). Ported from desu-yo's gfx.py.

usage: gfx.py ids                 row number, id and Japanese of every row (row number = line of graphics.tsv under the
                                  header, counting from 1)
Pixels only ever change inside a row's rect, through tim.with_pixels, so the STP bit and the CLUT stay untouched.
Colours come from the TIM's first real CLUT row (tim.best_clut): row 0 is a one-colour placeholder in many files here."""
import sys
from collections import namedtuple
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx_script
import tim

KEEP_FORMS = {"keep"}
# One font and size per label class (form column of graphics.tsv): (file in fonts/, size, 1 px outline). D11.
J10 = 1400 / 75  # Jersey 10's native size (upm / pixel unit): off-grid sizes make strokes uneven
CLASSES = {
    "menu": ("LiberationSans-Bold.ttf", 14, True),  # labels on bars and panels: Bangers' slant and halo closed counters
    "message": ("Bangers-Regular.ttf", 16, True),
    "piece": ("Bangers-Regular.ttf", 16, True),
    "list": ("Jersey10-Regular.ttf", J10, False),
    "voice": ("Jersey10-Regular.ttf", J10, False),
    "name": ("Bangers-Regular.ttf", 16, True),
    "label": ("Bangers-Regular.ttf", 14, True),
    "badge": ("Jersey10-Regular.ttf", 10, False),
    "stamp": ("Bangers-Regular.ttf", 18, True),
    "banner": ("Bangers-Regular.ttf", 22, True),
    "sfx": ("Bangers-Regular.ttf", 22, True),
    "tag": ("Jersey10-Regular.ttf", 10, True),
    "card": ("Bangers-Regular.ttf", 28, True),
    "sign": ("LiberationSans-Bold.ttf", 12, False),
    "credit": ("Jersey15-Regular.ttf", 15, True),
}
DIGITS = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
    ".": ("000", "000", "000", "000", "010"),
}


def pal(t, row=None):
    """The colours of CLUT row `row`, or of the TIM's first real row."""
    n = 2 ** t.bpp
    row = tim.best_clut(t) if row is None else row
    return list(t.clut[row * t.clut_wh[0]:row * t.clut_wh[0] + n]) if t.clut else []


def luma(c):
    return (c & 31) * 2 + ((c >> 5) & 31) * 4 + ((c >> 10) & 31)


def ink_indices(t):
    """(dark, bright) indices of the real CLUT row, skipping the transparent colour 0."""
    n = 2 ** t.bpp
    used = [(i, c) for i, c in enumerate(pal(t)) if c]
    if not used:
        return 1, n - 1
    return min(used, key=lambda e: luma(e[1]))[0], max(used, key=lambda e: luma(e[1]))[0]


def paint_marker(vals, width, rect, label, dark, bright):
    """Solid dark rect with a bright 1 px frame, filled with the label repeated, so a clipped edge or a stray neighbour
    shows at once in game. Wrapped into lines when the rect is too narrow for one copy."""
    x0, y0, w, h = rect
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            edge = y in (y0, y0 + h - 1) or x in (x0, x0 + w - 1)
            vals[y * width + x] = bright if edge else dark
    per_line = max(1, (w - 2) // 4)
    text = (label + " ") * (per_line * h // (len(label) + 1) + 2)
    lines = (h - 2) // 6 or 1
    for ln in range(lines):
        row = text[ln * per_line:(ln + 1) * per_line]
        for ci, ch in enumerate(row):
            g = DIGITS.get(ch)
            if not g:
                continue
            for gy, bits in enumerate(g):
                for gx, b in enumerate(bits):
                    px, py = x0 + 1 + ci * 4 + gx, y0 + 1 + ln * 6 + gy
                    if b == "1" and px < x0 + w - 1 and py < y0 + h - 1:
                        vals[py * width + px] = bright


def row_numbers():
    return {r.id: i + 1 for i, r in enumerate(gfx_script.rows())}


def marker_rects():
    """{file: [(rect, label), ...]} for the whole marker build."""
    out = {}
    for i, r in enumerate(gfx_script.rows()):
        if r.form not in KEEP_FORMS:
            out.setdefault(r.file, []).append(((r.x, r.y, r.w, r.h), str(i + 1)))
    return out


def pixel_width(t):
    return t.px_wh[0] * (4 if t.bpp == 4 else 2)


def tim_px(t, data):
    return np.array(tim.pixels(t, data), dtype=np.int32).reshape(t.px_wh[1], pixel_width(t))


def raster(text, form):
    """Boolean ink of the text on a frame that is the same for every one-line text of a class."""
    name, size, _ = CLASSES[form]
    font = ImageFont.truetype(str(ROOT / "fonts" / name), size)
    lines = text.split("|")
    w = max(int(font.getlength(ln)) for ln in lines) + 8
    pitch = sum(font.getmetrics())
    img = Image.new("1", (w, pitch * len(lines) + 8))
    d = ImageDraw.Draw(img)
    d.fontmode = "1"  # no antialiasing: smoothed small text turns to mush in a 16-colour palette
    for n, ln in enumerate(lines):
        d.text((w // 2, 4 + n * pitch), ln, font=font, fill=1, anchor="ma")
    return np.array(img)


def glyphs(text, form):
    """(ink, outline) boolean arrays of the text in its class style, cropped to the ink. "|" breaks a line."""
    outline = CLASSES[form][2]
    ink = raster(text, form)
    own, cols = np.flatnonzero(ink.any(axis=1)), np.flatnonzero(ink.any(axis=0))
    ink = ink[own[0]:own[-1] + 1, cols[0]:cols[-1] + 1]
    if not outline:
        return ink, np.zeros_like(ink)
    ink = np.pad(ink, 1)
    halo = np.zeros_like(ink)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            halo |= np.roll(np.roll(ink, dy, 0), dx, 1)
    return ink, halo & ~ink


def row_width(text, form):
    """The width gate: pixels this text takes in its class. typeset() refuses a text wider than its rect."""
    return glyphs(text, form)[0].shape[1]


def mode(vals):
    v, c = np.unique(vals, return_counts=True)
    return int(v[c.argmax()])


def sampled_inks(px, clut, margin=None):
    """(background per row, fill per row, outline) indices of a rect of the original; per row because labels sit on
    palette gradients. Background: the commonest of the margin (columns beside the rect), or of the rect's end columns.
    Fill: the commonest inside the strokes, per row only when no index dominates. Thin strokes take the brightest ink."""
    ends = np.concatenate([px[:, :2], px[:, -2:]], axis=1)
    side = ends if margin is None or not margin.size else margin
    if clut[0] == 0 and (px == 0).mean() >= 0.1:  # see-through: in a packed atlas the margin holds neighbours' ink
        bg = np.zeros(len(px), int)
    elif (side == mode(side)).mean() >= 0.6:
        bg = np.full(len(px), mode(side))
    else:
        bg = np.array([mode(row) for row in side])
    ink = px != bg[:, None]
    if not ink.any():
        return bg, bg, int(bg[0])
    lum = lambda i: luma(clut[i])  # noqa: E731
    core = np.zeros_like(ink)
    core[1:-1, 1:-1] = ink[1:-1, 1:-1] & ink[:-2, 1:-1] & ink[2:, 1:-1] & ink[1:-1, :-2] & ink[1:-1, 2:]
    if not core.any():
        fill = np.full(len(px), max(np.unique(px[ink]).tolist(), key=lum))
    elif (px[core] == mode(px[core])).mean() >= 0.6:
        fill = np.full(len(px), mode(px[core]))
    else:
        have = np.flatnonzero(core.any(axis=1))
        fill = np.array([mode(px[y][core[y]]) for y in have[np.abs(have[:, None] - np.arange(len(px))).argmin(axis=0)]])
    rest = px[ink & ~np.isin(px, fill)]
    return bg, fill, mode(rest) if rest.size else int(fill[0])


Inks = namedtuple("Inks", "fill line clear bg", defaults=(True, None))


def typeset(data, rows):
    """data (a TIM file) with each (rect, text, form, align[, Inks or CLUT row]) rect cleared and lettered. Raises
    ValueError on overflow: English is never clipped silently. A CLUT row (budgets.tsv's clut column) picks fill and
    outline by the colours the game draws the row with; without one, the first real row's colours are used."""
    t = tim.parse(data)
    assert t and t.bpp in (4, 8), "not a CLUT TIM"
    px = tim_px(t, data)
    for (x, y, w, h), text, form, align, *forced in rows:
        clut = pal(t, forced.pop() if forced and isinstance(forced[0], int) else None)
        assert x + w <= px.shape[1] and y + h <= px.shape[0], f"rect {x, y, w, h} outside {px.shape[1]}x{px.shape[0]}"
        ink, halo = glyphs(text, form)
        gh, gw = ink.shape
        if gw > w or gh > h:
            raise ValueError(f"{text!r} is {gw}x{gh} in class {form}, rect is {w}x{h}")
        margin = np.concatenate([px[y:y + h, max(x - 3, 0):x], px[y:y + h, x + w:x + w + 3]], axis=1)
        bg, fill, line = sampled_inks(px[y:y + h, x:x + w], clut, margin)
        clear = True
        if forced:
            fill, line, clear = np.full(h, forced[0].fill), forced[0].line, forced[0].clear
            if forced[0].bg is not None:
                bg = np.full(h, forced[0].bg)
        cell = px[y:y + h, x:x + w]
        if clear:
            cell[:] = bg[:, None]
        oy, ox = (h - gh) // 2, {"l": 0, "r": w - gw}.get(align, (w - gw) // 2)
        box = cell[oy:oy + gh, ox:ox + gw]
        box[halo] = line
        box[ink] = np.broadcast_to(fill[oy:oy + gh, None], ink.shape)[ink]
    return tim.with_pixels(t, data, px.reshape(-1).tolist())


def spike_rows(path=ROOT / "script" / "spike.tsv"):
    """{file: [(rect, text, form, align), ...]} of the font spike's test lines. Columns id, en, class (empty = the
    row's form)."""
    by_id = {r.id: r for r in gfx_script.rows()}
    cluts = drawn_cluts()
    out = {}
    for ln in path.read_text(encoding="utf-8").splitlines()[1:]:
        rid, en, *form = ln.split("\t")  # an empty class may lose its tab to an editor
        r = by_id[rid]
        form = form[0] if form and form[0] else r.form
        row = ((r.x, r.y, r.w, r.h), en, form, "l" if r.form == "credit" else "c")
        out.setdefault(r.file, []).append(row + ((cluts[rid],) if rid in cluts else ()))
    return out


def drawn_cluts(path=ROOT / "script" / "budgets.tsv"):
    """{row id: the first CLUT row the game drew it with} from script/budgets.tsv."""
    out = {}
    for ln in path.read_text(encoding="utf-8").splitlines()[1:]:
        c = ln.split("\t")
        if len(c) > 6 and c[6]:
            out[c[0]] = int(c[6].split(",")[0])
    return out


def marked(data, rects):
    """data (a TIM file) with every rect painted."""
    t = tim.parse(data)
    assert t, "not a TIM"
    vals = tim.pixels(t, data)
    width = pixel_width(t)
    dark, bright = ink_indices(t)
    for rect, label in rects:
        x, y, w, h = rect
        assert x + w <= width and y + h <= t.px_wh[1], f"rect {rect} outside {width}x{t.px_wh[1]}"
        paint_marker(vals, width, rect, label, dark, bright)
    return tim.with_pixels(t, data, vals)


if __name__ == "__main__":
    for i, r in enumerate(gfx_script.rows()):
        print(i + 1, r.id, r.jp, sep="\t")
