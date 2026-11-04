"""E120 fuel probe: BOT vs OPP on a map range, both sides, replays kept; per game the outcome, the engine's bot-fault
count for BOT (diagnostics.botFaults) and BOT's last NNFUEL line (A2_NN_FUEL builds print the running mean fuel per
network decision: features, network, and the fuel left when the decision started). Without --fuel the engine's real
per-turn fuel applies. Summary: wins, faults, mean feature / network fuel, budget range.
usage (project root): python -P agent2/lab/fuel_probe.py BOT OPP DIR:A:B [--fuel N]"""
import json, os, re, shutil, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4 = os.path.join(ROOT, "v4")
A = sys.argv[1:]
FUEL = A[A.index("--fuel") + 1] if "--fuel" in A else None
A = [a for i, a in enumerate(A) if not a.startswith("--") and (i == 0 or not A[i - 1].startswith("--"))]
BOT, OPP, SPEC = A[0], A[1], A[2]
d, a, b = (SPEC.split(":") + ["0", "100000"])[:3]
maps = sorted(f for f in os.listdir(os.path.join(V4, d)) if f.endswith(".map26a"))[int(a):int(b)]
tag = f"bench_out/fuelprobe/{BOT}_vs_{OPP}_{'f' + FUEL if FUEL else 'real'}"
shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
os.makedirs(os.path.join(V4, tag))
lines, keys = [], []
for m in maps:
    for s in "AB":
        x, y = (BOT, OPP) if s == "A" else (OPP, BOT)
        f = f"{tag}/{m[:-7]}_{s}"
        lines.append(f"bots/{x} bots/{y} {d}/{m} {f}.repl26a --statistics {f}.json --json")
        keys.append((m[:-7], s, f))
man = os.path.join(V4, ".m_fuelprobe.txt")
open(man, "w").write("\n".join(lines) + "\n")
subprocess.run([os.path.join(V4, "cambc.exe"), "run-batch", man, "--jobs", "5", "--json", "--color", "never", "--release",
                "--log-limit", "67108864"] + (["--fuel-quantum", FUEL] if FUEL else []), cwd=V4,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
pat = re.compile(r"NNFUEL feats (\d+) net (\d+) per turn \(budget (\d+)\)")
w = n = faults = 0.0
fe, ne, bud = [], [], []
for m, s, f in keys:
    try:
        st = json.load(open(os.path.join(V4, f + ".json")))
    except Exception:
        print(f"{m} {s}: no result")
        continue
    me = "teamA" if s == "A" else "teamB"
    oc = st["match"].get("outcome")
    win = 1.0 if oc == me else 0.0 if oc in ("teamA", "teamB") else 0.5
    flt = st["diagnostics"]["botFaults"].get(me, 0)
    try:
        txt = zipfile.ZipFile(os.path.join(V4, f + ".repl26a")).read(f"team-{s.lower()}.stdout").replace(b"\0", b"").decode("utf-8", "replace")
    except Exception:
        txt = ""
    rows = pat.findall(txt)
    if rows:
        fe.append(int(rows[-1][0])); ne.append(int(rows[-1][1]))
        bud += [int(r[2]) for r in rows]
    w += win; n += 1; faults += flt
    print(f"{m} {s}: {'win' if win == 1 else 'loss' if win == 0 else 'draw'}, faults {flt}, rounds {st['match'].get('roundsCompleted')}"
          + (f", feats {rows[-1][0]} net {rows[-1][1]} per decision" if rows else ", no NNFUEL lines"), flush=True)
mean = lambda v: sum(v) / max(1, len(v))
print(f"{BOT} vs {OPP} ({'fuel ' + FUEL if FUEL else 'real fuel'}): {w:.1f}/{n:.0f} wins, bot faults {faults:.0f}; fuel per network "
      f"decision: features {mean(fe):.0f}, network {mean(ne):.0f}; fuel left at the decision: "
      + (f"min {min(bud)} median {sorted(bud)[len(bud) // 2]} max {max(bud)}" if bud else "n/a"))
