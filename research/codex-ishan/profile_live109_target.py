"""Measure one actor-turn per ordinary-budget diagnostic and defer buffered output."""
from concurrent.futures import ThreadPoolExecutor
import os
import re
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import CLI, ENGINE, HERE, SDK_ROOT, read
from engine3_qualify import build
from freeze_engine3_discovery import write
from profile_live109_fine import prepare as prepare_fine
from qualify_local import partition
from turn_prefix import action_prefix

HEADER = r'''#pragma once
#if CODEX_FINE
#include <cstdio>
namespace codex_trace {
struct Record { const char* name; unsigned actual; unsigned long long fuel; long long a, b; };
inline Record records[96];
inline unsigned count = 0;
inline void mark(const char* name, int type, int round, long long a = 0, long long b = 0) {
    if (type != CODEX_TARGET_TYPE || round != CODEX_TARGET_ROUND || count >= 96) return;
    records[count++] = {name, bc::round_number(), bc::fuel_remaining(), a, b};
}
inline char buffer[16384];
inline char* put_s(char* p, const char* s) { while (*s) *p++ = *s++; return p; }
inline char* put_i(char* p, long long value) {
    if (value < 0) { *p++ = '-'; value = -value; }
    char digits[24]; unsigned n = 0;
    do { digits[n++] = static_cast<char>('0' + value % 10); value /= 10; } while (value);
    while (n) *p++ = digits[--n];
    return p;
}
inline void flush() {
    char* p = buffer;
    for (unsigned i = 0; i < count; ++i) {
        const auto& v = records[i];
        p = put_s(p, "CODEX_FINE R"); p = put_i(p, CODEX_TARGET_ROUND);
        p = put_s(p, " T"); p = put_i(p, CODEX_TARGET_TYPE); *p++ = ' ';
        p = put_s(p, v.name); *p++ = ' '; p = put_i(p, v.actual); *p++ = ' ';
        p = put_i(p, v.fuel); *p++ = ' '; p = put_i(p, v.a); *p++ = ' '; p = put_i(p, v.b); *p++ = '\n';
    }
    std::fwrite(buffer, 1, static_cast<std::size_t>(p - buffer), stdout);
    count = 0;
}
}
#define CODEX_FINE_MARK(...) codex_trace::mark(__VA_ARGS__)
#else
#define CODEX_FINE_MARK(...) ((void)0)
#endif
'''


def prepare(src, enabled, case, reference_name="live109"):
    prepare_fine(src, enabled, reference_name=reference_name)
    (src / "codex_trace.h").write_text(f"#define CODEX_TARGET_TYPE {case['type']}\n#define CODEX_TARGET_ROUND {case['round']}\n" + HEADER, encoding="utf8", newline="\n")
    apply(src / "main.cpp", (("        CODEX_FINE_FLUSH();", """#if CODEX_FINE
        if (codex_trace::count) {
            // The policy work is finished. Emit only in the next ordinary charged turn, then stop this diagnostic.
            bc::end_turn();
            codex_trace::flush();
            bc::resign();
        }
#endif"""),))
    apply(src / "nnrec.cpp", (("#define NN_FPROF(s)\n", '#define NN_FPROF(s) CODEX_FINE_MARK("feat" #s, static_cast<int>(type), round)\n'),))


