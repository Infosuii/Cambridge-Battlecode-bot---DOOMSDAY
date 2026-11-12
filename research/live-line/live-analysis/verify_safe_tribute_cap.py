"""Check the original Cassi crossings and the Issac control on the capped source."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json

from cpg_safe_tribute_cap import prepare
from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from pg_dash_followup import read_turn
from qualify_local import build
from stress_heart_cast_path import OUT as RAW, SEED
from verify_heart_camp_mask_fixture import actions

OUT = bench.CACHE / "cpg-safe-tribute-cap-fixture"


def event_key(event):
    return event["owner"]["id"], event["timestamp"]["round"]


def play(item):
    base, mp, wasm = item
    opponent, side = base["opponent"], base["side"]
    row = bench.one(("capped", SEED, opponent, mp, side, wasm), fuel=100000)
    assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    key = f"{SEED}-{opponent}-{mp.stem}-{side}"
    old, new = RAW / "games" / f"path-{key}", OUT / "games" / f"capped-{key}"
    a, b = (read(p / "native.json") for p in (old, new))
    errors = bool(b["diagnostics"]["codes"] or any(b["diagnostics"]["botFaults"].values()))
    events = native_fuel(row, OUT)
    original = {event_key(e) for e in base["events"]}
    observed = {event_key(e) for e in events}
    turns = []
    for event in base["events"]:
        actor, rnd = event_key(event)
        previous, current = (read_turn(p, rnd, side, actor) for p in (old, new))
        before, after = actions(previous), actions(current)
        turns.append({"round": rnd, "actor": actor, "removed": (actor, rnd) not in observed,
                      "same_input": bool(previous and current and previous["observation"] == current["observation"]),
                      "same_action_prefix": bool(previous and current and before == after[:len(before)]),
                      "base_actions": before, "candidate_actions": after})
    return {"base": base, "candidate": row, "same_draft": a["roster"]["draft"] == b["roster"]["draft"],
            "errors": errors, "events": events, "new_events": sorted(observed - original), "turns": turns}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--specialized", action="store_true")
    mode.add_argument("--shared", action="store_true")
    mode.add_argument("--post-ward", action="store_true")
    mode.add_argument("--combined", action="store_true")
    mode.add_argument("--ward-decide", action="store_true")
    mode.add_argument("--ward-retry", action="store_true")
    args = parser.parse_args()
    variant = next((name for enabled, name in ((args.ward_retry, "ward-retry"), (args.ward_decide, "ward-decide"), (args.combined, "combined"), (args.post_ward, "post-ward"), (args.shared, "shared"),
                                               (args.specialized, "specialized")) if enabled), "cap")
    OUT = bench.CACHE / f"cpg-safe-tribute-{variant}-fixture"
    source = read(HERE / "CPG_HEART_CAST_PATH_STRESS.json")
    cases = source["affected"]
    assert source["seed"] == SEED and len(cases) == 2
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    src = OUT / "source/src"
    prepare(src, True, specialized=args.specialized or args.combined,
            shared=args.shared, post_ward=args.post_ward or args.combined, ward_decide=args.ward_decide, ward_retry=args.ward_retry)
    wasm = build(src, OUT / "candidate", SEED)
    jobs = []
    for row in cases:
        mp = STRESS / "maps" / f"{row['map']}.map26a"
        assert bench.digest(mp) == row["map_hash"]
        file, expected = bench.OPPS[row["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
        jobs.append((row, mp, wasm))
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(play, jobs))
    turns = {turn["round"]: turn for cell in rows for turn in cell["turns"]}
    assert set(turns) == {321, 334, 566} and turns[321]["base_actions"][0]["kind"] == 14
    errors = sum(r["errors"] or not r["same_draft"] for r in rows)
    increases = sum(bool(r["new_events"]) or r["candidate"]["fuel_outs"] > r["base"]["fuel_outs"] for r in rows)
    first = turns[321]
    passed = first["same_input"] and first["same_action_prefix"] and first["removed"] and turns[334]["removed"]
    result = {"engine": bench.ENGINE, "reference": source["wasm"], "candidate": bench.digest(wasm),
              "seed": SEED, "n": len(rows), "errors": errors, "increases": increases, "turns": turns,
              "pass": passed and not errors and not increases}
    name = f"CPG_SAFE_TRIBUTE_{variant.upper().replace('-', '_')}_FIXTURE.json"
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
