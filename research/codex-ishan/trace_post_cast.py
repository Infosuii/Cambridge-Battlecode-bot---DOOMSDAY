"""Measure residual fuel at accepted ability calls in the three exact stress turns."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from large_roster_stress import DENSE_OUT, OUT as STRESS, HERE, bench, native_fuel, read
from pg_camp_reserve import prepare

OUT = bench.CACHE / "post-cast-boundary"
CASES = (
    (DENSE_OUT, "pool_719398", "x3inv", "A", 229, 5, "Heart of Ruin", "heart_of_ruin"),
    (DENSE_OUT, "pool_719496", "p65pack", "A", 26, 3, "Issac", "issac"),
    (STRESS, "pool_604904", "p65pack", "B", 1215, 5, "Vendetta", "vendetta"),
)


def instrument(src):
    condition = " || ".join(f"(round == {round_number} && type == bc::champion_type::{champion})"
                            for _, _, _, _, round_number, _, _, champion in CASES)
    common = src / "common.h"
    with common.open("ab") as f:
        f.write(('''

struct CodexPostCast {
    const char* caller;
    int round;
    unsigned engine_round;
    unsigned long long fuel;
};
inline CodexPostCast codex_post_cast[4];
inline int codex_post_cast_count = 0;
inline void codex_sample_cast(int round, bc::champion_type type, const char* caller) {
    if ((''' + condition + ''') && codex_post_cast_count < 4)
        codex_post_cast[codex_post_cast_count++] = {caller, round, bc::round_number(), bc::fuel_remaining()};
}
''').encode())
    patterns = ("bot.cpp", "pressure.cpp", "tsearch.cpp")
    replaced = 0
    for name in patterns:
        path = src / name
        data = path.read_bytes()
        nl = b"\r\n" if b"\r\n" in data else b"\n"
        lines = data.split(nl)
        for i, line in enumerate(lines):
            if line.strip() == b"cast_done = true;":
                indent = line[:len(line) - len(line.lstrip())]
                lines[i] += nl + indent + b"codex_sample_cast(round, type, __func__);"
            elif line.strip().startswith(b"if (") and line.endswith(b" cast_done = true;"):
                lines[i] = line.replace(b" cast_done = true;", b" { cast_done = true; codex_sample_cast(round, type, __func__); }")
            else:
                continue
            replaced += 1
        path.write_bytes(nl.join(lines))
    assert replaced == 22
    apply(src / "bot.cpp", (("void Bot::play_turn() {", '''void Bot::play_turn() {
    for (int i = 0; i < codex_post_cast_count; ++i) {
        const auto& s = codex_post_cast[i];
        std::printf("CODEX_POST_CAST %s R%d engineR%u fuel%llu\\n", s.caller, s.round, s.engine_round, s.fuel);
    }
    codex_post_cast_count = 0;'''),))


def play(job):
    arm, case, wasm = job
    directory, name, opponent, side, round_number, actor, champion, _ = case
    mp = directory / "maps" / f"{name}.map26a"
    manifest = read(HERE / ("DENSE_ROSTER_MAPS.json" if directory == DENSE_OUT else "LARGE_ROSTER_MAPS.json"))["maps"]
    assert bench.digest(mp) == manifest[mp.name]
    row = bench.one((arm, 0, opponent, mp, side, wasm), log_limit=1048576)
    work = OUT / "games" / f"{arm}-0-{opponent}-{name}-{side}"
    replay, output = work / "raw.repl26a", work / "turn.json"
    with ZipFile(next(work.glob("*.repl26a"))) as bundle:
        replay.write_bytes(bundle.read("replay.repl26a"))
        log = bundle.read(f"team-{side.lower()}.stdout")
    with (work / "turn.log").open("wb") as f:
        rc = subprocess.run(["node", HERE / "trace_turn.mjs", replay, str(round_number), str("AB".index(side)), str(actor), output],
                            cwd=bench.ROOT, stdout=f, stderr=subprocess.STDOUT,
                            env={**os.environ, "NFS_REPLAY_ENGINE": "2.0.0"}).returncode
    state = read(output) if rc == 0 else None
    if state:
        state["observation"].pop("input")
    events = {(e["owner"]["name"], e["timestamp"]["round"]) for e in native_fuel(row, OUT)}
    markers = [v.decode("ascii") for v in re.findall(rb"CODEX_POST_CAST [^\n]+", log)]
    return {**row, "target_event": (champion, round_number) in events, "markers": markers, "state": state}


def main():
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    project = OUT / "diagnostic"
    src = project / "src"
    prepare(src, True)
    instrument(src)
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    exact = bench.ROOT / "bots/codex-pg-camp-reserve/bot.wasm"
    assert bench.digest(exact) == read(HERE / "PG_CAMP_RESERVE_BUILDS.json")["primary"]
    for o in {c[2] for c in CASES}:
        file, expected = bench.OPPS[o]
        assert bench.digest(bench.CACHE / file) == expected
    jobs = [(arm, case, bin) for case in CASES for arm, bin in (("exact", exact), ("trace", wasm))]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(play, jobs))
    joins = []
    for a, b in zip(rows[::2], rows[1::2], strict=True):
        assert all(a[k] == b[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
        joins.append({"map": a["map"], "target_event": a["target_event"] and b["target_event"], "markers": b["markers"],
                      "same_observation": bool(a["state"] and b["state"] and a["state"]["observation"] == b["state"]["observation"]),
                      "same_first_action": bool(a["state"] and b["state"] and a["state"]["executed_actions"][:1] == b["state"]["executed_actions"][:1])})
    result = {"release": bench.digest(exact), "trace": bench.digest(wasm), "joins": joins}
    with (HERE / "POST_CAST_BOUNDARY.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
