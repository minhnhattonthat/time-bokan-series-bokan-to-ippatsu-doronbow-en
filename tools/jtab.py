"""Print a jump table from BOKAN.EXE (or an overlay with --base): u32 entries from ADDR.

    python -X utf8 tools/jtab.py ADDR COUNT [--file work/x/BOKAN.EXE] [--base HEX]
"""
import argparse
import struct

ap = argparse.ArgumentParser()
ap.add_argument("addr")
ap.add_argument("count", type=int)
ap.add_argument("--file", default="work/x/BOKAN.EXE")
ap.add_argument("--base", help="RAM address of file offset 0 (default: PS-X EXE header)")
a = ap.parse_args()
d = open(a.file, "rb").read()
base = int(a.base, 16) if a.base else struct.unpack_from("<I", d, 0x18)[0] - 0x800
addr = int(a.addr, 16)
for i in range(a.count):
    print(f"{i:3X} {struct.unpack_from('<I', d, addr - base + 4 * i)[0]:08X}")
