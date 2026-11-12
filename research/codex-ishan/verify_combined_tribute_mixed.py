"""Verify the combined cap on the exact three-event mixed-roster replay."""
import argparse
import json

from cpg_safe_tribute_cap import prepare
from large_roster_stress import HERE, bench, read
import profile_cast_path_stress as trace
from qualify_local import build
from stress_mixed_post_ward import COMPILED_SEED, OUT as RAW
from verify_heart_camp_mask_fixture import actions

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--ward-decide", action="store_true")
    mode.add_argument("--ward-retry", action="store_true")
    args = parser.parse_args()
    variant = "ward-retry" if args.ward_retry else "ward-decide" if args.ward_decide else "combined"
    out_dir = bench.CACHE / f"safe-tribute-{variant}-mixed-fixture"
    frozen = read(HERE / "CPG_POST_WARD_MIXED_STRESS.json")
    (case,) = frozen["affected"]
    mp = RAW / "maps" / f"{case['map']}.map26a"
    assert frozen["seed"] == COMPILED_SEED and bench.digest(mp) == case["map_hash"]
    file, expected = bench.OPPS[case["opponent"]]
    assert bench.digest(bench.CACHE / file) == expected
    bench.OUT = trace.OUT = out_dir
    trace.REFERENCE_OUT = RAW
    (out_dir / "games").mkdir(parents=True)
    src = out_dir / "source/src"
    combined = variant == "combined"
    prepare(src, True, specialized=combined, post_ward=combined, ward_decide=args.ward_decide, ward_retry=args.ward_retry)
    wasm = build(src, out_dir / "candidate", COMPILED_SEED)
    row = trace.play((case, mp, wasm))
    turns = []
    for original in row["checks"]:
        before, after = (actions(original[k]) for k in ("base_turn", "diagnostic_turn"))
        turns.append({"round": original["round"], "same_input": original["same_input"],
                      "same_action_prefix": before == after[:len(before)], "removed": not original["same_event"],
                      "base_actions": before, "candidate_actions": after})
    assert [r["round"] for r in turns] == [637, 639, 641]
    first = turns[0]
    assert [a["kind"] for a in first["base_actions"]] == [6, 14]
    passed = (row["same_draft"] and not row["errors"] and not row["observed"] and first["same_input"]
              and first["same_action_prefix"] and all(t["removed"] for t in turns))
    result = {"engine": bench.ENGINE, "reference": frozen["wasm"], "candidate": bench.digest(wasm),
              "seed": COMPILED_SEED, "same_draft": row["same_draft"], "errors": row["errors"],
              "events": row["observed"], "turns": turns, "pass": passed}
    name = f"CPG_SAFE_TRIBUTE_{variant.upper().replace('-', '_')}_MIXED.json"
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "row": row}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
