"""Prepare the immutable upstream PG configuration for local qualification."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply

HERE = Path(__file__).resolve().parent
ARCHIVE = bench.CACHE / "cpg-archive-1/src"
OUT = bench.CACHE / "pg-rival-probe"
OPPONENTS = ("x3inv", "public-khiri")
LIMIT = 1048576


def prepare(src, enabled, diagnostic=False):
    copytree(ARCHIVE, src)
    config = src / "jd_config.h"
    data = config.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    expected = nl.join((b"#define JD_CONTACT 3", b"#define JD_PROGRESS 1", b"#define JD_GOV 5", b""))
    assert data.startswith(expected)
    settings = [b"#define JD_CONTACT 0", f"#define JD_PROGRESS {int(enabled)}".encode(),
                f"#define JD_GOV {5 if enabled else 0}".encode()]
    if diagnostic:
        settings.append(b"#define JD_STRATLOG 1")
    config.write_bytes(nl.join([*settings, data[len(expected):]]))
    if diagnostic:
        apply(src / "main.cpp", (
            ("                play_draft();",
             """                static bool capture_announced = false;
                if (!capture_announced) { std::puts("CODEX_PG_CAPTURE"); capture_announced = true; }
                play_draft();"""),
        ))


def play(job):
    row = bench.one(job, log_limit=LIMIT)
    _, _, opp, mp, side, _ = job
    case = OUT / "games" / f"pg-0-{opp}-{mp.stem}-{side}"
    with ZipFile(next(case.glob("*.repl26a"))) as z:
        log = z.read(f"team-{side.lower()}.stdout").replace(b"\0", b"")
    assert len(log) < LIMIT and b"CODEX_PG_CAPTURE" in log
    last = {}
    for m in re.findall(rb"JDCT R(\d+) t(\d+) [^\n]*prog_stuck (\d+) prog_osc (\d+) prog_unreach (\d+) prog_bank (\d+) prog_rescore (\d+)", log):
        rnd, champion, *counts = map(int, m)
        if champion not in last or rnd >= last[champion][0]:
            last[champion] = [rnd, *counts]
    return {**row, "last_by_champion_type": last,
            "counts": [sum(v[i] for v in last.values()) for i in range(1, 6)]}


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
    jobs = [("pg", 0, opp, mp, side, wasm) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(play, jobs))
    keys = ("stuck", "oscillation", "unreachable", "bank", "rescore")
    result = {"engine": bench.ENGINE, "map_digest": md, "wasm": bench.digest(wasm), "n": len(rows),
              "affected_maps": sorted({r["map"] for r in rows if any(r["counts"])}),
              "progress_counts_lower_bound": {k: sum(r["counts"][i] for r in rows) for i, k in enumerate(keys)},
              "faults": sum(r["faults"] for r in rows), "rows": rows}
    with (HERE / "PG_RIVAL_PROBE.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k != "rows"}, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src", type=Path)
    p.add_argument("--off", action="store_true")
    a = p.parse_args()
    if a.src:
        prepare(a.src, not a.off)
    else:
        probe()


if __name__ == "__main__":
    main()
