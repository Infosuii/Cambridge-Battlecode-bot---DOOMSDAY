"""Validate same actor/round views and action prefixes for existing stage traces."""
from collections import defaultdict
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import HERE, read
from freeze_engine3_discovery import write

NAMES = ("Ryth", "Vesper Vale", "Vendetta", "Cassi", "Issac", "Stellar", "Prism", "Marcella", "Willow", "Ren", "Varg", "Tavi", "Heart of Ruin")


def main():
    data = read(HERE / "LIVE109_RUNTIME_PROFILE.json")
    candidates = defaultdict(list)
    for row in data["rows"]:
        base = {(e["round"], e["name"]): e["actor"] for e in row["baseline_events"]}
        diag = {(e["round"], e["name"]): e["actor"] for e in row["diagnostic_events"]}
        for round_number, first, last, champion_type in row["stages"]:
            key = round_number, NAMES[champion_type]
            if key in base and key in diag and base[key] == diag[key]:
                candidates[f"{first}->{last}"].append({"row": row, "round": round_number, "actor": base[key], "type": champion_type})
    selected = {stage: min(rows, key=lambda r: (r["round"], r["row"]["map_hash"], r["row"]["opponent"], r["row"]["side"])) for stage, rows in candidates.items()}
    output = bench.CACHE / "engine3-live109-runtime-profile/matched-turns"
    output.mkdir()
    rows = []
    for stage, case in sorted(selected.items()):
        observations, actions = [], []
        record = {"stage": stage, "round": case["round"], "actor": case["actor"], "type": case["type"], "champion": NAMES[case["type"]],
                  **{key: case["row"][key] for key in ("map", "side", "opponent", "map_hash")}, "traces": {}}
        for arm, path_key in (("base", "baseline_directory"), ("profile", "profile_directory")):
            directory = bench.ROOT / case["row"][path_key]
            (archive,) = directory.glob("*.repl26a")
            replay = output / (stage.replace("->", "-") + "-" + arm + ".repl26a")
            with ZipFile(archive) as bundle:
                with replay.open("xb") as out:
                    out.write(bundle.read("replay.repl26a"))
            target = replay.with_suffix(".json")
            subprocess.run(["node", HERE / "trace_turn.mjs", replay, str(case["round"]), str(int(case["row"]["side"] == "B")), str(case["actor"]), target], cwd=bench.ROOT, env={**os.environ, "NFS_REPLAY_ENGINE": "3.0.0"}, check=True)
            turn = read(target)
            view = turn["observation"]
            view.pop("input")
            observations.append(view)
            prefix = []
            hit = False
            for action in turn["executed_actions"]:
                if action["kind"] == 26:
                    hit = True
                    break
                prefix.append(action)
            actions.append(prefix)
            record["traces"][arm] = {"path": target.relative_to(bench.ROOT).as_posix(), "sha256": bench.digest(target), "recorded_fuel_step": hit}
        record["same_own_view"] = observations[0] == observations[1]
        record["same_action_prefix"] = actions[0] == actions[1]
        record["matched_view_and_prefix"] = record["same_own_view"] and record["same_action_prefix"] and all(v["recorded_fuel_step"] for v in record["traces"].values())
        rows.append(record)
    report = {"limits": "Charged profiler may change other trajectories or private state; matches establish observed input/action equality and the same native actor/round crossing, not whole-history identity.", "n_stages": len(rows), "matched_stages": sum(r["matched_view_and_prefix"] for r in rows), "rows": rows}
    write(HERE / "LIVE109_RUNTIME_MATCHED_TURNS.json", report)
    print(report, flush=True)


if __name__ == "__main__":
    main()
