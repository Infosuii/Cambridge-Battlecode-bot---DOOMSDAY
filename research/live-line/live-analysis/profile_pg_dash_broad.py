"""Compare exact and charged PG dash across the full frozen development cohort."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

import ablate_dev as bench
from pg_dash_camps import prepare, read
import profile_pg_runtime as trace
from qualify_local import DEV, partition

HERE = Path(__file__).resolve().parent
OUT = bench.CACHE / "pg-dash-broad"


def main():
    project = OUT / "diagnostic"
    prepare(project / "src", True, True, True)
    profiled = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", profiled],
                       cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    release = bench.ROOT / "bots/codex-pg-dash/bot.wasm"
    assert bench.digest(release) == read(HERE / "PG_DASH_BUILDS.json")["primary"]
    for opponent in DEV:
        file, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == expected
    maps = partition("dev")
    trace.OUT = bench.OUT = OUT
    (OUT / "games").mkdir()
    jobs = [(arm, 0, opponent, mp, side, wasm) for mp in maps for opponent in DEV for side in "AB"
            for arm, wasm in (("exact", release), ("profile", profiled))]

    def play(job):
        return trace.play(job) if job[0] == "profile" else bench.one(job)

    rows = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 180 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    crossings = Counter()
    for exact, profile in pairs:
        assert all(exact[k] == profile[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
        crossings.update(profile["crossings"])
    result = {
        "engine": bench.ENGINE, "release": bench.digest(release), "profile": bench.digest(profiled),
        "summary": bench.summary(pairs), "crossings": dict(crossings.most_common()),
        "error_cells": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows),
        "affected": [{"exact": e, "profile": p} for e, p in pairs if e["fuel_outs"] or p["fuel_outs"]],
    }
    with (OUT / "rows.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(rows, f, indent=2)
        f.write("\n")
    with (HERE / "PG_DASH_BROAD.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k != "affected"}, flush=True)


if __name__ == "__main__":
    main()
