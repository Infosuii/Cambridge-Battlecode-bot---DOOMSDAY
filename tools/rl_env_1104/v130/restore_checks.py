"""Handover 9.4: restore v112's `(bc::fuel_remaining() + nn_spent)` fuel checks in a v113-based source, outside
nnrec.cpp, only where v113's line is exactly v112's line with that swap (every other v113 change is kept).
usage: restore_checks.py V112_SRC V113_SRC OUT_SRC"""
import difflib, os, shutil, sys

OLD, NEW = "(bc::fuel_remaining() + nn_spent)", "bc::fuel_remaining()"
a_dir, b_dir, out = sys.argv[1:4]
if os.path.exists(out):
    sys.exit(f"{out} exists")
shutil.copytree(b_dir, out)
total, review = 0, []
for f in sorted(os.listdir(a_dir)):
    if not f.endswith((".cpp", ".h")) or f == "nnrec.cpp":
        continue
    a_text = open(os.path.join(a_dir, f), encoding="utf-8", newline="").read()
    if OLD not in a_text:
        continue
    b_path = os.path.join(out, f)
    b_lines = open(b_path, encoding="utf-8", newline="").read().splitlines(keepends=True)
    a_lines = a_text.splitlines(keepends=True)
    norm = lambda s: s.rstrip("\r\n")
    sm = difflib.SequenceMatcher(None, [norm(x) for x in a_lines], [norm(x) for x in b_lines], autojunk=False)
    res, n = [], 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "replace" and i2 - i1 == j2 - j1:
            for a, b in zip(a_lines[i1:i2], b_lines[j1:j2]):
                if OLD in a and norm(a).replace(OLD, NEW) == norm(b):
                    res.append(norm(a) + b[len(norm(b)):]); n += norm(a).count(OLD)
                else:
                    res.append(b)
                    if OLD in a:
                        review.append((f, norm(a).strip()[:120], norm(b).strip()[:120]))
        else:
            res.extend(b_lines[j1:j2])
            if op in ("replace", "delete"):
                for a in a_lines[i1:i2]:
                    if OLD in a:
                        review.append((f, norm(a).strip()[:120], "(no 1:1 v113 line)"))
    open(b_path, "w", encoding="utf-8", newline="").write("".join(res))
    want = a_text.count(OLD)
    print(f"{f:20s} restored {n:3d} of {want:3d} v112 sites")
    total += n
print("total restored", total)
for r in review:
    print("REVIEW", r)
