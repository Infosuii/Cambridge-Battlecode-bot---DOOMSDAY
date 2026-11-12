"""Compare the original and compact greedy target in the exact native SDK."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from cpg_greedy_near import NEARBY, prepare
from large_roster_stress import HERE, bench
from qualify_local import partition

OUT = bench.CACHE / "cpg-greedy-near-equivalence-r2"


def instrument(src):
    apply(src / "bot.cpp", (
        ("void Bot::play_turn() {", """static void verify_nearby_targets() {
    const auto allies = bc::champions(bc::team::ally);
    if (allies.empty() || !(allies.front() == bc::self())) return;
    const int width = bc::map::width(), height = bc::map::height();
    const bc::bitboard open = ~(bc::map::walls() | bc::map::holes() | bc::map::altars());
    int tests = 0, compacted = 0, differences = 0;
    auto check = [&](const bc::bitboard& goals, vec2 pos) {
        auto nearest = [&](const bc::bitboard& mask) {
            int distance = 1 << 20;
            vec2 target{-1, -1};
            for (vec2 p : mask.positions()) {
                const int d = cheb(pos, p);
                if (d < distance) distance = d, target = p;
            }
            return target;
        };
""" + NEARBY + """        ++tests;
        compacted += &candidates != &goals;
        differences += nearest(candidates) != nearest(goals);
    };
    for (vec2 pos : {vec2{0, 0}, vec2{width - 1, height - 1},
                    vec2{width / 2, height / 2}, vec2{width / 3, height / 3}}) {
        bc::bitboard dense = open;
        dense.set(pos, false);
        check(dense, pos);
        bc::bitboard local;
        local.clear();
        local.draw_chebyshev(pos, 2.0f);
        check(dense & local, pos);
        local.draw_chebyshev(pos, 4.0f);
        check(dense & ~local, pos);
    }
    std::printf("CODEX_NEAR_EQ %d %d %d\\n", tests, compacted, differences);
    bc::resign();
}

void Bot::play_turn() {
    static bool tested = false;
    if (!tested) {
        tested = true;
        verify_nearby_targets();
    }"""),
    ))


def play(job):
    row = bench.one(job, fuel=10000000, log_limit=1048576)
    case = OUT / "games" / f"proof-0-v92-{row['map']}-{row['side']}"
    (archive,) = case.glob("*.repl26a")
    with ZipFile(archive) as z:
        log = z.read(f"team-{row['side'].lower()}.stdout")
    (match,) = re.findall(rb"CODEX_NEAR_EQ (\d+) (\d+) (\d+)", log)
    tests, compacted, differences = map(int, match)
    assert tests == 12
    return {**row, "tests": tests, "compacted": compacted, "differences": differences}


def main():
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    project = OUT / "diagnostic"
    prepare(project / "src", True)
    instrument(project / "src")
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    file, digest = bench.OPPS["v92"]
    assert bench.digest(bench.CACHE / file) == digest
    jobs = [("proof", 0, "v92", mp, side, wasm) for mp in partition("conf") for side in "AB"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    errors = sum(bool(r["faults"] or r["diagnostic_codes"] or r["fuel_outs"]) for r in rows)
    differences = sum(r["differences"] for r in rows)
    compacted = sum(r["compacted"] for r in rows)
    report = {"engine": bench.ENGINE, "diagnostic": bench.digest(wasm), "n": len(rows),
              "tests": sum(r["tests"] for r in rows), "compacted": compacted, "differences": differences,
              "errors": errors, "pass": len(rows) == 32 and compacted > 0 and not differences and not errors}
    with (HERE / "CPG_GREEDY_NEAR_PROOF.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "rows": rows}, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
