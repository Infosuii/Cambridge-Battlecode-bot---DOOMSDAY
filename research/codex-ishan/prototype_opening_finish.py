"""Validate the opening finish switch on the frozen native development cohort."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "opening-finish-prototype"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("x3inv", "public-khiri")
LOG_LIMIT = 1048576

PATCH = Path(__file__).with_name("opening_finish.inc")


def prepare_source(src, *, enabled, diagnostic):
    copytree(bench.ROOT / "bots/v92/src", src)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"bool Bot::farm()")
    end = data.index(b"void Bot::opportunistic_attack()", start)
    body = data[start:end]
    anchor = b"    if (best != target_group) {"
    assert body.count(anchor) == 1
    block = PATCH.read_bytes().replace(b"\r\n", b"\n").rstrip(b"\n").replace(b"\n", nl)
    body = body.replace(anchor, block + nl + anchor, 1)
    defines = nl.join([
        f"#define CODEX_OPENING_FINISH {int(enabled)}".encode(),
        f"#define CODEX_OPENING_FINISH_DIAG {int(diagnostic)}".encode(),
        b"",
    ])
    bot.write_bytes(defines + data[:start] + body + data[end:])


def prepare():
    src = PROJECT / "src"
    prepare_source(src, enabled=True, diagnostic=True)
    main = src / "main.cpp"
    data = main.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    draft = b"                play_draft();"
    assert data.count(draft) == 1
    main.write_bytes(data.replace(draft, nl.join([
        b"                static bool capture_announced = false;",
        b'                if (!capture_announced) { std::puts("CODEX_FINISH_CAPTURE"); capture_announced = true; }',
        draft,
    ]), 1))
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", PROJECT, "--release", "--output", WASM], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)

def run(job):
    row = bench.one(job, log_limit=LOG_LIMIT)
    arm, seed, opp, mp, side, _ = job
    case = OUT / "games" / f"{arm}-{seed}-{opp}-{mp.stem}-{side}"
    (path,) = case.glob("*.repl26a")
    with ZipFile(path) as archive:
        log = archive.read(f"team-{side.lower()}.stdout").replace(b"\0", b"")
    assert len(log) < LOG_LIMIT and b"CODEX_FINISH_CAPTURE" in log
    observations = [[int(x) for x in m] for m in re.findall(rb"CODEX_FINISH_ACTION R(\d+) S(\d+) G(\d+) I(\d+) H([01])", log)]
    assert all(1 <= r <= 300 for r, *_ in observations)
    return {**row, "differences":observations}


def main():
    prepare()
    bench.OUT = OUT
    for name in OPPONENTS:
        file, expected = bench.OPPS[name]
        assert bench.digest(bench.CACHE / file) == expected
    maps = sorted((bench.CACHE / "jd-sets/conf").glob("*.map26a"))
    assert len(maps) == 16
    digest = bench.sha256("\n".join(f"{bench.digest(p)} {p.name}" for p in maps).encode()).hexdigest()
    assert digest == "94b6b4b43167ba179171f6ff3d616d802531c5cd632704412126cc3a21506852"
    (OUT / "games").mkdir()
    jobs = [("finish",0,opp,mp,side,WASM) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    matched = sum(len({tuple(x[:4]) for x in r["differences"]}) for r in rows)
    cleared = sorted({r["map"] for r in rows if any(x[4] for x in r["differences"])})
    affected = sorted({r["map"] for r in rows if r["differences"]})
    result = dict(engine=bench.ENGINE, fixture_sha256=bench.digest(WASM), cells=len(rows),
                  affected_maps=affected, same_turn_clear_maps=cleared,
                  unique_decisions=matched, same_turn_clears=sum(x[4] for r in rows for x in r["differences"]), raw_calls=sum(len(r["differences"]) for r in rows),
                  faults=sum(r["faults"] for r in rows), rows=rows)
    path = Path(__file__).with_name("OPENING_FINISH_PROTOTYPE.json")
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k:v for k,v in result.items() if k!="rows"}, flush=True)

if __name__ == "__main__":
    main()
