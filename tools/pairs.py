"""Review files from script/en/: one per chapter in story order, `>> id | speaker | JP` then the English.
Adapted from desu-yo's pairs.py.

usage: pairs.py [OUT_DIR]   default work/qa/story/chapters; the same files feed the phase 6 review and qa_gate.py.
Story order: docs/synopsis.md (docs/re/state.md: movie ids after title, new game, stage 3 and stage 7)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fmv_burn
import gfx_script
import tl_check

STORY = "MOVE01 MOVE02 ST1 ST2 ST3 MOVE03 ST4 ST5 ST6 ST7 MOVE04 MOVE05 MOVE06".split()


def fmv_lines(movie, en_rows):
    src = fmv_burn.read_rows(movie)
    out = [f"## {movie}"]
    for r in tl_check.en_rows(movie, en_rows):
        ns = tl_check.span(r["n"])
        jp = " / ".join(src[n - 1][4] for n in ns)
        out += [f">> {movie}.{r['n']} | {src[ns[0] - 1][3]} | {jp}", r["en"].replace(" || ", " / ") or f"({r['note']})", ""]
    return out


def main(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = {r.id: r for r in gfx_script.rows()}
    gfx = {r["id"]: (rows[r["id"]], r["en"]) for r in tl_check.table(tl_check.EN / "graphics.tsv")}
    en_rows = tl_check.table(tl_check.EN / "fmv.tsv")
    story = []
    for s in STORY:
        if s.startswith("ST"):
            g, en = gfx[f"stage{s[2]}.title"]
            story += [f"## {s}", f">> {g.id} | card | {g.jp}", en.replace("|", " / "), ""]
        else:
            story += fmv_lines(s, en_rows)
    files = {"story": story}
    files["labels"] = [ln for g, en in gfx.values() if g.form != "card"
                       for ln in (f">> {g.id} | {g.form} | {g.jp}", en.replace("|", " / ") or "(canvas part)", "")]
    src = tl_check.table(ROOT / "script" / "credits.tsv")
    text = tl_check.table(tl_check.EN / "text.tsv")
    files["credits"] = [ln for s, r in zip(src, tl_check.table(tl_check.EN / "credits.tsv")) if s["kind"] != "icon"
                        for ln in (f">> {s['n']} | {s['kind']} | {s['jp']}", r["en"].replace("|", " / "), "")]
    files["credits"] += [ln for r in text for ln in (f">> {r['id']} | memory card title", r["en"], "")]
    for name, lines in files.items():
        (out_dir / f"{name}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(len(files), "chapters in", out_dir)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "work" / "qa" / "story" / "chapters")
