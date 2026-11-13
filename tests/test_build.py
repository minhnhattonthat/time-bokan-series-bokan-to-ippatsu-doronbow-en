"""Identity build: rom/ through the whole build path, with no edits, must come out byte-identical."""
import hashlib
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import disc
import tim
from test_recon import make_tim

needs_rom = pytest.mark.skipif(not (build.ROM / build.TRACK1).exists(), reason="needs the dump in rom/")


def test_with_pixels_replaces_only_the_pixel_block():
    b = make_tim() + b"tail"
    t = tim.parse(b)
    vals = tim.pixels(t, b)
    assert vals[:4] == [0, 0, 1, 0]  # 4 bpp, low nibble first
    assert tim.with_pixels(t, b, vals) == b
    new = tim.with_pixels(t, b, [15] * len(vals))
    assert new[:t.px_off] == b[:t.px_off] and new[-4:] == b"tail"
    assert tim.pixels(t, new) == [15] * len(vals)
    with pytest.raises(AssertionError):
        tim.with_pixels(t, b, [0, 0])


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("build")
    build.build(out, identity=True)
    return out


def sha1s():
    return {Path(p).name: h for h, p in (ln.split(" ", 1) for ln in (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines()
                                         if ln and not ln.startswith("#"))}


@needs_rom
def test_identity_build_matches_the_dump(built):
    want = sha1s()
    for name in (build.TRACK1, build.CUE):
        with open(built / name, "rb") as f:
            assert hashlib.file_digest(f, "sha1").hexdigest() == want[name], name
    assert {p.name for p in built.iterdir()} == set(want)  # every track and the cue


@needs_rom
def test_identity_rewrote_every_form1_file(built):
    """Guards against a vacuous identity: every non-XA file passed through write_file, TIMs through with_pixels."""
    d = disc.Disc(str(built / build.TRACK1))
    files = [e for e in d.files.values() if not d.is_xa(e)]
    tims = sum(1 for e in files if tim.parse(d.read(e.path)))
    d.f.close()
    assert tims == 188 and len(files) > tims


@needs_rom
def test_write_file_changes_only_that_file(built, tmp_path):
    """An edit must land, read back, and touch no other sector."""
    copy = tmp_path / "t.bin"
    shutil.copyfile(built / build.TRACK1, copy)
    d = disc.Disc(str(copy), write=True)
    e = d.files["/BOKAN.EXE"]
    old = d.read(e.path)
    new = bytes([old[0] ^ 1]) + old[1:-1] + bytes([old[-1] ^ 1])
    d.write_file(e.path, new)
    assert d.read(e.path) == new
    d.f.close()
    a, b = (built / build.TRACK1).read_bytes(), copy.read_bytes()
    n = -(-e.size // 2048)
    changed = [lba for lba in {e.lba, e.lba + n - 1} if a[lba * disc.SECTOR:(lba + 1) * disc.SECTOR] != b[lba * disc.SECTOR:(lba + 1) * disc.SECTOR]]
    assert sorted(changed) == sorted({e.lba, e.lba + n - 1})
    start, end = e.lba * disc.SECTOR, (e.lba + n) * disc.SECTOR
    assert a[:start] == b[:start] and a[end:] == b[end:]
    last = bytearray(b[(e.lba + n - 1) * disc.SECTOR:(e.lba + n) * disc.SECTOR])
    sealed = bytearray(last)
    disc.form1_seal(sealed)
    assert sealed == last  # EDC/ECC of the changed sector are valid
