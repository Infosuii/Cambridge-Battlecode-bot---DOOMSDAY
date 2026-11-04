"""Localize the three standard-budget events from the frozen seed-14107 stress run."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import re
from zipfile import ZipFile

from bounded_verdict import apply
from cpg_heart_cast_path import prepare
from cpg_safe_tribute_cap import prepare as prepare_tribute
from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from pg_dash_followup import read_turn
from profile_roster_stress import prepare_coarse, summarize_scoped
from qualify_local import build
from stress_heart_cast_path import OUT as RAW, SEED

OUT = bench.CACHE / "heart-cast-path-stress-profile-14107"
REFERENCE_OUT = RAW
STAGES = ("world", "support", "wardrev", "ambush", "e_in", "e_td", "enemies", "farm0",
          "farmsel", "d_farm", "decide", "tail", "fields", "bushpre")
FARM_PHASES = ("wardrev", "farm_begin", "farm0", "farmsel", "farmmove", "c_zones",
               "c_staged", "c_safe", "c_walked", "c_cast", "d_farm", "altar_before", "altar_after",
               "bank_before", "bank_after", "wait_walk_before", "wait_walk_after", "safe_before", "safe_after")


def instrument_issac(src):
    apply(src / "bot.cpp", (
        ('#include "bot.h"', '''#include "bot.h"

static unsigned codex_issac_round;
static unsigned long long codex_issac_before, codex_issac_after;'''),
        ('        handle_enemies();', '''        ([&] {
            const bool sample = round == 566 && type == bc::champion_type::issac;
            if (sample) codex_issac_before = bc::fuel_remaining();
            const bool result = handle_enemies();
            if (sample) {
                codex_issac_round = bc::round_number();
                codex_issac_after = bc::fuel_remaining();
            }
            return result;
        })();'''),
        ('void Bot::play_turn() {', '''void Bot::play_turn() {
    if (codex_issac_round) {
        std::printf("CODEX_ISSAC_COMBAT %u %llu %llu\\n", codex_issac_round, codex_issac_before, codex_issac_after);
        codex_issac_round = 0;
    }'''),
    ))


def instrument_vendetta(src):
    route = """#if CODEX_SAFE_TRIBUTE_CAP
                if constexpr (bounded_wait) {
                    const auto cap = rb::search_cap(rb::kTailReserve);
                    if (cap == 0) return true;
                    const auto levels = safe_field.compute_to_with_expansion_count(blocked, ring, single(pos), visited, cap);
                    // An unfinished search does not establish that the plain route is safe.
                    if (fdist(safe_field, pos) == kUnreach && levels + 1 >= cap) return true;
                } else
