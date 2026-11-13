"""PS1 STR version 2 frames: parse a frame's bitstream to coefficients, write them back, and edit pixels macroblock by
macroblock, so only the macroblocks under a subtitle are re-encoded and the rest of the frame stays bit-exact.

Library: frames(sectors), parse(bs), encode(q, blocks, ...), Picture.
Bitstream: 8-byte header (u16 MDEC words, u16 0x3800, u16 qscale, u16 version 2), then little-endian 16-bit words read
MSB first. Six blocks per macroblock (Cr Cb Y0 Y1 Y2 Y3), macroblocks in column order. Each block: 10-bit signed DC, VLC
(run, level) pairs in zigzag order, EOB."""
import struct
from collections import namedtuple

import numpy as np

SECTOR = 2352
MAGIC = 0x80010160
CHUNK = 2016
EOB = "10"
ESC = "000001"
MB_BLOCKS = 6
MAX_Q = 63  # the MDEC takes qscale in 6 bits

# (code without sign bit, run, level): the MPEG-1 intra AC table
_VLC = """11 0 1|011 1 1|0100 0 2|0101 2 1|00101 0 3|00111 3 1|00110 4 1|000110 1 2|000111 5 1|000101 6 1|000100 7 1
0000110 0 4|0000100 2 2|0000111 8 1|0000101 9 1|00100110 0 5|00100001 0 6|00100101 1 3|00100100 3 2|00100111 10 1
00100011 11 1|00100010 12 1|00100000 13 1|0000001010 0 7|0000001100 1 4|0000001011 2 3|0000001111 4 2|0000001001 5 2
0000001110 14 1|0000001101 15 1|0000001000 16 1|000000011101 0 8|000000011000 0 9|000000010011 0 10|000000010000 0 11
000000011011 1 5|000000010100 2 4|000000011100 3 3|000000010010 4 3|000000011110 6 2|000000010101 7 2|000000010001 8 2
000000011111 17 1|000000011010 18 1|000000011001 19 1|000000010111 20 1|000000010110 21 1|0000000011010 0 12
0000000011001 0 13|0000000011000 0 14|0000000010111 0 15|0000000010110 1 6|0000000010101 1 7|0000000010100 2 5
0000000010011 3 4|0000000010010 5 3|0000000010001 9 2|0000000010000 10 2|0000000011111 22 1|0000000011110 23 1
0000000011101 24 1|0000000011100 25 1|0000000011011 26 1|00000000011111 0 16|00000000011110 0 17|00000000011101 0 18
00000000011100 0 19|00000000011011 0 20|00000000011010 0 21|00000000011001 0 22|00000000011000 0 23|00000000010111 0 24
00000000010110 0 25|00000000010101 0 26|00000000010100 0 27|00000000010011 0 28|00000000010010 0 29|00000000010001 0 30
00000000010000 0 31|000000000011000 0 32|000000000010111 0 33|000000000010110 0 34|000000000010101 0 35
000000000010100 0 36|000000000010011 0 37|000000000010010 0 38|000000000010001 0 39|000000000010000 0 40
000000000011111 1 8|000000000011110 1 9|000000000011101 1 10|000000000011100 1 11|000000000011011 1 12
000000000011010 1 13|000000000011001 1 14|0000000000010011 1 15|0000000000010010 1 16|0000000000010001 1 17
0000000000010000 1 18|0000000000010100 6 3|0000000000011010 11 2|0000000000011001 12 2|0000000000011000 13 2
0000000000010111 14 2|0000000000010110 15 2|0000000000010101 16 2|0000000000011111 27 1|0000000000011110 28 1
0000000000011101 29 1|0000000000011100 30 1|0000000000011011 31 1"""

DECODE, ENCODE = {}, {}
for _e in _VLC.replace("\n", "|").split("|"):
    _c, _r, _l = _e.split()
    DECODE[_c] = (int(_r), int(_l))
    ENCODE[(int(_r), int(_l))] = _c
