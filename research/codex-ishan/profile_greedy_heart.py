"""Trace only the independent standard-budget Heart of Ruin crossings."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import re
from zipfile import ZipFile

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
CAST_PHASES = ("camp_pick", "camp_cast_before", "strike_before", "scan_start", "scan_end", "cast_attempt",
               "cast_return", "strike_after", "camp_cast_after")


def cast_sample(phase):
    return f"codex_heart_phase({CAST_PHASES.index(phase)}, round, type);"


def instrument_cast(src):
    apply(src / "bot.cpp", (
        ('#include "bot.h"', f'''#include "bot.h"

static unsigned codex_heart_round[{len(CAST_PHASES)}];
static unsigned long long codex_heart_fuel[{len(CAST_PHASES)}];
static int codex_heart_walked = -1, codex_heart_exclusive = -1;

static void codex_heart_phase(int phase, int round, bc::champion_type type) {{
    if (round != 232 || type != bc::champion_type::heart_of_ruin) return;
    codex_heart_round[phase] = bc::round_number();
    codex_heart_fuel[phase] = bc::fuel_remaining();
}}'''),
        ('t = pick_target(); PROF_CHECK("c_pick2");',
         't = pick_target(); PROF_CHECK("c_pick2"); ' + cast_sample("camp_pick")),
        ("#else\n    cast_on_camp(t);\n#endif\n#if CODEX_PG_HEART_ATTACK",
         "#else\n    " + cast_sample("camp_cast_before") + "\n    cast_on_camp(t);\n    " +
         cast_sample("camp_cast_after") + "\n#endif\n#if CODEX_PG_HEART_ATTACK"),
        ("    if (cast_camp_strike(ci)) return true;",
         "    " + cast_sample("strike_before") + "\n    const bool struck = cast_camp_strike(ci);\n    " +
         cast_sample("strike_after") + "\n    if (struck) return true;"),
        ("        int best_hits = 0, best_home = kUnreach;",
         """        if (round == 232) {
            codex_heart_walked = walked;
            codex_heart_exclusive = sp.excludes_walk;
        }
        """ + cast_sample("scan_start") + "\n        int best_hits = 0, best_home = kUnreach;"),
        ("        if (best.x < 0 || best_hits <= 0) return false;\n        try {\n            if (bc::self().abilities()[s].use(best)) {",
         "        " + cast_sample("scan_end") + "\n        if (best.x < 0 || best_hits <= 0) return false;\n        try {\n            " +
         cast_sample("cast_attempt") + "\n            const bool cast_ok = bc::self().abilities()[s].use(best);\n            " +
         cast_sample("cast_return") + "\n            if (cast_ok) {"),
        ("void Bot::play_turn() {", f'''void Bot::play_turn() {{
    if (codex_heart_round[{CAST_PHASES.index('camp_cast_before')}]) {{
        std::printf("CODEX_HEART_STATE %d %d\\n", codex_heart_walked, codex_heart_exclusive);
        for (int i = 0; i < {len(CAST_PHASES)}; ++i) {{
            if (codex_heart_round[i])
                std::printf("CODEX_HEART_CAST %d %u %llu\\n", i, codex_heart_round[i], codex_heart_fuel[i]);
            codex_heart_round[i] = 0;
        }}
        codex_heart_walked = codex_heart_exclusive = -1;
    }}'''),
    ))


def play(item):
    base, mp, wasm = item
    opponent, side = base["opponent"], base["side"]
    row = bench.one(("profile", SEED, opponent, mp, side, wasm), fuel=100000, log_limit=1048576)
    assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    key = f"{SEED}-{opponent}-{mp.stem}-{side}"
    old = RAW / "games" / f"full-{key}"
    new = OUT / "games" / f"profile-{key}"
    row = summarize_scoped(row, new)
    (bundle,) = new.glob("*.repl26a")
    with ZipFile(bundle) as archive:
        log = archive.read(f"team-{side.lower()}.stdout")
    cast_phases = {CAST_PHASES[int(i)]: [int(r), int(f)]
                   for i, r, f in re.findall(rb"CODEX_HEART_CAST (\d+) (\d+) (\d+)", log)}
    cast_state = [list(map(int, s)) for s in re.findall(rb"CODEX_HEART_STATE (-?\d+) (-?\d+)", log)]
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
            "cast_phases": cast_phases, "cast_state": cast_state, "base_turn": t0, "diagnostic_turn": t1}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cast", action="store_true")
    cast = parser.parse_args().cast
    if cast:
        OUT = bench.CACHE / "cpg-greedy-heart-cast"
    source = read(HERE / "CPG_GREEDY_PAIR_STRESS.json")
    cases = [r for r in source["affected"] if r["arm"] == "full"]
    assert len(cases) == 3 and all(len(r["events"]) == 1 for r in cases)
    assert all(r["events"][0]["owner"]["name"] == "Heart of Ruin" for r in cases)
    if cast:
        cases = [r for r in cases if r["events"][0]["timestamp"]["round"] == 232]
    rounds = {r["events"][0]["timestamp"]["round"] for r in cases}
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    src = OUT / "source/src"
    prepare(src, True)
    if cast:
        instrument_cast(src)
    else:
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
              "phases": [r["cast_phases"] if cast else r["diagnostic"]["examples"] for r in matched],
              "cast_state": [r["cast_state"] for r in matched] if cast else []}
    name = "CPG_GREEDY_HEART_CAST.json" if cast else "CPG_GREEDY_HEART_TRACE.json"
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
