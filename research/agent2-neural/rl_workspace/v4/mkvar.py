"""bots/NAME = bots/SRC with defines replaced in place (or prepended). usage: python mkvar.py SRC NAME DEF=V ..."""
import re, shutil, sys
from pathlib import Path
src, name, defs = sys.argv[1], sys.argv[2], sys.argv[3:]
d = Path("bots") / name
if d.exists(): shutil.rmtree(d)
shutil.copytree(Path("bots") / src, d, ignore=shutil.ignore_patterns(".cambc"))
p = d / "src" / "common.h"; t = p.read_text(encoding="utf-8")
pre = []
for kv in defs:
    k, v = kv.split("=", 1)
    pat = re.compile(rf"^#define {re.escape(k)}\b.*$", re.M)
    m = pat.search(t)
    if m and m.start() < t.find("#pragma once"): t = t[:m.start()] + f"#define {k} {v}" + t[m.end():]
    else: pre.append(f"#define {k} {v}\n")
p.write_text("".join(pre) + t, encoding="utf-8", newline="\n")