assert len(DECODE) == 111 and not any(c.startswith(EOB) or c.startswith(ESC) for c in DECODE)
MAXLEN = max(map(len, DECODE))

ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21,
          28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54,
          47, 55, 62, 63]
# The MDEC's default table, in zigzag order (index 0 is the DC's own multiplier)
QT = [2, 16, 16, 19, 16, 19, 22, 22, 22, 22, 22, 22, 26, 24, 26, 27, 27, 27, 26, 26, 26, 26, 27, 27, 27, 29, 29, 29, 34, 34,
      34, 29, 29, 29, 27, 27, 29, 29, 32, 32, 34, 34, 37, 38, 37, 35, 35, 34, 35, 38, 38, 40, 40, 40, 48, 48, 46, 46, 56, 56,
      58, 69, 69, 83]
_U = np.array([[np.sqrt(1 / 8 if u == 0 else 2 / 8) * np.cos((2 * x + 1) * u * np.pi / 16) for u in range(8)] for x in range(8)])


def s10(v):
    return v - 1024 if v & 512 else v


# Version 3 (this game's movies): DC is the difference to the previous DC of the same kind (Cr, Cb, Y), in steps of 4,
# coded as an MPEG-1 DC size code then that many bits; a negative difference has its top bit clear, offset by 2^size-1.
Y_DC = {"100": 0, "00": 1, "01": 2, "101": 3, "110": 4, "1110": 5, "11110": 6, "111110": 7, "1111110": 8}
C_DC = {"00": 0, "01": 1, "10": 2, "110": 3, "1110": 4, "11110": 5, "111110": 6, "1111110": 7, "11111110": 8}
Y_DC_CODE, C_DC_CODE = ({v: k for k, v in t.items()} for t in (Y_DC, C_DC))
END = {2: "0111111111", 3: "1111111111"}  # after the last block


def dc_kind(i):
    """Predictor of block i in a frame: 0 Cr, 1 Cb, 2 Y."""
    return min(i % MB_BLOCKS, 2)


def parse(bs, nblocks=None):
    """Header fields and blocks of one frame. blocks = [(dc, [(run, level), ...]), ...]; extra = bytes after the last
    block's padding, so encode() can reproduce the file exactly. Raises ValueError on a bad code. Version 3 has no DC
    that marks the end, so it needs nblocks (the frame's width/16 * height/16 * 6)."""
    words, _mark, q, ver = struct.unpack_from("<4H", bs)
    if ver not in (2, 3) or (ver == 3 and nblocks is None):
        raise ValueError(f"STR version {ver}")
    n = (len(bs) - 8) // 2
    bits = "".join(f"{w:016b}" for w in struct.unpack_from(f"<{n}H", bs, 8))
    p = 0
    blocks = []
    total = len(bits)
    pred = [0, 0, 0]
    while p + 10 <= total and (nblocks is None or len(blocks) < nblocks):
        if ver == 3:
            k = dc_kind(len(blocks))
            tab = Y_DC if k == 2 else C_DC
            size = next((tab[bits[p:p + ln]] for ln in range(2, 9) if bits[p:p + ln] in tab), None)
            if size is None:
                raise ValueError(f"bad DC code at bit {p}")
            p += len((Y_DC_CODE if k == 2 else C_DC_CODE)[size])
            diff = int(bits[p:p + size], 2) if size else 0
            if size and bits[p] == "0":
                diff -= (1 << size) - 1
            p += size
            pred[k] += diff * 4
            dc = pred[k] & 0x3FF
        else:
            dc = int(bits[p:p + 10], 2)
            if dc == 0x1FF:  # end of frame marker, never a real DC here
                break
            p += 10
        ac = []
        while True:
            if bits.startswith(EOB, p):
                p += 2
                break
            if bits.startswith(ESC, p):
                ac.append((int(bits[p + 6:p + 12], 2), s10(int(bits[p + 12:p + 22], 2)), True))
                p += 22
                continue
            for ln in range(2, MAXLEN + 1):
                rl = DECODE.get(bits[p:p + ln])
                if rl:
                    p += ln
                    ac.append((rl[0], -rl[1] if bits[p] == "1" else rl[1], False))
                    p += 1
                    break
            else:
                raise ValueError(f"bad VLC at bit {p}")
        blocks.append((s10(dc), ac))
    return words, q, blocks, p, ver


