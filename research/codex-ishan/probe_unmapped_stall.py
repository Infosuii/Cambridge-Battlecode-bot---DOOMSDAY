"""Measure persistent stationary solo approaches while group fields are unavailable."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "unmapped-stall-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("x3inv", "public-khiri")
LOG_LIMIT = 1048576

OBSERVE = r"""        if (round <= 150 && need == 1 && hp >= 0.65f * max_hp &&
            w.enemies.empty() && !bit(w.hot_zone, pos)) {
            const int gi = static_cast<int>(&g - w.groups.data());
            if (!w.has_field(gi) && !w.value_cut_off()) {
                static int last_round = -1, last_group = -1, held = 0;
                static vec2 last_pos{-1, -1};
                if (last_round == round - 1 && last_group == gi && last_pos == pos)
                    ++held;
                else
                    held = 1;
                last_round = round;
                last_group = gi;
                last_pos = pos;
                if (held == 8) std::printf("CODEX_STALL_DELTA R%d S%d G%d\n", round, slot, gi);
            }
        }
"""


def prepare():
    src = PROJECT / "src"
    copytree(bench.ROOT / "bots/v92/src", src)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"bool Bot::fight_camps(")
    end = data.index(b"bool Bot::break_out()", start)
    body = data[start:end]
    anchor = b'        mode = "approach";'
    assert body.count(anchor) == 1
    body = body.replace(anchor, anchor + nl + OBSERVE.encode().replace(b"\n", nl), 1)
    data = data[:start] + body + data[end:]
    bot.write_bytes(data)
    main = src / "main.cpp"
    data = main.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    draft = b"                play_draft();"
    assert data.count(draft) == 1
    main.write_bytes(data.replace(draft, nl.join([
        b"                static bool capture_announced = false;",
        b'                if (!capture_announced) { std::puts("CODEX_STALL_CAPTURE"); capture_announced = true; }',
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
    assert len(log) < LOG_LIMIT and b"CODEX_STALL_CAPTURE" in log
    observations = [[int(x) for x in m] for m in re.findall(rb"CODEX_STALL_DELTA R(\d+) S(\d+) G(\d+)", log)]
    assert all(1 <= r <= 150 for r, _, _ in observations)
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
    jobs = [("stall",0,opp,mp,side,WASM) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    matched = sum(len({tuple(x[:3]) for x in r["differences"]}) for r in rows)
    affected = sorted({r["map"] for r in rows if r["differences"]})
    result = dict(engine=bench.ENGINE, fixture_sha256=bench.digest(WASM), cells=len(rows),
                  affected_maps=affected,
                  unique_decisions=matched, raw_calls=sum(len(r["differences"]) for r in rows),
                  faults=sum(r["faults"] for r in rows), rows=rows)
    path = Path(__file__).with_name("UNMAPPED_STALL_PROBE.json")
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k:v for k,v in result.items() if k!="rows"}, flush=True)

if __name__ == "__main__":
    main()
