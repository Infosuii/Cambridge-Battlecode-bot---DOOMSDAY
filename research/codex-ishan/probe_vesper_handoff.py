"""Measure shared reward decisions that a healthy on-tile Vesper would change."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "vesper-handoff-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("v92", "x3inv")
LOG_LIMIT = 1048576

HANDOFF = """    std::optional<bool> handoff;
    if (round < 300 && bit(g.tiles, pos)) {
        for (const auto& ally : w.allies) {
            if (!bit(g.tiles, ally.pos)) continue;
            if (type == bc::champion_type::vesper_vale && hp >= 0.65f * max_hp) {
                handoff = false;
                break;
            }
            if (ally.type == bc::champion_type::vesper_vale && ally.hp >= 0.65f * ally.max_hp) {
                handoff = true;
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
    start = data.index(b"bool Bot::poorer_ally_takes(")
    end = data.index(b"bool Bot::a3_other_owner(", start)
    body = data[start:end]
    head = b"    const float mine = my_items();"
    tail = b"    return false;" + nl + b"}"
    assert body.count(head) == body.count(tail) == 1
    body = body.replace(head, b"    const bool original = [&]() {" + nl + head, 1)
    extra = """    return false;
    }();
""" + HANDOFF + r"""    if (handoff && *handoff != original) {
        std::printf("CODEX_VESPER_DELTA R%d S%d G%d T%d Y%d\n", round, slot, gi, on_tile_only, *handoff);
    }
    return original;
}"""
    body = body.replace(tail, extra.encode().replace(b"\n", nl), 1)
    bot.write_bytes(data[:start] + body + data[end:])
    main = src / "main.cpp"
    data = main.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    draft = b"                play_draft();"
    assert data.count(draft) == 1
    main.write_bytes(data.replace(draft, nl.join([
        b"                static bool capture_announced = false;",
        b'                if (!capture_announced) { std::puts("CODEX_VESPER_CAPTURE"); capture_announced = true; }',
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
    assert len(log) < LOG_LIMIT and b"CODEX_VESPER_CAPTURE" in log
    observations = [[int(x) for x in m] for m in re.findall(rb"CODEX_VESPER_DELTA R(\d+) S(\d+) G(\d+) T([01]) Y([01])", log)]
    assert all(0 < r < 300 for r, *_ in observations)
    native = json.loads((case / "native.json").read_bytes())
    picked = any(c["name"] == "Vesper Vale" and c["team"] == "team" + side
                 for c in native["roster"]["champions"])
    return {**row, "vesper_present":picked, "differences":observations}

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
    jobs = [("vesper",0,opp,mp,side,WASM) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    matched = sum(len({tuple(x[:3]) for x in r["differences"]}) for r in rows)
    affected = sorted({r["map"] for r in rows if r["differences"]})
    result = dict(engine=bench.ENGINE, fixture_sha256=bench.digest(WASM), cells=len(rows),
                  vespers=sum(r["vesper_present"] for r in rows), affected_maps=affected,
                  unique_decisions=matched, raw_calls=sum(len(r["differences"]) for r in rows),
                  faults=sum(r["faults"] for r in rows), rows=rows)
    path = Path(__file__).with_name("VESPER_HANDOFF_PROBE.json")
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k:v for k,v in result.items() if k!="rows"}, flush=True)

if __name__ == "__main__":
    main()
