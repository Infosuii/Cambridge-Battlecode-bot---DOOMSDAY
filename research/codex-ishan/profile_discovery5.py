"""Measure early income, conversion and deaths in each reserved Discovery 5 split."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
from statistics import mean, median
import subprocess
import sys
from zipfile import ZipFile

from freeze_discovery5 import CACHE, HERE, read

sys.path.insert(0, str(HERE / "discovery4"))
from capture_metrics import team_metrics
from metrics import timeline

ROOT = HERE.parents[1]
ROUNDS = (50, 100, 150, 200, 250, 300)


def replays(rows, local):
    extracts = local / "extracted"
    extracts.mkdir()
    paths = []
    for m in rows:
        mid = m["matchId"]
        replay = extracts / f"{mid}.repl26a"
        with ZipFile(local / "replays" / f"{mid}.zip") as bundle:
            replay.write_bytes(bundle.read("replay.repl26a"))
        paths.append(replay)
    env = {**os.environ, "NFS_REPLAY_ENGINE": "2.0.0", "NFS_FUNNEL_UNTIL": "300"}
    results = {}
    for tool, args in (("winner_profile", []), ("capture_pressure", []), ("death_context", ["600"])):
        out = local / f"{tool}.json"
        subprocess.run(["node", ROOT / "tools/replay" / f"{tool}.mjs", *args, out, *paths], cwd=ROOT,
                       env=env, check=True)
        results[tool] = {Path(r["id"]).stem: r for r in read(out)}
        assert len(results[tool]) == len(rows)
    return results


def side(summary, profile, camp, deaths, index):
    name = "team" + "AB"[index]
    event_rows = [r for r in summary["events"] if r["owner"]["team"] == name]
    loss = [entry for r in event_rows if r["kind"] == "gemLoss" for entry in r["entries"]]
    first = min((entry["timestamp"]["round"] for r in event_rows if r["kind"] == "gemSubmission"
                 for entry in r["entries"]), default=None)
    result = {key: {str(r): timeline(summary, name, field, r) for r in ROUNDS}
              for key, field in (("gold", "earnedGold"), ("collected", "collectedGems"), ("banked", "submittedGems"))}
    result["lost"] = {str(r): sum(int(e["value"]) for e in loss if e["timestamp"]["round"] <= r) for r in (150, 300, 600)}
    result["first_bank"] = first
    result["wards"] = sum(len(e["entries"]) for e in event_rows if e["kind"] == "wardPlacement")
    result["no_action_deaths"] = sum(d["pvp_attacks"] == d["casts"] == 0 for d in deaths if d["team"] == index)
    result["camp"] = team_metrics(camp, index)
    result["first_contact"] = profile["teams"][index]["first_contact"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split", choices=("discovery", "confirm"))
    parser.add_argument("--wave", type=int, choices=(5, 6), default=5)
    args = parser.parse_args()
    matches = [r for r in read(HERE / f"DISCOVERY{args.wave}_SAMPLE.json")["matches"] if r["partition"] == args.split]
    local = CACHE / f"discovery{args.wave}" / args.split
    profiles = replays(matches, local)
    rows = []
    for m in matches:
        mid = m["matchId"]
        summary = read(local / "summaries" / f"{mid}.json")
        us = "AB".index(m["side"].upper())
        assert summary["match"]["engineVersion"] == "2.0.0" and summary["match"]["outcome"] == "team" + "AB"[1 - us]
        p = profiles["winner_profile"][mid]
        c = profiles["capture_pressure"][mid]
        d = profiles["death_context"][mid]["deaths"]
        ours, theirs = (side(summary, p, c, d, s) for s in (us, 1 - us))
        lead = [theirs["banked"][str(r)] - ours["banked"][str(r)] >= 40 for r in ROUNDS]
        first_gap = next((r for i, r in enumerate(ROUNDS[:-1]) if lead[i] and lead[i + 1]), None)
        rows.append({**m, "ours": ours, "winner": theirs, "first_sustained_bank_gap": first_gap})
    gaps = {k: [r["winner"][k]["300"] - r["ours"][k]["300"] for r in rows]
            for k in ("gold", "collected", "banked", "lost")}
    totals = {k: {"winner_ahead": sum(v > 0 for v in vs), "ours_ahead": sum(v < 0 for v in vs),
                  "median_winner_minus_ours": median(vs)} for k, vs in gaps.items()}
    events = {"bank_gap_despite_equal_or_more_ours_collected": sum(c <= 0 and b > 0 for c, b in zip(gaps["collected"], gaps["banked"], strict=True)),
              "winner_banked_more_and_ours_lost_more": sum(b > 0 and loss < 0 for b, loss in zip(gaps["banked"], gaps["lost"], strict=True)),
              "more_winner_wards": sum(r["winner"]["wards"] > r["ours"]["wards"] for r in rows),
              "more_ours_no_action_deaths": sum(r["ours"]["no_action_deaths"] > r["winner"]["no_action_deaths"] for r in rows)}
    bank_starts = Counter(r["first_sustained_bank_gap"] or "none" for r in rows)
    report = {"n": len(rows), "round300": totals, "events": events, "first_sustained_bank_gap": dict(bank_starts),
              "lost_600_mean_ours_winner": [mean(r[k]["lost"]["600"] for r in rows) for k in ("ours", "winner")]}
    with (HERE / f"DISCOVERY{args.wave}_{args.split.upper()}.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "rows": rows}, out, indent=2, ensure_ascii=False)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