#endif
                {
                    safe_field.compute_to(blocked, ring, single(pos), visited);
                }"""
    apply(src / "bot.cpp", (
        ('#include "bot.h"', '''#include "bot.h"

static unsigned codex_vend_bank_round;
static bool codex_vend_bank_bounded;
static unsigned long long codex_vend_bank_before, codex_vend_bank_after;'''),
        (route, '''                const bool sample = round == 614 && type == bc::champion_type::vendetta;
                if (sample) {
                    codex_vend_bank_bounded = bounded_wait;
                    codex_vend_bank_before = bc::fuel_remaining();
                }
''' + route + '''
                if (sample) {
                    codex_vend_bank_round = bc::round_number();
                    codex_vend_bank_after = bc::fuel_remaining();
                }'''),
        ('void Bot::play_turn() {', '''void Bot::play_turn() {
    if (codex_vend_bank_round) {
        std::printf("CODEX_VEND_BANK %u %d %llu %llu\\n", codex_vend_bank_round, codex_vend_bank_bounded,
                    codex_vend_bank_before, codex_vend_bank_after);
        codex_vend_bank_round = 0;
    }'''),
    ))


def instrument_farm(src, altar, wait):
    count = len(FARM_PHASES)

    def marker(phase):
        return ("if ((round == 321 || round == 334) && type == bc::champion_type::cassi) "
                f"codex_cassi_sample({FARM_PHASES.index(phase)}, round);")

    phases = ("farmmove", "d_farm") if altar or wait else FARM_PHASES[:FARM_PHASES.index("altar_before")]
    edits = [
        ('#include "bot.h"', f'''#include "bot.h"

static unsigned codex_cassi_round;
static unsigned codex_cassi_engine[{count}];
static unsigned long long codex_cassi_fuel[{count}];

[[gnu::noinline]] static void codex_cassi_sample(int phase, int round) {{
    codex_cassi_round = round;
    codex_cassi_engine[phase] = bc::round_number();
    codex_cassi_fuel[phase] = bc::fuel_remaining();
}}'''),
        *((f'PROF_CHECK("{phase}");', f'PROF_CHECK("{phase}"); ' + marker(phase))
          for phase in phases if phase != "farm_begin"),
        ("void Bot::play_turn() {", f'''void Bot::play_turn() {{
    if (codex_cassi_round) {{
        for (int i = 0; i < {count}; ++i) {{
            if (codex_cassi_engine[i])
                std::printf("CODEX_CASSI_FARM %u %d %u %llu\\n", codex_cassi_round, i,
                            codex_cassi_engine[i], codex_cassi_fuel[i]);
            codex_cassi_engine[i] = 0;
        }}
        codex_cassi_round = 0;
    }}'''),
    ]
    if altar:
        edits.extend((
            ('    switch (g.state) {\n    case GroupState::reward: {\n        mode = "capture";',
             '''    if ((round == 321 || round == 334) && type == bc::champion_type::cassi) {
        codex_cassi_state = static_cast<int>(g.state);
        codex_cassi_altar_ready = w.altar_ready;
        codex_cassi_altar_gated = w.altar_gated;
        codex_cassi_no_bank = w.no_bank;
    }
    switch (g.state) {
    case GroupState::reward: {
        mode = "capture";'''),
            ('            const int altar_trip = gems >= 10 && w.ensure_altar_field()\n',
             '            ' + marker("altar_before") + '\n' +
             '            const bool has_altar = gems >= 10 && w.ensure_altar_field();\n' +
             '            ' + marker("altar_after") + '\n            const int altar_trip = has_altar\n'),
        ))
    elif wait:
        safe_search = """    if (sr_hold && !force_tribute) return false;