def code_count(blocks):
    """MDEC words the frame decodes to: DC + each AC pair + end marker, per block."""
    return sum(len(ac) + 2 for _, ac in blocks)


def dc_code(i, dc, pred):
    """Version 3 bits of block i's DC; updates pred. dc must be a multiple of 4 (to_block rounds it so)."""
    k = dc_kind(i)
    diff = (s10(dc & 0x3FF) - pred[k]) // 4
    assert (s10(dc & 0x3FF) - pred[k]) % 4 == 0 and abs(diff) < 256, f"DC {dc} after {pred[k]}"
    pred[k] += diff * 4
    size = abs(diff).bit_length()
    bits = f"{diff if diff > 0 else diff + (1 << size) - 1:0{size}b}" if size else ""
    return (Y_DC_CODE if k == 2 else C_DC_CODE)[size] + bits


def encode(q, blocks, size=None, ver=2):
    """Bytes of one frame: blocks, the end marker, zeros to a 32-bit boundary, then zeros up to size when given. A code
    parsed as an escape stays one, so an unedited frame comes out bit-exact."""
    out = []
    pred = [0, 0, 0]
    for i, (dc, ac) in enumerate(blocks):
        out.append(dc_code(i, dc, pred) if ver == 3 else f"{dc & 0x3FF:010b}")
        for item in ac:
            run, level = item[0], item[1]
            esc = item[2] if len(item) > 2 else False
            code = None if esc else ENCODE.get((run, abs(level)))
            if code:
                out.append(code + ("1" if level < 0 else "0"))
            else:
                out.append(f"{ESC}{run:06b}{level & 0x3FF:010b}")
        out.append(EOB)
    bits = "".join(out) + END[ver]
    bits += "0" * (-len(bits) % 32)
    data = b"".join(struct.pack("<H", int(bits[i:i + 16], 2)) for i in range(0, len(bits), 16))
    words = ((code_count(blocks) + 1) // 2 + 31) // 32 * 32
    res = struct.pack("<4H", words, 0x3800, q, ver) + data
    if size is not None:
        if len(res) > size:
            raise ValueError(f"frame {len(res)} bytes over {size}")
        res += b"\0" * (size - len(res))
    return res


def coefs(block, q):
    """Dequantized 8x8 coefficients (float, spatial-frequency layout)."""
    dc, ac = block
    m = np.zeros(64)
    m[0] = dc * QT[0]
    k = 0
    for item in ac:
        k += item[0] + 1
        if k > 63:
            raise ValueError("coefficient past 63")
        m[ZIGZAG[k]] = np.trunc((item[1] * QT[k] * q + (4 if item[1] >= 0 else -4)) / 8)
    return np.clip(m, -1024, 1023).reshape(8, 8)


def to_block(pix, q, step=1):
    """Quantize an 8x8 array of signed samples back to (dc, ac). step 4 for version 3, whose DC moves in steps of 4."""
    f = (_U.T @ pix @ _U).reshape(64)
    dc = int(np.clip(round(f[0] / QT[0] / step) * step, -512, 511 - 511 % step))
    ac = []
    run = 0
    for k in range(1, 64):
        level = int(round(f[ZIGZAG[k]] * 8 / (QT[k] * q)))
        if level == 0:
            run += 1
        else:
            ac.append((run, max(-512, min(511, level))))
            run = 0
    return dc, ac


class Picture:
    """A frame as coefficient blocks, with pixel access macroblock by macroblock. W, H in pixels, multiples of 16."""

    def __init__(self, bs, w, h):
        n = w // 16 * (h // 16) * MB_BLOCKS
        self.words, self.q, self.blocks, self.end, self.ver = parse(bs, n)
        self.w, self.h = w, h
        self.cols, self.rows = w // 16, h // 16
        if len(self.blocks) < n:
            raise ValueError(f"{len(self.blocks)} blocks, need {n}")
        self.tail = self.blocks[n:]
        self.blocks = self.blocks[:n]

    def _mb(self, col, row):
        return (col * self.rows + row) * MB_BLOCKS

    def get_mb(self, col, row):
        """(y 16x16, cb 8x8, cr 8x8), signed samples, y in -128..127."""
        i = self._mb(col, row)
        px = [_U @ coefs(self.blocks[i + j], self.q) @ _U.T for j in range(MB_BLOCKS)]
        y = np.block([[px[2], px[3]], [px[4], px[5]]])
        return y, px[1], px[0]

    def set_mb(self, col, row, y, cb, cr):
        i = self._mb(col, row)
        q, step = self.q, 4 if self.ver == 3 else 1
        self.blocks[i] = to_block(cr, q, step)
        self.blocks[i + 1] = to_block(cb, q, step)
        for j, (a, b) in enumerate(((0, 0), (0, 8), (8, 0), (8, 8))):
            self.blocks[i + 2 + j] = to_block(y[a:a + 8, b:b + 8], q, step)

    def rgb(self):
        """Whole frame as H x W x 3 uint8."""
        out = np.zeros((self.h, self.w, 3))
        for c in range(self.cols):
            for r in range(self.rows):
                y, cb, cr = self.get_mb(c, r)
                cb, cr = np.kron(cb, np.ones((2, 2))), np.kron(cr, np.ones((2, 2)))
                y = y + 128
                out[r * 16:r * 16 + 16, c * 16:c * 16 + 16, 0] = y + 1.402 * cr
                out[r * 16:r * 16 + 16, c * 16:c * 16 + 16, 1] = y - 0.3437 * cb - 0.7143 * cr
                out[r * 16:r * 16 + 16, c * 16:c * 16 + 16, 2] = y + 1.772 * cb
        return np.clip(out, 0, 255).astype("uint8")

    def tobytes(self, size=None):
        return encode(self.q, self.blocks + self.tail, size, self.ver)

    def tobytes_at(self, q):
        """The frame at a coarser qscale, for one that no longer fits its sectors. Always scales from the current levels:
        stepping q+1 repeatedly would round level 1 back to 1 forever."""
        new = []
        for dc, ac in self.blocks:
            out, run = [], 0
            for item in ac:
                level = int(round(item[1] * self.q / q))
                if level:
                    out.append((item[0] + run, level))
                    run = 0
                else:
                    run += item[0] + 1
            new.append((dc, out))
        return encode(q, new + self.tail, None, self.ver)


Frame = namedtuple("Frame", "no sectors chunks size w h")


def frames(sector_iter):
    """Group video sectors by frame. sector_iter yields (index, raw 2352-byte sector)."""
    out = {}
    for i, s in sector_iter:
        if struct.unpack_from("<I", s, 24)[0] != MAGIC:
            continue
        idx, cnt, no, size, w, h = struct.unpack_from("<HHIIHH", s, 28)
        f = out.setdefault(no, Frame(no, [], cnt, size, w, h))
        assert idx == len(f.sectors) and cnt == f.chunks, f"frame {no} chunk {idx} of {cnt}"
        f.sectors.append(i)
    return [out[k] for k in sorted(out)]


def frame_bytes(frame, sector):
    """Demuxed bitstream of a Frame; sector(i) returns raw sector i."""
    return b"".join(sector(i)[56:56 + CHUNK] for i in frame.sectors)[:frame.size]
