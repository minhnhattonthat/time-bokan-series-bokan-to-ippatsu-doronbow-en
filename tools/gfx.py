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
    "credit": ("Jersey15-Regular.ttf", 15, False),  # flat, as the roll's Japanese glyphs; an outline overfills END_STF0
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


Inks = namedtuple("Inks", "fill line clear bg shadow", defaults=(True, None, None))  # shadow: 1 px down-right


def inpaint(cell, mask):
    """cell (in place) with each masked pixel taken from the nearest unmasked one, sideways first, then up/down."""
    mask = mask.copy()
    h, w = cell.shape
    while mask.any():
        before = mask.sum()
        for dy, dx in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            src, ok = np.zeros_like(cell), np.zeros_like(mask)
            ys, yd = slice(max(-dy, 0), h - max(dy, 0)), slice(max(dy, 0), h - max(-dy, 0))
            xs, xd = slice(max(-dx, 0), w - max(dx, 0)), slice(max(dx, 0), w - max(-dx, 0))
            src[yd, xd], ok[yd, xd] = cell[ys, xs], ~mask[ys, xs]  # each pixel's neighbour at (-dy, -dx)
            take = mask & ok
            cell[take] = src[take]
            mask &= ~take
        if mask.sum() == before:
            raise ValueError("inpaint: nothing left to copy from")


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
        if not text:  # a clear-only rect (CLEARS): a glyph piece the row's own rect can't reach
            px[y:y + h, x:x + w] = forced[0].bg
            continue
        ink, halo = glyphs(text, form)
        sh = forced[0].shadow if forced else None
        if sh is not None:
            ink, halo = np.pad(ink, ((0, 1), (0, 1))), np.pad(halo, ((0, 1), (0, 1)))
            shadow = np.roll(np.roll(ink | halo, 1, 0), 1, 1) & ~ink & ~halo
        gh, gw = ink.shape
        if gw > w or gh > h:
            raise ValueError(f"{text!r} is {gw}x{gh} in class {form}, rect is {w}x{h}")
        margin = np.concatenate([px[y:y + h, max(x - 3, 0):x], px[y:y + h, x + w:x + w + 3]], axis=1)
        bg, fill, line = sampled_inks(px[y:y + h, x:x + w], clut, margin)
        clear = True
        if forced:
            if isinstance(forced[0].fill, tuple):  # a gradient, top to bottom over the rect, as the Japanese glyphs
                fill = np.array(forced[0].fill)[np.linspace(0, len(forced[0].fill) - 1, h).round().astype(int)]
            elif forced[0].fill is not None:  # None keeps the sampled fill
                fill = np.full(h, forced[0].fill)
            line, clear = forced[0].line, forced[0].clear
            if forced[0].bg == "above":  # textured plate: the rect takes the same-size patch just above it
                px[y:y + h, x:x + w] = px[y - h:y, x:x + w]
                clear = False
            elif isinstance(forced[0].bg, tuple):  # art behind the glyphs: erase only these indices, keep the rest
                cell0 = px[y:y + h, x:x + w]
                inpaint(cell0, np.isin(cell0, forced[0].bg))
                clear = False
            elif forced[0].bg == "row":  # each row's commonest non-text index of the rect itself (plates with bevels)
                cell0 = px[y:y + h, x:x + w]
                bg = np.array([mode(r[~np.isin(r, (forced[0].fill, line))]) if (~np.isin(r, (forced[0].fill, line))).any()
                               else int(r[0]) for r in cell0])
            elif forced[0].bg is not None:
                bg = np.full(h, forced[0].bg)
        cell = px[y:y + h, x:x + w]
        if clear:
            cell[:] = bg[:, None]
        oy, ox = (h - gh) // 2, {"l": 0, "r": w - gw}.get(align, (w - gw) // 2)
        box = cell[oy:oy + gh, ox:ox + gw]
        if sh is not None:
            box[shadow] = sh
        box[halo] = line
        box[ink] = np.broadcast_to(fill[oy:oy + gh, None], ink.shape)[ink]
    return tim.with_pixels(t, data, px.reshape(-1).tolist())


def uv_box(budget, rect):
    """The row's smallest drawn box that holds its rect, or the rect when nothing was measured (desu-yo)."""
    x, y, w, h = rect
    boxes = [tuple(map(int, u.split(","))) for u in budget["uv"].split(";")] if budget["uv"] else []
    held = [b for b in boxes if b[0] <= x and b[1] <= y and x + w <= b[0] + b[2] and y + h <= b[1] + b[3]]
    return min(held, key=lambda b: b[2] * b[3]) if held else rect


