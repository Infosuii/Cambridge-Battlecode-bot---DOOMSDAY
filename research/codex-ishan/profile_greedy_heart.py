"""Trace only the independent standard-budget Heart of Ruin crossings."""
from concurrent.futures import ThreadPoolExecutor
import json

from bounded_verdict import apply
from cpg_greedy_full import prepare
from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from pg_dash_followup import read_turn
from profile_roster_stress import prepare_coarse, summarize_scoped
from qualify_local import build
from stress_greedy_pair import OUT as RAW, SEED

OUT = bench.CACHE / "cpg-greedy-heart-trace"
STAGES = ("world", "support", "wardrev", "ambush", "enemies", "c_walked", "c_cast", "d_farm",
          "decide", "tail", "fields", "bushpre")


def play(item):
    base, mp, wasm = item
    opponent, side = base["opponent"], base["side"]
    row = bench.one(("profile", SEED, opponent, mp, side, wasm), fuel=100000, log_limit=1048576)
    assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    key = f"{SEED}-{opponent}-{mp.stem}-{side}"
    old = RAW / "games" / f"full-{key}"
    new = OUT / "games" / f"profile-{key}"
    row = summarize_scoped(row, new)
    a, b = (read(p / "native.json") for p in (old, new))
    same_draft = a["roster"]["draft"] == b["roster"]["draft"]
    errors = bool(b["diagnostics"]["codes"] or any(b["diagnostics"]["botFaults"].values()))
    original = base["events"][0]
    actor, rnd = original["owner"]["id"], original["timestamp"]["round"]
    events = native_fuel(row, OUT)
    same_event = any(e["owner"] == original["owner"] and e["timestamp"]["round"] == rnd for e in events)
    t0, t1 = (read_turn(p, rnd, side, actor) for p in (old, new))
    before, after = ([a for a in t["executed_actions"] if a["kind"] not in (3, 26)] if t else [] for t in (t0, t1))
    same_input = bool(t0 and t1 and t0["observation"] == t1["observation"])
    same_prefix = bool(t0 and t1 and before == after[:len(before)])
    return {"base": base, "diagnostic": row, "same_draft": same_draft, "errors": errors, "events": events,
            "same_event": same_event, "same_input": same_input, "same_action_prefix": same_prefix,
            "base_turn": t0, "diagnostic_turn": t1}


def main():
    source = read(HERE / "CPG_GREEDY_PAIR_STRESS.json")
    cases = [r for r in source["affected"] if r["arm"] == "full"]
    assert len(cases) == 3 and all(len(r["events"]) == 1 for r in cases)
    assert all(r["events"][0]["owner"]["name"] == "Heart of Ruin" for r in cases)
    rounds = {r["events"][0]["timestamp"]["round"] for r in cases}
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    src = OUT / "source/src"
    prepare(src, True)
    prepare_coarse(src, rounds, STAGES)
    condition = " || ".join(f"round == {r}" for r in sorted(rounds))
    apply(src / "bot.cpp", ((f"    codex_stress_trace = {condition};",
                            f"    codex_stress_trace = ({condition}) && type == bc::champion_type::heart_of_ruin;"),))
    wasm = build(src, OUT / "diagnostic", SEED)
    jobs = []
    for row in cases:
        mp = STRESS / "maps" / f"{row['map']}.map26a"
        assert bench.digest(mp) == row["map_hash"]
        file, expected = bench.OPPS[row["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
        jobs.append((row, mp, wasm))
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(play, jobs))
    required = ("same_draft", "same_event", "same_input", "same_action_prefix")
    matched = [r for r in rows if all(r[k] for k in required) and not r["errors"]]
    result = {"engine": bench.ENGINE, "reference": source["binaries"]["full"], "diagnostic": bench.digest(wasm),
              "seed": SEED, "n": len(rows), "matched": len(matched),
              "phases": [r["diagnostic"]["examples"] for r in matched]}
    with (HERE / "CPG_GREEDY_HEART_TRACE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
