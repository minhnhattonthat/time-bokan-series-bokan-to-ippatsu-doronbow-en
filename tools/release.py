"""release.py: build, run every gate, then make and verify the patch zip in release/. Stops at the first failure.

    python -X utf8 tools/release.py [--version 1.0] [--no-build] [--force]

--no-build uses the disc already in build/ (the full build takes about 4 min). --force overwrites this version's files.
Never publishes: uploading a release is the owner's call. Only Track 01 changes, so the patch covers that one file.
Adapted from desu-yo's release.py."""
import argparse
import hashlib
import re
import string
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build import CUE, TRACK1  # noqa: E402

# As docs/re/text.md scanned; on the original the one hit is the card title (BOKAN.EXE 0x8FA75), which the build replaces.
PROGRAM_FILES = re.compile(r"SLPS_006\.09|BOKAN\.EXE|BOKAN[1-7]\.BIN|MOVIE1\.BIN")


def run(*cmd):
    print("$", *cmd, flush=True)
    if subprocess.run([str(c) for c in cmd], cwd=ROOT).returncode:
        sys.exit(f"release stopped: {cmd[1] if len(cmd) > 1 else cmd[0]} failed")


def py(*args):
    run(sys.executable, "-X", "utf8", *args)


def open_polish(text):
    """Polish lines still unticked."""
    return [line for line in text.splitlines() if line.startswith("- [ ]")]


def placeholders(text):
    """Template placeholders left in a README, like <repo> or <sha1>."""
    return re.findall(r"<[^<>\n]+>", text)


def hashes(path):
    data = Path(path).read_bytes()
    return {"size": len(data), "crc32": f"{zlib.crc32(data):08x}", "md5": hashlib.md5(data).hexdigest(),
            "sha1": hashlib.sha1(data).hexdigest()}


def gates(scripts):
    py("tools/check.py")
    py("tools/tl_check.py")
    py("tools/build_check.py")
    py(f"{scripts}/emu.py", f"build/{CUE}", "--out", "work/qa/smoke_release", "--route", "tools/routes/boot.txt", "--smoke")
    jp_stand_in(scripts)
    manifests = sorted((ROOT / "work/qa").rglob("manifest.tsv"))
    if len(manifests) < 2:
        sys.exit("release stopped: expected the visual and the story manifest under work/qa")
    for m in manifests:
        py(f"{scripts}/qa_gate.py", "check", m, m.parent / "verdicts")
    py(f"{scripts}/textcover.py", "work/qa/cover", "work/qa/cover/strings.tsv", "--waive", "docs/text_unshown.tsv")
    left = open_polish((ROOT / "docs/polish.md").read_text(encoding="utf-8"))
    if left:
        sys.exit("release stopped: unticked lines in docs/polish.md:\n" + "\n".join(left))
    found = placeholders((ROOT / "README.md").read_text(encoding="utf-8"))
    if found:
        sys.exit(f"release stopped: template placeholders in README.md: {found}")
    # The debug tool is Lua fed to the emulator; build_check above proves nothing else reached the disc.
    if "tools/debug" in (ROOT / "tools/build.py").read_text(encoding="utf-8"):
        sys.exit("release stopped: build.py refers to the debug tool")


def jp_stand_in(scripts):
    """The game has no text encoding (docs/re/text.md), so this scans what could hold any: the program files, for
    Shift-JIS the build left as it was. Text drawn as graphics is covered by build_check, textcover and the visual gate."""
    import disc
    built = disc.Disc(str(ROOT / "build" / TRACK1))
    out = ROOT / "work/qa/jp_left"
    out.mkdir(parents=True, exist_ok=True)
    names = [p for p in built.files if PROGRAM_FILES.fullmatch(p.rsplit("/", 1)[-1].split(";")[0])]
    if len(names) != 10:
        sys.exit(f"release stopped: expected 10 program files, found {names}")
    for path in names:
        copy = out / path.rsplit("/", 1)[-1].split(";")[0]
        copy.write_bytes(built.read(path))
        py(f"{scripts}/jp_left.py", copy, "--sjis")


def patch(version, force):
    orig, built = ROOT / "rom" / TRACK1, ROOT / "build" / TRACK1
    base = f"Time_Bokan_Bokan_to_Ippatsu_Doronbow_EN_v{version}"
    out = ROOT / "release"
    out.mkdir(exist_ok=True)
    xd, readme, zipped = out / f"{base}.xdelta", out / "README.txt", out / f"{base}.zip"
    if not force and (xd.exists() or zipped.exists()):
        sys.exit(f"release stopped: {base} already exists; --force overwrites it")
    a, b = hashes(orig), hashes(built)
    if a["size"] != b["size"]:
        sys.exit(f"release stopped: Track 01 size changed, {a['size']} to {b['size']}")
    # Without -B xdelta3 only looks for matches within 64 MB.
    run("xdelta3", "-e", "-f", "-9", "-S", "djw", "-B", a["size"], "-s", orig, built, xd)
    check = out / "reapply.bin"
    run("xdelta3", "-d", "-f", "-s", orig, xd, check)
    same = hashes(check)["sha1"] == b["sha1"]
    check.unlink()
    if not same:
        sys.exit("release stopped: re-applied patch differs from the build")
    template = string.Template((ROOT / "docs/release_readme.txt").read_text(encoding="utf-8"))
    readme.write_text(template.substitute(version=version, patch=xd.name, size=a["size"], crc32=a["crc32"], md5=a["md5"],
                                          sha1=a["sha1"], new_crc32=b["crc32"], new_sha1=b["sha1"]), encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(zipped, "w", zipfile.ZIP_STORED) as z:
        z.write(xd, xd.name)
        z.write(readme, readme.name)
    print(f"{zipped}: {zipped.stat().st_size:,} bytes; patched Track 01 SHA-1 {b['sha1']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--no-build", action="store_true", help="use the disc already in build/")
    ap.add_argument("--force", action="store_true", help="overwrite this version's files")
    args = ap.parse_args()
    from skill import SCRIPTS
    py("tools/check_rom.py")
    if not args.no_build:
        py("tools/build.py")
    gates(SCRIPTS)
    patch(args.version, args.force)


if __name__ == "__main__":
    main()
