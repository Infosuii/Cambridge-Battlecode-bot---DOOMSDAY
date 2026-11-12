"""Per-version fuel use of our live bot on the ladder, from the engine's own trace (team-<side>.fuel in match downloads).

Lists our ranked matches since --since, assigns each to a version by --window vNNN=START (UTC ISO; a window ends at
the next start), downloads up to --per-version matches per version (cached under --cache; read-only platform calls
with backoff), and reports per version: games, win rate, play turns, mean / p50 / p90 / p99 fuel per turn, fuel-outs
(a turn word equal to the 100,000 budget) per game, and the share of games with at least one fuel-out.

Engine 3.0.0 trace format: 13-byte header ('a62leuf' + version), u64 words: 8 budget words (draft 10M, turn 100k,
first play turn 200k, 100k; twice), then one word per body-turn in execution order (draft picks first). The first
12 turn words (draft picks and the 200k first play turns) are skipped.

usage: python -I tools/rl_env_1104/ladder_fuel.py --since 2026-11-08T05:25 --window v112=2026-11-08T05:25 \
           --window v113=2026-11-08T22:08 --window v114=2026-11-08T23:15 [--per-version 40]
"""
import argparse
import json
import os
import struct
import subprocess
import time
import zipfile

CLI = r"C:/Users/info/.venvs/cambc5/Scripts/cambc.exe"
ME = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"
BUDGET = 100000


def run(args, json_out=True):
    for attempt in range(10):
        r = subprocess.run([CLI] + args, capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0:
            return json.loads(r.stdout) if json_out else r.stdout
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(r.stdout + r.stderr)


def turns(path, side):
    b = zipfile.ZipFile(path).read(f"team-{side}.fuel")
    n = (len(b) - 13) // 8
    v = struct.unpack("<%dQ" % n, b[13:13 + 8 * n])
    return list(v[8 + 12:])


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True)
    ap.add_argument("--window", action="append", required=True)
    ap.add_argument("--per-version", type=int, default=40)
    ap.add_argument("--cache", default="artifacts/tmp/ladder_fuel")
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    wins = sorted((s.split("=", 1)[1], s.split("=", 1)[0]) for s in a.window)
    ms, cur = [], None
    while True:
        d = run(["matches", "list", "--team", "me", "--kind", "ranked", "--limit", "100", "--json"] + (["--cursor", cur] if cur else []))
        ms += d["matches"]
        cur = d.get("nextCursor")
        if not cur or not d["matches"] or d["matches"][-1]["createdAt"] < a.since:
            break
    by_v = {}
    for m in ms:
        if m["status"] != "finished" or m["createdAt"] < a.since:
            continue
        for i, (start, name) in enumerate(wins):
            end = wins[i + 1][0] if i + 1 < len(wins) else "9999"
            if start <= m["createdAt"] < end:
                by_v.setdefault(name, []).append(m)
    for name in sorted(by_v):
        sample = by_v[name][: a.per_version]  # newest first
        stats = dict(games=0, wins=0, turns=[], outs=[], maps=[])
        for m in sample:
            us = next(t for t in m["teams"] if t["teamId"] == ME)
            path = os.path.join(a.cache, m["matchId"] + ".zip")
            if not os.path.exists(path):
                tmp = path + ".part"
                run(["matches", "download", m["matchId"], "-o", tmp], json_out=False)
                os.replace(tmp, path)
                time.sleep(1.0)
            try:
                t = turns(path, us["side"])
            except (KeyError, zipfile.BadZipFile, struct.error):
                continue
            stats["games"] += 1
            stats["wins"] += us["result"] == "win"
            stats["turns"] += t
            stats["outs"].append(sum(x >= BUDGET for x in t))
            stats["maps"].append(m["map"])
        tt, outs, g = stats["turns"], stats["outs"], max(1, stats["games"])
        print(f"{name}: {stats['games']}/{len(by_v[name])} games sampled, win {stats['wins'] / g:.0%}, {len(tt)} turns, "
              f"mean {sum(tt) / max(1, len(tt)):,.0f} p50 {pct(tt, .5):,} p90 {pct(tt, .9):,} p99 {pct(tt, .99):,}; "
              f"fuel-outs {sum(outs) / g:.2f}/game (max {max(outs or [0])}), games with any {sum(o > 0 for o in outs) / g:.0%}, "
              f">=90k turns {sum(x >= 90000 for x in tt) / max(1, len(tt)):.1%}")


if __name__ == "__main__":
    main()
