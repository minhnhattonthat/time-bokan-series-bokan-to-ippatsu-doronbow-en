"""Independent visual-QA verdicts for one qa_gate.py chunk, by `codex exec` in a read-only sandbox (Orca refuses nested
Claude workers). The sheets are attached as images with docs/visual-qa-brief.md; the original's sheet of the same id is
attached too when JP_DIR has one. The answer's verdict lines go to OUT (TSV id, ok|issue, note); ids it skipped are
listed and make the exit 1.

usage: qa_codex.py CHUNK.txt OUT.tsv [--jp work/qa/tsheets_jp]
CHUNK.txt is qa_gate.py todo --out-dir output (id<TAB>path per line)."""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chunk")
    ap.add_argument("out")
    ap.add_argument("--jp", default=str(ROOT / "work" / "qa" / "tsheets_jp"))
    a = ap.parse_args()
    rows = [ln.split("\t") for ln in Path(a.chunk).read_text(encoding="utf-8").splitlines() if ln.strip()]
    ids, paths = [r[0] for r in rows], [r[1] for r in rows]
    images, listing = [], []
    for i, p in zip(ids, paths):
        images.append(p)
        listing.append(f"- image {len(images)}: sheet `{i}` (English build)")
        jp = Path(a.jp) / f"{i}.png"
        if jp.exists():
            images.append(str(jp))
            listing.append(f"- image {len(images)}: the original disc's sheet for `{i}` (comparison only, no verdict)")
    prompt = (Path(ROOT / "docs" / "visual-qa-brief.md").read_text(encoding="utf-8")
              + "\n\n## This chunk\nAttached images, in order:\n" + "\n".join(listing)
              + "\n\nGive exactly one verdict line for each of these ids: " + ", ".join(ids)
              + ".\n\n## glossary.md (codex's sandbox can't run a shell here, so it is inlined)\n"
              + (ROOT / "glossary.md").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        last = Path(tmp) / "last.txt"
        cmd = [shutil.which("codex"), "exec", "-s", "read-only", "-C", str(ROOT), "--skip-git-repo-check", "-o", str(last)]
        for img in images:
            cmd += ["-i", img]
        # the prompt goes on stdin ("-"): codex is a .cmd shim on Windows, and cmd.exe mangles multi-line arguments
        subprocess.run(cmd + ["-"], check=True, input=prompt.encode("utf-8"), stdout=subprocess.DEVNULL)
        answer = last.read_text(encoding="utf-8")
    got = {}
    for line in answer.splitlines():
        f = [x.strip().strip("`") for x in line.split("\t")]
        if len(f) >= 2 and f[0] in ids and f[1] in ("ok", "issue"):
            got[f[0]] = (f[1], f[2] if len(f) > 2 else "")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("".join(f"{i}\t{v}\t{n} (codex)\n" for i, (v, n) in got.items()), encoding="utf-8")
    for i in ids:
        if i in got and got[i][0] == "issue":
            print(f"ISSUE {i}: {got[i][1]}")
    missing = [i for i in ids if i not in got]
    print(f"{len(got)}/{len(ids)} verdicts, {sum(v == 'issue' for v, _ in got.values())} issues -> {a.out}")
    for i in missing:
        print(f"no verdict: {i}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
