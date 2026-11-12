"""Measure campwatch and dominant-group opportunities lost at the v92 bound."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "camp-bound-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("x3inv", "public-khiri")
LOG_LIMIT = 1048576

OBSERVE = r"""                if (round <= 300) {
                    const float bound = prune_bound();
#if A2_CAMPWATCH
                    if (g.state == GroupState::respawning && g.respawn_round - round <= A2_CW_LEAD &&
                        round - g.enemy_round <= A2_CW_MEM && hp >= max_hp * 0.8f && gems < 20 &&
                        best_case * A2_CW_MULT > bound && allies_near_group(g) >= 1)
                        std::printf("CODEX_BOUND_DELTA R%d S%d G%zu M1\n", round, slot, gi);
#endif
                    if (NOVA_BIGJOB > 0.0f && round >= NOVA_BIGJOB_FROM && gi < big_group.size() &&
                        big_group[gi] && best_case * NOVA_BIGJOB_MULT > bound)
                        std::printf("CODEX_BOUND_DELTA R%d S%d G%zu M2\n", round, slot, gi);
                }
"""


def prepare():
    src = PROJECT / "src"
    copytree(bench.ROOT / "bots/v92/src", src)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    anchor = b"            if (best_case <= prune_bound()) {"
    assert data.count(anchor) == 1
    data = data.replace(anchor, anchor + nl + OBSERVE.encode().replace(b"\n", nl), 1)
    bot.write_bytes(data)
    main = src / "main.cpp"
    data = main.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    draft = b"                play_draft();"
    assert data.count(draft) == 1
    main.write_bytes(data.replace(draft, nl.join([
        b"                static bool capture_announced = false;",
        b'                if (!capture_announced) { std::puts("CODEX_BOUND_CAPTURE"); capture_announced = true; }',
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
    assert len(log) < LOG_LIMIT and b"CODEX_BOUND_CAPTURE" in log
    observations = [[int(x) for x in m] for m in re.findall(rb"CODEX_BOUND_DELTA R(\d+) S(\d+) G(\d+) M([12])", log)]
    assert all(1 <= r <= 300 for r, _, _, _ in observations)
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
    jobs = [("bound",0,opp,mp,side,WASM) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    matched = {mode: sum(len({tuple(x[:3]) for x in r["differences"] if x[3] == mode}) for r in rows)
               for mode in (1, 2)}
    affected = {mode: sorted({r["map"] for r in rows if any(x[3] == mode for x in r["differences"])})
                for mode in (1, 2)}
    result = dict(engine=bench.ENGINE, fixture_sha256=bench.digest(WASM), cells=len(rows),
                  affected_maps=affected,
                  unique_decisions=matched, raw_calls=sum(len(r["differences"]) for r in rows),
                  faults=sum(r["faults"] for r in rows), rows=rows)
    path = Path(__file__).with_name("CAMP_BOUND_PROBE.json")
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k:v for k,v in result.items() if k!="rows"}, flush=True)

if __name__ == "__main__":
    main()
