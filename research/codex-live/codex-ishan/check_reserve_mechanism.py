"""Recheck the original warm-up actor turn with the allocation-only candidate."""
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import HERE, SDK_ROOT, one, read
from freeze_engine3_discovery import write
from qualify_local import partition


def main():
    case = next(r for r in read(HERE / "LIVE109_RUNTIME_MATCHED_TURNS.json")["rows"] if r["stage"] == "61->62")
    wasm = SDK_ROOT / "bots/live109-reserve-mech-11801/bot.wasm"
    mp = next(p for p in partition("dev") if p.stem == case["map"])
    opponent = bench.CACHE / bench.OPPS[case["opponent"]][0]
    assert bench.digest(mp) == case["map_hash"] and bench.digest(opponent) == bench.OPPS[case["opponent"]][1]
    output = bench.CACHE / "engine3-live109-reserve-mechanism"
    output.mkdir()
    row = one(("candidate", mp, case["side"], wasm, opponent), output=output, seed=11801, opponent=case["opponent"])
    directory = output / f"{mp.stem}-{case['side']}-candidate"
    native = read(directory / "native.json")
    (archive,) = directory.glob("*.repl26a")
    replay = directory / "raw.repl26a"
    with ZipFile(archive) as bundle:
        with replay.open("xb") as out:
            out.write(bundle.read("replay.repl26a"))
    target = directory / "turn.json"
    subprocess.run(["node", HERE / "trace_turn.mjs", replay, str(case["round"]), str(int(case["side"] == "B")), str(case["actor"]), target], cwd=bench.ROOT, env={**os.environ, "NFS_REPLAY_ENGINE": "3.0.0"}, check=True)
    before, after = read(bench.ROOT / case["traces"]["base"]["path"]), read(target)
    for data in (before, after): data["observation"].pop("input")
    prefix = []
    for action in before["executed_actions"]:
        if action["kind"] == 26: break
        prefix.append(action)
    events = [entry["timestamp"]["round"] for event in native["events"] if event["kind"] == "fuelExhausted" and event["owner"]["id"] == case["actor"] and event["owner"]["team"] == "team" + case["side"] for entry in event["entries"]]
    result = {"noise_seed": 11801, "candidate_binary": bench.digest(wasm), "case": case,
              "same_own_view": before["observation"] == after["observation"],
              "same_original_action_prefix": prefix == after["executed_actions"][:len(prefix)],
              "original_round_suspension_removed": case["round"] not in events, "candidate_actor_events": events,
              "native": row, "trace_sha256": bench.digest(target)}
    write(HERE / "LIVE109_RESERVE_MECHANISM.json", result)
    print({k: v for k, v in result.items() if k not in ("case", "native")}, flush=True)


if __name__ == "__main__":
    main()
