"""Recount exact uploaded versions on the original, frozen engine-3 safety matrix."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from zipfile import ZipFile

from audit_uploaded_112_114 import OUT, write
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, bench, one, read

RUN = OUT / "original-pool"
REFERENCE = SDK_ROOT / "bots/v92-e3/bot.wasm"
OLD = bench.CACHE / "engine3-pool-20261105"
REF_HASH = "5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47"
FROZEN = HERE / "ENGINE3_REBASELINE_POOL.json"


def summarize(rows):
    return {"cells": len(rows), "score_context": sum(r["score"] for r in rows),
            "fuel": sum(r["fuel_outs"] for r in rows), "round1": sum(r["round1_fuel_outs"] for r in rows),
            "faults_both_teams": sum(r["faults"] + r["opponent_faults"] for r in rows),
            "diagnostic_code_cells": sum(bool(r["diagnostic_codes"]) for r in rows)}


def load_builds():
    path = HERE / "UPLOADED_112_114_BUILDS.json"
    built = read(path)
    sources_path = HERE / "UPLOADED_112_114_SOURCES.json"
    sources = read(sources_path)
    assert bench.digest(sources_path) == built["source_manifest_sha256"]
    assert bench.digest(CLI) == CLI_HASH == sources["cli_sha256"] == built["cli_sha256"]
    assert bench.digest(REFERENCE) == REF_HASH
    paths = {"v92": REFERENCE}
    for version, item in built["local_builds"].items():
        for suffix, record in item.items():
            binary = SDK_ROOT / "bots" / f"codex-upload-audit-v{version}-{suffix}-20261108" / "bot.wasm"
            assert binary.resolve() == Path(record["path"]).resolve()
            assert bench.digest(binary) == record["sha256"] == item["release"]["sha256"]
            expected = sources["submissions"][version]["source_sha256"]
            actual = {p.relative_to(binary.parent / "src").as_posix(): bench.digest(p)
                      for p in (binary.parent / "src").rglob("*") if p.is_file()}
            assert actual == expected
        paths["v" + version] = Path(item["release"]["path"])
    assert set(paths) == {"v92", "v112", "v113", "v114"}
    return paths, path


def run(job):
    return one(job, output=RUN)


def recount(row, frozen):
    directory = RUN / f'{row["map"]}-{row["side"]}-{row["arm"]}'
    summary = directory / "native.json"
    native = read(summary)
    match, diag = native["match"], native["diagnostics"]
    assert match["engineBuildHash"] == ENGINE and match["engineVersion"] == "3.0.0"
    assert match["mapHash"] == frozen["map_hash"] == row["map_hash"]
    assert match["seed"] == frozen["engine_seed"] == row["engine_seed"]
    assert diag["detailedCaptureComplete"]
    assert match["outcome"] in ("teamA", "teamB", "draw")
    own = "team" + row["side"]
    rival = "teamB" if own == "teamA" else "teamA"
    counts = [int(e["timestamp"]["round"]) for group in native["events"]
              if group["kind"] == "fuelExhausted" and group["owner"]["team"] == own for e in group["entries"]]
    assert len(counts) == row["fuel_outs"] and counts.count(1) == row["round1_fuel_outs"]
    assert diag["botFaults"][own] == row["faults"] and diag["botFaults"][rival] == row["opponent_faults"]
    assert diag["codes"] == row["diagnostic_codes"]
    assert row["score"] == (0.5 if match["outcome"] == "draw" else int(match["outcome"] == own))
    archive, = directory.glob("*.repl26a")
    with ZipFile(archive) as replay:
        member = replay.getinfo("replay.repl26a")
        assert member.file_size > 0
        # Reading to EOF verifies the member CRC.
        assert len(replay.read(member)) == member.file_size
    row["native_sha256"] = bench.digest(summary)
    row["archive_sha256"] = bench.digest(archive)
    if row["arm"] == "v92":
        old = OLD / f'{row["map"]}-{row["side"]}-base' / "native.json"
        assert native == read(old), (row["map"], row["side"], "v92 native control")
        for k in ("score", "fuel_outs", "round1_fuel_outs", "faults", "opponent_faults", "diagnostic_codes"):
            assert row[k] == frozen[k]


def main():
    builds, build_manifest = load_builds()
    frozen = {(r["map"], r["side"]): r for r in read(FROZEN)["rows"] if r["arm"] == "base"}
    maps = sorted((bench.ROOT / "maps/ladder-pool").glob("*.map26a"))
    assert len(maps) == 86 and len(frozen) == 172
    assert all(bench.digest(p) == frozen[p.stem, side]["map_hash"] for p in maps for side in "AB")
    RUN.mkdir()
    plan = {"engine": ENGINE, "fuel": 100000, "log_limit": 0, "reference_sha256": REF_HASH,
            "frozen_reference_sha256": bench.digest(FROZEN), "build_manifest_sha256": bench.digest(build_manifest),
            "arms": {name: bench.digest(wasm) for name, wasm in builds.items()},
            "maps": {p.stem: frozen[p.stem, "A"]["map_hash"] for p in maps},
            "rule": "No fault or diagnostic code, and no increase in total or R1 fuel-outs in any cell versus v92."}
    write(HERE / "UPLOADED_112_114_POOL_PLAN.json", plan)
    jobs = [(arm, p, side, wasm, REFERENCE) for p in maps for side in "AB" for arm, wasm in builds.items()]
    rows = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, row in enumerate(pool.map(run, jobs), 1):
            recount(row, frozen[row["map"], row["side"]])
            rows.append(row)
            if i % 32 == 0:
                print(f"{i}/{len(jobs)} native and replay checks passed", flush=True)
    reports = {}
    for arm in builds:
        group = [r for r in rows if r["arm"] == arm]
        result = summarize(group)
        result["total_fuel_increase_cells"] = sum(r["fuel_outs"] > frozen[r["map"], r["side"]]["fuel_outs"] for r in group)
        result["r1_fuel_increase_cells"] = sum(r["round1_fuel_outs"] > frozen[r["map"], r["side"]]["round1_fuel_outs"] for r in group)
        result["safety_pass"] = not any(result[k] for k in
            ("faults_both_teams", "diagnostic_code_cells", "total_fuel_increase_cells", "r1_fuel_increase_cells"))
        reports[arm] = result
    write(HERE / "UPLOADED_112_114_POOL_RESULT.json", {"plan": plan, "reports": reports, "rows": rows})
    print(reports, flush=True)


if __name__ == "__main__":
    main()
