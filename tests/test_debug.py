"""Debug tool (tools/debug/): the scene list covers its families, and the task addresses warp.lua waits on are the
tasks the EXE really spawns (docs/re/state.md)."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "debug"))
import warp_all

EXE = ROOT / "work" / "x" / "BOKAN.EXE"


def test_scene_families():
    names = warp_all.scene_names()
    for fam in ("card", "stage", "clear", "select", "tour"):
        assert [f"{fam}{n}" for n in range(1, 8)] == [x for x in names if re.fullmatch(fam + r"\d", x)]
    assert {"title", "menu", "options", "optvals", "sound", "memcard", "gameover", "movie01", "continue",
            "join2p"} <= set(names)
    assert not [x for x in names if x.startswith("x_")]
    # every per-scene card or hardware var names a real scene
    assert set(warp_all.CARDS) | set(warp_all.VARS) <= set(names)


def test_mcd_cards():
    sys.path.insert(0, str(ROOT / "tools"))
    import mcd
    blank, full, unf = mcd.card("blank"), mcd.card("full"), mcd.card("unformatted")
    assert len(blank) == len(full) == len(unf) == 128 * 1024 and not any(unf)
    for d in (blank, full):
        for i in range(64):  # every frame's last byte is the XOR of the other 127
            f = d[i * 128:(i + 1) * 128]
            x = 0
            for b in f[:127]:
                x ^= b
            assert f[127] == x
    assert [blank[i * 128] for i in range(1, 16)] == [0xA0] * 15
    assert [full[i * 128] for i in range(1, 16)] == [0x51] * 15


@pytest.mark.skipif(not EXE.exists(), reason="needs work/x from tools/disc.py x")
def test_warp_tasks_are_spawned():
    out = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "task_spawns.py"), str(EXE)],
                         capture_output=True, text=True, check=True).stdout
    spawned = set(re.findall(r"fn=([0-9A-F]{8})", out))
    src = (ROOT / "tools" / "debug" / "warp.lua").read_text(encoding="utf-8")
    tasks = {m.upper() for m in re.findall(r"^W\.\w+ = 0x(8[0-9A-Fa-f]{7})$", src, re.M)}
    assert tasks and tasks <= spawned
