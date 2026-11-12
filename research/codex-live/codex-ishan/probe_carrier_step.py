"""Measure exposed carrier steps with an equally short safer alternative."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "carrier-step-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("v92", "x3inv")
LOG_LIMIT = 1048576

OBSERVE = r"""                if (codex_probe_carrier_route && gems >= 30 && !walked && !w.enemies.empty()) {
                    auto exposed = [&](vec2 q) {
                        for (const auto& e : w.enemies)
                            if (cheb(e.pos, q) <= e.range + 1) return true;
                        return false;
                    };
                    if (exposed(pos) && exposed(cands[i].p)) {
                        for (int j = 0; j < n; ++j) {
                            if (j == i || cands[j].score / 4 != cands[i].score / 4) continue;
                            if (bit(w.hot_zone, cands[j].p) || exposed(cands[j].p)) continue;
                            std::printf("CODEX_CARRIER_DELTA R%d S%d G%d\n", round, slot, gems);
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
    start = data.index(b"bool Bot::follow_field(")
    end = data.index(b"bool Bot::try_teleport(", start)
    helper = """namespace {
bool codex_probe_carrier_route = false;
struct CodexCarrierScope {
    CodexCarrierScope() { codex_probe_carrier_route = true; }
    ~CodexCarrierScope() { codex_probe_carrier_route = false; }
};
}

"""
    body = data[start:end]
    anchor = b"            if (me.move_absolute(cands[i].p)) {"
    assert body.count(anchor) == 1
    body = body.replace(anchor, anchor + nl + OBSERVE.encode().replace(b"\n", nl), 1)
    data = data[:start] + helper.encode().replace(b"\n", nl) + body + data[end:]
    for anchor in (
        b"    if (!follow_field(w.spawn_field, blocked, true)) {",
        b"    if (!follow_field(walk_field, blocked, true) && tune::kUnstick && !walk_toward(w.altar_ring))",
    ):
        assert data.count(anchor) == 1, anchor
        data = data.replace(anchor, b"    CodexCarrierScope codex_probe_route;" + nl + anchor, 1)
    bot.write_bytes(data)
    main = src / "main.cpp"
    data = main.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    draft = b"                play_draft();"
    assert data.count(draft) == 1
    main.write_bytes(data.replace(draft, nl.join([
        b"                static bool capture_announced = false;",
        b'                if (!capture_announced) { std::puts("CODEX_CARRIER_CAPTURE"); capture_announced = true; }',
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
    assert len(log) < LOG_LIMIT and b"CODEX_CARRIER_CAPTURE" in log
    observations = [[int(x) for x in m] for m in re.findall(rb"CODEX_CARRIER_DELTA R(\d+) S(\d+) G(\d+)", log)]
    assert all(r > 0 and gems >= 30 for r, _, gems in observations)
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
    jobs = [("carrier",0,opp,mp,side,WASM) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    matched = sum(len({tuple(x[:3]) for x in r["differences"]}) for r in rows)
    affected = sorted({r["map"] for r in rows if r["differences"]})
    result = dict(engine=bench.ENGINE, fixture_sha256=bench.digest(WASM), cells=len(rows),
                  affected_maps=affected,
                  unique_decisions=matched, raw_calls=sum(len(r["differences"]) for r in rows),
                  faults=sum(r["faults"] for r in rows), rows=rows)
    path = Path(__file__).with_name("CARRIER_STEP_PROBE.json")
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k:v for k,v in result.items() if k!="rows"}, flush=True)

if __name__ == "__main__":
    main()
