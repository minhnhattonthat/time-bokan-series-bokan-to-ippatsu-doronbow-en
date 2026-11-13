"""FMV bitstream: an unedited frame must come out bit-exact, and an edit must stay inside its macroblocks."""
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import disc
import mdec

needs_rom = pytest.mark.skipif(not (build.ROM / build.TRACK1).exists(), reason="needs the dump in rom/")


@pytest.fixture(scope="module")
def movie():
    d = disc.Disc(str(build.ROM / build.TRACK1))
    e = d.files["/STR/MOVE01.STR"]
    n = -(-e.size // 2048)
    raw = {i: d.raw(e.lba + i) for i in range(n)}
    return mdec.frames(raw.items()), raw.__getitem__


@needs_rom
def test_frames_roundtrip_bit_exact(movie):
    fr, sec = movie
    for f in fr[::37]:
        bs = mdec.frame_bytes(f, sec)
        assert mdec.Picture(bs, f.w, f.h).tobytes(len(bs)) == bs, f"frame {f.no}"


@needs_rom
def test_edit_touches_only_its_macroblock(movie):
    fr, sec = movie
    f = fr[100]
    bs = mdec.frame_bytes(f, sec)
    p = mdec.Picture(bs, f.w, f.h)
    before = list(p.blocks)
    y, cb, cr = p.get_mb(3, 11)
    p.set_mb(3, 11, np.full((16, 16), 100.0), cb, cr)
    i = (3 * p.rows + 11) * 6
    assert p.blocks[:i] == before[:i] and p.blocks[i + 6:] == before[i + 6:]
    y2, _, _ = mdec.Picture(p.tobytes(), f.w, f.h).get_mb(3, 11)
    assert abs(y2 - 100).max() < 4


@needs_rom
def test_coarser_q_shrinks_the_frame(movie):
    fr, sec = movie
    f = fr[100]
    bs = mdec.frame_bytes(f, sec)
    p = mdec.Picture(bs, f.w, f.h)
    coarse = p.tobytes_at(p.q + 3)
    assert len(coarse) < len(p.tobytes())
    assert struct.unpack_from("<H", coarse, 2)[0] == 0x3800 and mdec.parse(coarse, len(p.blocks))[1] == p.q + 3


def test_block_transform_roundtrip():
    rng = np.random.default_rng(1)
    pix = np.clip(rng.normal(0, 30, (8, 8)), -128, 127)
    got = mdec._U @ mdec.coefs(mdec.to_block(pix, 1), 1) @ mdec._U.T
    assert abs(got - pix).mean() < 8
