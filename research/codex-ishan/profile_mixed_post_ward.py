"""Trace the standard-budget Heart crossings on the frozen mixed-roster fixture."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json

from bounded_verdict import apply
from cpg_safe_tribute_cap import prepare
from large_roster_stress import HERE, bench, read
import profile_cast_path_stress as trace
from profile_roster_stress import prepare_coarse
from qualify_local import build
from stress_mixed_post_ward import COMPILED_SEED, OUT as RAW

OUT = bench.CACHE / "post-ward-mixed-heart-trace"
STAGES = ("world", "support", "wardrev", "ambush", "e_in", "e_td", "e_prefight", "enemies",
          "route0", "farmsel", "c_zones", "c_cast", "d_farm", "decide", "tail", "fields", "bushpre")


def build_trace(directory, rounds, phase=None):
    (directory / "games").mkdir(parents=True)
    src = directory / "source/src"
    prepare(src, True, post_ward=True)
    condition = " || ".join(f"round == {rnd}" for rnd in rounds)
    if phase:
        marker = f'PROF_CHECK("{phase}");'
        apply(src / "bot.cpp", ((marker, marker + f'''
    if (({condition}) && type == bc::champion_type::heart_of_ruin && static_cast<int>(bc::round_number()) != round)
        std::printf("CODEX_STRESS R%d t%d {phase}\\n", round, static_cast<int>(type));'''),))
    else:
        prepare_coarse(src, rounds, STAGES)
        apply(src / "bot.cpp", ((f"    codex_stress_trace = {condition};",
                                f"    codex_stress_trace = ({condition}) && type == bc::champion_type::heart_of_ruin;"),))
    return build(src, directory / "diagnostic", COMPILED_SEED)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--single-boundaries", action="store_true")
    single = parser.parse_args().single_boundaries
    frozen = read(HERE / "CPG_POST_WARD_MIXED_STRESS.json")
    assert frozen["seed"] == COMPILED_SEED and frozen["n"] == 800
    (case,) = frozen["affected"]
    rounds = [e["timestamp"]["round"] for e in case["events"]]
    assert rounds == [637, 639, 641] and {e["owner"]["name"] for e in case["events"]} == {"Heart of Ruin"}
    mp = RAW / "maps" / f"{case['map']}.map26a"
    assert bench.digest(mp) == case["map_hash"]
    file, expected = bench.OPPS[case["opponent"]]
    assert bench.digest(bench.CACHE / file) == expected
    trace.REFERENCE_OUT = RAW
    if single:
        phases = ("wardrev", "enemies", "d_farm")
        paths = {p: bench.CACHE / "post-ward-mixed-heart-boundaries" / p for p in phases}
        with ThreadPoolExecutor(max_workers=3) as pool:
            binaries = list(pool.map(lambda p: build_trace(paths[p], rounds, p), phases))
    else:
        phases = ("coarse",)
        paths = {"coarse": OUT}
        binaries = [build_trace(OUT, rounds)]
    rows = {}
    for phase, wasm in zip(phases, binaries, strict=True):
        bench.OUT = trace.OUT = paths[phase]
        row = trace.play((case, mp, wasm))
        rows[phase] = {"diagnostic": bench.digest(wasm),
                       "matches": {r["round"]: r["phases"] for r in row["checks"] if r["matched"]}, "row": row}
    report = {"engine": bench.ENGINE, "reference": frozen["wasm"], "seed": COMPILED_SEED}
    name = "CPG_POST_WARD_MIXED_HEART_BOUNDARIES.json" if single else "CPG_POST_WARD_MIXED_HEART_TRACE.json"
    result = {**report, "boundaries": rows} if single else {**report, **rows["coarse"]}
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({**report, "matches": {p: rows[p]["matches"] for p in phases}}, flush=True)


if __name__ == "__main__":
    main()
