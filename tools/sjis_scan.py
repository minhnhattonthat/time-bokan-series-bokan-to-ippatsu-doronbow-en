"""List Shift-JIS runs (full-width only) at any byte alignment, so a run that starts on an odd offset is not missed.

usage: sjis_scan.py [--swap] FILE.. [min_chars=4]   prints file, offset and text; noise is runs that do not read as words."""
import sys


def runs(b, n=4):
    i, out = 0, []
    while i < len(b) - 1:
        j, s = i, []
        while j < len(b) - 1:
            c = b[j:j + 2]
            if 0x81 <= c[0] <= 0x84 or 0x88 <= c[0] <= 0x9F or 0xE0 <= c[0] <= 0xEA:
                try:
                    s.append(c.decode("cp932"))
                    j += 2
                    continue
                except UnicodeDecodeError:
                    pass
            break
        if len(s) >= n:
            out.append((i, "".join(s)))
            i = j
        else:
            i += 1
    return out


def swapped(b, n=4):
    """Runs stored as little-endian 16-bit words (BOKAN.EXE's memory card title is byte-swapped this way)."""
    out = []
    for start in (0, 1):
        s = bytearray(b[start:start + (len(b) - start) // 2 * 2])
        s[0::2], s[1::2] = s[1::2], s[0::2]
        out += [(off + start, t) for off, t in runs(bytes(s), n)]
    return sorted(out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--swap"]
    scan = swapped if "--swap" in sys.argv else runs
    n = int(args[-1]) if len(args) > 1 and args[-1].isdigit() else 4
    for f in [a for a in args if not a.isdigit()]:
        for off, t in scan(open(f, "rb").read(), n):
            print(f"{f} {off:#08x} {t}")
