"""Profile combined PG across the whole frozen dev set and three diverse bots."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

import ablate_dev as bench
from bounded_verdict import apply
from pg_budget import prepare
import profile_pg_runtime as trace
from qualify_local import partition

HERE = Path(__file__).resolve().parent
OUT = bench.CACHE / "pg-budget-broad-trace"
OPPONENTS = ("v92", "x3inv", "public-khiri")


def augment(src):
    apply(src / "common.h", (("inline constexpr int kMarks = 64;", "inline constexpr int kMarks = 96;"),))
    bot = src / "bot.cpp"
    apply(bot, (
        ("    std::uint16_t levels = field.compute_to_with_expansion_count(fblocked, goals, single(pos), visited, cap);",
         """    PROF_CHECK("wt_primary_enter");
    std::uint16_t levels = field.compute_to_with_expansion_count(fblocked, goals, single(pos), visited, cap);
    PROF_CHECK("wt_primary_done");"""),
        ("        levels = field.compute_to_with_expansion_count(terrain, goals_in & ~w.static_blocked, single(pos), visited, cap);",
         """        PROF_CHECK("wt_fallback_enter");
        levels = field.compute_to_with_expansion_count(terrain, goals_in & ~w.static_blocked, single(pos), visited, cap);
        PROF_CHECK("wt_fallback_done");"""),
        ("    drop_ward();\n    if (tune::kTSearch", """    PROF_CHECK("tail_drop");
    drop_ward();
    PROF_CHECK("tail_dropped");
    if (tune::kTSearch"""),
        ("    prelock_altars();\n    update_priority();\n    PROF_CHECK(\"tail\");",
         """    PROF_CHECK("tail_prelock");
    prelock_altars();
    PROF_CHECK("tail_priority");
    update_priority();
    PROF_CHECK("tail");"""),
    ))


def main():
    trace.OUT = OUT
    project = OUT / "diagnostic"
    prepare(project / "src", "combined")
    trace.instrument(project / "src")
    augment(project / "src")
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm],
                       cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    for opponent in OPPONENTS:
        file, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == expected
    maps = partition("dev")
    bench.OUT = OUT
    (OUT / "games").mkdir()
    jobs = [("profile", 0, opponent, mp, side, wasm)
            for mp in maps for opponent in OPPONENTS for side in "AB"]
    rows = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for row in pool.map(trace.play, jobs):
            rows.append(row)
            if len(rows) % 90 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    counts = Counter()
    for row in rows:
        counts.update(row["crossings"])
    result = {"engine": bench.ENGINE, "wasm": bench.digest(wasm), "n": len(rows),
              "fuel": sum(r["fuel_outs"] for r in rows), "faults": sum(r["faults"] for r in rows),
              "crossings": dict(counts.most_common()), "rows": rows}
    with (HERE / "PG_BUDGET_BROAD_TRACE.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k != "rows"}, flush=True)


if __name__ == "__main__":
    main()