def main(*, label="r4", cases=None, prepare_fn=prepare, build_fn=build, expected_hash=None, project_prefix="live109-target"):
    output = bench.CACHE / f"engine3-live109-runtime-target-{label}"
    output.mkdir()
    cases = cases or read(HERE / "LIVE109_RUNTIME_MATCHED_TURNS.json")["rows"]
    off_source = output / "off-source"
    prepare_fn(off_source, False, cases[0])
    off = build_fn(off_source, SDK_ROOT / "bots" / f"{project_prefix}-{label}-off-11801", 11801)
    expected = expected_hash or read(HERE / "ENGINE3_LIVE109_GREEDY_DEV.json")["binaries"]["base-11801"]
    assert bench.digest(off) == expected
    maps = {mp.stem: mp for mp in partition("dev")}

    def run(case):
        stage_label = case["stage"].replace("->", "-")
        source = output / ("source-" + stage_label)
        prepare_fn(source, True, case)
        wasm = build_fn(source, SDK_ROOT / "bots" / f"{project_prefix}-{label}-{stage_label}-11801", 11801)
        directory = output / ("game-" + stage_label)
        directory.mkdir()
        side, opponent = case["side"], case["opponent"]
        mp, reference = maps[case["map"]], bench.CACHE / bench.OPPS[opponent][0]
        assert bench.digest(mp) == case["map_hash"] and bench.digest(reference) == bench.OPPS[opponent][1]
        bots = (wasm, reference) if side == "A" else (reference, wasm)
        with (directory / "run.log").open("wb") as log:
            subprocess.run([CLI, "run", *bots, "--map", mp, "--release", "--fuel", "100000", "--rounds", str(case["round"] + 32), "--log-limit", "1048576", "--json", "--statistics", directory / "native.json", "--out-dir", directory], cwd=SDK_ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
        native = read(directory / "native.json")
        assert (native["match"]["engineVersion"], native["match"]["engineBuildHash"]) == ("3.0.0", ENGINE)
        assert native["match"]["mapHash"] == case["map_hash"] and native["diagnostics"]["detailedCaptureComplete"]
        (bundle,) = directory.glob("*.repl26a")
        with ZipFile(bundle) as archive:
            stdout = archive.read(f"team-{side.lower()}.stdout").replace(b"\0", b"")
            replay = directory / "raw.repl26a"
            with replay.open("xb") as out:
                out.write(archive.read("replay.repl26a"))
        assert len(stdout) < 1048576
        samples = [{"mark": name.decode(), "actual_round": int(actual), "fuel": int(fuel), "a": int(a), "b": int(b)}
                   for r, t, name, actual, fuel, a, b in re.findall(rb"CODEX_FINE R(\d+) T(\d+) (\w+) (\d+) (\d+) (-?\d+) (-?\d+)", stdout)
                   if int(r) == case["round"] and int(t) == case["type"]]
        target = directory / "turn.json"
        subprocess.run(["node", HERE / "trace_turn.mjs", replay, str(case["round"]), str(int(side == "B")), str(case["actor"]), target], cwd=bench.ROOT, env={**os.environ, "NFS_REPLAY_ENGINE": "3.0.0"}, stdout=subprocess.DEVNULL, check=True)
        turn = read(target)
        baseline = read(bench.ROOT / case["traces"]["base"]["path"])
        for data in (turn, baseline):
            data["observation"].pop("input")
        prefix = action_prefix
        matched = turn["observation"] == baseline["observation"] and prefix(turn) == prefix(baseline)
        own_events = [entry["timestamp"]["round"] for event in native["events"] if event["kind"] == "fuelExhausted" and event["owner"]["id"] == case["actor"] and event["owner"]["team"] == "team" + side for entry in event["entries"]]
        crossings = [{"from": a["mark"], "to": b["mark"], "start": a, "end": b,
                      "charged_spend": 100000 * (b["actual_round"] - a["actual_round"]) + a["fuel"] - b["fuel"]}
                     for a, b in zip(samples, samples[1:]) if b["actual_round"] != a["actual_round"]]
        return {"case": case, "diagnostic": bench.digest(wasm), "directory": directory.relative_to(bench.ROOT).as_posix(),
                "same_own_view": turn["observation"] == baseline["observation"], "same_action_prefix": prefix(turn) == prefix(baseline),
                "matched_view_and_prefix": matched, "same_native_actor_round": case["round"] in own_events,
                "native_rounds": own_events, "turn_sha256": bench.digest(target), "samples": samples, "buffered_crossings": crossings}

    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(run, cases))
    report = {"engine": ENGINE, "off_matches_recorded_baseline": True, "off": bench.digest(off), "rows": rows}
    write(HERE / f"LIVE109_RUNTIME_TARGET_{label.upper()}.json", report)
    print({"matched": sum(r["matched_view_and_prefix"] and r["same_native_actor_round"] for r in rows), "n": len(rows),
           "crossings": [{"stage": r["case"]["stage"], "matched": r["matched_view_and_prefix"], "crossings": r["buffered_crossings"]} for r in rows]}, flush=True)


if __name__ == "__main__":
    main()
