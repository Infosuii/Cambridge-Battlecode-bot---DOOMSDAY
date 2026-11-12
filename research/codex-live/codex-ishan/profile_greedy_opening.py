"""Trace the repeated reduced-budget R1 and R3 opening events."""
from concurrent.futures import ThreadPoolExecutor
import json
import subprocess

from cpg_greedy_full import prepare
from large_roster_stress import DENSE_OUT, HERE, bench, native_fuel, read
from pg_dash_followup import read_turn
from profile_roster_stress import prepare_coarse, summarize_scoped

OUT = bench.CACHE / "cpg-greedy-opening-trace"
RAW = bench.CACHE / "cpg-greedy-full-stress"
STAGES = ("init", "refresh", "world", "episode", "sight", "events", "shop", "support", "wardrev",
          "ambush", "enemies", "farmsel", "farmmove", "d_farm", "decide", "tail", "fields", "bushpre")


def play(item):
    base, mp, wasm = item
    arm, opponent, side = (base[k] for k in ("arm", "opponent", "side"))
    row = bench.one((arm, 0, opponent, mp, side, wasm), fuel=80000, log_limit=1048576)
    assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    key = f"{arm}-0-{opponent}-{mp.stem}-{side}"
    old, new = (p / "games" / key for p in (RAW, OUT))
    row = summarize_scoped(row, new)
    a, b = (read(p / "native.json") for p in (old, new))
    same_draft = a["roster"]["draft"] == b["roster"]["draft"]
    errors = bool(b["diagnostics"]["codes"] or any(b["diagnostics"]["botFaults"].values()))
    events = native_fuel(row, OUT)
    original = native_fuel(base, RAW)
    late = next(e for e in original if e["timestamp"]["round"] == 3)
    actor = late["owner"]["id"]
    first = None
    for rnd in (4, 5, 6):
        turn = read_turn(old, rnd, side, actor)
        if turn:
            observed = read_turn(new, rnd, side, actor)
            before, after = ([a for a in t["executed_actions"] if a["kind"] not in (3, 26)] if t else []
                             for t in (turn, observed))
            first = {"round": rnd, "same_input": bool(observed and turn["observation"] == observed["observation"]),
                     "same_actions": bool(observed and before == after)}
            break
    return {"base": base, "diagnostic": row, "same_draft": same_draft, "errors": errors,
            "same_native": original == events, "original": original, "events": events, "first_turn": first}


def main():
    release = read(HERE / "CPG_GREEDY_FULL_EXACT.json")
    select = [p["candidate"] for p in release["rows"] if p["candidate"]["round1_fuel_outs"] == 6]
    assert len(select) == 8 and {r["arm"] for r in select} == {"80000"}
    assert len({r["map"] for r in select}) == 1
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    project = OUT / "diagnostic"
    src = project / "src"
    prepare(src, True)
    prepare_coarse(src, {1, 3}, STAGES)
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    jobs = []
    for row in select:
        mp = DENSE_OUT / "maps" / f"{row['map']}.map26a"
        assert bench.digest(mp) == row["map_hash"]
        file, expected = bench.OPPS[row["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
        jobs.append((row, mp, wasm))
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    matched = [r for r in rows if r["same_draft"] and r["same_native"] and not r["errors"] and r["first_turn"]
               and r["first_turn"]["same_input"] and r["first_turn"]["same_actions"]]
    result = {"engine": bench.ENGINE, "reference": release["sha256"], "diagnostic": bench.digest(wasm),
              "n": len(rows), "matched": len(matched), "phases": [r["diagnostic"]["examples"] for r in matched]}
    with (HERE / "CPG_GREEDY_OPENING_TRACE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
