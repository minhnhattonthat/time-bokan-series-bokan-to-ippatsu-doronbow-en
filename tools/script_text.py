"""script/text.tsv: the game's only encoded text (the memory card title), with its codec.

Rows: id file offset size form jp note. Form sjis_swapped = Shift-JIS whose 16-bit words are stored byte-swapped
(docs/re/text.md), padded with zero bytes to size."""
from collections import namedtuple
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Row = namedtuple("Row", "id file offset size form jp note")


def rows(path=ROOT / "script" / "text.tsv"):
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines()[1:]:
        c = ln.split("\t")
        out.append(Row(c[0], c[1], int(c[2], 0), int(c[3]), c[4], c[5], c[6] if len(c) > 6 else ""))
    return out


def swap(b):
    return bytes(x for i in range(0, len(b) - 1, 2) for x in (b[i + 1], b[i]))


def encode(text, size):
    b = text.encode("cp932")
    assert len(b) % 2 == 0 and len(b) <= size, f"{text!r}: {len(b)} bytes, slot holds {size} (full-width only)"
    return swap(b) + bytes(size - len(b))


def decode(b):
    return swap(b.rstrip(b"\0")).decode("cp932")
