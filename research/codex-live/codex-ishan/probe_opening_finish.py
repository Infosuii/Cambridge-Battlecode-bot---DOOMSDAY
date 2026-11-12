"""Measure ordinary opening retargets that leave an affordable last basic hit."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "opening-finish-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("x3inv", "public-khiri")
LOG_LIMIT = 1048576

OBSERVE = r"""    if (round <= 300 && target_group >= 0 && target_group != best &&
        static_cast<std::size_t>(target_group) < w.groups.size() && hp > max_hp * 0.65f &&
        w.enemies.empty() && round >= avoid_until[target_group]) {
        const auto& previous = w.groups[target_group];
        int live = 0;
        int visible_in_range = -1;
        if (previous.state == GroupState::alive) {
            for (int ci : previous.camps) {
                const auto& camp = w.camps[ci];
                if (camp.dead) continue;
                ++live;
                if (camp.hp > 0.0f && camp.hp <= strength && bit(w.visible, camp.pos) &&
                    cheb(camp.pos, pos) <= range)
                    visible_in_range = ci;
            }
        }
        if (live == 1 && visible_in_range >= 0 && bc::self().can_attack())
            std::printf("CODEX_FINISH_DELTA R%d S%d G%d B%d\n", round, slot, target_group, best);
    }
"""


def prepare():
    src = PROJECT / "src"
    copytree(bench.ROOT / "bots/v92/src", src)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"bool Bot::farm()")
    end = data.index(b"void Bot::opportunistic_attack()", start)
    body = data[start:end]
    anchor = b"    if (best != target_group) {"
    assert body.count(anchor) == 1
    body = body.replace(anchor, OBSERVE.encode().replace(b"\n", nl) + anchor, 1)
    data = data[:start] + body + data[end:]
    bot.write_bytes(data)
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
    observations = [[int(x) for x in m] for m in re.findall(rb"CODEX_FINISH_DELTA R(\d+) S(\d+) G(\d+) B(-?\d+)", log)]
    assert all(1 <= r <= 300 and g != best for r, _, g, best in observations)
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
    matched = sum(len({tuple(x[:3]) for x in r["differences"]}) for r in rows)
    affected = sorted({r["map"] for r in rows if r["differences"]})
    result = dict(engine=bench.ENGINE, fixture_sha256=bench.digest(WASM), cells=len(rows),
                  affected_maps=affected,
                  unique_decisions=matched, raw_calls=sum(len(r["differences"]) for r in rows),
                  faults=sum(r["faults"] for r in rows), rows=rows)
    path = Path(__file__).with_name("OPENING_FINISH_PROBE.json")
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k:v for k,v in result.items() if k!="rows"}, flush=True)

if __name__ == "__main__":
    main()
