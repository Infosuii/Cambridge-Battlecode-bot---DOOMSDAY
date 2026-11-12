"""Build exact archived v105/v106 and compare their safety with frozen current controls."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

from audit_uploaded_112_114 import build, files, write
import audit_uploaded_112_114_pool as pool_audit
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, bench, one, read

OUT = bench.CACHE / "uploaded-105-106-audit-20261109"
SOURCE = {
    105: ("CPG-source.zip", "24aaefff-96b2-40c9-92ba-22ca6c6258b6", 672781,
          "829d20498aac49120bd1e97267e6d8385beb481e15c7f777f848a0587981ddeb"),
    106: ("bot (14).zip", "9bd70a8a-7840-45f9-be43-c28adff7f92c", 717895,
          "747942bb5904d2c2fa15d281f864a5db495d7113eab4624214fee2305ad446eb"),
}
PARENT = HERE / "UPLOADED_112_114_POOL_RESULT.json"


def main():
    assert bench.digest(CLI) == CLI_HASH
    OUT.mkdir()
    sources, provenance = {}, {}
    for version, (filename, submission, size, digest) in SOURCE.items():
        source = Path("C:/Users/ishan/Downloads") / filename
        assert source.stat().st_size == size and bench.digest(source) == digest
        archive = OUT / f"v{version}.zip"
        with archive.open("xb") as out:
            out.write(source.read_bytes())
        sources[version] = files(archive)
        provenance[version] = {"id": submission, "archive_sha256": digest, "size": size,
                               "source_sha256": {k: sha256(v).hexdigest() for k, v in sorted(sources[version].items())}}
    write(HERE / "UPLOADED_105_106_SOURCES.json", provenance)
    jobs = [(v, s, source) for v, source in sources.items() for s in ("release", "repeat")]
    builds = {}
    with ThreadPoolExecutor(max_workers=2) as workers:
        for v, s, result in workers.map(build, jobs):
            builds.setdefault(v, {})[s] = result
    for version, variants in builds.items():
        assert variants["release"]["sha256"] == variants["repeat"]["sha256"]
        for variant in variants.values():
            path = Path(variant["path"])
            assert bench.digest(path) == variant["sha256"]
            src = path.parent / "src"
            assert {p.relative_to(src).as_posix(): bench.digest(p) for p in src.rglob("*") if p.is_file()} == provenance[version]["source_sha256"]

    parent = read(PARENT)
    reference = SDK_ROOT / "bots/v92-e3/bot.wasm"
    assert parent["plan"]["engine"] == ENGINE and bench.digest(reference) == parent["plan"]["reference_sha256"]
    frozen = {(row["map"], row["side"]): row for row in parent["rows"] if row["arm"] == "v92"}
    maps = sorted((bench.ROOT / "maps/ladder-pool").glob("*.map26a"))
    assert len(maps) == 86 and len(frozen) == 172
    for (name, side), row in frozen.items():
        path = pool_audit.RUN / f"{name}-{side}-v92" / "native.json"
        assert bench.digest(path) == row["native_sha256"]
        assert bench.digest(bench.ROOT / "maps/ladder-pool" / (name + ".map26a")) == row["map_hash"]
    output = OUT / "original-pool"
    output.mkdir()
    pool_audit.RUN = output  # The shared native/replay recount operates on this audit's new directory.
    plan = {"engine": ENGINE, "cli_sha256": CLI_HASH, "reference": parent["plan"]["reference_sha256"],
            "native_controls_sha256": bench.digest(PARENT), "source_manifest_sha256": bench.digest(HERE / "UPLOADED_105_106_SOURCES.json"),
            "builds": builds, "fuel": 100000, "log_limit": 0, "maps": parent["plan"]["maps"]}
    write(HERE / "UPLOADED_105_106_POOL_PLAN.json", plan)
    jobs = [(f"v{v}", p, side, Path(variants["release"]["path"]), reference)
            for p in maps for side in "AB" for v, variants in builds.items()]

    def run(job):
        return one(job, output=output)

    rows = []
    with ThreadPoolExecutor(max_workers=8) as workers:
        for i, row in enumerate(workers.map(run, jobs), 1):
            pool_audit.recount(row, frozen[row["map"], row["side"]])
            rows.append(row)
            if i % 32 == 0:
                print(f"{i}/{len(jobs)} native and replay checks passed", flush=True)
    reports = {}
    for v in builds:
        arm = f"v{v}"
        group = [row for row in rows if row["arm"] == arm]
        report = pool_audit.summarize(group)
        for field, key in (("fuel_outs", "total_fuel_increase_cells"), ("round1_fuel_outs", "r1_fuel_increase_cells")):
            report[key] = sum(r[field] > frozen[r["map"], r["side"]][field] for r in group)
        report["safety_pass"] = not any(report[k] for k in
            ("faults_both_teams", "diagnostic_code_cells", "total_fuel_increase_cells", "r1_fuel_increase_cells"))
        reports[arm] = report
    write(HERE / "UPLOADED_105_106_POOL_RESULT.json", {"plan": plan, "reports": reports, "rows": rows})
    print(reports, flush=True)


if __name__ == "__main__":
    main()
