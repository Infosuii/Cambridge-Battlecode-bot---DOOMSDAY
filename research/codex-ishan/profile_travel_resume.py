"""Trace the original R536 crossing in the noised development game."""
import argparse
import json
import re
from zipfile import ZipFile

from bounded_verdict import apply
from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from pg_dash_followup import read_turn
from pg_travel_scan import prepare
from profile_noised_stress import STAGES
from profile_roster_stress import play_scoped, prepare_coarse, summarize_scoped
from qualify_local import build

OUT = bench.CACHE / "travel-scan-resume-profile"
ROUND = 536


def prepare_attack(src):
    apply(src / "bot.cpp", (
        ("bool Bot::attack_unit(const bc::unit& target, vec2 where) {", """static unsigned codex_attack_round;
static unsigned long long codex_attack_fuel;

bool Bot::attack_unit(const bc::unit& target, vec2 where) {"""),
        ("        me.attack(target);\n        return true;", """        me.attack(target);
        if (round == 536 && type == bc::champion_type::marcella) {
            codex_attack_fuel = bc::fuel_remaining();
            codex_attack_round = bc::round_number();
        }
        return true;"""),
        ("void Bot::play_turn() {", """void Bot::play_turn() {
    if (codex_attack_round) {
        std::printf("CODEX_RESUME_ATTACK %u %llu\\n", codex_attack_round, codex_attack_fuel);
        codex_attack_round = 0;
    }"""),
    ))


def prepare_disengage(src):
    apply(src / "bot.cpp", (
        ('#include "bot.h"', '''#include "bot.h"

static unsigned codex_disengage_round;
static unsigned long long codex_disengage_before, codex_disengage_after;'''),
        ("        if (!moved) walk_toward(~danger_zone & ~w.static_blocked);", """        if (!moved) {
            const bool sample = round == 536 && type == bc::champion_type::marcella;
            if (sample) codex_disengage_before = bc::fuel_remaining();
            walk_toward(~danger_zone & ~w.static_blocked);
            if (sample) {
                codex_disengage_after = bc::fuel_remaining();
                codex_disengage_round = bc::round_number();
            }
        }"""),
        ("void Bot::play_turn() {", """void Bot::play_turn() {
    if (codex_disengage_round) {
        std::printf("CODEX_RESUME_DISENGAGE %u %llu %llu\\n", codex_disengage_round,
                    codex_disengage_before, codex_disengage_after);
        codex_disengage_round = 0;
    }"""),
    ))


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recount", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--attack", action="store_true")
    modes.add_argument("--disengage", action="store_true")
    args = parser.parse_args()
    if args.attack:
        OUT = bench.CACHE / "travel-scan-resume-attack"
    elif args.disengage:
        OUT = bench.CACHE / "travel-scan-resume-disengage"
    bench.OUT = OUT
    manifest = read(HERE / "TRAVEL_SCAN_ROSTER_NOISE.json")
    row = next(r for r in manifest["affected"] if r["fuel_outs"] == 6)
    seed, opponent, name, side = (row[k] for k in ("noise_seed", "opponent", "map", "side"))
    original = bench.CACHE / f"travel-scan-roster-noise/games/stress-{seed}-{opponent}-{name}-{side}"
    mp = STRESS / "maps" / f"{name}.map26a"
    assert bench.digest(mp) == read(HERE / "LARGE_ROSTER_MAPS.json")["maps"][mp.name]
    filename, digest = bench.OPPS[opponent]
    assert bench.digest(bench.CACHE / filename) == digest
    actor = row["events"][0]["owner"]["id"]
    trace = OUT / "games" / f"profile-{seed}-{opponent}-{name}-{side}"
    project = OUT / f"seed-{seed}"
    if args.recount:
        wasm = project / "bot.wasm"
        doc = read(trace / "native.json")
        match = doc["match"]
        team = "team" + side
        assert match["engineBuildHash"] == bench.ENGINE and doc["diagnostics"]["detailedCaptureComplete"]
        current = {"arm": "profile", "noise_seed": seed, "opponent": opponent, "map": name, "side": side,
                   "engine_seed": match["seed"], "map_hash": match["mapHash"],
                   "faults": doc["diagnostics"]["botFaults"][team], "diagnostic_codes": doc["diagnostics"]["codes"]}
        current = summarize_scoped(current, trace)
    else:
        (OUT / "games").mkdir(parents=True)
        src = OUT / "source/src"
        prepare(src, True)
        if args.attack:
            prepare_attack(src)
        elif args.disengage:
            prepare_disengage(src)
        else:
            prepare_coarse(src, {ROUND}, (*STAGES, "fields", "bushpre"))
        wasm = build(src, project, seed)
        current = play_scoped(("profile", seed, opponent, mp, side, wasm))
    b, c = (read_turn(folder, ROUND, side, actor) for folder in (original, trace))
    assert all(row[k] == current[k] for k in ("noise_seed", "opponent", "map_hash", "engine_seed", "side"))
    result = {"reference": manifest["binaries"][str(seed)], "diagnostic": bench.digest(wasm),
              "same_observation": bool(b and c and b["observation"] == c["observation"]),
              "same_first_two_actions": bool(b and c and b["executed_actions"][:2] == c["executed_actions"][:2]),
              "events": native_fuel(current, OUT), "row": current, "base_turn": b, "trace_turn": c}
    name = ("TRAVEL_RESUME_ATTACK.json" if args.attack else "TRAVEL_RESUME_DISENGAGE.json" if args.disengage else
            "TRAVEL_RESUME_PROFILE.json")
    if args.attack or args.disengage:
        (archive,) = (p for p in trace.glob("*.repl26a") if p.name != "raw.repl26a")
        with ZipFile(archive) as z:
            log = z.read(f"team-{side.lower()}.stdout")
        pattern = (rb"CODEX_RESUME_ATTACK (\d+) (\d+)" if args.attack else
                   rb"CODEX_RESUME_DISENGAGE (\d+) (\d+) (\d+)")
        result["samples"] = [list(map(int, x)) for x in re.findall(pattern, log)]
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if not k.endswith("turn")}, flush=True)


if __name__ == "__main__":
    main()
