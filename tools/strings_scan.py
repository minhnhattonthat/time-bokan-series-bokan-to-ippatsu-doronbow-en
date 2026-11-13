"""List ASCII strings of a binary with offsets, dropping file paths and noise. usage: strings_scan.py FILE [min_len]"""
import re
import sys

b = open(sys.argv[1], "rb").read()
n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
for m in re.finditer(rb"[\x20-\x7e]{%d,}" % n, b):
    t = m.group().decode()
    if not t.startswith(chr(92)) and re.search("[A-Za-z]{2}", t) and not re.fullmatch("[r_P/b ]+", t):
        print(f"{m.start():#08x} {t}")
