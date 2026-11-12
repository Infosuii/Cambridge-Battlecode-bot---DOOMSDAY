"""Ladder monitor: ranked results of our live versions against Elo expectation (read-only platform calls).

Fetches our ranked matches since --since (UTC ISO), assigns each to a version by activation windows given as
--window vNNN=START (UTC ISO; the window ends at the next start), and reports per version: games, wins, mean
opponent rating (current ladder ratings), expected score at our current rating, and the performance-rating
difference (wins - expected) / games converted to Elo, plus a Wilson interval.

usage: python -I tools/rl_env_1104/ladder_monitor.py --since 2026-11-08T05:25 --window v112=2026-11-08T05:25 [--window v113=...]
"""
import argparse
import json
import math
import subprocess
import time

CLI = r"C:/Users/info/.venvs/cambc5/Scripts/cambc.exe"
ME = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"


def call(args):
    for attempt in range(8):
        r = subprocess.run([CLI] + args, capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0:
            return json.loads(r.stdout)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(r.stdout + r.stderr)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True)
    ap.add_argument("--window", action="append", required=True)
    a = ap.parse_args()
    wins = sorted((s.split("=", 1)[1], s.split("=", 1)[0]) for s in a.window)
    rating = {}
    for page in range(1, 8):
        d = call(["ladder", "--page", str(page), "--limit", "100", "--json"])
        rows = d if isinstance(d, list) else (d.get("entries") or d.get("teams") or list(d.values())[0])
        if not rows:
            break
        for r in rows:
            rating[r["teamId"]] = r["rating"]
    me_r = rating.get(ME)
    ms, cur = [], None
    while True:
        d = call(["matches", "list", "--team", "me", "--kind", "ranked", "--limit", "100", "--json"] + (["--cursor", cur] if cur else []))
        ms += d["matches"]
        cur = d.get("nextCursor")
        if not cur or not d["matches"] or d["matches"][-1]["createdAt"] < a.since:
            break
    agg = {}
    for m in ms:
        if m["status"] != "finished" or m["createdAt"] < a.since:
            continue
        v = None
        for i, (start, name) in enumerate(wins):
            end = wins[i + 1][0] if i + 1 < len(wins) else "9999"
            if start <= m["createdAt"] < end:
                v = name
        if not v:
            continue
        me = [t for t in m["teams"] if t["teamId"] == ME][0]
        op = [t for t in m["teams"] if t["teamId"] != ME][0]
        r = rating.get(op["teamId"])
        k = agg.setdefault(v, dict(n=0, w=0, exp=0.0, opp=0.0, rn=0))
        k["n"] += 1
        k["w"] += me["result"] == "win"
        if r and me_r:
            k["exp"] += 1 / (1 + 10 ** ((r - me_r) / 400))
            k["opp"] += r
            k["rn"] += 1
    print(f"our rating now: {me_r:.1f}" if me_r else "our rating unknown")
    for v, k in agg.items():
        n, w = k["n"], k["w"]
        p = w / n
        z = 1.96
        den = 1 + z * z / n
        c = (p + z * z / (2 * n)) / den
        h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
        ex = k["exp"] / max(1, k["rn"]) if k["rn"] else float("nan")
        perf = ""
        if k["rn"]:
            pe = min(max(p, 0.01), 0.99)
            mo = k["opp"] / k["rn"]
            perf = f" | mean opp {mo:.0f}, performance rating ~{mo + 400 * math.log10(pe / (1 - pe)):.0f}"
        print(f"{v}: {w}/{n} = {p:.3f} [{c - h:.3f}, {c + h:.3f}] | expected at current rating {ex:.3f}{perf}")


if __name__ == "__main__":
    main()
