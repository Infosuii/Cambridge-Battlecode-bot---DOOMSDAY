"""Matched evaluation runner (task rl-env-collector-1104, JOHNDOE #45 item 3 / #49 map manifest).

Plays one or more candidate bots against a frozen opponent pool on the maps of ONE split of the evaluation map
manifest, both sides, through `cambc run-batch`, and writes a report: per-game rows, per candidate x opponent
summaries, and a map-family-clustered bootstrap interval for the win rate. All candidates play the identical cells
(same maps, sides, opponents, build mode), so candidates are compared paired. Map hashes are checked against the
manifest before any game runs. The `confirmation` split is refused unless --confirm is given (no tuning on it).

usage (repo root):
  python tools/rl_env_1104/eval/run_eval.py --manifest EVALUATION_MAP_MANIFEST.json --split development \
      --candidate native=bots/claude-native-1104 --candidate v92=bots/v92 --opponent v92=bots/v92 \
      --out runs/rl_env_1104/eval/dev-01 [--release] [--jobs 3] [--max-maps N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CLI = os.path.join(ROOT, "tools", "vendor", "cambc.exe" if os.name == "nt" else "cambc")
MAP_DIR = os.path.join(ROOT, "maps", "ladder-pool")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def absp(p: str) -> str:
    return os.path.abspath(os.path.join(ROOT, p)).replace("\\", "/")


def named(items: list) -> list:
    out = []
    for it in items:
        name, _, path = it.partition("=")
        if not path:
            raise SystemExit(f"expected name=path, got {it}")
        out.append((name, path.replace("\\", "/")))
    return out


def build_hash(bot: str, work: str, release: bool) -> str:
    out = os.path.join(work, os.path.basename(bot.rstrip("/")) + ("-rel" if release else "-dbg") + ".wasm")
    r = subprocess.run([CLI, "build", bot] + (["--release"] if release else []) + ["--output", out], cwd=ROOT,
                       capture_output=True, text=True, timeout=900)
    if r.returncode or not os.path.exists(out):
        raise SystemExit(f"build of {bot} failed: " + r.stdout[-2000:])
    return sha256(out)


def wilson(w: float, n: int) -> tuple:
    if n == 0:
        return (None, None)
    z, p = 1.96, w / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return (round(c - h, 4), round(c + h, 4))


def cluster_bootstrap(rows: list, reps: int = 4000, seed: int = 1104) -> tuple:
    """95% interval of the win rate resampling whole map families (cells of a family are correlated)."""
    fam = {}
    for r in rows:
        fam.setdefault(r["family"], []).append(r["score"])
    keys = sorted(fam)
    if not keys:
        return (None, None)
    rng = random.Random(seed)
    stats = []
    for _ in range(reps):
        pick = [fam[rng.choice(keys)] for _ in keys]
        tot = sum(len(p) for p in pick)
        stats.append(sum(sum(p) for p in pick) / tot)
    stats.sort()
    return (round(stats[int(0.025 * reps)], 4), round(stats[int(0.975 * reps) - 1], 4))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", required=True, choices=["training", "development", "confirmation"])
    ap.add_argument("--confirm", action="store_true", help="allow the confirmation split (never for tuning)")
    ap.add_argument("--candidate", action="append", required=True, help="name=bot_dir (repeatable)")
    ap.add_argument("--opponent", action="append", required=True, help="name=bot_dir (repeatable)")
    ap.add_argument("--sides", default="A,B")
    ap.add_argument("--release", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--max-maps", type=int, help="first N maps of the split in manifest order (smoke runs)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.split == "confirmation" and not a.confirm:
        raise SystemExit("refusing the confirmation split without --confirm")
    out_dir = os.path.join(ROOT, a.out)
    if os.path.exists(out_dir):
        raise SystemExit("output directory must be new")
    os.makedirs(out_dir)
    with open(a.manifest, encoding="utf-8") as f:
        man = json.load(f)
    maps = [m for m in man["maps"] if m["split"] == a.split]
    if a.max_maps:
        maps = maps[:a.max_maps]
    for m in maps:  # pin the map content to the manifest before playing anything
        got = sha256(os.path.join(MAP_DIR, m["file"]))
        if got != m["sha256"]:
            raise SystemExit(f"map {m['file']} sha256 {got} != manifest {m['sha256']}")
    cands, opps = named(a.candidate), named(a.opponent)
    work = os.path.join(out_dir, "work")
    os.makedirs(work)
    hashes = {n: build_hash(p, work, a.release) for n, p in cands + opps}
    cells, lines = [], []
    for cn, cp in cands:
        for on, op in opps:
            for m in maps:
                for side in a.sides.split(","):
                    gi = len(cells)
                    rep, st = os.path.join(work, f"g{gi}.repl26a"), os.path.join(work, f"g{gi}.json")
                    pair = (absp(cp), absp(op)) if side == "A" else (absp(op), absp(cp))
                    lines.append(f"{pair[0]} {pair[1]} {absp(os.path.join('maps', 'ladder-pool', m['file']))} "
                                 f"{rep.replace(chr(92), '/')} --statistics {st.replace(chr(92), '/')} --json")
                    cells.append(dict(candidate=cn, opponent=on, map=m["file"], family=m["family"], side=side,
                                      rep=rep, st=st))
    batch = os.path.join(work, "batch.txt")
    with open(batch, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    cmd = [CLI, "run-batch", batch.replace("\\", "/"), "--jobs", str(a.jobs), "--json", "--color", "never",
           "--timeout", str(a.timeout), "--log-limit", "0"] + (["--release"] if a.release else [])
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    with open(os.path.join(work, "batch.log"), "w", encoding="utf-8") as f:
        f.write(r.stdout + "\n---\n" + r.stderr)
    rows = []
    for c in cells:
        row = dict(candidate=c["candidate"], opponent=c["opponent"], map=c["map"], family=c["family"], side=c["side"])
        if not os.path.exists(c["st"]):
            row.update(status="failed")
            rows.append(row)
            continue
        with open(c["st"], encoding="utf-8") as f:
            s = json.load(f)
        our = "teamA" if c["side"] == "A" else "teamB"
        th = "teamB" if our == "teamA" else "teamA"
        sc = {t["team"]: int(t["submittedGems"]) for t in s["teams"]}
        fo = lambda t: sum(len(e["entries"]) for e in s["events"] if e["kind"] == "fuelExhausted"
                           and e["owner"].get("team") == t)
        oc = s["match"]["outcome"]
        row.update(status="ok", outcome=oc, score=1.0 if oc == our else (0.0 if oc == th else 0.5), ours=sc.get(our),
                   theirs=sc.get(th), rounds=s["match"]["roundsCompleted"], fuel_outs=fo(our), opp_fuel_outs=fo(th),
                   faults=s["diagnostics"]["botFaults"].get(our, 0), engine=s["match"]["engineBuildHash"])
        rows.append(row)
    summary = {}
    for cn, _ in cands:
        for on, _ in opps + [("ALL", None)]:
            rs = [x for x in rows if x["candidate"] == cn and (on == "ALL" or x["opponent"] == on) and x["status"] == "ok"]
            w = sum(x["score"] for x in rs)
            summary[f"{cn} vs {on}"] = dict(games=len(rs), score=w, win_rate=round(w / len(rs), 4) if rs else None,
                                            wilson95=wilson(w, len(rs)), family_bootstrap95=cluster_bootstrap(rs),
                                            fuel_outs=sum(x["fuel_outs"] for x in rs),
                                            faults=sum(x["faults"] for x in rs),
                                            failed=sum(1 for x in rows if x["candidate"] == cn and x["status"] != "ok"
                                                       and (on == "ALL" or x["opponent"] == on)))
    report = dict(kind="matched evaluation (descriptive; deterministic engine)", split=a.split,
                  manifest=dict(path=a.manifest, sha256=sha256(a.manifest), schema=man.get("schema"),
                                status=man.get("status")),
                  build="release" if a.release else "debug", wasm_sha256=hashes,
                  candidates=dict(cands), opponents=dict(opps), maps=[m["file"] for m in maps], sides=a.sides,
                  summary=summary, games=rows)
    with open(os.path.join(out_dir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    for k, v in summary.items():
        print(f"{k}: {v['score']}/{v['games']} win {v['win_rate']} wilson {v['wilson95']} family-bootstrap "
              f"{v['family_bootstrap95']} fuel-outs {v['fuel_outs']} faults {v['faults']} failed {v['failed']}")


if __name__ == "__main__":
    main()
