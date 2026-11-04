"""Compare opening completion-window rewards to v92 route rates."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "opening-window-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("x3inv", "public-khiri")
LOG_LIMIT = 1048576

def prepare():
    src = PROJECT / "src"
    copytree(bench.ROOT / "bots/v92/src", src)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"int Bot::route_search(")
    end = data.index(b"// Farming planner", start)
    body = data[start:end]
    edits = [
        (b"    int best_i = -1;", b"""    const bool opening = round <= 150;
    float window[8] = {};
    bool has_second[8] = {};
    int window_best = -1;
    int best_i = -1;"""),
        (b"        const float sticky =", b"""        if (opening && c.need == 1 && c.finish <= 49 && w.has_field(c.gi))
            window[i] = c.value;
        const float sticky ="""),
        (b"                if (rate > route) route = rate;", b"""                if (window[i] > 0.0f && done2 <= 49 && c.value + fv[g2] > window[i]) {
                    window[i] = c.value + fv[g2];
                    has_second[i] = true;
                }
                if (rate > route) route = rate;"""),
        (b"        if (route > best_rate)", b"""        if (window[i] > 0.0f && (window_best < 0 || window[i] > window[window_best]))
            window_best = i;
        if (route > best_rate)"""),
        (b"    return best_i;", b"""    if (best_i >= 0 && window_best >= 0 && window_best != best_i && has_second[window_best] &&
        window[best_i] > 0.0f && window[window_best] >= 1.25f * window[best_i])
        std::printf("CODEX_WINDOW_DELTA R%d S%d B%d W%d\\n", round, slot, top[best_i].gi, top[window_best].gi);
    return best_i;"""),
    ]
    for anchor, replace in edits:
        assert body.count(anchor) == 1, anchor
        body = body.replace(anchor, replace.replace(b"\n", nl), 1)
    data = data[:start] + body + data[end:]
    bot.write_bytes(data)
    main = src / "main.cpp"
    data = main.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    draft = b"                play_draft();"
    assert data.count(draft) == 1
    main.write_bytes(data.replace(draft, nl.join([
        b"                static bool capture_announced = false;",
        b'                if (!capture_announced) { std::puts("CODEX_WINDOW_CAPTURE"); capture_announced = true; }',
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
    assert len(log) < LOG_LIMIT and b"CODEX_WINDOW_CAPTURE" in log
    observations = [[int(x) for x in m] for m in re.findall(rb"CODEX_WINDOW_DELTA R(\d+) S(\d+) B(\d+) W(\d+)", log)]
    assert all(1 <= r <= 150 and b != w for r, _, b, w in observations)
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
    jobs = [("window",0,opp,mp,side,WASM) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    matched = sum(len({tuple(x) for x in r["differences"]}) for r in rows)
    affected = sorted({r["map"] for r in rows if r["differences"]})
    opponents = sorted({r["opponent"] for r in rows if r["differences"]})
    result = dict(engine=bench.ENGINE, fixture_sha256=bench.digest(WASM), cells=len(rows),
                  affected_maps=affected, affected_opponents=opponents,
                  unique_decisions=matched, raw_calls=sum(len(r["differences"]) for r in rows),
                  faults=sum(r["faults"] for r in rows), rows=rows)
    path = Path(__file__).with_name("OPENING_WINDOW_PROBE.json")
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k:v for k,v in result.items() if k!="rows"}, flush=True)

if __name__ == "__main__":
    main()
