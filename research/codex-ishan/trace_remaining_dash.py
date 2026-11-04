"""Capture a single exact dash boundary without logging in the low-fuel turn."""
import json
import os
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from large_roster_stress import HERE, OUT as STRESS, bench, read
from pg_siege_resume import prepare

OUT = bench.CACHE / "remaining-dash-1215"
MAP = "pool_604904"


def state(game, output):
    replay = output.with_suffix(".repl26a")
    with ZipFile(next(game.glob("*.repl26a"))) as bundle:
        replay.write_bytes(bundle.read("replay.repl26a"))
    subprocess.run(["node", HERE / "trace_turn.mjs", replay, "1215", "1", "5", output], cwd=bench.ROOT,
                   env={**os.environ, "NFS_REPLAY_ENGINE": "2.0.0"}, check=True)
    result = read(output)
    result["observation"].pop("input")
    return result


def main():
    project = OUT / "diagnostic"
    src = project / "src"
    prepare(src, True)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    begin = data.index(b"bool Bot::try_dash(")
    end = data.index(b"bool Bot::follow_field(", begin)
    marker = nl.join([b"                cast_done = true;", b"                return true;"])
    injected = nl.join([b"                cast_done = true;",
                        b"                if (round == 1215 && type == bc::champion_type::vendetta)",
                        b"                    codex_dash = {true, bc::round_number(), bc::fuel_remaining(), pos};",
                        b"                return true;"])
    section = data[begin:end]
    assert section.count(marker) == 1
    bot.write_bytes(data[:begin] + section.replace(marker, injected) + data[end:])
    apply(bot, (
        ('#include "bot.h"', '''#include "bot.h"

static struct CodexDashSample {
    bool pending = false;
    std::uint32_t engine_round = 0;
    std::uint64_t fuel = 0;
    vec2 destination{};
} codex_dash;'''),
        ("void Bot::play_turn() {", '''void Bot::play_turn() {
    if (codex_dash.pending) {
        std::printf("CODEX_DASH_BOUNDARY engineR%u fuel%llu (%d,%d)\\n", codex_dash.engine_round,
                    static_cast<unsigned long long>(codex_dash.fuel), codex_dash.destination.x, codex_dash.destination.y);
        codex_dash.pending = false;
    }'''),
    ))
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    map_file = STRESS / "maps" / f"{MAP}.map26a"
    assert bench.digest(map_file) == read(HERE / "LARGE_ROSTER_MAPS.json")["maps"][map_file.name]
    opponent, expected = bench.OPPS["p65pack"]
    assert bench.digest(bench.CACHE / opponent) == expected
    bench.OUT = OUT
    (OUT / "games").mkdir()
    row = bench.one(("trace", 0, "p65pack", map_file, "B", wasm), log_limit=1048576)
    game = OUT / "games" / f"trace-0-p65pack-{MAP}-B"
    baseline = bench.CACHE / f"pg-siege-resume-exact-stress/games/exact-0-p65pack-{MAP}-B"
    base_state, trace_state = (state(p, OUT / f"{tag}.json") for tag, p in (("baseline", baseline), ("observed", game)))
    with ZipFile(next(game.glob("*.repl26a"))) as bundle:
        log = bundle.read("team-b.stdout")
    samples = [x.decode("ascii") for x in re.findall(rb"CODEX_DASH_BOUNDARY [^\n]+", log)]
    report = {"wasm": bench.digest(wasm), "row": row, "samples": samples,
              "same_observation": base_state["observation"] == trace_state["observation"],
              "same_first_action": base_state["executed_actions"][:1] == trace_state["executed_actions"][:1],
              "baseline_actions": base_state["executed_actions"], "trace_actions": trace_state["executed_actions"]}
    with (HERE / "REMAINING_DASH_TRACE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(report, out, indent=2)
        out.write("\n")
    print({k: v for k, v in report.items() if not k.endswith("actions")}, flush=True)


if __name__ == "__main__":
    main()
