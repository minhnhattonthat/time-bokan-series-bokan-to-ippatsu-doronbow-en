"""Phase 6 gate over script/en/: ids complete, plain ASCII, within the measured widths, glossary spellings.
Adapted from desu-yo's tl_check.py.

usage: tl_check.py        prints errors and warnings, exit 1 on any error. tests/test_translation.py runs it.
Library: budgets() {row id: (w, h)}; subs(movie) gives the timed subtitles the build burns.

Formats (all TSV, header first):
  script/en/graphics.tsv  id en class note   "|" breaks a line; class empty = the row's form. An empty en is allowed
                                             only with a note starting "canvas:" (drawn by another row).
  script/en/credits.tsv   n en note          one per script/credits.tsv line; "|" separates the parts the original
                                             spaces apart (role, names); icons have no en.
  script/en/fmv.tsv       movie n en note    n is a row of script/fmv/<movie>.tsv or a span "3-5"; " || " splits one
                                             row's time into consecutive subtitles, by length.
  script/en/text.tsv      id en note         full-width, encoded into the row's slot (tools/script_text.py)."""
import csv
import re
import sys
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fmv_burn
import gfx
import gfx_script
import script_text

EN = ROOT / "script" / "en"
SKIP_FORMS = {"keep", "credit"}
CREDIT_W = 296  # screen is 320 wide; keep 12 px each side, as the movies
CREDIT_GAP = 16  # px between parts of one credit line
MIN_SHOW = 1.2  # s: a short row stays up this long, unless the next row starts first
MAX_CPS, WARN_CPS = 30, 22
# Rows whose box the uv rule below gets wrong (docs/re/credits.md):
OVERRIDE = {
    "card.p_memory": (128, 40),  # one canvas over the two 64x40 no-card quads, side by side on screen
    "hud.wait": (32, 32),  # two 32x16 pieces, one line each (the game draws them side by side)
    "rnk.ranking": (108, 30),  # RANKING, skull, SCORE share one 192x32 quad side by side
    "rnk.score": (66, 30),  # from its rect to the quad's right edge
}
SONG_W = 206  # song plates (OPTI_03-05): inside the bolts, x 18-224, read zoomed


def table(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE, restval=""))


def budgets():
    """{id: (w, h)}: width from the row's rect start to the right edge of the drawn quads (budgets.tsv uv), height the
    rect's, since quads often hold several rows stacked. Rows never drawn keep their rect."""
    out = {}
    for b in table(ROOT / "script" / "budgets.tsv"):
        x, y, w, h = map(int, b["rect"].split(","))
        boxes = [list(map(int, u.split(","))) for u in b["uv"].split(";")] if b["uv"] else []
        if boxes:
            left, right = min(u[0] for u in boxes), max(u[0] + u[2] for u in boxes)
            w = right - max(left, x)
        if b["id"].startswith("song."):
            w = SONG_W  # the plate art ends inside its 240 px quad
        out[b["id"]] = OVERRIDE.get(b["id"], (w, h))
    return out


def span(n):
    a, _, b = n.partition("-")
    return list(range(int(a), int(b or a) + 1))


def en_rows(movie, rows=None):
    return [r for r in (rows or table(EN / "fmv.tsv")) if r["movie"] == movie]


def subs(movie, rows=None):
    """[(start, end, text)] for one movie: rows without English are skipped, split rows share their time by length,
    and short ones stretch to MIN_SHOW."""
    src, out = fmv_burn.read_rows(movie), []
    for r in en_rows(movie, rows):
        ns = span(r["n"])
        if not r["en"]:
            continue
        start, end = src[ns[0] - 1][0], max(src[n - 1][1] for n in ns)
        parts = [p.strip() for p in r["en"].split("||")]
        total, at = sum(len(p) for p in parts), start
        for p in parts:
            nxt = at + (end - start) * len(p) / total
            out.append((round(at, 2), round(nxt, 2), p))
            at = nxt
        later = [s[0] for s in src[ns[-1]:] if s[0] > start]
        limit = min(later) if later else end + MIN_SHOW
        s, e, t = out[-1]
        out[-1] = (s, max(e, min(s + MIN_SHOW, limit)), t)
    # burn_movie shows the first match, so an overlap would only delay the next line
    return [(s, min(e, out[i + 1][0]) if i + 1 < len(out) else e, t) for i, (s, e, t) in enumerate(out)]


def glossary():
    """(jp terms, en, avoid) of every glossary table row."""
    out = []
    for ln in (ROOT / "glossary.md").read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if not ln.startswith("|") or len(c) != 5 or c[0] in ("JP", "---"):
            continue
        out.append(([t.strip() for t in c[0].split("/")], c[1], [t.strip() for t in c[4].split(",") if t.strip()]))
    return out


def check_text(where, text, terms, errors):
    if not text.isascii() or "\t" in text or "\\u" in text:
        errors.append(f"{where}: not plain ASCII: {text!r}")
    for _, _, avoid in terms:
        for a in avoid:
            if re.search(rf"\b{re.escape(a)}\b", text):
                errors.append(f"{where}: avoided spelling {a!r}: {text!r}")


def check_term(where, jp, text, terms, errors):
    flat = " ".join(text.replace("||", " ").replace("|", " ").split()).lower()
    for jps, en, _ in terms:
        if any(j in jp for j in jps) and en.lower() not in flat:
            errors.append(f"{where}: {jp!r} needs {en!r}: {text!r}")


