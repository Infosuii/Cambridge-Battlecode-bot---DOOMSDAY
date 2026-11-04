"""Verify the matched Heart cast and the other two independent stress cases."""
from concurrent.futures import ThreadPoolExecutor
import json

from cpg_heart_camp_mask import prepare
from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from pg_dash_followup import read_turn
from qualify_local import build
from stress_greedy_pair import OUT as RAW, SEED

OUT = bench.CACHE / "cpg-heart-camp-mask-fixture"


def actions(turn):
    return [a for a in turn["executed_actions"] if a["kind"] not in (3, 26)] if turn else []


def play(item):
    base, mp, wasm = item
    opponent, side = base["opponent"], base["side"]
    row = bench.one(("mask", SEED, opponent, mp, side, wasm), fuel=100000)
    assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    key = f"{SEED}-{opponent}-{mp.stem}-{side}"
    old = RAW / "games" / f"full-{key}"
    new = OUT / "games" / f"mask-{key}"
    a, b = (read(p / "native.json") for p in (old, new))
    errors = bool(b["diagnostics"]["codes"] or any(b["diagnostics"]["botFaults"].values()))
    original = base["events"][0]
    actor, rnd = original["owner"]["id"], original["timestamp"]["round"]
    events = native_fuel(row, OUT)
    target = None
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
    return {"base": base, "candidate": row, "same_draft": a["roster"]["draft"] == b["roster"]["draft"],
            "errors": errors, "events": events, "target": target}


def main():
    source = read(HERE / "CPG_GREEDY_PAIR_STRESS.json")
    cases = [r for r in source["affected"] if r["arm"] == "full"]
    assert len(cases) == 3 and all(len(r["events"]) == 1 for r in cases)
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    src = OUT / "source/src"
    prepare(src, True)
    wasm = build(src, OUT / "candidate", SEED)
    jobs = []
    for row in cases:
        mp = STRESS / "maps" / f"{row['map']}.map26a"
        assert bench.digest(mp) == row["map_hash"]
        file, expected = bench.OPPS[row["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
        jobs.append((row, mp, wasm))
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(play, jobs))
    (target,) = (r["target"] for r in rows if r["target"])
    errors = sum(r["errors"] or not r["same_draft"] for r in rows)
    increases = sum(r["candidate"]["fuel_outs"] > r["base"]["fuel_outs"] for r in rows)
    passed = all(target[k] for k in ("same_input", "same_move", "same_cast_landing", "removed")) and not errors and not increases
    result = {"engine": bench.ENGINE, "reference": source["binaries"]["full"], "candidate": bench.digest(wasm),
              "seed": SEED, "n": len(rows), "errors": errors, "increases": increases, "target": target, "pass": passed}
    with (HERE / "CPG_HEART_CAMP_MASK_FIXTURE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
