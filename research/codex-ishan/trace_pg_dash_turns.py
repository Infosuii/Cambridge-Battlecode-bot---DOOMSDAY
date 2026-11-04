"""Re-run the two exact development suspensions with scoped charged markers."""
import argparse
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


def prepare_scoped(src, champion, round_number):
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


def prepare_move(src, champion, round_number):
    prepare(src, True, True, False)
    path = src / "bot.cpp"
    data = path.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    addition = (f"if (round == {round_number} && type == bc::champion_type::{champion}) "
                'std::printf("CODEX_MOVE %s R%d engineR%u (%d,%d) fuel%llu mode=%s\\n", '
                '__func__, round, bc::round_number(), pos.x, pos.y, '
                'static_cast<unsigned long long>(bc::fuel_remaining()), mode);').encode()
    lines = data.split(nl)
    count = 0
    for i, line in enumerate(lines):
        if line.strip() == b"walked = true;":
            indentation = line[:len(line) - len(line.lstrip())]
            lines[i] = line + nl + indentation + addition
            count += 1
    assert count == 12
    path.write_bytes(nl.join(lines))


def probe(case, maps, mode):
    champion, round_number, actor, opponent, map_name, side = case
    project = bench.OUT / champion
    src = project / "src"
    (prepare_move if mode == "move" else prepare_scoped)(src, champion, round_number)
    wasm = project / "bot.wasm"
    with (project / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    row = bench.one(("scoped", 0, opponent, maps[map_name], side, wasm), log_limit=trace.LIMIT)
    game = bench.OUT / "games" / f"scoped-0-{opponent}-{map_name}-{side}"
    replay = game / "raw.repl26a"
    with ZipFile(next(game.glob("*.repl26a"))) as archive:
        log = archive.read(f"team-{side.lower()}.stdout")
        replay.write_bytes(archive.read("replay.repl26a"))
    pattern = (rb"CODEX_MOVE [^\n]+" if mode == "move" else
               rb"A2SUS R" + str(round_number).encode() + rb" t\d+ to R\d+:[^\n]+")
    captures = [m.decode("utf8", "replace") for m in re.findall(pattern, log)]
    native = read(game / "native.json")
    events = [(e["owner"]["name"], x["timestamp"]["round"]) for e in native["events"]
              if e["kind"] == "fuelExhausted" and e["owner"]["team"] == "team" + side for x in e["entries"]]
    return {"case": case, "wasm": bench.digest(wasm), "row": row, "captures": captures, "native_events": events}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--move", action="store_true")
    args = parser.parse_args()
    mode = "move" if args.move else "scoped"
    maps = {p.stem: p for p in partition("dev")}
    for _, _, _, opponent, _, _ in CASES:
        name, sha = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / name) == sha
    bench.OUT = bench.CACHE / "pg-dash-move-trace-r2" if args.move else OUT
    (bench.OUT / "games").mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(lambda case: probe(case, maps, mode), CASES))
    with (HERE / f"PG_DASH_{mode.upper()}.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(rows, f, indent=2)
        f.write("\n")
    print(json.dumps(rows, indent=2), flush=True)


if __name__ == "__main__":
    main()
