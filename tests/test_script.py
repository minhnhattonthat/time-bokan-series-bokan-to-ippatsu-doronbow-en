"""Phase 4: every TIM roundtrips and is accounted for, the script tables point at real pixels and bytes."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import disc
import gfx_script
import ink_boxes
import script_text
import tim

BIN = build.ROM / build.TRACK1
needs_rom = pytest.mark.skipif(not BIN.exists(), reason="needs the dump in rom/")
FORMS = {"keep", "stamp", "menu", "message", "piece", "list", "voice", "name", "label", "banner", "badge", "sfx", "tag",
         "card", "sign", "credit"}


@pytest.fixture(scope="module")
def d():
    return disc.Disc(str(BIN))


@pytest.fixture(scope="module")
def tims(d):
    out = {}
    for path in d.files:
        if path.startswith(("/STR/", "/DA/")):
            continue
        data = d.read(path)
        if tim.parse(data):
            out[path.strip("/").removesuffix(".BIN")] = data
    return out


def test_gfx_rows_are_unique_and_complete():
    rows = gfx_script.rows()
    ids = [r.id for r in rows]
    assert len(ids) == len(set(ids))
    for r in rows:
        assert r.jp and r.w > 0 and r.h > 0 and r.form in FORMS, r.id
        assert re.search(r"[぀-ヿ一-鿿]", r.jp), f"{r.id}: no Japanese in the reading"


def test_card_title_codec_roundtrips():
    s = "「　ボカンと一発！」"
    assert script_text.decode(script_text.encode(s, 20)) == s
    with pytest.raises(AssertionError):
        script_text.encode("ABC", 34)  # half-width: odd byte count, the BIOS draws full-width only


def test_ink_boxes_splits_on_gaps():
    from PIL import Image
    img = Image.new("RGBA", (20, 6))
    for x, y in [(1, 1), (2, 2), (12, 3), (13, 4)]:
        img.putpixel((x, y), (255, 255, 255, 255))
    assert ink_boxes.boxes(img, 0, 0, 20, 6, 3) == [(1, 1, 2, 2), (12, 3, 2, 2)]
    assert ink_boxes.boxes(img, 0, 0, 20, 6, 20) == [(1, 1, 13, 4)]


def test_fmv_scripts_cover_all_6_movies_in_time_order():
    files = sorted((ROOT / "script" / "fmv").glob("MOVE*.tsv"))
    assert [f.stem for f in files] == [f"MOVE0{n}" for n in range(1, 7)]
    for f in files:
        last = 0.0
        for ln in f.read_text(encoding="utf-8").splitlines()[1:]:
            start, end, form, speaker, jp, *_ = ln.split("\t")
            assert form in ("dlg", "caption"), ln
            assert speaker, ln
            assert last <= float(start) < float(end), ln
            assert jp and not re.search(r"[A-Za-z]{4}", jp), ln
            last = float(start)


@needs_rom
def test_text_rows_decode_from_the_disc(d):
    for r in script_text.rows():
        b = d.read("/" + r.file)[r.offset:r.offset + r.size]
        assert script_text.decode(b) == r.jp, r.id
        assert script_text.encode(r.jp, r.size) == b, r.id


@needs_rom
def test_every_tim_roundtrips(tims):
    assert len(tims) == 188
    for name, data in tims.items():
        t = tim.parse(data)
        assert tim.with_pixels(t, data, tim.pixels(t, data)) == data, name


@needs_rom
def test_every_tim_is_accounted_for_once(tims):
    no_text = {ln for ln in (ROOT / "script" / "no_text.txt").read_text(encoding="utf-8").splitlines() if not ln.startswith("#")}
    text = {r.file for r in gfx_script.rows()}
    assert not no_text & text
    assert no_text | text == set(tims)


@needs_rom
def test_gfx_rects_hold_pixels(tims):
    for r in gfx_script.rows():
        t = tim.parse(tims[r.file])
        img = tim.to_image(t, tims[r.file], tim.best_clut(t))
        assert r.x + r.w <= img.width and r.y + r.h <= img.height, r.id
        assert img.crop((r.x, r.y, r.x + r.w, r.y + r.h)).getbbox(), f"{r.id} is blank"
