"""Verify the matched Heart cast and the other two independent stress cases."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json

from cpg_heart_camp_mask import prepare
from cpg_heart_cast_path import prepare as prepare_path
from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from pg_dash_followup import read_turn
from qualify_local import build
from stress_greedy_pair import OUT as RAW, SEED

MASK_FIXTURE = bench.CACHE / "cpg-heart-camp-mask-fixture"
OUT = MASK_FIXTURE


def actions(turn):
    return [a for a in turn["executed_actions"] if a["kind"] not in (3, 26)] if turn else []


def play(item):
    base, mp, wasm, path = item
    opponent, side = base["opponent"], base["side"]
    arm = "path" if path else "mask"
    row = bench.one((arm, SEED, opponent, mp, side, wasm), fuel=100000)
    assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    key = f"{SEED}-{opponent}-{mp.stem}-{side}"
    old = RAW / "games" / f"full-{key}"
    new = OUT / "games" / f"{arm}-{key}"
    a, b = (read(p / "native.json") for p in (old, new))
    errors = bool(b["diagnostics"]["codes"] or any(b["diagnostics"]["botFaults"].values()))
    original = base["events"][0]
    actor, rnd = original["owner"]["id"], original["timestamp"]["round"]
    events = native_fuel(row, OUT)
    target = None
    control = None
    if rnd == 232:
        previous, current = (read_turn(p, rnd, side, actor) for p in (old, new))
        after_resume = read_turn(old, rnd + 1, side, actor)
        before, after = actions(previous), actions(current)
        assert len(before) == 1 and before[0]["kind"] == 4
        cast = next(a for a in actions(after_resume) if a["kind"] == 6 and a["from"] == before[-1]["to"])
        candidate_cast = next((a for a in after[len(before):] if a["kind"] == 6), None)
        target = {"same_input": bool(previous and current and previous["observation"] == current["observation"]),
                  "same_move": before == after[:len(before)],
                  "same_cast_landing": bool(candidate_cast and candidate_cast["to"] == cast["to"]),
                  "removed": not any(e["owner"] == original["owner"] and e["timestamp"]["round"] == rnd for e in events),
                  "original_move": before[0], "original_resume_cast": cast, "candidate_cast": candidate_cast}
    elif path:
        reference = MASK_FIXTURE / "games" / f"mask-{key}" if rnd == 353 else old
        previous, current = (read_turn(p, rnd, side, actor) for p in (reference, new))
        before, after = actions(previous), actions(current)
        expected_kind = 5 if rnd == 353 else 6
        assert before and before[0]["kind"] == expected_kind
        control = {"round": rnd, "same_input": bool(previous and current and previous["observation"] == current["observation"]),
                   "same_action_prefix": bool(previous and current and before == after[:len(before)]),
                   "removed": not any(e["owner"] == original["owner"] and e["timestamp"]["round"] == rnd for e in events),
                   "base_actions": before, "candidate_actions": after}
    return {"base": base, "candidate": row, "same_draft": a["roster"]["draft"] == b["roster"]["draft"],
            "errors": errors, "events": events, "target": target, "control": control}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", action="store_true")
    path = parser.parse_args().path
    if path:
        OUT = bench.CACHE / "cpg-heart-cast-path-fixture"
    source = read(HERE / "CPG_GREEDY_PAIR_STRESS.json")
    cases = [r for r in source["affected"] if r["arm"] == "full"]
    assert len(cases) == 3 and all(len(r["events"]) == 1 for r in cases)
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    src = OUT / "source/src"
    prepare_source = prepare_path if path else prepare
    prepare_source(src, True)
    wasm = build(src, OUT / "candidate", SEED)
    jobs = []
    for row in cases:
        mp = STRESS / "maps" / f"{row['map']}.map26a"
        assert bench.digest(mp) == row["map_hash"]
        file, expected = bench.OPPS[row["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
        jobs.append((row, mp, wasm, path))
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(play, jobs))
    (target,) = (r["target"] for r in rows if r["target"])
    errors = sum(r["errors"] or not r["same_draft"] for r in rows)
    increases = sum(r["candidate"]["fuel_outs"] > r["base"]["fuel_outs"] for r in rows)
    passed = all(target[k] for k in ("same_input", "same_move", "same_cast_landing", "removed")) and not errors and not increases
    controls = [r["control"] for r in rows if r["control"]]
    if path:
        passed = passed and len(controls) == 2 and all(
            c["same_input"] and c["same_action_prefix"] and c["removed"] for c in controls)
    result = {"engine": bench.ENGINE, "reference": source["binaries"]["full"], "candidate": bench.digest(wasm),
              "seed": SEED, "n": len(rows), "errors": errors, "increases": increases, "target": target,
              "controls": controls, "pass": passed}
    name = "CPG_HEART_CAST_PATH_FIXTURE.json" if path else "CPG_HEART_CAMP_MASK_FIXTURE.json"
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
