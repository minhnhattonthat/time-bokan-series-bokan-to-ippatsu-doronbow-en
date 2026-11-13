"""Recon facts the later phases build on (docs/re/). ROM-dependent tests skip when the dump is absent."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import disc
import sjis_scan
import tim

BIN = ROOT / "rom" / "Time Bokan Series - Bokan to Ippatsu! Doronbow (Japan) (Track 01).bin"
needs_rom = pytest.mark.skipif(not BIN.exists(), reason="needs the dump in rom/")


def make_tim():
    """A 4x1 VRAM-unit (16x1 pixel) 4bpp TIM with a placeholder CLUT row 0 and a real row 1."""
    clut = struct.pack("<I4H", 12 + 64, 0, 480, 16, 2) + struct.pack("<16H", 0, *[0x7C3F] * 15) + struct.pack("<16H", *range(16))
    px = struct.pack("<I4H", 12 + 8, 320, 0, 4, 1) + bytes(range(8))
    return struct.pack("<II", 0x10, 8) + clut + px


def test_tim_parse_and_best_clut():
    t = tim.parse(make_tim())
    assert (t.bpp, t.px_wh, t.clut_wh) == (4, (4, 1), (16, 2))
    assert tim.best_clut(t) == 1


def test_sjis_scan_finds_byte_swapped_title():
    s = "「ボカンと一発！」".encode("cp932")
    swapped = bytes(b for i in range(0, len(s), 2) for b in (s[i + 1], s[i]))
    assert "ボカン" not in "".join(t for _, t in sjis_scan.runs(swapped))
    assert [t for _, t in sjis_scan.swapped(b"\0" + swapped + b"\0")] == ["「ボカンと一発！」"]


def test_form1_seal_keeps_a_clean_sector():
    s = bytearray(disc.SECTOR)
    disc.form1_seal(s)
    assert bytes(s) == bytes(disc.SECTOR)


@needs_rom
def test_disc_layout():
    d = disc.Disc(str(BIN))
    tims = [p for p in d.files if not p.startswith(("/STR/", "/DA/")) and tim.parse(d.read(p))]
    assert len(tims) == 188
    assert d.files["/BOKAN.EXE"].size == 772096
    # /DA/*.DA entries point past Track 01's end (89,166 sectors) into the CD audio tracks
    assert all(e.lba >= 89166 for p, e in d.files.items() if p.startswith("/DA/"))
    assert sorted(p for p in d.files if p.startswith("/STR/")) == [f"/STR/MOVE0{i}.STR" for i in range(1, 7)]


@needs_rom
def test_only_japanese_bytes_are_the_card_title():
    """docs/re/text.md: no Shift-JIS text in code except the memory card title, stored as byte-swapped words."""
    d = disc.Disc(str(BIN))
    for p in ["/BOKAN.EXE"] + [f"/BOKAN{i}.BIN" for i in range(1, 8)] + ["/MOVIE1.BIN"]:
        b = d.read(p)
        real = [t for _, t in sjis_scan.swapped(b, 6) if "ボカン" in t or "ドロン" in t]
        assert real == (["「　ボカンと一発！　ドロンボー　」"] if p == "/BOKAN.EXE" else []), p
