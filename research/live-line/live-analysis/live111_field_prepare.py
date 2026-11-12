"""Test the single observed unguarded current111 preparation call."""
from concurrent.futures import ThreadPoolExecutor
import os
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, one, read
from freeze_engine3_discovery import write
from profile_live111_first import exact_build
from qualify_local import partition


def prepare(source, target, enabled):
    copytree(source, target)
    header = target / "common.h"
    header.write_bytes(f"#define CODEX_FIELD_PREPARE {int(enabled)}\n".encode() + header.read_bytes())
    apply(target / "bot.cpp", (("        if (!w.fields_ready() && quota > 0) w.prepare_field_order();", '''        if (!w.fields_ready() && quota > 0
#if CODEX_FIELD_PREPARE
            && room()
#endif
        ) w.prepare_field_order();'''),))


def main():
    identity = read(HERE / "LIVE111_SOURCE_VERIFIED.json")
    source = SDK_ROOT / "bots/live111/src"
    assert bench.digest(CLI) == CLI_HASH
    assert all(bench.digest(source / n) == h for n, h in identity["source_file_hashes"].items())
    output = bench.CACHE / "live111-field-prepare"
    output.mkdir()
    builds = {}
    for label, enabled in (("off", False), ("on", True), ("rebuild", True)):
        src = output / ("source-" + label)
        prepare(source, src, enabled)
        wasm = exact_build(src, SDK_ROOT / "bots" / ("live111-field-prepare-" + label), 1)
        builds[label] = {"path": str(wasm), "sha256": bench.digest(wasm)}
    assert builds["off"]["sha256"] == identity["wasm_sha256"]
    assert builds["on"]["sha256"] == builds["rebuild"]["sha256"]
    write(HERE / "LIVE111_FIELD_PREPARE_BUILDS.json", {"source_archive": identity["archive_sha256"], "builds": builds})
    wasm = SDK_ROOT / "bots/live111-field-prepare-on/bot.wasm"
    maps = {p.stem: p for p in partition("dev")}
    case = read(HERE / "LIVE111_FIRST_TURN_PLAN.json")["case"]
    frozen = read(HERE / "LIVE111_LARGE_DEV_CENSUS.json")["rows"]
    ordered = sorted(frozen, key=lambda r: (not all(r[k] == case[k] for k in ("map", "side", "opponent")), r["map_hash"], r["side"], r["opponent"]))
    for opponent in {r["opponent"] for r in frozen}: (output / opponent).mkdir()
    def run(base):
        mp = maps[base["map"]]
        reference = bench.CACHE / bench.OPPS[base["opponent"]][0]
        assert bench.digest(mp) == base["map_hash"]
        assert bench.digest(reference) == bench.OPPS[base["opponent"]][1]
        cand = one(("prepare", mp, base["side"], wasm, reference), output=output / base["opponent"], opponent=base["opponent"])
        assert all(cand[k] == base[k] for k in ("map_hash", "side", "opponent", "engine_seed", "noise_seed"))
        return base, cand
    first_base, first = run(ordered[0])
    directory = output / first["opponent"] / f"{first['map']}-{first['side']}-prepare"
    native = read(directory / "native.json")
    actor_events = [x["timestamp"]["round"] for e in native["events"] if e["kind"] == "fuelExhausted" and e["owner"]["team"] == "teamA" and e["owner"]["id"] == case["actor"] for x in e["entries"]]
    (archive,) = directory.glob("*.repl26a")
    replay = directory / "raw.repl26a"
    with ZipFile(archive) as z:
        with replay.open("xb") as handle: handle.write(z.read("replay.repl26a"))
    turn_path = directory / "turn.json"
    subprocess.run(["node", HERE / "trace_turn.mjs", replay, "1", "0", str(case["actor"]), turn_path], cwd=bench.ROOT, env={**os.environ, "NFS_REPLAY_ENGINE": "3.0.0"}, check=True)
    before, after = read(bench.ROOT / case["traces"]["base"]["path"]), read(turn_path)
    for doc in (before, after): doc["observation"].pop("input")
    def prefix(doc):
        actions = []
        for action in doc["executed_actions"]:
            if action["kind"] == 26: break
            actions.append(action)
        return actions
    mechanism = {"case": case, "same_own_view": before["observation"] == after["observation"], "same_action_prefix": prefix(before) == prefix(after),
                 "actor_round1_removed": 1 not in actor_events, "actor_fuel_rounds": actor_events,
                 "turn_sha256": bench.digest(turn_path), "native_sha256": bench.digest(directory / "native.json")}
    mechanism["pass"] = all(mechanism[k] for k in ("same_own_view", "same_action_prefix", "actor_round1_removed")) and not(first["faults"] or first["opponent_faults"] or first["diagnostic_codes"])
    write(HERE / "LIVE111_FIELD_PREPARE_MECHANISM.json", mechanism)
    print({"builds": builds, "mechanism": mechanism}, flush=True)
    if not mechanism["pass"]: return
    pairs = [(first_base, first)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for pair in pool.map(run, ordered[1:]):
            pairs.append(pair)
            if len(pairs) % 15 == 0: print(f"{len(pairs)}/60", flush=True)
    summary = bench.summary(pairs)
    errors = sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for pair in pairs for r in pair)
    result = {"engine": ENGINE, "builds": builds, "overall": summary, "error_cells": errors,
              "pass": not errors and not summary["per_cell_fuel_regressions"] and summary["round1"][1] <= summary["round1"][0], "pairs": pairs}
    write(HERE / "LIVE111_FIELD_PREPARE_LARGE.json", result)
    print({k: v for k, v in result.items() if k != "pairs"}, flush=True)


if __name__ == "__main__": main()
