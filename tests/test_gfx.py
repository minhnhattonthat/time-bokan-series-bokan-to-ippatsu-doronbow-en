"""Phase 5 tools: marker paints stay in their rects, typeset refuses overflow, the packet reader decodes this game's
sprite packets, and the budget table covers every row."""
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import budgets
import fmv_burn
import gfx
import gfx_script
import prims
import tim
from test_recon import make_tim

X = ROOT / "work" / "x"
needs_x = pytest.mark.skipif(not X.exists(), reason="needs the extracted disc in work/x")


def tim16(px_rows=16):
    """A 64x16 4 bpp TIM, placeholder CLUT row 0 and a real row 1 (grey ramp), pixels 0..255 repeated."""
    clut = struct.pack("<I4H", 12 + 64, 0, 480, 16, 2) + struct.pack("<16H", *[0x7C3F] * 16)
    clut += struct.pack("<16H", 0, *(i * 0x421 * 2 for i in range(1, 16)))
    pixels = struct.pack("<I4H", 12 + 16 * px_rows * 2, 320, 0, 16, px_rows) + bytes(range(256)) * (px_rows // 8)
    return struct.pack("<II", 0x10, 8) + clut + pixels


def test_marker_changes_only_the_rect():
    data = make_tim()
    t = tim.parse(data)
    new = gfx.marked(data, [((1, 0, 4, 1), "1")])
    a, b = tim.pixels(t, data), tim.pixels(t, new)
    assert new[:t.px_off] == data[:t.px_off]
    assert a[:1] == b[:1] and a[5:] == b[5:] and a[1:5] != b[1:5]


def test_ink_indices_skip_the_placeholder_row():
    t = tim.parse(tim16())
    assert gfx.ink_indices(t) == (1, 15)  # row 1's darkest and brightest, not row 0's flat magenta


def test_typeset_stays_in_rect_and_refuses_overflow():
    data = tim16()
    t = tim.parse(data)
    rect = (2, 2, 40, 12)
    new = gfx.typeset(data, [(rect, "Ok", "tag", "c")])
    a, b = [np.array(tim.pixels(t, d)).reshape(16, 64) for d in (data, new)]
    inside = np.zeros((16, 64), bool)
    inside[2:14, 2:42] = True
    assert (a[~inside] == b[~inside]).all() and (a != b).any()
    with pytest.raises(ValueError):
        gfx.typeset(data, [((2, 2, gfx.row_width("Ok", "tag") - 1, 12), "Ok", "tag", "c")])
    gfx.typeset(data, [((2, 2, gfx.row_width("Ok", "tag"), 12), "Ok", "tag", "c")])  # exactly full fits


def test_forced_inks_clear_gradient_and_patch_from_above():
    data = tim16()
    t = tim.parse(data)
    px = lambda d: np.array(tim.pixels(t, d)).reshape(16, 64)  # noqa: E731
    a = px(data)
    b = px(gfx.typeset(data, [((4, 2, 8, 4), "", "tag", "c", gfx.Inks(9, 9, True, 9))]))
    assert (b[2:6, 4:12] == 9).all() and (b[:2] == a[:2]).all() and (b[6:] == a[6:]).all()
    b = px(gfx.typeset(data, [((2, 2, 40, 12), "Ok", "tag", "c", gfx.Inks((3, 7), 1, True, 0))]))
    assert set(np.unique(b[2:8, 2:42])) <= {0, 1, 3} and set(np.unique(b[8:14, 2:42])) <= {0, 1, 7}
    b = px(gfx.typeset(data, [((2, 8, 40, 8), "Ok", "tag", "c", gfx.Inks(15, 1, True, "above"))]))
    keep = ~np.isin(b[8:16, 2:42], (1, 15))
    assert (b[8:16, 2:42][keep] == a[0:8, 2:42][keep]).all() and (b[:8] == a[:8]).all()


def test_inpaint_takes_neighbours_and_keeps_the_rest():
    cell = np.array([[1, 9, 9, 2], [3, 9, 4, 5]])
    gfx.inpaint(cell, cell == 9)
    assert 9 not in cell and cell[0, 0] == 1 and cell[0, 3] == 2 and cell[1].tolist() == [3, 4, 4, 5]
    with pytest.raises(ValueError):
        gfx.inpaint(np.full((2, 2), 9), np.ones((2, 2), bool))


def test_row_inks_name_real_rows():
    ids = {r.id for r in gfx_script.rows()}
    assert set(gfx.ROW_INKS) <= ids and set(gfx.CLEARS) <= ids
    assert all(i.fill != 0 for i in gfx.ROW_INKS.values())  # index 0 is see-through on the PS1


def test_inks_come_from_inside_the_strokes():
    clut = [0] * 16
    clut[1], clut[2] = 0x001F, 0x7FFF  # red, white
    thick = np.zeros((9, 9), int)
    thick[1:8, 1:8] = 2
    thick[2:7, 2:7] = 1
    bg, fill, line = gfx.sampled_inks(thick, clut)
    assert (bg == 0).all() and (fill == 1).all() and line == 2


def test_sprite_packet_decodes():
    """E1 draw mode then SPRT, n=5: the title menu's packet from a RAM dump (800F5F8C)."""
    ram = bytearray(prims.RAM)
    words = [0x050F2488 & 0xFF000000 | 0xFFFFFF, 0xE100022C, 0x64808080, 0x00600058, 0x7808B070, 0x00500090]
    struct.pack_into("<6I", ram, 0x1000, *words)
    p = next(q for q in prims.scan(bytes(ram)) if q.addr == 0x1000)
    assert (p.x, p.y, p.sw, p.sh, p.u, p.v, p.bpp, p.clut) == (88, 96, 144, 80, 112, 176, 4, 0x7808)
    assert (p.vx, p.vy) == (12 * 64 + 112 // 4, 176)


@needs_x
def test_clut_word_maps_to_the_tims_row():
    assert budgets.clut_row("CHRPLY2/OPTI_01", 0x7889) == 2  # (144, 482): OPTI_01's CLUT starts at (144, 480)
    assert budgets.clut_row("CHRPLY2/OPTI_01", 0x7808) is None


@needs_x
def test_every_row_rect_is_inside_its_tim():
    for r in gfx_script.rows():
        t = tim.parse((X / (r.file + ".BIN")).read_bytes())
        assert r.x + r.w <= gfx.pixel_width(t) and r.y + r.h <= t.px_wh[1], r.id


@needs_x
def test_spike_lines_fit_their_rects():
    for file, rows in gfx.spike_rows().items():
        gfx.typeset((X / (file + ".BIN")).read_bytes(), rows)


@needs_x
def test_credit_pages_and_lines_match():
    """Every line of the EXE's page table is a line of script/credits.tsv and back; the 19 one-piece groups at the end
    are ending art frames (no text)."""
    import credits
    lines = credits.table_lines()
    by_shape = {tuple(p[1:] for p in ps): n for n, _, _, ps in lines}
    used, art = set(), 0
    for _, es in credits.pages():
        for g in credits.page_lines(es):
            k = tuple((e.u, e.v, e.w, e.h, e.x - g[0].x) for e in g)
            if k in by_shape:
                used.add(by_shape[k])
            else:
                assert len(es) == 1 and es[0].w >= 32 and es[0].h >= 24, f"page line {k} not in credits.tsv"
                art += 1
    assert used == {n for n, *_ in lines} and art == 19


def test_budgets_cover_rows():
    path = ROOT / "script" / "budgets.tsv"
    ids = [ln.split("\t")[0] for ln in path.read_text(encoding="utf-8").splitlines()[1:]]
    assert ids == [r.id for r in gfx_script.rows() if r.form != "keep"]


def test_subtitle_wraps_to_width():
    from PIL import ImageFont
    font = ImageFont.truetype(str(fmv_burn.FONT), fmv_burn.SIZE)
    lines = fmv_burn.balance(fmv_burn.wrap(fmv_burn.MARKER * 2, font), font)
    assert all(font.getlength(ln) <= fmv_burn.MAX_W for ln in lines)
    ink, halo = fmv_burn.text_masks(["Wide"], 640, 240)
    cols = np.flatnonzero(ink.any(axis=0))
    assert cols[-1] - cols[0] > 2 * font.getlength("Wide") - 6  # stretched 2x for the 640-wide picture
