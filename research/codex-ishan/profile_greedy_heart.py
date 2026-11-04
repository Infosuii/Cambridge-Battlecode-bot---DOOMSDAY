"""Trace only the independent standard-budget Heart of Ruin crossings."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import re
from zipfile import ZipFile

from bounded_verdict import apply
from cpg_greedy_full import prepare
from cpg_heart_camp_mask import prepare as prepare_camp_mask
from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from pg_dash_followup import read_turn
from profile_roster_stress import prepare_coarse, summarize_scoped
from qualify_local import build
from stress_greedy_pair import OUT as RAW, SEED
from verify_heart_camp_mask_fixture import OUT as MASK_RAW

OUT = bench.CACHE / "cpg-greedy-heart-trace"
STAGES = ("world", "support", "wardrev", "ambush", "enemies", "c_walked", "c_cast", "d_farm",
          "decide", "tail", "fields", "bushpre")
CAST_PHASES = ("camp_pick", "camp_cast_before", "strike_before", "scan_start", "scan_end", "cast_attempt",
               "cast_return", "strike_after", "camp_cast_after", "after_attack", "decision_return",
               "dispatch_before", "dispatch_after", "reserve_refusal")


def control_turns(pairs):
    comparisons = []
    for pair in pairs:
        if pair["target"]:
            continue
        base = pair["base"]
        e = base["events"][0]
        actor, rnd = e["owner"]["id"], e["timestamp"]["round"]
        side = base["side"]
        key = f"{SEED}-{base['opponent']}-{base['map']}-{side}"
        before = read_turn(RAW / "games" / f"full-{key}", rnd, side, actor)
        after = read_turn(MASK_RAW / "games" / f"mask-{key}", rnd, side, actor)
        old, new = ([a for a in t["executed_actions"] if a["kind"] not in (3, 26)] if t else []
                    for t in (before, after))
        comparisons.append({"round": rnd, "actor": actor, "side": side,
                            "same_input": bool(before and after and before["observation"] == after["observation"]),
                            "same_action_prefix": bool(before and after and old == new[:len(old)]),
                            "base_actions": old, "candidate_actions": new, "events": pair["events"],
                            "base_turn": before, "candidate_turn": after})
    return comparisons


def cast_sample(phase):
    return f"codex_heart_phase({CAST_PHASES.index(phase)}, round, type);"


def instrument_cast(src, target_round, rejection):
    apply(src / "bot.cpp", (
        ('#include "bot.h"', f'''#include "bot.h"

static unsigned codex_heart_round[{len(CAST_PHASES)}];
static unsigned long long codex_heart_fuel[{len(CAST_PHASES)}];
static int codex_heart_walked = -1, codex_heart_exclusive = -1;

static void codex_heart_phase(int phase, int round, bc::champion_type type) {{
    if (round != {target_round} || type != bc::champion_type::heart_of_ruin) return;
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
         f"""        if (round == {target_round}) {{
            codex_heart_walked = walked;
            codex_heart_exclusive = sp.excludes_walk;
        }}
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
    if rejection:
        apply(src / "bot.cpp", (
            ("static int codex_heart_walked = -1, codex_heart_exclusive = -1;",
             """static int codex_heart_walked = -1, codex_heart_exclusive = -1;
static int codex_heart_error = -1;
static vec2 codex_heart_rejected_tile;"""),
            ("        } catch (...) { }\n    }\n    return false;\n}\n#endif\n\nbool Bot::cast_on_camp(int ci) {",
             f"""        }} catch (const bc::error& e) {{
            if (round == {target_round}) {{
                codex_heart_error = static_cast<int>(e.code());
                codex_heart_rejected_tile = best;
            }}
        }} catch (...) {{ }}
    }}
    return false;
}}
#endif

bool Bot::cast_on_camp(int ci) {{"""),
            ("        codex_heart_walked = codex_heart_exclusive = -1;",
             """        if (codex_heart_error >= 0) {
            std::printf("CODEX_HEART_REJECT %d %d %d\\n", codex_heart_error, codex_heart_rejected_tile.x,
                        codex_heart_rejected_tile.y);
            codex_heart_error = -1;
        }
        codex_heart_walked = codex_heart_exclusive = -1;"""),
        ))


def instrument_attack(src, dispatch):
    phases = CAST_PHASES[CAST_PHASES.index("after_attack"):] if dispatch else ("after_attack", "decision_return")

    def marker(phase):
        return ("if (round == 353 && type == bc::champion_type::heart_of_ruin) "
                f"codex_heart_attack({phases.index(phase)});")

    edits = [
        ('#include "bot.h"', f'''#include "bot.h"

static unsigned codex_attack_round[{len(phases)}];
static unsigned long long codex_attack_fuel[{len(phases)}];

[[gnu::noinline]] static void codex_heart_attack(int phase) {{
    codex_attack_round[phase] = bc::round_number();
    codex_attack_fuel[phase] = bc::fuel_remaining();
}}'''),
        ('    PROF_CHECK("c_cast"); if (attack_unit(w.camps[t].camp, w.camps[t].pos)) {',
         '    PROF_CHECK("c_cast"); if (attack_unit(w.camps[t].camp, w.camps[t].pos)) {\n        ' + marker("after_attack")),
        ('    return true;\n}\n\n// NOVA_UNBOX:',
         '    ' + marker("decision_return") + '\n    return true;\n}\n\n// NOVA_UNBOX:'),
        ("void Bot::play_turn() {", f'''void Bot::play_turn() {{
    if (codex_attack_round[0]) {{
        for (int i = 0; i < {len(phases)}; ++i) {{
            if (codex_attack_round[i])
                std::printf("CODEX_HEART_CAST %d %u %llu\\n", {CAST_PHASES.index(phases[0])} + i,
                            codex_attack_round[i], codex_attack_fuel[i]);
            codex_attack_round[i] = 0;
        }}
    }}'''),
    ]
    if dispatch:
        edits.extend((
            ("#else\n    cast_on_camp(t);\n#endif\n#if CODEX_PG_HEART_ATTACK",
             "#else\n    " + marker("dispatch_before") + "\n    cast_on_camp(t);\n    " +
             marker("dispatch_after") + "\n#endif\n#if CODEX_PG_HEART_ATTACK"),
            ("#if CODEX_PG_CAMP_RESERVE\n        if (rb::turn_guard()) return false;\n#endif",
             "#if CODEX_PG_CAMP_RESERVE\n        if (rb::turn_guard()) {\n            " +
             marker("reserve_refusal") + "\n            return false;\n        }\n#endif"),
        ))
    apply(src / "bot.cpp", edits)


