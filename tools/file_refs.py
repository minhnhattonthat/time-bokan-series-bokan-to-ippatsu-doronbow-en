"""Which code loads which disc file: every `\\DIR\\NAME.EXT;1` string in BOKAN.EXE with the addresses of the
lui+addiu pairs (or pointer words) that build its address, and the task function (from tools/task_spawns.py's list)
whose code comes last before that site. Recon for docs/re/state.md.

    python -X utf8 tools/file_refs.py [work/x/BOKAN.EXE]
"""
import re
import struct
import sys

from capstone import CS_ARCH_MIPS, CS_MODE_32, CS_MODE_LITTLE_ENDIAN, Cs

path = sys.argv[1] if len(sys.argv) > 1 else "work/x/BOKAN.EXE"
d = open(path, "rb").read()
base = struct.unpack_from("<I", d, 0x18)[0] - 0x800
strings = {m.start() + base: m.group().decode() for m in re.finditer(rb"\\[A-Z0-9_\\]+\.[A-Z0-9]+;1", d)}
md = Cs(CS_ARCH_MIPS, CS_MODE_32 | CS_MODE_LITTLE_ENDIAN)
md.skipdata = True
refs = {a: [] for a in strings}
hi = {}
for x in md.disasm(d[0x800:], base + 0x800):
    ops = [o.strip() for o in x.op_str.split(",")]
    if x.mnemonic == "lui":
        hi[ops[0]] = (int(ops[1], 16) << 16, x.address)
    elif x.mnemonic == "addiu" and ops[1] in hi:
        t = (hi[ops[1]][0] + int(ops[2], 16)) & 0xFFFFFFFF
        if t in refs:
            refs[t].append(x.address)
for off in range(0x800, len(d) - 3, 4):
    w = struct.unpack_from("<I", d, off)[0]
    if w in refs:
        refs[w].append(base + off)
for a in sorted(strings):
    print(f"{a:08X} {strings[a]:28} {' '.join(f'{r:08X}' for r in refs[a])}")
