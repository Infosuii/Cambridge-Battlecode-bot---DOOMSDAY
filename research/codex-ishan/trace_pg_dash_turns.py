"""Re-run the two exact development suspensions with scoped charged markers."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from pg_dash_camps import prepare, read
import profile_pg_runtime as trace
from qualify_local import partition

HERE = Path(__file__).resolve().parent
OUT = bench.CACHE / "pg-dash-scoped-trace"
CASES = (
    ("marcella", 47, 10, "v92", "pf_pool_77068", "B"),
    ("vendetta", 659, 0, "x3inv", "pf_pool_77082", "A"),
)


def probe(case, maps):
    champion, round_number, actor, opponent, map_name, side = case
    project = OUT / champion
    src = project / "src"
    prepare(src, True, True, True)
    apply(src / "common.h", (
        ("inline bc::champion_type who{};\ninline void mark(const char* where) {",
         "inline bc::champion_type who{};\ninline bool pg_target_turn = false;\ninline void mark(const char* where) {\n"
         "    if (!pg_target_turn) return;"),
        ("    TurnGuard() {\n        turn_round = bc::round_number();\n        nt = 0;",
         "    explicit TurnGuard(bc::champion_type actor) {\n        turn_round = bc::round_number();\n"
         f"        pg_target_turn = turn_round == {round_number} && actor == bc::champion_type::{champion};\n"
         "        if (!pg_target_turn) return;\n        who = actor;\n        nt = 0;"),
        ("    ~TurnGuard() {\n        mark(\"end\");", "    ~TurnGuard() {\n        if (!pg_target_turn) return;\n        mark(\"end\");"),
        ("        if (now == turn_round) {\n            td_dump(static_cast<int>(now));\n            return;\n        }\n", ""),
    ))
    apply(src / "bot.cpp", (
        ("    a2tel::TurnGuard a2_guard;", "    a2tel::TurnGuard a2_guard{type};"),
        ("    if (ward_reveal()) w.update(round); // the ward shows the bush now: look again",
         "    if (ward_reveal()) {\n        PROF_CHECK(\"ward_refresh\");\n        w.update(round);\n    }"),
    ))
    wasm = project / "bot.wasm"
    with (project / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    row = bench.one(("scoped", 0, opponent, maps[map_name], side, wasm), log_limit=trace.LIMIT)
    game = OUT / "games" / f"scoped-0-{opponent}-{map_name}-{side}"
    replay = game / "raw.repl26a"
    with ZipFile(next(game.glob("*.repl26a"))) as archive:
        log = archive.read(f"team-{side.lower()}.stdout")
        replay.write_bytes(archive.read("replay.repl26a"))
    pattern = rb"A2SUS R" + str(round_number).encode() + rb" t\d+ to R\d+:[^\n]+"
    captures = [m.decode("utf8", "replace") for m in re.findall(pattern, log)]
    native = read(game / "native.json")
    events = [(e["owner"]["name"], x["timestamp"]["round"]) for e in native["events"]
              if e["kind"] == "fuelExhausted" and e["owner"]["team"] == "team" + side for x in e["entries"]]
    return {"case": case, "wasm": bench.digest(wasm), "row": row, "captures": captures, "native_events": events}


def main():
    maps = {p.stem: p for p in partition("dev")}
    for _, _, _, opponent, _, _ in CASES:
        name, sha = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / name) == sha
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(lambda case: probe(case, maps), CASES))
    with (HERE / "PG_DASH_SCOPED.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(rows, f, indent=2)
        f.write("\n")
    print(json.dumps(rows, indent=2), flush=True)


if __name__ == "__main__":
    main()
