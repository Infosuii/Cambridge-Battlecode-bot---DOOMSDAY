"""Single heavy-subsystem ablation on exact111 with frozen paired development games."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from shutil import copytree

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, read
from engine3_qualify import build, play
from freeze_engine3_discovery import write
from profile_live111_first import exact_build
from qualify_local import DEV, partition


def prepare(target, enabled):
    identity = read(HERE / "LIVE111_SOURCE_VERIFIED.json")
    source = SDK_ROOT / "bots/live111/src"
    assert all(bench.digest(source / n) == h for n, h in identity["source_file_hashes"].items())
    copytree(source, target)
    header = target / "common.h"
    header.write_bytes(f"#define CODEX_NN_RUNTIME_OFF {int(enabled)}\n".encode() + header.read_bytes())
    for name in ("nn_decide", "nn_lazy_score", "nn_turn_end"):
        anchor = f"void Bot::{name}() {{"
        apply(target / "nnrec.cpp", ((anchor, anchor + '''
#if CODEX_NN_RUNTIME_OFF
    nn_group = -1;
    nn_beh = -1;
    nn_spent = 0;
    return;
#endif'''),))


if __name__ == "__main__":
    assert bench.digest(CLI) == CLI_HASH
    identity = read(HERE / "LIVE111_SOURCE_VERIFIED.json")
    output = bench.CACHE / "live111-runtime-ablation"
    output.mkdir()
    sources, releases = {}, {}
    for arm, enabled in (("base", False), ("ablation", True)):
        hashes = []
        for suffix in ("", "-rebuild") if enabled else ("",):
            source = output / (arm + suffix + "-source")
            prepare(source, enabled)
            wasm = exact_build(source, SDK_ROOT / "bots" / ("live111-runtime-" + arm + suffix), 1)
            hashes.append(bench.digest(wasm))
            if not suffix: sources[arm] = source
        assert len(set(hashes)) == 1
        releases[arm] = hashes[0]
    assert releases["base"] == identity["wasm_sha256"]
    write(HERE / "LIVE111_RUNTIME_ABLATION_BUILDS.json", {"source_archive": identity["archive_sha256"], "releases": releases})
    categories = read(HERE / "ENGINE3_CATEGORIES_DEV.json")
    manifest = read(HERE / "LIVE109_STELLAR_DEV_MAPS.json")
    indexed = {p.name: p for p in partition("dev")}
    maps = [indexed[name] for name in manifest]
    assert all(bench.digest(p) == manifest[p.name]["sha256"] == categories["maps"][p.stem]["map_hash"] for p in maps)
    opponents = {n: bench.CACHE / bench.OPPS[n][0] for n in DEV}
    assert all(bench.digest(p) == bench.OPPS[n][1] for n, p in opponents.items())
    opponents["live111"] = SDK_ROOT / "bots/live111/bot.wasm"
    assert bench.digest(opponents["live111"]) == identity["wasm_sha256"]
    seeds = (31469, 34031)
    binaries = {(arm, seed): build(src, SDK_ROOT / "bots" / f"live111-runtime-{arm}-{seed}", seed) for arm, src in sources.items() for seed in seeds}
    write(HERE / "LIVE111_RUNTIME_ABLATION_PLAN.json", {"engine": ENGINE, "releases": releases, "maps": {p.name: bench.digest(p) for p in maps},
          "opponents": {n: bench.digest(p) for n,p in opponents.items()}, "seeds": seeds,
          "binaries": {f"{arm}-{seed}": bench.digest(p) for (arm,seed),p in binaries.items()}})
    for seed in seeds:
        for opponent in opponents: (output / f"{seed}-{opponent}").mkdir()
    jobs = [(arm, seed, opponent, mp, side, binaries[arm, seed], wasm, output / f"{seed}-{opponent}", categories["maps"][mp.stem]["category"])
            for mp in maps for opponent, wasm in opponents.items() for side in "AB" for seed in seeds for arm in sources]
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 120 == 0: print(f"{len(rows)}/{len(jobs)}", flush=True)
    key = lambda r: tuple(r[k] for k in ("map_hash", "side", "opponent", "noise_seed", "engine_seed"))
    base = {key(r): r for r in rows if r["arm"] == "base"}
    pairs = [(base[key(r)],r) for r in rows if r["arm"] == "ablation"]
    strata = {}
    for field in ("opponent", "size", "category"):
        grouped = defaultdict(list)
        for a,b in pairs: grouped[a[field]].append((a,b))
        strata[field] = {n:bench.summary(p) for n,p in sorted(grouped.items())}
    overall = bench.summary(pairs)
    errors = sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for r in rows)
    result = {"engine":ENGINE,"releases":releases,"n_games":len(rows),"overall":overall,"strata":strata,"error_cells":errors,
              "safety_pass":not errors and not overall["per_cell_fuel_regressions"],
              "win_filter_pass":not errors and overall["map_cluster_ci_pp"][1]>=0 and all(v["delta_pp"]>=-10 for group in strata.values() for v in group.values())}
    write(output / "rows.json",rows)
    write(HERE / "LIVE111_RUNTIME_ABLATION_DEV.json",result)
    print(json.dumps({k:v for k,v in result.items() if k!='strata'},indent=2),flush=True)
