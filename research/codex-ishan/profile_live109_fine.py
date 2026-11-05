"""Buffer charged method boundaries for the matched current-line failure turns."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import CLI, HERE, SDK_ROOT, read
from engine3_qualify import build
from freeze_engine3_discovery import write
from qualify_local import partition

HEADER = r'''#pragma once
#if CODEX_FINE
#include <cstdio>
namespace codex_trace {
struct Record { const char* name; unsigned actual; unsigned long long fuel; long long a, b; };
inline Record records[64];
inline unsigned count = 0;
inline int expected = 0, champion = 0;
inline bool tracked(int type, int round) {
    return (type == 2 && round == 46) || (type == 4 && round == 66) ||
           (type == 3 && round == 17) || (type == 12 && (round == 179 || round == 285));
}
inline void mark(const char* name, int type, int round, long long a = 0, long long b = 0) {
    if (!tracked(type, round) || count >= 64) return;
    expected = round; champion = type;
    records[count++] = {name, bc::round_number(), bc::fuel_remaining(), a, b};
}
inline void flush() {
    for (unsigned i = 0; i < count; ++i) {
        const auto& v = records[i];
        std::printf("CODEX_FINE R%d T%d %s %u %llu %lld %lld\n", expected, champion, v.name, v.actual, v.fuel, v.a, v.b);
    }
    count = 0;
}
}
#define CODEX_FINE_MARK(...) codex_trace::mark(__VA_ARGS__)
#define CODEX_FINE_FLUSH() codex_trace::flush()
#else
#define CODEX_FINE_MARK(...) ((void)0)
#define CODEX_FINE_FLUSH() ((void)0)
#endif
'''


def scoped(path, start, end, edits):
    data = path.read_text(encoding="utf8")
    first = data.index(start)
    last = data.index(end, first) if end else len(data)
    body = data[first:last]
    for old, new in edits:
        assert body.count(old) == 1, (path.name, old, body.count(old))
        body = body.replace(old, new, 1)
    path.write_text(data[:first] + body + data[last:], encoding="utf8", newline="\n")


def prepare(target, enabled, reference_name="live109"):
    source = SDK_ROOT / "bots" / reference_name / "src"
    identity = read(HERE / f"{reference_name.upper()}_SOURCE_VERIFIED.json")
    assert all(bench.digest(source / name) == value for name, value in identity["source_file_hashes"].items())
    copytree(source, target)
    header = target / "common.h"
    header.write_bytes(f"#define CODEX_FINE {int(enabled)}\n".encode() + header.read_bytes())
    (target / "codex_trace.h").write_text(HEADER, encoding="utf8", newline="\n")
    for name in ("main.cpp", "bot.cpp", "nnrec.cpp"):
        apply(target / name, (('#include "bot.h"', '#include "bot.h"\n#include "codex_trace.h"'),))
    apply(target / "main.cpp", (("        bc::end_turn();", "        codex_trace::flush();\n        bc::end_turn();"),))
    path = target / "bot.cpp"
    data = path.read_text(encoding="utf8")
    data = re.sub(r'PROF_CHECK\("([a-zA-Z0-9_]+)"\);', r'PROF_CHECK("\1"); codex_trace::mark("\1", static_cast<int>(type), round);', data)
    for signature, name in (("bool Bot::fight_camps(GroupRec& g, int need) {", "fight_in"),
                            ("bool Bot::walk_toward(const bc::bitboard& goals_in) {", "walk_in"),
                            ("bool Bot::follow_field(const bc::distance_field& field, const bc::bitboard& blocked, bool allow_dash) {", "follow_in"),
                            ("bool Bot::cast_camp_strike(int ci) {", "strike_in"), ("bool Bot::cast_on_camp(int ci) {", "castcamp_in")):
        assert data.count(signature) == 1, signature
        data = data.replace(signature, signature + f'\n    codex_trace::mark("{name}", static_cast<int>(type), round);', 1)
    path.write_text(data, encoding="utf8", newline="\n")
    path = target / "nnrec.cpp"
    scoped(path, "void Bot::nn_lazy_score() {", "#ifdef A2_NN_FCMP", (
        ("    static bool first_camps = true;", '    codex_trace::mark("lazy_in", static_cast<int>(type), round);\n    static bool first_camps = true;'),
        ("    std::uint64_t enemy_used = 0;", '    codex_trace::mark("lazy_gate", static_cast<int>(type), round, nn_est_camps, floor_f);\n    std::uint64_t enemy_used = 0;'),
        ("#define cmark(i)\n", '#define cmark(i) codex_trace::mark("lazy" #i, static_cast<int>(type), round)\n'),
        ("        const std::uint64_t f1 = bc::fuel_remaining();\n        if (bc::round_number() != r0 || f1 > f0) {\n            nn_est_camps", '        codex_trace::mark("lazy_pub", static_cast<int>(type), round);\n        const std::uint64_t f1 = bc::fuel_remaining();\n        if (bc::round_number() != r0 || f1 > f0) {\n            nn_est_camps'),
    ))
    scoped(path, "void Bot::nn_turn_end() {", None, (
        ("    nn_spent = 0;", '    codex_trace::mark("end_in", static_cast<int>(type), round, nn_warm, w.groups.size());\n    nn_spent = 0;'),
        ("            nn_feats_t<kC, kAF>(nn_lf, nn_near(), 3);", '            codex_trace::mark("warm_feats_begin", static_cast<int>(type), round, nn_warm, w.groups.size());\n            nn_feats_t<kC, kAF>(nn_lf, nn_near(), 3);\n            codex_trace::mark("warm_feats_end", static_cast<int>(type), round);'),
        ("            nn::live_camps(nn_lf, nn_lv, w.groups.size());", '            codex_trace::mark("warm_camps_begin", static_cast<int>(type), round, nn_warm, w.groups.size());\n            nn::live_camps(nn_lf, nn_lv, w.groups.size());\n            codex_trace::mark("warm_camps_end", static_cast<int>(type), round);'),
        ("            nn::live_rebuild(nn_lv);", '            codex_trace::mark("rebuild_begin", static_cast<int>(type), round);\n            nn::live_rebuild(nn_lv);\n            codex_trace::mark("rebuild_end", static_cast<int>(type), round);'),
        ("            nn_x_refresh(x);", '            codex_trace::mark("x_begin", static_cast<int>(type), round, x, nn_xest[x]);\n            nn_x_refresh(x);\n            codex_trace::mark("x_end", static_cast<int>(type), round, x, nn_xest[x]);'),
    ))
    scoped(path, "void Bot::nn_x_refresh(int x) {", "#endif", (
        ("    nn_feats_t<kC, kAF>(nn_lf, nn_near(), kXPart[x]);", '    codex_trace::mark("x_feats_begin", static_cast<int>(type), round, x);\n    nn_feats_t<kC, kAF>(nn_lf, nn_near(), kXPart[x]);\n    codex_trace::mark("x_feats_end", static_cast<int>(type), round, x);'),
        ("    nn::live_block(nn_lf, nn_lv, kXOrder[x]);", '    codex_trace::mark("x_block_begin", static_cast<int>(type), round, x);\n    nn::live_block(nn_lf, nn_lv, kXOrder[x]);\n    codex_trace::mark("x_block_end", static_cast<int>(type), round, x);'),
    ))
    for name in ("main.cpp", "bot.cpp", "nnrec.cpp"):
        path = target / name
        data = path.read_text(encoding="utf8").replace("codex_trace::mark(", "CODEX_FINE_MARK(").replace("codex_trace::flush()", "CODEX_FINE_FLUSH()")
        path.write_text(data, encoding="utf8", newline="\n")


def main():
    output = bench.CACHE / "engine3-live109-runtime-fine-r3"
    output.mkdir()
    source, off_source = output / "source", output / "off-source"
    prepare(source, True)
    prepare(off_source, False)
    off = build(off_source, SDK_ROOT / "bots/live109-fine-r3-off-11801", 11801)
    expected = read(HERE / "ENGINE3_LIVE109_GREEDY_DEV.json")["binaries"]["base-11801"]
    assert bench.digest(off) == expected
    wasm = build(source, SDK_ROOT / "bots/live109-fine-r3-11801", 11801)
    cases = read(HERE / "LIVE109_RUNTIME_MATCHED_TURNS.json")["rows"]
    jobs = sorted({(r["map"], r["side"], r["opponent"]) for r in cases})
    maps = {mp.stem: mp for mp in partition("dev")}
    write(HERE / "LIVE109_RUNTIME_FINE_PLAN.json", {"diagnostic": bench.digest(wasm), "off": bench.digest(off), "cases": cases, "jobs": jobs})

    def run(job):
        map_name, side, opponent = job
        directory = output / f"{map_name}-{side}-{opponent}"
        directory.mkdir()
        mp, reference = maps[map_name], bench.CACHE / bench.OPPS[opponent][0]
        assert bench.digest(reference) == bench.OPPS[opponent][1]
        bots = (wasm, reference) if side == "A" else (reference, wasm)
        with (directory / "run.log").open("wb") as log:
            subprocess.run([CLI, "run", *bots, "--map", mp, "--release", "--fuel", "100000", "--log-limit", "1048576", "--json", "--statistics", directory / "native.json", "--out-dir", directory], cwd=SDK_ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
        (bundle,) = directory.glob("*.repl26a")
        with ZipFile(bundle) as archive:
            stdout = archive.read(f"team-{side.lower()}.stdout").replace(b"\0", b"")
        assert len(stdout) < 1048576
        samples = [{"round": int(r), "type": int(t), "mark": name.decode(), "actual_round": int(actual), "fuel": int(fuel), "a": int(a), "b": int(b)}
                   for r, t, name, actual, fuel, a, b in re.findall(rb"CODEX_FINE R(\d+) T(\d+) (\w+) (\d+) (\d+) (-?\d+) (-?\d+)", stdout)]
        return {"map": map_name, "side": side, "opponent": opponent, "directory": directory.relative_to(bench.ROOT).as_posix(), "samples": samples}

    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(run, jobs))
    report = {"diagnostic": bench.digest(wasm), "off_matches_recorded_baseline": True, "rows": rows}
    write(HERE / "LIVE109_RUNTIME_FINE.json", report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
