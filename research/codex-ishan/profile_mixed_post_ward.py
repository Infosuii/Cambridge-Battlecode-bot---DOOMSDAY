"""Trace the standard-budget Heart crossings on the frozen mixed-roster fixture."""
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


def main():
    frozen = read(HERE / "CPG_POST_WARD_MIXED_STRESS.json")
    assert frozen["seed"] == COMPILED_SEED and frozen["n"] == 800
    (case,) = frozen["affected"]
    rounds = [e["timestamp"]["round"] for e in case["events"]]
    assert rounds == [637, 639, 641] and {e["owner"]["name"] for e in case["events"]} == {"Heart of Ruin"}
    mp = RAW / "maps" / f"{case['map']}.map26a"
    assert bench.digest(mp) == case["map_hash"]
    file, expected = bench.OPPS[case["opponent"]]
    assert bench.digest(bench.CACHE / file) == expected
    bench.OUT = trace.OUT = OUT
    trace.REFERENCE_OUT = RAW
    (OUT / "games").mkdir(parents=True)
    src = OUT / "source/src"
    prepare(src, True, post_ward=True)
    prepare_coarse(src, rounds, STAGES)
    condition = " || ".join(f"round == {rnd}" for rnd in rounds)
    apply(src / "bot.cpp", ((f"    codex_stress_trace = {condition};",
                            f"    codex_stress_trace = ({condition}) && type == bc::champion_type::heart_of_ruin;"),))
    wasm = build(src, OUT / "diagnostic", COMPILED_SEED)
    result = trace.play((case, mp, wasm))
    matches = {r["round"]: r["phases"] for r in result["checks"] if r["matched"]}
    report = {"engine": bench.ENGINE, "reference": frozen["wasm"], "diagnostic": bench.digest(wasm),
              "seed": COMPILED_SEED, "matches": matches}
    with (HERE / "CPG_POST_WARD_MIXED_HEART_TRACE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "row": result}, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