def check_graphics(terms, errors):
    rows = {r.id: r for r in gfx_script.rows()}
    want = {i for i, r in rows.items() if r.form not in SKIP_FORMS}
    en = table(EN / "graphics.tsv")
    ids = [r["id"] for r in en]
    if len(ids) != len(set(ids)) or set(ids) != want:
        errors.append(f"graphics ids: missing {sorted(want - set(ids))}, extra {sorted(set(ids) - set(want))}")
    sizes = budgets()
    for r in en:
        rid = r["id"]
        if rid not in rows:
            continue
        if not r["en"]:
            if not r["note"].startswith("canvas:"):
                errors.append(f"{rid}: no English and no canvas note")
            continue
        check_text(rid, r["en"], terms, errors)
        check_term(rid, rows[rid].jp, r["en"], terms, errors)
        form = r["class"] or rows[rid].form
        if form not in gfx.CLASSES:
            errors.append(f"{rid}: unknown class {form!r}")
            continue
        ink = gfx.glyphs(r["en"], form)[0]
        w, h = sizes.get(rid, (rows[rid].w, rows[rid].h))
        if ink.shape[1] > w or ink.shape[0] > h:
            errors.append(f"{rid}: {r['en']!r} is {ink.shape[1]}x{ink.shape[0]} in {form}, budget {w}x{h}")


def check_credits(terms, errors):
    src = table(ROOT / "script" / "credits.tsv")
    en = table(EN / "credits.tsv")
    if [r["n"] for r in en] != [r["n"] for r in src]:
        errors.append("credits: line numbers differ from script/credits.tsv")
    for r, s in zip(en, src):
        where = f"credits {r['n']}"
        if s["kind"] == "icon":
            if r["en"]:
                errors.append(f"{where}: icon line has English")
            continue
        if not r["en"]:
            errors.append(f"{where}: no English")
            continue
        check_text(where, r["en"], terms, errors)
        check_term(where, s["jp"], r["en"], terms, errors)
        parts = [p.strip() for p in r["en"].split("|")]
        w = sum(gfx.row_width(p, "credit") for p in parts) + CREDIT_GAP * (len(parts) - 1)
        if w > CREDIT_W:
            errors.append(f"{where}: {r['en']!r} is {w} px, room {CREDIT_W}")


def notes(movie, n):
    ln = (ROOT / "script" / "fmv" / f"{movie}.tsv").read_text(encoding="utf-8").splitlines()[n]
    c = ln.split("\t")
    return c[5] if len(c) > 5 else ""


def check_fmv(terms, errors, warnings):
    en = table(EN / "fmv.tsv")
    font = ImageFont.truetype(str(fmv_burn.FONT), fmv_burn.SIZE)
    for movie in sorted(p.stem for p in (ROOT / "script" / "fmv").glob("*.tsv")):
        src = fmv_burn.read_rows(movie)
        seen = []
        for r in en_rows(movie, en):
            where = f"{movie}.{r['n']}"
            ns = span(r["n"])
            seen += ns
            check_text(where, r["en"], terms, errors)
            if not r["en"]:
                if "dropped" not in r["note"]:
                    errors.append(f"{where}: no English and no reason")
                elif not any("?" in src[n - 1][4] + notes(movie, n) for n in ns):
                    errors.append(f"{where}: dropped, but the source row isn't marked uncertain")
                continue
            jp = "".join(src[n - 1][4] for n in ns)
            check_term(where, jp, r["en"], terms, errors)
            if "様" in jp and "-sama" not in r["en"]:  # D1 keeps honorifics; ちゃん and さん hit too many other words
                errors.append(f"{where}: {jp!r} has 様, English has no -sama: {r['en']!r}")
            for part in r["en"].split("||"):
                lines = fmv_burn.wrap(part.strip(), font)
                if max(font.getlength(ln) for ln in lines) > fmv_burn.MAX_W or len(lines) > fmv_burn.MAX_LINES:
                    errors.append(f"{where}: {len(lines)} lines or over {fmv_burn.MAX_W} px: {part.strip()!r}")
                elif len(lines) > 2:
                    warnings.append(f"{where}: {len(lines)} lines: {part.strip()!r}")
        if sorted(seen) != list(range(1, len(src) + 1)):
            errors.append(f"{movie}: rows covered {sorted(seen)}, need 1-{len(src)}")
        for s, e, t in subs(movie, en):
            cps = len(t) / max(e - s, 0.01)
            if cps > MAX_CPS:
                errors.append(f"{movie}: {cps:.0f} chars/s: {t!r}")
            elif cps > WARN_CPS:
                warnings.append(f"{movie}: {cps:.0f} chars/s: {t!r}")


def check_text_rows(errors):
    src = {r.id: r for r in script_text.rows()}
    en = table(EN / "text.tsv")
    if {r["id"] for r in en} != set(src):
        errors.append("text: ids differ from script/text.tsv")
    for r in en:
        if r["id"] not in src:
            continue
        try:
            script_text.encode(r["en"], src[r["id"]].size)
        except (AssertionError, UnicodeEncodeError) as e:
            errors.append(f"text {r['id']}: {e}")
        if re.search(r"[぀-ヿ一-鿿]", r["en"]):
            errors.append(f"text {r['id']}: Japanese left: {r['en']!r}")


def run():
    errors, warnings = [], []
    terms = glossary()
    check_graphics(terms, errors)
    check_credits(terms, errors)
    check_fmv(terms, errors, warnings)
    check_text_rows(errors)
    return errors, warnings


if __name__ == "__main__":
    errs, warns = run()
    for w in warns:
        print("warn:", w)
    for e in errs:
        print("ERROR:", e)
    print(f"{len(errs)} errors, {len(warns)} warnings" if errs or warns else "OK")
    sys.exit(1 if errs else 0)
