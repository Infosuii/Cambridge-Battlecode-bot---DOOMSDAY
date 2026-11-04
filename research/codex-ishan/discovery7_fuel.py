"""Compare native opening fuel suspension in the frozen seventh replay cohort."""
import argparse
from collections import Counter
import json
import os
import subprocess

from profile_discovery5 import CACHE, HERE, ROOT, read


def fuel(doc, team):
    return sorted(((entry["timestamp"]["round"], event["owner"]["id"], event["owner"]["name"])
                   for event in doc["events"] if event["kind"] == "fuelExhausted" and event["owner"]["team"] == team
                   for entry in event["entries"] if 1 <= entry["timestamp"]["round"] <= 150))


def buckets(events):
    return {"r1": sum(r == 1 for r, _, _ in events), "r2_50": sum(2 <= r <= 50 for r, _, _ in events),
            "r51_150": sum(51 <= r <= 150 for r, _, _ in events)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split", choices=("discovery", "confirm"))
    split = parser.parse_args().split
    matches = read(HERE / f"DISCOVERY7_{split.upper()}.json")["rows"]
    local = CACHE / f"discovery7/{split}"
    report, traced = [], set()
    trace_path = HERE / f"discovery7-{split}-turns"
    trace_path.mkdir(exist_ok=True)
    counts = Counter()
    for m in matches:
        doc = read(local / "summaries" / f"{m['matchId']}.json")
        team = m["side"].upper()
        ours = fuel(doc, "team" + team)
        theirs = fuel(doc, "team" + ("B" if team == "A" else "A"))
        our_buckets, their_buckets = buckets(ours), buckets(theirs)
        for phase in our_buckets:
            counts[f"ours_more_{phase}"] += our_buckets[phase] > their_buckets[phase]
        counts["ours_more_through_150"] += len(ours) > len(theirs)
        counts["winner_collected_more_at_150"] += m["winner"]["collected"]["150"] > m["ours"]["collected"]["150"]
        case = {"matchId": m["matchId"], "map": m["map"], "opponent": m["opponent"], "our_side": team,
                "ours": ours, "winner": theirs, "our_buckets": our_buckets, "winner_buckets": their_buckets,
                "collection_gap_150": m["winner"]["collected"]["150"] - m["ours"]["collected"]["150"],
                "first_sustained_bank_gap": m["first_sustained_bank_gap"]}
        if ours and m["map"] not in traced and len(traced) < 3:
            traced.add(m["map"])
            round_number, actor, _ = ours[0]
            output = trace_path / f"{m['matchId']}-R{round_number}.json"
            run = subprocess.run(["node", HERE / "trace_turn.mjs", local / "extracted" / f"{m['matchId']}.repl26a",
                                  str(round_number), str("AB".index(team)), str(actor), output],
                                 cwd=ROOT, env={**os.environ, "NFS_REPLAY_ENGINE": "2.0.0"},
                                 capture_output=True, text=True)
            case["own_view"] = output.relative_to(HERE).as_posix() if not run.returncode else None
            if run.returncode:
                case["trace_error"] = run.stderr.strip() or f"Replay reader exited {run.returncode}"
        report.append(case)
    result = {"n": len(matches), "counts": counts, "rows": report}
    with (HERE / f"DISCOVERY7_FUEL_{split.upper()}.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({"n": len(matches), "counts": counts, "traced": len(traced)})


if __name__ == "__main__":
    main()
