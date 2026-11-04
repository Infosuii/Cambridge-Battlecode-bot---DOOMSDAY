"""Locate remaining PG runtime crossings using its existing charged profiler."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from pg_rivals import prepare

HERE = Path(__file__).resolve().parent
OUT = bench.CACHE / "pg-rival-runtime-r1"
LIMIT = 1048576
OPPONENTS = ("x3inv", "public-khiri")


def instrument(src):
    common = src / "common.h"
    data = common.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    common.write_bytes(b"#define APEX_PROFILE 1" + nl + data)
    apply(src / "main.cpp", (
        ("            if (bc::is_draft()) {\n                play_draft();",
         """            if (bc::is_draft()) {
                static bool capture_announced = false;
                if (!capture_announced) { std::puts("CODEX_PG_RUNTIME_CAPTURE"); capture_announced = true; }
                play_draft();"""),
    ))
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    spans = (
        (b"bool Bot::ward_ahead()", b"#if A2_FOG", (
            ("    const int mine = w.bush_cluster(pos);", """    PROF_CHECK("ahead_mine");
    const int mine = w.bush_cluster(pos);
    PROF_CHECK("ahead_allied");"""),
            ("    vec2 aim = pos;", """    PROF_CHECK("ahead_local");
    vec2 aim = pos;"""),
            ("    if (best.x < 0) return false;", """    PROF_CHECK("ahead_place");
    if (best.x < 0) return false;"""),
        )),
        (b"bool Bot::ward_reveal()", b"bool Bot::hidden_here()", (
            ("    const int mine = w.bush_cluster(pos);", """    PROF_CHECK("reactive_scan");
    const int mine = w.bush_cluster(pos);"""),
            ("    if (n == 0) return false;", """    PROF_CHECK("reactive_place");
    if (n == 0) return false;"""),
        )),
    )
    for first, last, edits in spans:
        start = data.index(first)
        end = data.index(last, start)
        body = data[start:end]
        for old, new in edits:
            old, new = (s.encode().replace(b"\n", nl) for s in (old, new))
            assert body.count(old) == 1, old
            body = body.replace(old, new, 1)
        data = data[:start] + body + data[end:]
    bot.write_bytes(data)
    # The upstream release has its own annotations around ward placement; keep
    # those and add only the unambiguous post-ambush marker.
    apply(bot, (
        ("    if (counter_ambush()) {", """    PROF_CHECK("ambush_enter");
    if (counter_ambush()) {
        PROF_CHECK("ambush_refresh");"""),
    ))


def play(job):
    row = bench.one(job, log_limit=LIMIT)
    _, _, opp, mp, side, _ = job
    case = OUT / "games" / f"profile-0-{opp}-{mp.stem}-{side}"
    with ZipFile(next(case.glob("*.repl26a"))) as z:
        log = z.read(f"team-{side.lower()}.stdout").replace(b"\0", b"")
    assert len(log) < LIMIT and b"CODEX_PG_RUNTIME_CAPTURE" in log
    crossings = Counter()
    examples = {}
    for line in re.findall(rb"A2SUS [^\n]+", log):
        trail = re.findall(rb"([a-zA-Z0-9_]+)=\d+(\*?)", line)
        for i, (tag, cross) in enumerate(trail):
            if not cross or i == 0:
                continue
            a = trail[i-1][0].decode()
            b = tag.decode()
            k = f"{a} -> {b}"
            crossings[k] += 1
            examples.setdefault(k, line.decode("utf-8", "replace"))
    return {**row, "crossings": dict(crossings), "examples": examples}


def main():
    project = OUT / "diagnostic"
    prepare(project / "src", True)
    instrument(project / "src")
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
    jobs = [("profile", 0, opp, mp, side, wasm) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(play, jobs))
    count = Counter()
    for row in rows:
        count.update(row["crossings"])
    result = {"engine": bench.ENGINE, "map_digest": md, "wasm": bench.digest(wasm), "n": len(rows),
              "fuel": sum(r["fuel_outs"] for r in rows), "faults": sum(r["faults"] for r in rows),
              "traced_crossings": count.total(), "crossings": dict(count.most_common()), "rows": rows}
    with (HERE / "PG_RUNTIME_PROFILE.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k != "rows"}, flush=True)


if __name__ == "__main__":
    main()
