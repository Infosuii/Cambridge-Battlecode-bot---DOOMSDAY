"""Localize the recurring independent Vendetta suspension with separate charged builds."""
from concurrent.futures import ThreadPoolExecutor
import json

from bounded_verdict import apply
from cpg_safe_tribute_cap import prepare
from large_roster_stress import HERE, OUT as STRESS, bench, read
from pg_dash_followup import read_turn
import profile_cast_path_stress as trace
from qualify_local import build
from stress_heart_cast_path import SEED
from verify_heart_camp_mask_fixture import actions

OUT = bench.CACHE / "combined-vendetta-boundaries"
ROUND = 614
ACTOR = 0
PHASES = ("wardrev", "enemies", "d_farm", "decide")
VARIANTS = ("cap", "specialized", "combined")


def reference(variant):
    fixture = read(HERE / f"CPG_SAFE_TRIBUTE_{variant.upper()}_FIXTURE.json")
    assert fixture["seed"] == SEED
    (row,) = (r for r in fixture["rows"] if r["new_events"])
    assert row["new_events"] == [[ACTOR, ROUND]]
    case = {**row["candidate"], "events": row["events"]}
    key = f"{case['noise_seed']}-{case['opponent']}-{case['map']}-{case['side']}"
    directory = bench.CACHE / f"cpg-safe-tribute-{variant}-fixture"
    return fixture["candidate"], case, directory, directory / "games" / f"capped-{key}"


def prepare_trace(phase):
    directory = OUT / phase
    (directory / "games").mkdir(parents=True)
    src = directory / "source/src"
    prepare(src, True, specialized=True, post_ward=True)
    marker = f'PROF_CHECK("{phase}");'
    apply(src / "bot.cpp", ((marker, marker + f'''
    if (round == {ROUND} && type == bc::champion_type::vendetta && static_cast<int>(bc::round_number()) != round)
        std::printf("CODEX_STRESS R%d t%d {phase}\\n", round, static_cast<int>(type));'''),))
    return build(src, directory / "diagnostic", SEED)


def main():
    refs = {v: reference(v) for v in VARIANTS}
    sha, case, trace.REFERENCE_OUT, _ = refs["combined"]
    mp = STRESS / "maps" / f"{case['map']}.map26a"
    file, expected = bench.OPPS[case["opponent"]]
    assert bench.digest(mp) == case["map_hash"] and bench.digest(bench.CACHE / file) == expected
    assert all(all(ref[1][k] == case[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
               for ref in refs.values())
    with ThreadPoolExecutor(max_workers=len(PHASES)) as pool:
        binaries = list(pool.map(prepare_trace, PHASES))
    turns = {v: read_turn(refs[v][3], ROUND, case["side"], ACTOR) for v in VARIANTS}
    combined = turns["combined"]
    comparisons = {v: {"same_input": t["observation"] == combined["observation"],
                       "same_actions": actions(t) == actions(combined), "sha256": refs[v][0]}
                   for v, t in turns.items()}
    diagnostics = {}
    for phase, wasm in zip(PHASES, binaries, strict=True):
        trace.OUT = bench.OUT = OUT / phase
        row = trace.play((case, mp, wasm))
        diagnostics[phase] = {"sha256": bench.digest(wasm), "row": row}
    result = {"engine": bench.ENGINE, "seed": SEED, "reference": sha,
              "comparisons": comparisons, "turns": turns, "diagnostics": diagnostics}
    with (HERE / "CPG_SAFE_TRIBUTE_COMBINED_VENDETTA_BOUNDARIES.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print(comparisons, flush=True)
    for phase, entry in diagnostics.items():
        (r,) = entry["row"]["checks"]
        print(phase, {k: r[k] for k in ("matched", "same_input", "same_actions", "same_event", "phases")}, flush=True)


if __name__ == "__main__":
    main()
