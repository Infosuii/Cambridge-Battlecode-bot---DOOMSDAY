"""Verify the combined cap on the exact three-event mixed-roster replay."""
import json

from cpg_safe_tribute_cap import prepare
from large_roster_stress import HERE, bench, read
import profile_cast_path_stress as trace
from qualify_local import build
from stress_mixed_post_ward import COMPILED_SEED, OUT as RAW
from verify_heart_camp_mask_fixture import actions

OUT = bench.CACHE / "safe-tribute-combined-mixed-fixture"


def main():
    frozen = read(HERE / "CPG_POST_WARD_MIXED_STRESS.json")
    (case,) = frozen["affected"]
    mp = RAW / "maps" / f"{case['map']}.map26a"
    assert frozen["seed"] == COMPILED_SEED and bench.digest(mp) == case["map_hash"]
    file, expected = bench.OPPS[case["opponent"]]
    assert bench.digest(bench.CACHE / file) == expected
    bench.OUT = trace.OUT = OUT
    trace.REFERENCE_OUT = RAW
    (OUT / "games").mkdir(parents=True)
    src = OUT / "source/src"
    prepare(src, True, specialized=True, post_ward=True)
    wasm = build(src, OUT / "candidate", COMPILED_SEED)
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
    with (HERE / "CPG_SAFE_TRIBUTE_COMBINED_MIXED.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "row": row}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
