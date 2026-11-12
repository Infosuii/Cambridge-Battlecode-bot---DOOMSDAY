"""Localize an independent current111 first-turn crossing with an exact disabled control."""
import os
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI, HERE, SDK_ROOT, read
from freeze_engine3_discovery import write
from profile_live109_target import HEADER, main, prepare


def exact_build(source, project, unused_seed):
    copytree(source, project / "src")
    with (project / "build.log").open("wb") as log:
        subprocess.run([CLI, "build", project, "--release", "--output", project / "bot.wasm"], cwd=SDK_ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    return project / "bot.wasm"


def instrument(source, enabled, case, reference_name="live111"):
    prepare(source, enabled, case, reference_name=reference_name)
    header = HEADER.replace("inline unsigned count = 0;", """inline unsigned count = 0;
inline bool active = false;
inline void begin(int type, int round) { active = type == CODEX_TARGET_TYPE && round == CODEX_TARGET_ROUND; }""")
    header = header.replace("if (type != CODEX_TARGET_TYPE || round != CODEX_TARGET_ROUND || count >= 96)", "if (!active || count >= 96)")
    (source / "codex_trace.h").write_text(f"#define CODEX_TARGET_TYPE {case['type']}\n#define CODEX_TARGET_ROUND 1\n" + header, encoding="utf8", newline="\n")
    path = source / "main.cpp"
    text = path.read_text(encoding="utf8")
    anchor = "                bot.play_turn();"
    assert text.count(anchor) == 2
    text = text.replace(anchor, """#if CODEX_FINE
                codex_trace::begin(static_cast<int>(bc::self().champion_name()), bc::round_number());
                CODEX_FINE_MARK("main_play_begin", 0, 0);
#endif
                bot.play_turn();
                CODEX_FINE_MARK("main_play_end", 0, 0);""")
    path.write_text(text, encoding="utf8", newline="\n")


if __name__ == "__main__":
    rows = read(HERE / "LIVE111_LARGE_DEV_CENSUS.json")["rows"]
    eligible = [(row, event) for row in rows if row["side"] == "A" for event in row["early_events"] if event["round"] == 1 and event["actor"] == 0]
    if not eligible:
        eligible = [(row, event) for row in rows if row["side"] == "A" for event in row["early_events"] if event["round"] == 1]
    row, event = min(eligible, key=lambda p: (p[0]["map_hash"], p[1]["actor"], p[0]["opponent"]))
    directory = bench.CACHE / "live111-first-turn-baseline"
    directory.mkdir(exist_ok=True)
    old = bench.CACHE / "live111-large-development" / row["opponent"] / f"{row['map']}-A-stock111"
    (archive,) = old.glob("*.repl26a")
    replay = directory / "raw.repl26a"
    with ZipFile(archive) as z:
        data = z.read("replay.repl26a")
        if replay.exists(): assert replay.read_bytes() == data
        else:
            with replay.open("xb") as out: out.write(data)
    target = directory / "turn.json"
    subprocess.run(["node", HERE / "trace_turn.mjs", replay, "1", "0", str(event["actor"]), target], cwd=bench.ROOT, env={**os.environ, "NFS_REPLAY_ENGINE": "3.0.0"}, check=True)
    turn = read(target)
    case = {"stage": "first111", "round": 1, "actor": event["actor"], "type": turn["observation"]["actor"]["type"], "champion": event["name"],
            **{key: row[key] for key in ("map", "side", "opponent", "map_hash")}, "traces": {"base": {"path": target.relative_to(bench.ROOT).as_posix(), "sha256": bench.digest(target)}}}
    write(HERE / "LIVE111_FIRST_TURN_PLAN.json", {"selection": "First stable-hash large-dev R1 actor0/sideA event; no official-pool identity", "case": case})
    main(label="first111", cases=[case], prepare_fn=instrument, build_fn=exact_build, expected_hash=read(HERE / "LIVE111_SOURCE_VERIFIED.json")["wasm_sha256"], project_prefix="live111-target")
