"""Measure exact target equivalence and charged fuel across native SDK masks."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
import re
from statistics import median
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from cpg_greedy_full import NEAREST, prepare
from cpg_greedy_near import NEARBY
from large_roster_stress import HERE, bench, read
from qualify_local import partition

OUT = bench.CACHE / "cpg-greedy-full-equivalence"


def instrument(src, scratch):
    reference = """static vec2 old_nearest(const bc::bitboard& goals, vec2 pos) {
""" + NEARBY + """    int distance = 1 << 20;
    vec2 target{-1, -1};
    for (vec2 p : candidates.positions()) {
        const int d = cheb(pos, p);
        if (d < distance) distance = d, target = p;
    }
    return target;
}
"""
    if scratch:
        reference = NEAREST.replace("greedy_nearest", "old_nearest", 1)
    apply(src / "bot.cpp", (
        ("void Bot::play_turn() {", reference + """
static void verify_greedy_full() {
    const auto allies = bc::champions(bc::team::ally);
    if (allies.empty() || !(allies.front() == bc::self())) return;
    const int width = bc::map::width(), height = bc::map::height();
    const bc::bitboard open = ~(bc::map::walls() | bc::map::holes() | bc::map::altars());
    const auto check = [&](const bc::bitboard& goals, vec2 pos, int nearest_lower_bound) {
        const auto category = goals.count() <= 81 ? "small" : nearest_lower_bound > 4 ? "far" : "near";
        const auto before = bc::fuel_remaining();
        const vec2 old = old_nearest(goals, pos);
        const auto middle = bc::fuel_remaining();
        const vec2 next = greedy_nearest(goals, pos);
        const auto after = bc::fuel_remaining();
        std::printf("CODEX_FULL %s %llu %llu %d\\n", category,
                    static_cast<unsigned long long>(before - middle),
                    static_cast<unsigned long long>(middle - after), old != next);
    };
    for (vec2 pos : {vec2{0, 0}, vec2{width - 1, height - 1},
                    vec2{width / 2, height / 2}, vec2{width / 3, height / 3}}) {
        bc::bitboard dense = open;
        dense.set(pos, false);
        check(dense, pos, 0);
        bc::bitboard local;
        local.draw_chebyshev(pos, 2.0f);
        check(dense & local, pos, 0);
        check(bc::bitboard{}, pos, 0);
        for (int radius : {4, 8, 16, 24}) {
            local.clear();
            local.draw_chebyshev(pos, static_cast<float>(radius));
            check(dense & ~local, pos, radius + 1);
        }
    }
    bc::resign();
}

void Bot::play_turn() {
    static bool tested = false;
    if (!tested) {
        tested = true;
        verify_greedy_full();
    }"""),
    ))


def play(job):
    row = bench.one(job, fuel=10000000, log_limit=1048576)
    case = OUT / "games" / f"proof-0-v92-{row['map']}-{row['side']}"
    (archive,) = case.glob("*.repl26a")
    with ZipFile(archive) as z:
        log = z.read(f"team-{row['side'].lower()}.stdout")
    matches = re.findall(rb"CODEX_FULL (small|near|far) (\d+) (\d+) (\d+)", log)
    assert len(matches) == 28, case
    native = read(case / "native.json")
    errors = bool(native["diagnostics"]["codes"] or any(native["diagnostics"]["botFaults"].values()))
    return {**row, "errors": errors,
            "samples": [[category.decode(), int(old), int(new), int(diff)] for category, old, new, diff in matches]}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", action="store_true")
    scratch = parser.parse_args().scratch
    variant = "scratch" if scratch else "full"
    OUT = bench.CACHE / f"cpg-greedy-{variant}-equivalence"
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    project = OUT / "diagnostic"
    prepare(project / "src", True, scratch=scratch)
    instrument(project / "src", scratch)
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    file, digest = bench.OPPS["v92"]
    assert bench.digest(bench.CACHE / file) == digest
    jobs = [("proof", 0, "v92", mp, side, wasm) for mp in partition("conf") for side in "AB"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    errors = sum(bool(r["errors"] or r["fuel_outs"]) for r in rows)
    grouped = defaultdict(list)
    differences = 0
    for row in rows:
        for category, old, new, diff in row["samples"]:
            differences += diff
            grouped[category].append(new - old)
    costs = {category: {"n": len(values), "median_delta": median(values), "max_delta": max(values)}
             for category, values in grouped.items()}
    categories = ("near", "small") if scratch else ("near", "far")
    limit = 100 if scratch else 1000
    passed = (len(rows) == 32 and not differences and not errors and
              all(costs[k]["median_delta"] < 0 for k in categories) and
              all(v["max_delta"] <= limit for v in costs.values()))
    result = {"engine": bench.ENGINE, "diagnostic": bench.digest(wasm), "n": len(rows),
              "differences": differences, "errors": errors, "costs": costs, "pass": passed}
    with (HERE / f"CPG_GREEDY_{variant.upper()}_PROOF.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