def play(item):
    base, mp, wasm = item
    opponent, side = base["opponent"], base["side"]
    row = bench.one(("profile", SEED, opponent, mp, side, wasm), fuel=100000, log_limit=1048576)
    assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    key = f"{SEED}-{opponent}-{mp.stem}-{side}"
    old_root = MASK_RAW if base["arm"] == "mask" else RAW
    old = old_root / "games" / f"{base['arm']}-{key}"
    new = OUT / "games" / f"profile-{key}"
    row = summarize_scoped(row, new)
    (bundle,) = new.glob("*.repl26a")
    with ZipFile(bundle) as archive:
        log = archive.read(f"team-{side.lower()}.stdout")
    cast_phases = {CAST_PHASES[int(i)]: [int(r), int(f)]
                   for i, r, f in re.findall(rb"CODEX_HEART_CAST (\d+) (\d+) (\d+)", log)}
    cast_state = [list(map(int, s)) for s in re.findall(rb"CODEX_HEART_STATE (-?\d+) (-?\d+)", log)]
    rejections = [list(map(int, s)) for s in re.findall(rb"CODEX_HEART_REJECT (\d+) (-?\d+) (-?\d+)", log)]
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
            "cast_phases": cast_phases, "cast_state": cast_state, "rejections": rejections,
            "base_turn": t0, "diagnostic_turn": t1}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cast", action="store_true")
    mode.add_argument("--remaining", action="store_true")
    mode.add_argument("--attack", action="store_true")
    mode.add_argument("--dispatch", action="store_true")
    mode.add_argument("--remaining-scan", action="store_true")
    mode.add_argument("--rejection", action="store_true")
    args = parser.parse_args()
    remaining_scan = args.remaining_scan or args.rejection
    cast, attack = args.cast or remaining_scan, args.attack or args.dispatch
    remaining = args.remaining or attack or remaining_scan
    if args.cast:
        OUT = bench.CACHE / "cpg-greedy-heart-cast"
    if remaining:
        OUT = bench.CACHE / "cpg-heart-camp-mask-remaining"
    if attack:
        OUT = bench.CACHE / ("cpg-heart-camp-mask-dispatch" if args.dispatch else "cpg-heart-camp-mask-attack")
    if remaining_scan:
        OUT = bench.CACHE / ("cpg-heart-camp-mask-rejection" if args.rejection else "cpg-heart-camp-mask-scan")
    source = read(HERE / "CPG_GREEDY_PAIR_STRESS.json")
    cases = [r for r in source["affected"] if r["arm"] == "full"]
    assert len(cases) == 3 and all(len(r["events"]) == 1 for r in cases)
    assert all(r["events"][0]["owner"]["name"] == "Heart of Ruin" for r in cases)
    reference = source["binaries"]["full"]
    if args.cast:
        cases = [r for r in cases if r["events"][0]["timestamp"]["round"] == 232]
    controls = []
    if remaining:
        fixture = read(HERE / "CPG_HEART_CAMP_MASK_FIXTURE.json")
        reference = fixture["candidate"]
        controls = control_turns(fixture["rows"])
        cases = [{**p["candidate"], "events": p["events"]} for p in fixture["rows"] if p["events"]]
        assert len(cases) == 1 and cases[0]["events"][0]["timestamp"]["round"] == 353
    rounds = {r["events"][0]["timestamp"]["round"] for r in cases}
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    src = OUT / "source/src"
    prepare_source = prepare_camp_mask if remaining else prepare
    prepare_source(src, True)
    if attack:
        instrument_attack(src, args.dispatch)
    elif cast:
        (target_round,) = rounds
        instrument_cast(src, target_round, args.rejection)
    else:
        stages = (*STAGES, "f_camps") if remaining else STAGES
        prepare_coarse(src, rounds, stages)
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
    result = {"engine": bench.ENGINE, "reference": reference, "diagnostic": bench.digest(wasm),
              "seed": SEED, "n": len(rows), "matched": len(matched),
              "phases": [r["cast_phases"] if cast or attack else r["diagnostic"]["examples"] for r in matched],
              "cast_state": [r["cast_state"] for r in matched] if cast else [],
              "rejections": [r["rejections"] for r in matched] if args.rejection else []}
    name = ("CPG_HEART_CAMP_MASK_REJECTION.json" if args.rejection else
            "CPG_HEART_CAMP_MASK_SCAN.json" if args.remaining_scan else
            "CPG_HEART_CAMP_MASK_DISPATCH.json" if args.dispatch else "CPG_HEART_CAMP_MASK_ATTACK.json" if attack else
            "CPG_HEART_CAMP_MASK_REMAINING.json" if remaining else
            "CPG_GREEDY_HEART_CAST.json" if cast else "CPG_GREEDY_HEART_TRACE.json")
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows, "controls": controls}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
