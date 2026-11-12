"""Check exact SDK target order under the naturally charged first draft budget."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
import re
from statistics import median
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from cpg_greedy_full import NEAREST
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, read
from freeze_engine3_discovery import write
from qualify_local import partition

CPP = r'''#include "common.h"
#include <cstdio>
__NEAREST__
static vec2 original_nearest(const bc::bitboard& goals, vec2 pos) {
    vec2 goal{-1, -1};
    int distance = 1 << 20;
    for (vec2 p : goals.positions()) {
        const int d = cheb(p, pos);
        if (d < distance) distance = d, goal = p;
    }
    return goal;
}
static void verify() {
    const int width = bc::map::width(), height = bc::map::height();
    const vec2 positions[] = {{0, 0}, {width - 1, height - 1}, {width / 2, height / 2}, {width / 3, height / 3}};
    const vec2 pos = positions[CODEX_POSITION];
    const auto start = bc::fuel_remaining();
    std::printf("CODEX_E3_START %llu\n", static_cast<unsigned long long>(start));
    const bc::bitboard open = ~(bc::map::walls() | bc::map::holes() | bc::map::altars());
    const auto check = [&](const bc::bitboard& goals, const char* category) {
        const auto before = bc::fuel_remaining();
        const vec2 old = original_nearest(goals, pos);
        const auto middle = bc::fuel_remaining();
        const vec2 next = greedy_nearest(goals, pos);
        const auto after = bc::fuel_remaining();
        std::printf("CODEX_E3_EQ %s %llu %llu %d\n", category,
            static_cast<unsigned long long>(before - middle),
            static_cast<unsigned long long>(middle - after), old != next);
    };
    bc::bitboard dense = open;
    dense.set(pos, false);
    check(dense, "near");
    bc::bitboard local;
    local.draw_chebyshev(pos, 2.0f);
    check(dense & local, "small");
    check(bc::bitboard{}, "empty");
    for (int radius : {4, 8, 16, 24}) {
        local.clear();
        local.draw_chebyshev(pos, static_cast<float>(radius));
        check(dense & ~local, "far");
    }
    std::printf("CODEX_E3_END %llu\n", static_cast<unsigned long long>(bc::fuel_remaining()));
}
int main() {
    bool checked = false;
    while (true) {
        if (bc::is_draft()) {
            if (!checked) { checked = true; verify(); }
            const auto picked = bc::draft::current_draft(team::ally);
            for (int i = 0; i < 11; ++i) {
                const auto candidate = static_cast<bc::champion_draft>(i);
                if (std::find(picked.begin(), picked.end(), candidate) == picked.end()) {
                    bc::draft::pick(candidate);
                    break;
                }
            }
        } else bc::resign();
        bc::end_turn();
    }
}
'''


def main():
    assert bench.digest(CLI) == CLI_HASH
    identity = read(HERE / "LIVE109_SOURCE_VERIFIED.json")
    common = SDK_ROOT / "bots/live109/src/common.h"
    assert bench.digest(common) == identity["source_file_hashes"]["common.h"]
    output = bench.CACHE / "engine3-live109-greedy-equivalence"
    output.mkdir()
    binaries, sources = {}, {}
    for index in range(4):
        project = SDK_ROOT / "bots" / f"live109-greedy-proof-{index}"
        src = project / "src"
        src.mkdir(parents=True)
        (src / "common.h").write_bytes(common.read_bytes())
        (src / "main.cpp").write_text(f"#define CODEX_POSITION {index}\n" + CPP.replace("__NEAREST__", NEAREST), encoding="utf8", newline="\n")
        with (project / "build.log").open("wb") as log:
            subprocess.run([CLI, "build", project, "--release", "--output", project / "bot.wasm"], cwd=SDK_ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        binaries[index] = project / "bot.wasm"
        sources[index] = bench.digest(src / "main.cpp")
    reference = SDK_ROOT / "bots/v92-e3/bot.wasm"
    assert bench.digest(reference) == bench.OPPS["v92"][1]

    def run(job):
        index, mp, side = job
        directory = output / f"{mp.stem}-{side}-{index}"
        directory.mkdir()
        bots = (binaries[index], reference) if side == "A" else (reference, binaries[index])
        with (directory / "run.log").open("wb") as log:
            subprocess.run([CLI, "run", *bots, "--map", mp, "--release", "--fuel", "100000", "--rounds", "1", "--log-limit", "1048576", "--json", "--statistics", directory / "native.json", "--out-dir", directory], cwd=SDK_ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
        doc = read(directory / "native.json")
        assert (doc["match"]["engineVersion"], doc["match"]["engineBuildHash"]) == ("3.0.0", ENGINE)
        assert doc["match"]["mapHash"] == bench.digest(mp) and doc["diagnostics"]["detailedCaptureComplete"]
        (bundle,) = directory.glob("*.repl26a")
        with ZipFile(bundle) as archive:
            stdout = archive.read(f"team-{side.lower()}.stdout")
        (start,) = map(int, re.findall(rb"CODEX_E3_START (\d+)", stdout))
        (end,) = map(int, re.findall(rb"CODEX_E3_END (\d+)", stdout))
        samples = [[kind.decode(), int(old), int(new), int(diff)] for kind, old, new, diff in re.findall(rb"CODEX_E3_EQ (near|small|empty|far) (\d+) (\d+) (\d+)", stdout)]
        assert len(samples) == 7 and start >= 1000000 and end > 0
        errors = any(doc["diagnostics"]["botFaults"].values()) or bool(doc["diagnostics"]["codes"]) or any(e["kind"] == "fuelExhausted" and e["entries"] for e in doc["events"])
        return {"position": index, "map": mp.stem, "side": side, "map_hash": doc["match"]["mapHash"], "start_budget": start, "end_budget": end, "errors": errors, "samples": samples}

    jobs = [(index, mp, side) for mp in partition("conf") for side in "AB" for index in range(4)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    costs = defaultdict(list)
    for row in rows:
        for kind, old, new, diff in row["samples"]:
            costs[kind].append(new - old)
    differences = sum(sample[3] for row in rows for sample in row["samples"])
    result = {"engine": ENGINE, "cli_sha256": CLI_HASH, "n_games": len(rows), "n_selections": sum(len(r["samples"]) for r in rows),
              "probe_source_sha256": sources, "probe_wasm_sha256": {i: bench.digest(wasm) for i, wasm in binaries.items()},
              "source_common_sha256": bench.digest(common), "differences": differences, "errors": sum(bool(r["errors"]) for r in rows),
              "charged_cost_delta": {k: {"n": len(v), "median": median(v), "max": max(v)} for k, v in costs.items()},
              "natural_draft_budget_range": [min(r["start_budget"] for r in rows), max(r["start_budget"] for r in rows)],
              "pass": len(rows) == 128 and not differences and not any(r["errors"] for r in rows) and all(max(v) <= 1000 for v in costs.values()), "rows": rows}
    write(HERE / "LIVE109_GREEDY_EQ_PROOF.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2), flush=True)


if __name__ == "__main__":
    main()
