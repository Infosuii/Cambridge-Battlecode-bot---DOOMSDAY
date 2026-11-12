"""Held-out real-engine check (E103): each candidate plays each opponent on a map set, both sides, through e95_run.py
(one build at a time, RAM watchdog). Per-game rows go to OUT.tsv (bot, opp, map, side, win, gems us, gems them);
result JSONs and replays are deleted after scoring; finished (bot, opp, suite) runs are skipped on a rerun.
usage: python -P agent2/lab/held_run.py OUT.tsv CANDS OPPS SUITE [--fuel N]
  CANDS / OPPS: comma lists; OPPS may be "held" (v81_c3, x1_c3, v81_c4, x1_c4, v86h, b5_c3, v61_c3)
  SUITE: ladder (maps 0-70) | unseen (maps_mazetest 0-99 + maps_real200b 50-99) | DIR:A:B[,DIR:A:B]
"""
import glob, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V4 = os.path.join(ROOT, "v4")
RUN = os.path.join(ROOT, "agent2", "lab", "e95_run.py")
A = sys.argv[1:]
FUEL = A[A.index("--fuel") + 1] if "--fuel" in A else None
A = [a for i, a in enumerate(A) if not a.startswith("--") and (i == 0 or not A[i - 1].startswith("--"))]
OUT, CANDS, OPPS, SUITE = A[0], A[1].split(","), A[2], A[3]
HELD = ["v81_c3", "x1_c3", "v81_c4", "x1_c4", "v86h", "b5_c3", "v61_c3"]
OPPS = HELD if OPPS == "held" else OPPS.split(",")
SPEC = {"ladder": "maps:0:70", "unseen": "maps_mazetest:0:100,maps_real200b:50:100"}.get(SUITE, SUITE)
done = set()
if os.path.exists(OUT):
    done = {tuple(l.split("\t")[:2]) for l in open(OUT)}
for opp in OPPS:
    for bot in CANDS:
        if (bot, opp) in done or bot == opp:
            continue
        tag = f"held/{bot}_vs_{opp}"
        cmd = [sys.executable, "-P", RUN, opp, bot, "--maps", SPEC, "--tag", tag] + (["--fuel", FUEL] if FUEL else [])
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip()[-500:], flush=True)
        d = os.path.join(V4, "bench_out", "e95", tag)
        rows = []
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            base = os.path.basename(f)[:-5]
            side, mp = base[-1], base[2:-2]
            try:
                res = json.load(open(f))
            except Exception:
                continue
            oc = res["match"].get("outcome")
            me, them = ("teamA", "teamB") if side == "A" else ("teamB", "teamA")
            win = 1.0 if oc == me else 0.0 if oc == them else 0.5
            gems = {t["team"]: t["submittedGems"] for t in res.get("teams", [])}
            rows.append(f"{bot}\t{opp}\t{mp}\t{side}\t{win}\t{gems.get(me, '')}\t{gems.get(them, '')}\n")
        with open(OUT, "a") as fh:
            fh.writelines(rows)
        shutil.rmtree(d, ignore_errors=True)
# summary
tot = {}
for l in open(OUT):
    bot, opp, mp, side, win = l.split("\t")[:5]
    t = tot.setdefault(bot, {})
    t.setdefault(opp, [0.0, 0])
    t[opp][0] += float(win); t[opp][1] += 1
for bot, t in tot.items():
    w = sum(v[0] for v in t.values()); n = sum(v[1] for v in t.values())
    print(f"{bot}: {w:.1f}/{n} = {100 * w / max(1, n):.1f}%  (" + ", ".join(f"{o} {v[0]:.0f}/{v[1]}" for o, v in t.items()) + ")")