#else
    if (gems >= 15) {
        bc::bitboard threat = w.threat_zone(round, V58_SURVIVE ? 15 : 10, 4.0f);
        threat.set(pos, false);
        if (!threat.is_empty() || any_watch) {
            bc::bitboard blocked = w.static_blocked | threat;
            blocked.set(pos, false);
            bc::bitboard ring = w.altar_ring & ~blocked;
            if (any_watch) ring = ring & ~watched;
            if (!ring.is_empty()) {
                bc::bitboard visited;
                safe_field.compute_to(blocked, ring, single(pos), visited);"""
        edits.extend((
            ('            if (gems >= 10 && wait > altar_trip + 2) {\n                force_tribute = true;\n                return tribute_if_needed();',
             '            if (gems >= 10 && wait > altar_trip + 2) {\n                force_tribute = true;\n                ' +
             marker("bank_before") + '\n                const bool result = tribute_if_needed();\n                ' +
             marker("bank_after") + '\n                return result;'),
            ('        if (bit(g.tiles, pos) || !bit(goal, pos)) walk_toward(goal);',
             '        if (bit(g.tiles, pos) || !bit(goal, pos)) {\n            ' + marker("wait_walk_before") +
             '\n            walk_toward(goal);\n            ' + marker("wait_walk_after") + '\n        }'),
            (safe_search, safe_search.replace('                safe_field.compute_to',
                                               '                ' + marker("safe_before") + '\n                safe_field.compute_to') +
             '\n                ' + marker("safe_after")),
        ))
    else:
        edits.append(('        if (!farm()) mode = "nofarm";',
                      '        ' + marker("farm_begin") + '\n        if (!farm()) mode = "nofarm";'))
    apply(src / "bot.cpp", edits)
    if altar:
        apply(src / "bot.cpp", (
            ('static unsigned codex_cassi_round;', '''static unsigned codex_cassi_round;
static int codex_cassi_state = -1;
static bool codex_cassi_altar_ready, codex_cassi_altar_gated, codex_cassi_no_bank;'''),
            ('        codex_cassi_round = 0;', '''        std::printf("CODEX_CASSI_STATE %u %d %d %d %d\\n", codex_cassi_round,
                    codex_cassi_state, codex_cassi_altar_ready, codex_cassi_altar_gated, codex_cassi_no_bank);
        codex_cassi_state = -1;
        codex_cassi_round = 0;'''),
        ))


def play(item):
    base, mp, wasm = item
    opponent, side = base["opponent"], base["side"]
    row = bench.one(("profile", SEED, opponent, mp, side, wasm), fuel=100000, log_limit=1048576)
    assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    key = f"{SEED}-{opponent}-{mp.stem}-{side}"
    old, new = REFERENCE_OUT / "games" / f"{base['arm']}-{key}", OUT / "games" / f"profile-{key}"
    row = summarize_scoped(row, new)
    (bundle,) = new.glob("*.repl26a")
    with ZipFile(bundle) as archive:
        log = archive.read(f"team-{side.lower()}.stdout")
    markers = re.findall(rb"CODEX_STRESS R(\d+) t\d+ ([a-z_0-9]+)", log)
    samples = [list(map(int, m)) for m in re.findall(rb"CODEX_CASSI_FARM (\d+) (\d+) (\d+) (\d+)", log)]
    states = {int(r): [int(s), bool(int(ready)), bool(int(gated)), bool(int(no_bank))] for r, s, ready, gated, no_bank in
              re.findall(rb"CODEX_CASSI_STATE (\d+) (-?\d+) (\d+) (\d+) (\d+)", log)}
    combat = [list(map(int, m)) for m in re.findall(rb"CODEX_ISSAC_COMBAT (\d+) (\d+) (\d+)", log)]
    bank = [list(map(int, m)) for m in re.findall(rb"CODEX_VEND_BANK (\d+) (\d+) (\d+) (\d+)", log)]
    a, b = (read(p / "native.json") for p in (old, new))
    same_draft = a["roster"]["draft"] == b["roster"]["draft"]
    errors = bool(b["diagnostics"]["codes"] or any(b["diagnostics"]["botFaults"].values()))
    observed = native_fuel(row, OUT)
    checks = []
    for event in base["events"]:
        actor, rnd = event["owner"]["id"], event["timestamp"]["round"]
        old_turn, new_turn = (read_turn(p, rnd, side, actor) for p in (old, new))
        actions = [[a for a in t["executed_actions"] if a["kind"] not in (3, 26)] if t else []
                   for t in (old_turn, new_turn)]
        native_match = any(e["owner"] == event["owner"] and e["timestamp"]["round"] == rnd for e in observed)
        same_input = bool(old_turn and new_turn and old_turn["observation"] == new_turn["observation"])
        same_actions = bool(old_turn and new_turn and actions[0] == actions[1])
        phases = [phase.decode() for recorded, phase in markers if int(recorded) == rnd]
        fuel = {FARM_PHASES[i]: [engine_round, left] for recorded, i, engine_round, left in samples if recorded == rnd}
        checks.append({"round": rnd, "actor": actor, "same_input": same_input, "same_actions": same_actions,
                       "same_event": native_match, "phases": phases, "fuel": fuel, "state": states.get(rnd),
                       "matched": same_draft and not errors and native_match and same_input and same_actions,
                       "base_turn": old_turn, "diagnostic_turn": new_turn})
    return {"base": base, "diagnostic": row, "same_draft": same_draft, "errors": errors,
            "observed": observed, "checks": checks, "combat": combat, "bank": bank}


def main():
    global OUT, REFERENCE_OUT
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--farm", action="store_true")
    mode.add_argument("--altar", action="store_true")
    mode.add_argument("--wait", action="store_true")
    mode.add_argument("--issac", action="store_true")
    mode.add_argument("--vendetta", action="store_true")
    args = parser.parse_args()
    farm, altar, wait = args.farm or args.altar or args.wait, args.altar, args.wait
    if farm:
        suffix = "altar" if altar else "wait" if wait else "farm"
        OUT = bench.CACHE / f"heart-cast-path-cassi-{suffix}-14107"
    if args.issac:
        OUT = bench.CACHE / "heart-cast-path-issac-combat-14107"
    if args.vendetta:
        OUT = bench.CACHE / "safe-tribute-vendetta-bank-14107"
        REFERENCE_OUT = bench.CACHE / "cpg-safe-tribute-specialized-fixture"
    frozen = read(HERE / "CPG_HEART_CAST_PATH_STRESS.json")
    assert frozen["seed"] == SEED and frozen["n"] == 800
    cases = frozen["affected"]
    events = [(e["timestamp"]["round"], e["owner"]["name"].lower()) for r in cases for e in r["events"]]
    assert events == [(321, "cassi"), (334, "cassi"), (566, "issac")]
    if farm:
        cases = [r for r in cases if r["events"][0]["owner"]["name"] == "Cassi"]
    if args.issac:
        cases = [r for r in cases if r["events"][0]["owner"]["name"] == "Issac"]
    reference = frozen["wasm"]
    if args.vendetta:
        fixture = read(HERE / "CPG_SAFE_TRIBUTE_SPECIALIZED_FIXTURE.json")
        reference = fixture["candidate"]
        cases = [{**p["candidate"], "events": p["events"]} for p in fixture["rows"] if p["new_events"]]
        assert len(cases) == 1 and cases[0]["events"][0]["timestamp"]["round"] == 614
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    src = OUT / "source/src"
    if args.vendetta:
        prepare_tribute(src, True, specialized=True)
        instrument_vendetta(src)
    else:
        prepare(src, True)
    if args.issac:
        instrument_issac(src)
    elif farm:
        instrument_farm(src, altar, wait)
    elif not args.vendetta:
        rounds = sorted({rnd for rnd, _ in events})
        prepare_coarse(src, rounds, STAGES)
        initial = " || ".join(f"round == {rnd}" for rnd in rounds)
        condition = " || ".join(f"(round == {rnd} && type == bc::champion_type::{champion})" for rnd, champion in events)
        apply(src / "bot.cpp", ((f"    codex_stress_trace = {initial};", f"    codex_stress_trace = {condition};"),))
    wasm = build(src, OUT / "diagnostic", SEED)
    jobs = []
    for row in cases:
        mp = STRESS / "maps" / f"{row['map']}.map26a"
        assert bench.digest(mp) == row["map_hash"]
        file, expected = bench.OPPS[row["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
        jobs.append((row, mp, wasm))
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(play, jobs))
    matches = {r["round"]: r["fuel"] if farm else r["phases"] for cell in rows for r in cell["checks"] if r["matched"]}
    result = {"engine": bench.ENGINE, "reference": reference, "diagnostic": bench.digest(wasm),
              "seed": SEED, "matches": matches, "n": len(rows)}
    if args.issac:
        result["combat"] = [cell["combat"] for cell in rows]
    if args.vendetta:
        result["bank"] = [cell["bank"] for cell in rows]
    name = ("CPG_SAFE_TRIBUTE_VENDETTA_BANK.json" if args.vendetta else
            "CPG_CAST_PATH_ISSAC_COMBAT.json" if args.issac else
            "CPG_CAST_PATH_CASSI_WAIT.json" if wait else "CPG_CAST_PATH_CASSI_ALTAR.json" if altar else
            "CPG_CAST_PATH_CASSI_FARM.json" if farm else "CPG_HEART_CAST_PATH_STRESS_TRACE.json")
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
