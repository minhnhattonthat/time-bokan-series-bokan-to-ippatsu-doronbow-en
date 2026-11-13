"""PS1 MODE2/2352 raw track: ISO9660 listing, file read, in-place file write with EDC/ECC.

usage: disc.py list BIN | disc.py x BIN OUTDIR | disc.py verify BIN
Library: Disc(path); .files -> {path: Entry}; .read(path) -> bytes; .write_file(path, data)
Pure Python replaces mkpsxiso here: files keep their LBA, so no rebuild, and CD audio tracks stay untouched.
Form 2 sectors (XA/STR) are read as 2324 bytes and never rewritten."""
import os
import struct
import sys
from collections import namedtuple

SECTOR = 2352
SUB = 16        # subheader offset
USER = 24       # user data offset in mode 2
FORM2 = 0x20    # submode bit
Entry = namedtuple("Entry", "path lba size rec_pos flags")

_edc = []
for i in range(256):
    c = i
    for _ in range(8):
        c = (c >> 1) ^ 0xD8018001 if c & 1 else c >> 1
    _edc.append(c)
_gf_f = [0] * 256
_gf_b = [0] * 256
for i in range(256):
    j = (i << 1) ^ (0x11D if i & 0x80 else 0)
    _gf_f[i] = j & 0xFF
    _gf_b[i ^ j] = i


def edc(data):
    c = 0
    for b in data:
        c = (c >> 8) ^ _edc[(c ^ b) & 0xFF]
    return struct.pack("<I", c)


def _ecc(buf, major, minor, mult, inc, out):
    """ECC-P or ECC-Q over buf (the sector from offset 12), parity to buf[out:]."""
    size = major * minor
    for mj in range(major):
        idx = (mj >> 1) * mult + (mj & 1)
        a = b = 0
        for _ in range(minor):
            t = buf[idx]
            idx += inc
            if idx >= size:
                idx -= size
            a ^= t
            b ^= t
            a = _gf_f[a]
        a = _gf_b[_gf_f[a] ^ b]
        buf[out + mj] = a
        buf[out + mj + major] = a ^ b


def form1_seal(sec):
    """Recompute EDC and ECC of a mode 2 form 1 sector, in place. The header counts as zero for ECC."""
    sec[2072:2076] = edc(bytes(sec[16:2072]))
    hdr = bytes(sec[12:16])
    sec[12:16] = b"\0\0\0\0"
    buf = sec[12:]
    _ecc(buf, 86, 24, 2, 86, 0x81C - 12)    # parity offsets are per sector; buf starts at byte 12
    _ecc(buf, 52, 43, 86, 88, 0x8C8 - 12)
    sec[12:] = buf
    sec[12:16] = hdr


class Disc:
    def __init__(self, path, write=False):
        self.f = open(path, "r+b" if write else "rb")
        self.f.seek(0, 2)
        self.sectors = self.f.tell() // SECTOR
        self.files = {}
        pvd = self.user(16)
        assert pvd[1:6] == b"CD001", "no ISO9660 volume"
        self.volume = struct.unpack_from("<I", pvd, 80)[0]
        root = pvd[156:190]
        self._dir(struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0], "")

    def raw(self, lba):
        self.f.seek(lba * SECTOR)
        return self.f.read(SECTOR)

    def user(self, lba):
        s = self.raw(lba)
        return s[USER:USER + (2324 if s[SUB + 2] & FORM2 else 2048)]

    def _dir(self, lba, size, path):
        data = b"".join(self.user(lba + i)[:2048] for i in range(-(-size // 2048)))
        i = 0
        while i < size:
            n = data[i]
            if n == 0:
                i = (i // 2048 + 1) * 2048
                continue
            rec = data[i:i + n]
            pos = (lba + i // 2048, i % 2048)
            i += n
            name = rec[33:33 + rec[32]]
            if name in (b"\0", b"\1"):
                continue
            p = path + "/" + name.decode("latin1").split(";")[0]
            loc, ln = struct.unpack_from("<I", rec, 2)[0], struct.unpack_from("<I", rec, 10)[0]
            if rec[25] & 2:
                self._dir(loc, ln, p)
            else:
                self.files[p] = Entry(p, loc, ln, pos, rec[25])

    def is_xa(self, e):
        """True if any sector of the file is form 2 (STR/XA), or the entry points past this track (CD audio)."""
        n = max(1, -(-e.size // 2048))
        return e.lba + n > self.sectors or any(self.raw(e.lba + i)[SUB + 2] & FORM2 for i in range(n))

    def read(self, path):
        e = self.files[path]
        return b"".join(self.user(e.lba + i)[:2048] for i in range(-(-e.size // 2048)))[:e.size]

    def write_file(self, path, data):
        """Overwrite a form 1 file in place. Must fit its sectors; size field is unchanged unless it differs."""
        e = self.files[path]
        n = -(-e.size // 2048)
        assert len(data) <= n * 2048, f"{path}: {len(data)} > {n} sectors"
        assert len(data) == e.size, f"{path}: resize not supported ({len(data)} != {e.size})"
        data = data.ljust(n * 2048, b"\0")
        for i in range(n):
            sec = bytearray(self.raw(e.lba + i))
            assert not sec[SUB + 2] & FORM2, f"{path}: form 2 sector"
            new = data[i * 2048:(i + 1) * 2048]
            # keep the original tail padding of the last sector
            if i == n - 1 and e.size % 2048:
                tail = e.size % 2048
                new = new[:tail] + bytes(sec[USER + tail:USER + 2048])
            sec[USER:USER + 2048] = new
            form1_seal(sec)
            self.f.seek((e.lba + i) * SECTOR)
            self.f.write(sec)


if __name__ == "__main__":
    cmd, path = sys.argv[1], sys.argv[2]
    d = Disc(path)
    if cmd == "list":
        print("sectors", d.sectors, "volume", d.volume)
        for e in sorted(d.files.values(), key=lambda e: e.lba):
            print(f"{e.lba:8d} {e.size:11d} {e.path} {'XA' if d.is_xa(e) else ''}")
    elif cmd == "x":
        for p, e in d.files.items():
            out = sys.argv[3] + p
            os.makedirs(os.path.dirname(out), exist_ok=True)
            if d.is_xa(e):
                continue    # streams stay on the disc; read them by sector when needed
            with open(out, "wb") as f:
                f.write(d.read(p))
    elif cmd == "verify":   # form1_seal must reproduce every form 1 sector
        bad = 0
        for lba in range(d.sectors):
            s = d.raw(lba)
            if s[SUB + 2] & FORM2 or s[15] != 2:
                continue
            t = bytearray(s)
            form1_seal(t)
            if bytes(t) != s:
                bad += 1
                if bad < 5:
                    print("mismatch at", lba)
        print("bad", bad)
        sys.exit(bool(bad))
