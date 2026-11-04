"""Locate each exact stress suspension in its own-view replay input."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile

from large_roster_stress import HERE, OUT, bench, read
from large_roster_noised import OUT as NOISED_OUT


def trace(row, run_dir):
    game = run_dir / "games" / f"{row['arm']}-{row['noise_seed']}-{row['opponent']}-{row['map']}-{row['side']}"
    replay = game / "raw.repl26a"
    with ZipFile(next(game.glob("*.repl26a"))) as bundle:
        replay.write_bytes(bundle.read("replay.repl26a"))
    results = []
    for event in row["events"]:
        owner, stamp = event["owner"], event["timestamp"]
        output = game / f"turn-{stamp['input']}-{owner['id']}.json"
        with (game / f"turn-{stamp['input']}-{owner['id']}.log").open("wb") as log:
            subprocess.run(["node", HERE / "trace_turn.mjs", replay, str(stamp["round"]),
                            str("AB".index(row["side"])), str(owner["id"]), output], cwd=bench.ROOT, stdout=log,
                           stderr=subprocess.STDOUT, env={**os.environ, "NFS_REPLAY_ENGINE": "2.0.0"}, check=True)
        state = read(output)
        actions = state["executed_actions"]
        before = [a for a in actions[:next((i for i, a in enumerate(actions) if a["kind"] == 26), len(actions))]
                  if a["kind"] != 3]
        results.append({"map": row["map"], "opponent": row["opponent"], "side": row["side"], "seed": row["noise_seed"], "event": event,
                        "actions_before_suspension": before, "state": state})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--noised", action="store_true")
    args = parser.parse_args()
    run_dir = NOISED_OUT if args.noised else OUT
    stress = read(HERE / ("LARGE_ROSTER_NOISE.json" if args.noised else "LARGE_ROSTER_STRESS.json"))
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = [r for group in pool.map(lambda row: trace(row, run_dir), stress["affected"]) for r in group]
    counts = Counter(tuple(a["kind"] for a in r["actions_before_suspension"]) for r in rows)
    assert len(rows) == stress["fuel"]
    report = {"n": len(rows), "action_counts": [{"kinds": k, "count": n} for k, n in counts.most_common()], "rows": rows}
    name = "LARGE_ROSTER_NOISE_TURNS.json" if args.noised else "LARGE_ROSTER_TURNS.json"
    with (HERE / name).open("x", encoding="utf8", newline="\n") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    for row in rows:
        event = row["event"]
        state = row["state"]["observation"]
        print(row["map"], row["opponent"], row["side"], row["seed"], event["owner"]["name"], event["timestamp"]["round"],
              "seen", len(state["visible_enemies"]), len(state["visible_camps"]),
              "actions", [a["kind"] for a in row["actions_before_suspension"]], flush=True)


if __name__ == "__main__":
    main()
