"""Measure nearby home rewards passed over after direct enemy observation."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "home-reward-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("x3inv", "public-khiri")
LOG_LIMIT = 1048576

OBSERVE = r"""    if (round >= 300 && w.enemy_ready && w.enemies.empty() && !walked && bc::self().can_move()) {
        for (std::size_t i = 0; i < w.groups.size(); ++i) {
            const auto& alternate = w.groups[i];
            if (static_cast<int>(i) == best || alternate.state != GroupState::reward ||
                w.group_margin[i] <= 0 || round < avoid_until[i] || alternate.enemy_round <= 0 ||
                round - alternate.enemy_round > 6 || bit(alternate.tiles, pos)) continue;
            if (tune::kShareGold && poorer_ally_takes(alternate, static_cast<int>(i), false)) continue;
            bool nearby = false;
            for (vec2 dir : kDirs) {
                const vec2 q = pos + dir;
                if (!in_bounds(q, w.width, w.height) || !bit(alternate.tiles, q) ||
                    bit(w.static_blocked, q) || bit(w.unit_tiles, q) || bit(w.hot_zone, q)) continue;
                nearby = true;
                break;
            }
            if (nearby) {
                std::printf("CODEX_HOME_DELTA R%d S%d G%d B%d\n", round, slot, static_cast<int>(i), best);
                break;
            }
        }
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
    anchor = b"    auto& g = w.groups[best];"
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
        b'                if (!capture_announced) { std::puts("CODEX_HOME_CAPTURE"); capture_announced = true; }',
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
    assert len(log) < LOG_LIMIT and b"CODEX_HOME_CAPTURE" in log
    observations = [[int(x) for x in m] for m in re.findall(rb"CODEX_HOME_DELTA R(\d+) S(\d+) G(\d+) B(\d+)", log)]
    assert all(r >= 300 and g != best for r, _, g, best in observations)
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
    jobs = [("home",0,opp,mp,side,WASM) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    matched = sum(len({tuple(x[:3]) for x in r["differences"]}) for r in rows)
    affected = sorted({r["map"] for r in rows if r["differences"]})
    result = dict(engine=bench.ENGINE, fixture_sha256=bench.digest(WASM), cells=len(rows),
                  affected_maps=affected,
                  unique_decisions=matched, raw_calls=sum(len(r["differences"]) for r in rows),
                  faults=sum(r["faults"] for r in rows), rows=rows)
    path = Path(__file__).with_name("HOME_REWARD_PROBE.json")
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k:v for k,v in result.items() if k!="rows"}, flush=True)

if __name__ == "__main__":
    main()
