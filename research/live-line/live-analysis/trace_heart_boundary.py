"""Sample only the Heart camp strike in the registered dense stress turn."""
import argparse
import json
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from large_roster_stress import HERE, bench, read
from pg_camp_reserve import prepare
from pg_dash_followup import read_turn
from trace_post_cast import CASES, play
import trace_post_cast


def instrument(src, retarget, attack, error):
    bot = src / "bot.cpp"
    marker = "bool Bot::cast_camp_strike(int ci) {"
    end = "bool Bot::cast_on_camp(int ci) {"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start_idx, end_idx = data.index(marker.encode()), data.index(end.encode())
    segment = data[start_idx:end_idx]
    call = b"            if (bc::self().abilities()[s].use(best)) {"
    assert segment.count(call) == 1
    segment = segment.replace(call, nl.join((
        b"            if (round == 229) codex_heart_before = bc::fuel_remaining();",
        call,
        b"                if (round == 229) codex_heart_after = bc::fuel_remaining();",
    )))
    bot.write_bytes(data[:start_idx] + segment + data[end_idx:])
    apply(bot, (
        (marker, """static unsigned long long codex_heart_before, codex_heart_after;

bool Bot::cast_camp_strike(int ci) {"""),
        ("void Bot::play_turn() {", """void Bot::play_turn() {
    if (codex_heart_before || codex_heart_after) {
        std::printf("CODEX_HEART_BOUNDARY %llu %llu\\n", codex_heart_before, codex_heart_after);
        codex_heart_before = codex_heart_after = 0;
    }"""),
    ))
    if retarget:
        apply(bot, (
            ("static unsigned long long codex_heart_before, codex_heart_after;",
             "static unsigned long long codex_heart_before, codex_heart_after, codex_heart_step[5];"),
            ("    if (cast_on_camp(t)) {", """    if (cast_on_camp(t)) {
        if (codex_heart_after) codex_heart_step[0] = bc::fuel_remaining();"""),
            ("                w.camps[t].hp = fresh.health;", """                if (codex_heart_after) codex_heart_step[1] = bc::fuel_remaining();
                w.camps[t].hp = fresh.health;"""),
            ("            w.camps[t].dead = true;\n            t = pick_target();\n        }\n        if (t < 0) return true;",
             """            w.camps[t].dead = true;
            if (codex_heart_after) codex_heart_step[2] = bc::fuel_remaining();
            t = pick_target();
        }
        if (codex_heart_after) codex_heart_step[3] = bc::fuel_remaining();
        if (t < 0) return true;"""),
            ('    PROF_CHECK("c_cast"); if (attack_unit(w.camps[t].camp, w.camps[t].pos)) {',
             '''    if (codex_heart_after) codex_heart_step[4] = bc::fuel_remaining();
    PROF_CHECK("c_cast"); if (attack_unit(w.camps[t].camp, w.camps[t].pos)) {'''),
            ("        codex_heart_before = codex_heart_after = 0;", """        std::printf("CODEX_HEART_BOUNDARY steps %llu %llu %llu %llu %llu\\n",
                    codex_heart_step[0], codex_heart_step[1], codex_heart_step[2], codex_heart_step[3], codex_heart_step[4]);
        codex_heart_before = codex_heart_after = 0;"""),
        ))
    if attack:
        apply(bot, (
            ("static unsigned long long codex_heart_before, codex_heart_after;", ""),
            ("bool Bot::attack_unit(const bc::unit& target, vec2 where) {", """static unsigned long long codex_heart_before, codex_heart_after, codex_heart_attack[5];

bool Bot::attack_unit(const bc::unit& target, vec2 where) {
    if (codex_heart_after) codex_heart_attack[0] = bc::fuel_remaining();"""),
            ("    if (!me.can_attack() || cheb(pos, where) > range) return false;\n    try {\n        me.attack(target);",
             """    if (!me.can_attack() || cheb(pos, where) > range) {
        if (codex_heart_after) codex_heart_attack[1] = bc::fuel_remaining();
        return false;
    }
    if (codex_heart_after) codex_heart_attack[2] = bc::fuel_remaining();
    try {
        me.attack(target);
        if (codex_heart_after) codex_heart_attack[3] = bc::fuel_remaining();"""),
            ('        LOG("attack error %s\\n", e.what());', '''        if (codex_heart_after) codex_heart_attack[4] = bc::fuel_remaining();
        LOG("attack error %s\\n", e.what());'''),
            ("        codex_heart_before = codex_heart_after = 0;", """        std::printf("CODEX_HEART_BOUNDARY attack %llu %llu %llu %llu %llu\\n",
                    codex_heart_attack[0], codex_heart_attack[1], codex_heart_attack[2], codex_heart_attack[3], codex_heart_attack[4]);
        codex_heart_before = codex_heart_after = 0;"""),
        ))
    if error:
        apply(bot, (
            ("static unsigned long long codex_heart_before, codex_heart_after, codex_heart_attack[5];",
             """static unsigned long long codex_heart_before, codex_heart_after, codex_heart_attack[5];
static int codex_heart_error = -1;"""),
            ("        if (codex_heart_after) codex_heart_attack[4] = bc::fuel_remaining();",
             """        if (codex_heart_after) {
            codex_heart_attack[4] = bc::fuel_remaining();
            if (const auto* failure = dynamic_cast<const bc::error*>(&e))
                codex_heart_error = static_cast<int>(failure->code());
        }"""),
            ("        codex_heart_before = codex_heart_after = 0;", """        std::printf("CODEX_HEART_BOUNDARY error %d\\n", codex_heart_error);
        codex_heart_before = codex_heart_after = 0;"""),
        ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--retarget", action="store_true")
    modes.add_argument("--attack", action="store_true")
    modes.add_argument("--error", action="store_true")
    args = parser.parse_args()
    phase = next((phase for phase in ("retarget", "attack", "error") if getattr(args, phase)), "cast")
    name = f"heart-{phase}-boundary"
    out = bench.CACHE / name
    (out / "games").mkdir(parents=True)
    bench.OUT = trace_post_cast.OUT = out
    project = out / "diagnostic"
    prepare(project / "src", True)
    instrument(project / "src", args.retarget, args.attack or args.error, args.error)
    wasm = project / "bot.wasm"
    with (out / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm],
                       cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    case = CASES[0]
    _, mp, opponent, side, round_number, actor, _, _ = case
    file, digest = bench.OPPS[opponent]
    assert bench.digest(bench.CACHE / file) == digest
    row = play(("trace", case, wasm))
    work = out / "games" / f"trace-0-{opponent}-{mp}-{side}"
    prior = bench.CACHE / "pg-dash-followup-stress/games" / f"base-0-{opponent}-{mp}-{side}"
    old = read_turn(prior, round_number, side, actor)
    new = row["state"]
    with ZipFile(next(work.glob("*.repl26a"))) as bundle:
        log = bundle.read(f"team-{side.lower()}.stdout")
    markers = [v.decode("ascii") for v in re.findall(rb"CODEX_HEART_BOUNDARY [^\n]+", log)]
    result = {"wasm": bench.digest(wasm), "target_event": row["target_event"], "markers": markers,
              "same_observation": bool(old and new and old["observation"] == new["observation"]),
              "same_first_two_actions": bool(old and new and old["executed_actions"][:2] == new["executed_actions"][:2]),
              "row": row}
    with (HERE / f"{name.upper().replace('-', '_')}.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k != "row"})


if __name__ == "__main__":
    main()
