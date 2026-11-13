"""List every task the EXE spawns: each `jal 8002ED18` (create task: a0 group, a1 function, a2 delay) with the a0/a1
values built just before it. Recon for docs/re/state.md.

    python -X utf8 tools/task_spawns.py [work/x/BOKAN.EXE]
"""
import struct
import sys

from capstone import CS_ARCH_MIPS, CS_MODE_32, CS_MODE_LITTLE_ENDIAN, Cs

path = sys.argv[1] if len(sys.argv) > 1 else "work/x/BOKAN.EXE"
d = open(path, "rb").read()
base = struct.unpack_from("<I", d, 0x18)[0]
code = d[0x800:]
md = Cs(CS_ARCH_MIPS, CS_MODE_32 | CS_MODE_LITTLE_ENDIAN)
md.skipdata = True  # data words between functions would end the sweep
ins = list(md.disasm(code, base))
CREATE = 0x8002ED18
for i, x in enumerate(ins):
    if x.mnemonic != "jal" or int(x.op_str, 16) != CREATE:
        continue
    regs = {}
    for y in ins[max(0, i - 12): i + 2]:  # +2: the delay slot
        ops = [o.strip() for o in y.op_str.split(",")]
        if y.mnemonic == "lui":
            regs[ops[0]] = int(ops[1], 16) << 16
        elif y.mnemonic in ("addiu", "ori") and ops[1] in regs | {"$zero": 0}:
            v = (regs.get(ops[1], 0) + int(ops[2], 16)) if y.mnemonic == "addiu" else (regs.get(ops[1], 0) | int(ops[2], 16))
            regs[ops[0]] = v & 0xFFFFFFFF
        elif y.mnemonic == "move" and ops[1] == "$zero":
            regs[ops[0]] = 0
    a0, a1 = regs.get("$a0"), regs.get("$a1")
    print(f"{x.address:08X} group={a0 if a0 is None else hex(a0)} fn={a1 if a1 is None else f'{a1:08X}'}")
