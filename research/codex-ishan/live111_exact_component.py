"""Build a source-pinned component and verify the frozen first-turn/large-dev fixtures."""
from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, one, read
from freeze_engine3_discovery import write
from profile_live111_first import exact_build
from qualify_local import partition
from turn_prefix import action_prefix


def run(label, prepare):
    assert bench.digest(CLI) == CLI_HASH
    identity = read(HERE / "LIVE111_SOURCE_VERIFIED.json")
    output = bench.CACHE / ("live111-" + label)
    output.mkdir()
    prefix = "LIVE111_" + label.upper().replace("-", "_")
    builds = {}
    for arm, enabled in (("off", False), ("on", True), ("rebuild", True)):
        source = output / ("source-" + arm)
        prepare(source, enabled)
        wasm = exact_build(source, SDK_ROOT / "bots" / f"live111-{label}-{arm}", 1)
        builds[arm] = {"path": str(wasm), "sha256": bench.digest(wasm)}
    assert builds["off"]["sha256"] == identity["wasm_sha256"]
    assert builds["on"]["sha256"] == builds["rebuild"]["sha256"]
    write(HERE / f"{prefix}_BUILDS.json", {"source_archive": identity["archive_sha256"], "builds": builds})
    maps = {p.stem: p for p in partition("dev")}
    baseline = read(HERE / "LIVE111_LARGE_DEV_CENSUS.json")["rows"]
    case = read(HERE / "LIVE111_FIRST_TURN_PLAN.json")["case"]
    selected = [r for r in baseline if all(r[k] == case[k] for k in ("map", "side", "opponent"))]
    assert len(selected) == 1
    for opponent in {r["opponent"] for r in baseline}: (output / opponent).mkdir()
    wasm = SDK_ROOT / "bots" / f"live111-{label}-on/bot.wasm"
    def play(base):
        mp, ref = maps[base["map"]], bench.CACHE / bench.OPPS[base["opponent"]][0]
        assert bench.digest(mp) == base["map_hash"] and bench.digest(ref) == bench.OPPS[base["opponent"]][1]
        row = one((label, mp, base["side"], wasm, ref), output=output / base["opponent"], opponent=base["opponent"])
        assert all(row[k] == base[k] for k in ("map_hash", "side", "opponent", "engine_seed", "noise_seed"))
        return base,row
    first = play(selected[0])
    directory = output / case["opponent"] / f"{case['map']}-{case['side']}-{label}"
    doc = read(directory / "native.json")
    rounds = [x["timestamp"]["round"] for e in doc["events"] if e["kind"] == "fuelExhausted" and e["owner"]["team"] == "teamA" and e["owner"]["id"] == case["actor"] for x in e["entries"]]
    (archive,) = directory.glob("*.repl26a")
    replay = directory / "raw.repl26a"
    with ZipFile(archive) as z:
        with replay.open("xb") as f: f.write(z.read("replay.repl26a"))
    turn = directory / "turn.json"
    subprocess.run(["node", HERE / "trace_turn.mjs", replay, "1", "0", str(case["actor"]), turn], cwd=bench.ROOT, env={**os.environ,"NFS_REPLAY_ENGINE":"3.0.0"},check=True)
    before,after = read(bench.ROOT / case["traces"]["base"]["path"]),read(turn)
    for data in (before,after): data["observation"].pop("input")
    errors = any(doc["diagnostics"]["botFaults"].values()) or bool(doc["diagnostics"]["codes"])
    mechanism = {"case":case,"same_own_view":before["observation"]==after["observation"],"same_action_prefix":action_prefix(before)==action_prefix(after),
                 "actor_round1_removed":1 not in rounds,"actor_fuel_rounds":rounds,"errors":errors,
                 "turn_sha256":bench.digest(turn),"native_sha256":bench.digest(directory / "native.json")}
    mechanism["pass"] = not errors and all(mechanism[k] for k in ("same_own_view","same_action_prefix","actor_round1_removed"))
    write(HERE / f"{prefix}_MECHANISM.json",mechanism)
    print({"builds":builds,"mechanism":mechanism},flush=True)
    if not mechanism["pass"]: return
    pairs=[first]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for pair in pool.map(play,[r for r in baseline if r is not selected[0]]):
            pairs.append(pair)
            if len(pairs)%15==0: print(f"{len(pairs)}/60",flush=True)
    overall=bench.summary(pairs)
    errors=sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for pair in pairs for r in pair)
    result={"engine":ENGINE,"builds":builds,"overall":overall,"error_cells":errors,
            "pass":not errors and not overall["per_cell_fuel_regressions"],"pairs":pairs}
    write(HERE / f"{prefix}_LARGE.json",result)
    print({k:v for k,v in result.items() if k not in ("pairs","builds")},flush=True)
