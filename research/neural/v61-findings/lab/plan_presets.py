"""Specialist plan presets (E61): average the knob vectors of the later generations of each cluster search
(plan_c<k>.tsv from plan_search.ps1) and write plan_sel.h for a bot source tree. A cluster without a search result
keeps the base knobs (knobs_m62_init.txt).
usage: python plan_presets.py OUT_plan_sel.h [first_gen=8] [last_gen=all]"""
import sys

out = sys.argv[1]
G0 = int(sys.argv[2]) if len(sys.argv) > 2 else 8
G1 = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
base = [float(x) for x in open("knobs_m62_init.txt").read().strip().split(",")]
base += [0.0] * (48 - len(base))
plans = []
for k in range(4):
    try:
        rows = [line.rstrip("\n").split("\t") for line in open(f"plan_c{k}.tsv")][1:]
    except FileNotFoundError:
        rows = []
    sel = [r for r in rows if G0 <= int(r[0]) <= G1]
    if not sel:
        print(f"cluster {k}: no generations {G0}..{G1}, base knobs")
        plans.append(base)
        continue
    v = [sum(float(r[5 + i]) for r in sel) / len(sel) for i in range(48)]
    moved = sorted(range(48), key=lambda i: -abs(v[i] - base[i]))[:5]
    print(f"cluster {k}: gens {sel[0][0]}..{sel[-1][0]} ({len(sel)}), centre win " + " ".join(r[1] for r in sel)
          + " | biggest moves " + ", ".join(f"k{i} {base[i]:.2f}->{v[i]:.2f}" for i in moved))
    plans.append(v)
head = open(out, encoding="utf-8").read().split("inline constexpr float kPlan")[0]
body = "inline constexpr float kPlan[kPlans][kKnobs] = {\n" + "".join(
    "    {" + ", ".join(f"{x:.4f}f" for x in p) + "},\n" for p in plans) + "};\n} // namespace plan_sel\n"
open(out, "w", encoding="utf-8", newline="\n").write(head + body)
print("wrote", out)
