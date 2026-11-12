"""Prepare a separate v92 tactical budget candidate and verify it on native dev games."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench

HERE = Path(__file__).resolve().parent
OUT = bench.CACHE / "bounded-verdict-probe-r1"
OPPONENTS = ("x3inv", "public-khiri")
LOG_LIMIT = 1048576


def apply(file, edits):
    data = file.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    for before, after in edits:
        a, b = (s.encode().replace(b"\n", nl) for s in (before, after))
        assert data.count(a) == 1, (file, before)
        data = data.replace(a, b, 1)
    file.write_bytes(data)


def prepare(src, enabled, diagnostic):
    copytree(bench.ROOT / "bots/v92/src", src)
    common = src / "common.h"
    data = common.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    common.write_bytes(nl.join([
        f"#define CODEX_BOUNDED_VERDICT {int(enabled)}".encode(),
        f"#define CODEX_BOUNDED_VERDICT_DIAG {int(diagnostic)}".encode(),
        data,
    ]))
    apply(src / "tsearch.h", (
        ("inline void rollout(State& s, const Map& m, const Policy& p, int rounds) {",
         """#if CODEX_BOUNDED_VERDICT
template<bool bounded = false>
inline bool rollout(State& s, const Map& m, const Policy& p, int rounds, std::uint64_t floor = 0) {
    const auto room = [&] {
        if constexpr (bounded) return bc::fuel_remaining() >= floor;
        return true;
    };
#else
inline void rollout(State& s, const Map& m, const Policy& p, int rounds) {
#endif"""),
        ("    for (int r = 0; r <= rounds; ++r) {\n        if (r > 0) {",
         """    for (int r = 0; r <= rounds; ++r) {
#if CODEX_BOUNDED_VERDICT
        if (!room()) return false;
#endif
        if (r > 0) {"""),
        ("                if (!(s.u[idx].flags & U_ACTED)) act(s, m, idx, p);",
         """                if (!(s.u[idx].flags & U_ACTED)) {
#if CODEX_BOUNDED_VERDICT
                    if (!room()) return false;
#endif
                    act(s, m, idx, p);
                }"""),
        ("            if (idx < s.n) act(s, m, idx++, p);",
         """            if (idx < s.n) {
#if CODEX_BOUNDED_VERDICT
                if (!room()) return false;
#endif
                act(s, m, idx++, p);
            }"""),
        ("            if (ia >= s.n && ib >= s.n) break;\n        }\n    }\n}",
         """            if (ia >= s.n && ib >= s.n) break;
        }
    }
#if CODEX_BOUNDED_VERDICT
    return true;
#endif
}"""),
    ))
    apply(src / "tsearch.cpp", (
        ('#include "tsearch.h"', """#include "tsearch.h"
#if CODEX_BOUNDED_VERDICT
#include "runtime_budget.h"
#endif"""),
        ("            ts::act(c, m, 0, pol); // our turn, now\n            ts::rollout(c, m, pol, rounds);",
         """#if CODEX_BOUNDED_VERDICT
            if (tune::kDet) {
                // Keep enough fuel for the existing action reserve plus one simulation step.
                const std::uint64_t floor = reserve + rb::kTailReserve;
                if (left < floor) {
                    complete = false;
                    break;
                }
                ts::act(c, m, 0, pol);
                if (!ts::rollout<true>(c, m, pol, rounds, floor) || bc::fuel_remaining() < floor) {
#if CODEX_BOUNDED_VERDICT_DIAG
                    std::printf("CODEX_VERDICT_BOUND R%d S%d M%d P%d N%d\\\\n", round, slot, model, plan, s.n);
#endif
                    complete = false;
                    break;
                }
            } else
#endif
            {
                ts::act(c, m, 0, pol); // our turn, now
                ts::rollout(c, m, pol, rounds);
            }"""),
    ))
    if diagnostic:
        apply(src / "main.cpp", (
            ("                play_draft();",
             """                static bool capture_announced = false;
                if (!capture_announced) { std::puts("CODEX_VERDICT_CAPTURE"); capture_announced = true; }
                play_draft();"""),
        ))


def play(job):
    row = bench.one(job, log_limit=LOG_LIMIT)
    _, _, opp, mp, side, _ = job
    case = OUT / "games" / f"bounded-0-{opp}-{mp.stem}-{side}"
    with ZipFile(next(case.glob("*.repl26a"))) as archive:
        log = archive.read(f"team-{side.lower()}.stdout").replace(b"\0", b"")
    assert len(log) < LOG_LIMIT and b"CODEX_VERDICT_CAPTURE" in log
    hits = [[int(x) for x in m] for m in re.findall(rb"CODEX_VERDICT_BOUND R(\d+) S(\d+) M(\d+) P(\d+) N(\d+)", log)]
    return {**row, "fallbacks": hits}


def probe():
    project = OUT / "diagnostic"
    prepare(project / "src", True, True)
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm],
                       cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    for name in OPPONENTS:
        file, expected = bench.OPPS[name]
        assert bench.digest(bench.CACHE / file) == expected
    maps = sorted((bench.CACHE / "jd-sets/conf").glob("*.map26a"))
    md = bench.sha256("\n".join(f"{bench.digest(p)} {p.name}" for p in maps).encode()).hexdigest()
    assert len(maps) == 16 and md == "94b6b4b43167ba179171f6ff3d616d802531c5cd632704412126cc3a21506852"
    bench.OUT = OUT
    (OUT / "games").mkdir()
    jobs = [("bounded", 0, opp, mp, side, wasm) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(play, jobs))
    result = {"engine": bench.ENGINE, "map_digest": md, "wasm": bench.digest(wasm), "n": len(rows),
              "maps_with_fallback": sorted({r["map"] for r in rows if r["fallbacks"]}),
              "fallbacks": sum(len(r["fallbacks"]) for r in rows),
              "fuel": sum(r["fuel_outs"] for r in rows), "faults": sum(r["faults"] for r in rows), "rows": rows}
    with (HERE / "BOUNDED_VERDICT_PROBE.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k != "rows"}, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src", type=Path)
    p.add_argument("--off", action="store_true")
    a = p.parse_args()
    if a.src:
        prepare(a.src, not a.off, False)
    else:
        probe()


if __name__ == "__main__":
    main()
