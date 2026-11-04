"""Recount charged diagnostic markers with replay stdout explicitly enabled."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import json
import re
import subprocess

import ablate_dev as bench

SPECS = {
    "ward-cooldown-probe": (4, rb"CODEX_WARD_LATE R(\d+) C(\d+)"),
    "stage-chip-probe": (4, rb"CODEX_CHIP (siege|stage) R(\d+)"),
    "hunt-bank-probe": (16, rb"CODEX_HUNT_BANK R(\d+) G(\d+)"),
    "bush-wrapper-audit": (16, rb"CODEX_BUSH_WRAPPER [^\r\n]+"),
}
BUSH_ARMS = ("v92", "codex-bushlinear", "codex-bushsparse")


def cells():
    maps = sorted((bench.CACHE / "jd-sets/conf").glob("*.map26a"))
    assert len(maps) == 16
    for name, (count, pattern) in SPECS.items():
        cache = bench.CACHE / name
        for mp in maps[:count]:
            if name == "bush-wrapper-audit":
                for arm in BUSH_ARMS:
                    yield name, mp, "v92", "A", arm, cache / arm / "bot.wasm", pattern
            else:
                for opp in ("v92", "x3inv"):
                    for side in "AB":
                        yield name, mp, opp, side, "diagnostic", cache / "diagnostic/bot.wasm", pattern


def run(job):
    name, mp, opponent, side, arm, wasm, pattern = job
    cache = bench.CACHE / name / "games-with-logs" / f"{arm}-{mp.stem}-{opponent}-{side}"
    cache.mkdir(parents=True)
    opp = bench.CACHE / bench.OPPS[opponent][0]
    bots = (wasm, opp) if side == "A" else (opp, wasm)
    with (cache / "run.log").open("wb") as out:
        subprocess.run([bench.CLI, "run", *bots, "--map", mp, "--release", "--json",
                        "--log-limit", "1048576", "--statistics", cache / "native.json",
                        "--out-dir", cache], cwd=bench.ROOT, stdout=out, stderr=subprocess.STDOUT,
                       check=True, timeout=120)
    native = json.loads((cache / "native.json").read_bytes())
    assert native["match"]["engineBuildHash"] == bench.ENGINE
    assert native["diagnostics"]["detailedCaptureComplete"]
    assert native["diagnostics"]["botFaults"]["team" + side] == 0
    (replay,) = cache.glob("*.repl26a")
    with ZipFile(replay) as archive:
        raw = archive.read(f"team-{side.lower()}.stdout")
    assert len(raw) < 1048576, (name, cache, "stdout truncated")
    log = raw.replace(b"\0", b"")
    row = {"probe": name, "map": mp.name, "map_sha256": bench.digest(mp), "opponent": opponent,
           "side": side, "arm": arm, "stdout_bytes": len(raw)}
    if name == "bush-wrapper-audit":
        (line,) = re.findall(pattern, log)
        row.update({k.decode(): (v.decode() if k == b"labels" else int(v))
                    for k, v in re.findall(rb"(\w+)=(\d+)", line)})
        assert row["mask_equal"] == 1 and row["fuel"] > 0
        assert not any(x["timestamp"]["round"] == 0
                       for e in native["events"] if e["kind"] == "fuelExhausted" and e["owner"]["team"] == "teamA"
                       for x in e["entries"])
    else:
        row["observations"] = [[v.decode() for v in match] for match in re.findall(pattern, log)]
    return row


def main():
    for name in ("v92", "x3inv"):
        path, expected = bench.OPPS[name]
        assert bench.digest(bench.CACHE / path) == expected
    jobs = list(cells())
    assert len(jobs) == 144
    wasm_hashes = {f"{job[0]}/{job[4]}": bench.digest(job[5]) for job in jobs}
    with ThreadPoolExecutor(max_workers=6) as workers:
        rows = []
        for row in workers.map(run, jobs):
            rows.append(row)
            if len(rows) % 24 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)

    bush = [row for row in rows if row["probe"] == "bush-wrapper-audit"]
    for mp in {r["map"] for r in bush}:
        group = [r for r in bush if r["map"] == mp]
        assert len(group) == len(BUSH_ARMS)
        for field in ("map_sha256", "tiles", "components", "labels"):
            assert len({r[field] for r in group}) == 1, (field, group)
    summary = {}
    for name in SPECS:
        group = [r for r in rows if r["probe"] == name]
        counts = Counter()
        for r in group:
            if name == "bush-wrapper-audit":
                counts[r["arm"]] += r["fuel"]
            else:
                counts["observations"] += len(r["observations"])
                counts["cells_with_observation"] += bool(r["observations"])
        summary[name] = {"cells": len(group), "totals": dict(counts)}
    result = {"engine_hash": bench.ENGINE, "log_limit_per_team_stream": 1048576,
              "fixture_hashes": wasm_hashes, "summary": summary, "rows": rows}
    with Path(__file__).with_name("DIAGNOSTIC_RECOUNT.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
