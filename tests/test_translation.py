"""Phase 6: the English in script/en/ passes its gate, and the gate catches what it claims to."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import tl_check


def test_script_en_is_clean():
    errors, _ = tl_check.run()
    assert not errors, "\n".join(errors)


def test_avoided_spelling_non_ascii_and_missing_term_are_caught():
    terms = [(["トンズラー"], "Tonzra", ["Tonzura"]), (["整備中"], "Under Repair", [])]
    errors = []
    tl_check.check_text("x", "Tonzura car", terms, errors)
    tl_check.check_text("y", "café", terms, errors)
    tl_check.check_term("z", "トンズラー", "Someone else", terms, errors)
    assert len(errors) == 3
    tl_check.check_term("ok", "整備中", "Under|Repair", terms, errors)  # a line break is not a missing term
    assert len(errors) == 3


def test_budgets_use_the_drawn_quad_and_the_overrides():
    b = tl_check.budgets()
    assert b["opt.level1"] == (218, 16)  # rect x 22 to the 240 px quad's edge, rect height
    assert b["song.12"][0] == tl_check.SONG_W
    assert b["card.p_memory"] == (128, 40)


def test_split_rows_share_their_time_and_stay_in_order():
    rows = [dict(movie="MOVE01", n="19", en="aaaa || bbbbbbbbbbbb", note="")]
    (s1, e1, t1), (s2, e2, t2) = tl_check.subs("MOVE01", rows)
    assert (t1, t2) == ("aaaa", "bbbbbbbbbbbb")
    assert s1 == 53.08 and e1 == s2 and e2 >= 61.30 - 0.01
    assert abs((e1 - s1) * 3 - (e2 - s2)) < 0.05  # 4 chars against 12
