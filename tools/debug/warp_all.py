"""Run scenes of tools/debug/scenes.lua from cold boot, each in work/qa/warp/<scene>; exit 1 if any fails.

    python -X utf8 tools/debug/warp_all.py [--rom CUE] [--jobs 3] [--out DIR] [--god] [--states] [scene ...]

--states also saves work/states/<scene>.sstate. The state checks inside each scene fail the run on their own (exit 2
from emu.py); --smoke adds a flat-colour test on final.png.
"""
import argparse
import concurrent.futures as cf
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

DEFAULT_ROM = os.path.join(ROOT, "rom", "Time Bokan Series - Bokan to Ippatsu! Doronbow (Japan).cue")
SCENES = os.path.join(ROOT, "tools", "debug", "scenes.lua")
WARP = os.path.join(ROOT, "tools", "debug", "warp.lua")
LONG = {"clear7": 40000, "ending": 40000, "gameover": 30000, "ranking": 30000, "demo": 20000}
NO_SMOKE = {"movie06", "logo"}  # fades to black or white by design; the scene's own checks prove it


def scene_names():
    """Scene names, from scenes.lua's `S.name =` lines plus its `for n = 1, 7` families (kept in step by tests)."""
    src = open(SCENES, encoding="utf-8").read()
    names = [n for n in re.findall(r"^S\.(\w+) = ", src, re.M) if not n.startswith("x_")]
    for fam in re.findall(r'^for n = 1, 7 do S\["(\w+)" \.\. n\]', src, re.M):
        names += [f"{fam}{n}" for n in range(1, 8)]
    return names


def run(scene, rom, out, god, states):
    d = os.path.join(out, scene)
    cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), rom, "--out", d,
           "--frames", str(LONG.get(scene, 20000)), "--timeout", "2400", "--script", WARP, "--script", SCENES,
           "--var", f"SCENE='{scene}'"]
    if scene not in NO_SMOKE:
        cmd.append("--smoke")
    if god:
        cmd += ["--var", "GOD=1"]
    if states:
        cmd += ["--state-out", os.path.join(ROOT, "work", "states", scene + ".sstate")]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    log = os.path.join(d, "log.txt")
    last = ""
    if os.path.exists(log):
        lines = open(log, encoding="utf-8", errors="replace").read().splitlines()
        last = lines[-1] if lines else ""
    err = [x for x in r.stdout.splitlines() if "error" in x.lower()][-1:] if r.returncode else []
    return scene, r.returncode, last, err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default=DEFAULT_ROM)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "qa", "warp"))
    ap.add_argument("--god", action="store_true")
    ap.add_argument("--states", action="store_true")
    ap.add_argument("--list", action="store_true", help="print the scene names and stop")
    ap.add_argument("scenes", nargs="*")
    a = ap.parse_args()
    names = a.scenes or scene_names()
    if a.list:
        print("\n".join(names))
        return 0
    bad = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for scene, rc, last, err in ex.map(lambda s: run(s, a.rom, a.out, a.god, a.states), names):
            print(f"{'ok  ' if rc == 0 else 'FAIL'} {scene:14} rc={rc} {last} {' '.join(err)}", flush=True)
            bad += rc != 0
    print(f"{len(names) - bad}/{len(names)} scenes ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