def widened(rect, need_w, need_h, box, others):
    """rect grown to need_w x need_h, around its centre as far as box allows, clear of the other rows' rects. ValueError
    if it can't: an overflow must stop the build."""
    x, y, w, h = rect
    if need_w > w:
        x, w = max(box[0], min(x - (need_w - w) // 2, box[0] + box[2] - need_w)), need_w
    if need_h > h:
        y, h = max(box[1], min(y - (need_h - h) // 2, box[1] + box[3] - need_h)), need_h
    if x + w > box[0] + box[2] or y + h > box[1] + box[3]:
        raise ValueError(f"rect {rect} can't reach {need_w}x{need_h} inside {box}")
    for o in others:
        if x < o[0] + o[2] and o[0] < x + w and y < o[1] + o[3] and o[1] < y + h:
            raise ValueError(f"rect {rect} grown to {x, y, w, h} hits {o}")
    return x, y, w, h


CANVAS_ROWS = ("card.p_memory", "card.p_inserted", "card.p_card", "card.p_imasen")
# The no-card message: two 64x40 quads side by side on screen (budgets.tsv), so one 128x40 canvas cut in two.
CANVAS_PIECES = ((32, 0, 64, 40, 0), (40, 40, 64, 40, 64))  # TIM x, y, w, h, canvas column
# row id: Inks, for rows whose sampled inks fail, read on row_sheet.py crops. Title and card menus: the Japanese blue
# gradient with the white outline (sampling took the dark green shadow); options: white on black (sampling alternated).
MENU_BLUE = (2, 3, 4, 5, 6)  # TITLE3/TITLE4 cyan to blue
# rows the Japanese starts on one column (title menu at x 144, card menu at x 120 with EXIT), so left, not centred
LEFT = {"title.start", "title.options", "title.card", "card.save", "card.load"}
ROW_INKS = {**{f"title.{k}": Inks(MENU_BLUE, 10) for k in ("start", "options", "card")},
            "card.save": Inks(MENU_BLUE, 15), "card.load": Inks(MENU_BLUE, 15),
            **{f"opt.{k}": Inks(15, 1) for k in ("level1", "level2", "level3", "level4", "credit", "sound", "keys",
                                                 "shot", "bomb")},
            "st5.stop": Inks(15, 10, bg="above"), "sel.repair": Inks(15, 1, False),
            # ship select: each name's light ink on the white outline, as the Japanese (sampling striped them)
            **{f"ship.{k}": Inks(i, 15) for k, i in (("syareko", 14), ("andoro", 4), ("rakuda", 10), ("sya_bagi", 8),
                                                    ("denden", 6), ("doron", 14), ("boya", 6), ("tonzr", 8),
                                                    ("gaikotu", 12))},
            "sel.gameover": Inks(14, 15, bg=(14, 15)), "sel.join_ok": Inks(6, 15),  # gameover: keep its bubble art
            "sel.banner": Inks(15, 13, bg=(10, 14, 15)),  # erase the white glyphs and their shadow, keep the plates
            # card messages: short ones blue on white as the menu, sentences white on dark blue
            **{f"card.{k}": Inks(MENU_BLUE, 15) for k in ("access", "save_ok", "load_ok")},
            **{f"card.{k}": Inks(15, 14) for k in ("this_card", "unformatted", "format_q", "no_space", "no_data",
                                                  "p_broken", "p_temasu", "p_save", "p_load", "p_failed")},
            # sound test voice captions: solid yellow (sampling took the shadow on some rows, so the letters striped)
            **{f"voice.{i:02}": Inks(5, 1, shadow=1) for i in range(1, 28)},
            "hud.pochitto": Inks(15, 1, bg=(15, 1, 2), shadow=1),  # erase the glyphs, keep the round red badge "hud.wait": Inks(10, 12), "boss5.anger": Inks(6, 1),
            "st5.safety": Inks(6, 15, bg=15), "st5.sign_small": Inks(11, 1, bg=8),
            **{f"tag.{k}": Inks(15, 1) for k in ("andoro", "boya", "denden", "doron", "gaikotu", "rakuda", "syareko",
                                                "sya_bagi", "tonzr", "tyarinko")}}  # white on the dark tag bar
SONG_INKS = Inks(15, 1, bg="row", shadow=1)  # white with a dark drop shadow, as the Japanese, on each row's plate
# row id: ((x, y, w, h, background index), ..) cleared beside the row, for glyph pieces an art piece keeps its rect from
# reaching: the tail of スコア's ス sits under the ranking skull (x 108-125, y 96-110).
CLEARS = {"rnk.score": ((118, 112, 8, 14, 0),)}


def stamp_x(data):
    """SELNAME with 整備中 gone and the X it lay on redrawn. The art mirrors about y 235.5 and each arm steps 1 px a
    row, so clean row 226 gives every covered row (227-244). Only the row's own rect changes; the English is lettered
    on it with clear off (ROW_INKS)."""
    t = tim.parse(data)
    px = tim_px(t, data)
    x, y, w, h = next((r.x, r.y, r.w, r.h) for r in gfx_script.rows() if r.id == "sel.repair")
    top = 226
    for row in range(top + 1, 236):
        k = row - top
        drawn = np.zeros(px.shape[1], dtype=px.dtype)
        drawn[7:10], drawn[45:48] = px[top, 7:10], px[top, 45:48]
        drawn[13 + k:23 + k] = px[top, 13:23]
        drawn[33 - k:43 - k] = px[top, 33:43]
        px[row, x:x + w] = px[471 - row, x:x + w] = drawn[x:x + w]
    return tim.with_pixels(t, data, px.reshape(-1).tolist())


def no_card(data):
    """TITLE4 with the no-card message lettered across both quads in the inks of ・メモリー: white (15) on its dark navy
    outline (14); sampling took the teal shading (8) for the outline, pale on the tan plate."""
    import tl_check
    t = tim.parse(data)
    px = tim_px(t, data)
    by_id = {r.id: r for r in gfx_script.rows()}
    r = by_id["card.p_memory"]
    bg = sampled_inks(px[r.y:r.y + r.h, r.x:r.x + r.w], pal(t, 0))[0]
    fill, line = [15], 14
    text = next(e["en"] for e in tl_check.table(ROOT / "script" / "en" / "graphics.tsv") if e["id"] == r.id)
    ink, halo = glyphs(text, by_id[r.id].form)
    if ink.shape[1] > 128 or ink.shape[0] > 40:
        raise ValueError(f"{text!r} is {ink.shape[1]}x{ink.shape[0]}, canvas 128x40")
    cell = np.full((40, 128), int(bg[0]), dtype=np.int32)
    oy, ox = (40 - ink.shape[0]) // 2, (128 - ink.shape[1]) // 2
    box = cell[oy:oy + ink.shape[0], ox:ox + ink.shape[1]]
    box[halo] = line
    box[ink] = int(fill[len(fill) // 2])
    for rid in CANVAS_ROWS:
        o = by_id[rid]
        px[o.y:o.y + o.h, o.x:o.x + o.w] = int(bg[0])
    for u, v, w, h, cx in CANVAS_PIECES:
        px[v:v + h, u:u + w] = cell[:h, cx:cx + w]
    return tim.with_pixels(t, data, px.reshape(-1).tolist())


def english_items():
    """(row id, file, typeset row) of every row of script/en/graphics.tsv that typeset() letters: each rect widened to
    its text inside the row's drawn box if needed, with the CLUT row the game draws it with. The no-card canvas rows are
    no_card()'s."""
    import tl_check
    budgets = {b["id"]: b for b in tl_check.table(ROOT / "script" / "budgets.tsv")}
    by_id = {r.id: r for r in gfx_script.rows()}
    cluts = drawn_cluts()
    grown = {}  # row id: its finished rect, so two rows that both grow can't overlap
    for e in tl_check.table(ROOT / "script" / "en" / "graphics.tsv"):
        r = by_id[e["id"]]
        if r.id in CANVAS_ROWS or not e["en"]:
            continue
        form = e["class"] or r.form
        rect = (r.x, r.y, r.w, r.h)
        if r.id.startswith("song."):  # the whole plate inside its bolts, so the rect takes 」 too; left, as the Japanese
            rect = (r.x, r.y, tl_check.SONG_W, r.h)
        inks = ROW_INKS.get(r.id, SONG_INKS if r.id.startswith("song.") else None)
        gh, gw = glyphs(e["en"], form)[0].shape
        if inks and inks.shadow is not None:
            gh, gw = gh + 1, gw + 1
        others = [grown.get(o.id, (o.x, o.y, o.w, o.h)) for o in by_id.values()
                  if o.file == r.file and o.id != r.id and o.form != "keep"]
        if gw > rect[2] or gh > rect[3]:
            rect = widened(rect, max(gw, rect[2]), max(gh, rect[3]), uv_box(budgets[r.id], rect), others)
        grown[r.id] = rect
        for *c, bg in CLEARS.get(r.id, ()):
            yield r.id, r.file, (tuple(c), "", form, "c", Inks(bg, bg, True, bg))
        row = (rect, e["en"], form, "l" if r.id.startswith("song.") or r.id in LEFT else "c")
        if inks:
            row += (inks,)
        elif r.id in cluts:
            row += (cluts[r.id],)
        yield r.id, r.file, row


def english_rows():
    """{file: [typeset row, ...]} of english_items()."""
    out = {}
    for _, file, row in english_items():
        out.setdefault(file, []).append(row)
    return out


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
