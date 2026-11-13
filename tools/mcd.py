"""Write test PS1 memory card images (128 KiB) for the memory card scenes in tools/debug/scenes.lua.

    python -X utf8 tools/mcd.py blank|unformatted|full OUT.mcd

blank: formatted, 15 free blocks. unformatted: all zeros (the game offers to format). full: 15 blocks used by a dummy
save (BIDUMMY00..14) so a new save finds no room. Frame layout: header frame 0 ("MC", XOR byte 127), directory frames
1-15 (0xA0 free, 0x51 first block of a file), each frame's byte 127 = XOR of bytes 0-126.
"""
import sys

FRAME, SIZE = 128, 128 * 1024


def frame(data):
    f = bytearray(data.ljust(FRAME - 1, b"\0"))
    x = 0
    for b in f:
        x ^= b
    return bytes(f + bytes([x]))


def card(kind):
    if kind == "unformatted":
        return bytes(SIZE)
    d = bytearray(SIZE)
    d[0:FRAME] = frame(b"MC")
    for i in range(1, 16):
        if kind == "full":
            name = b"BIDUMMY%02d" % (i - 1)
            ent = bytes([0x51, 0, 0, 0]) + (8192).to_bytes(4, "little") + b"\xff\xff" + name
        else:
            ent = bytes([0xA0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xFF])
        d[i * FRAME:(i + 1) * FRAME] = frame(ent)
    for i in range(16, 36):  # broken-sector list: none
        d[i * FRAME:(i + 1) * FRAME] = frame(b"\xff\xff\xff\xff\0\0\0\0\xff\xff")
    d[63 * FRAME:64 * FRAME] = d[0:FRAME]  # write-test frame: a copy of the header
    if kind == "full":  # each block a save with a title frame ("SC" header, 1 icon frame)
        for b in range(1, 16):
            o = b * 8192
            d[o:o + 4] = b"SC\x11\x01"
            d[o + 4:o + 4 + 10] = "ダミー".encode("shift_jis").ljust(10, b"\0")
    return bytes(d)


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("blank", "unformatted", "full"):
        sys.exit(__doc__)
    d = card(sys.argv[1])
    assert len(d) == SIZE and (sys.argv[1] == "unformatted" or d[:2] == b"MC")
    open(sys.argv[2], "wb").write(d)


if __name__ == "__main__":
    main()
