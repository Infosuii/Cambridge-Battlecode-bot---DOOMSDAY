"""Separate ward search, placement and post-action observation in dev fuel trails."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
import re
import shutil
import subprocess
from zipfile import ZipFile

import ablate_dev as bench

OUT = bench.CACHE / "runtime-ward-split"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("v92", "x3inv")
LOG_LIMIT = 1048576
SOURCE = bench.ROOT / "bots/v92/src"
RESULT = "RUNTIME_WARD_SPLIT.json"
DEEP = False
FARM = False

def prepare():
    src = PROJECT / "src"
    shutil.copytree(SOURCE, src)
    header = src / "common.h"
    header.write_bytes(b"#define A2_TEL 1\n" + header.read_bytes())
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    edits = [
        ("bool Bot::ward_ahead() {", 'bool Bot::ward_ahead() {\n    PROF_CHECK("ahead_enter");'),
        ("bool Bot::ward_reveal() {", 'bool Bot::ward_reveal() {\n    PROF_CHECK("reveal_enter");'),
        ("    if (!hit && lost.x < 0) return NOVA_WARD_AHEAD > 0 && ward_ahead();",
         '    if (!hit && lost.x < 0) return NOVA_WARD_AHEAD > 0 && ward_ahead();\n    PROF_CHECK("reactive_enter");'),
        ("    if (ward_reveal()) w.update(round); // the ward shows the bush now: look again",
         '    if (ward_reveal()) {\n        PROF_CHECK("ward_placed");\n        w.update(round);\n        PROF_CHECK("ward_update_done");\n    }'),
        ("        // We moved (into the attacker's bush, or away from it): look again before deciding.",
         '        PROF_CHECK("ambush_moved");\n        // We moved (into the attacker\'s bush, or away from it): look again before deciding.'),
    ]
    for before, after in edits:
        key = before.encode().replace(b"\n", newline)
        assert data.count(key) == 1, before
        data = data.replace(key, after.encode().replace(b"\n", newline), 1)
    if DEEP:
        start = data.index(b"bool Bot::ward_ahead() {")
        end = data.index(b"\nbool ", start)
        region = data[start:end]
        for anchor, mark in [
            ("    const int mine = w.bush_cluster(pos);", "ahead_mine"),
            ("    vec2 aim = pos;", "ahead_coverage_done"),
            ("    if (best.x < 0) return false;", "ahead_scan_done"),
            ("        const bc::bitboard wt = bc::vision::ward_tiles(team::ally);", "ahead_coverage_enter"),
            ("        if (me.place_ward(best)) {", "ahead_place"),
        ]:
            key = anchor.encode()
            assert region.count(key) == 1, anchor
            prefix = " " * (len(anchor)-len(anchor.lstrip()))
            region = region.replace(key, (prefix + f'PROF_CHECK("{mark}");').encode() + newline + key, 1)
        data = data[:start] + region + data[end:]
    if FARM:
        def insert(start, end, entries):
            nonlocal data
            first = data.index(start)
            last = data.index(end, first+len(start))
            region = data[first:last]
            for before, mark in entries:
                key = before.encode()
                assert region.count(key) == 1, before
                prefix = " " * (len(before)-len(before.lstrip()))
                region = region.replace(key, (prefix + f'PROF_CHECK("{mark}");').encode() + newline + key, 1)
            data = data[:first] + region + data[last:]

        insert(b"bool Bot::farm()", b"void Bot::opportunistic_attack()", [
            ('        mode = "capture";', "farm_capture"),
            ('        mode = "wait-respawn";', "farm_respawn"),
        ])
        insert(b"bool Bot::fight_camps(", b"bool Bot::farm()", [
            ('    auto pick_target = [&]() {', "camp_enter"),
            ('    const float incoming = incoming_from_group(g, pos);', "camp_threat"),
            ('        mode = "stage";', "camp_stage"),
            ('            mode = "siege";', "camp_siege"),
            ('    struct NearCamp {', "camp_safety_scan"),
            ('        mode = "disengage";', "camp_disengage"),
            ('    if (t < 0 && NOVA_BUSH_WARD && reveal_bush_camp(g)) t = pick_target();', "camp_bush_ward"),
        ])
        insert(b"bool Bot::walk_toward(", b"bool Bot::ward_ahead()", [
            ('    PROF(move);', "walk_enter"),
            ('    std::uint16_t levels = field.compute_to_with_expansion_count(fblocked, goals, single(pos), visited, cap);', "walk_compute"),
            ('        levels = field.compute_to_with_expansion_count(terrain, goals_in & ~w.static_blocked, single(pos), visited, cap);', "walk_terrain"),
            ('    if (tp_held != 0 && !combat_move && w.enemies.empty() && try_teleport(field)) return true;', "walk_teleport"),
        ])
    bot.write_bytes(data)
    world = src / "world.cpp"
    data = world.read_bytes()
    needle = b"void World::update(int round) {"
    assert data.count(needle) == 1
    world.write_bytes(data.replace(needle, needle + newline + b'    PROF_CHECK("world_update_enter");', 1))
    build()


def build():
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI,"build",PROJECT,"--release","--output",WASM], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)

def run(job):
    row = bench.one(job, log_limit=LOG_LIMIT)
    arm, seed, opp, mp, side, _ = job
    case = OUT / "games" / f"{arm}-{seed}-{opp}-{mp.stem}-{side}"
    (path,) = case.glob("*.repl26a")
    with ZipFile(path) as archive:
        raw = archive.read(f"team-{side.lower()}.stdout")
    assert len(raw) < LOG_LIMIT
    log = raw.replace(b"\0", b"").decode("ascii", "replace")
    spans = Counter()
    examples = {}
    for trail in re.findall(r"(?m)^A2SUS [^\r\n]+", log):
        marks = re.findall(r"(\w+)=(\d+)(\*?)", trail)
        phase = ""
        for left, right in zip(marks, marks[1:]):
            if left[0] in ("ward_placed", "ambush_moved", "wardrev", "refresh"):
                phase = left[0]
            if right[2]:
                key = f"{left[0]} -> {right[0]}"
                if phase and left[0].startswith(("world_update", "w_")):
                    key = f"{phase}: {key}"
                spans[key] += 1
                examples.setdefault(key, trail)
    return {**row, "stdout_bytes":len(raw), "spans":dict(spans), "examples":examples}

def main():
    global OUT, PROJECT, WASM, SOURCE, RESULT, DEEP, FARM
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--detail", choices=("v92", "codex-ward-local-labels", "farm", "codex-siege-rays", "codex-siege-lazy"))
    ap.add_argument("--rebuild-prepared", action="store_true", help="Retry compilation of a previously prepared diagnostic")
    args = ap.parse_args()
    if args.detail:
        FARM = args.detail in ("farm", "codex-siege-rays", "codex-siege-lazy")
        DEEP = not FARM
        SOURCE = bench.ROOT / "bots" / ("v92" if args.detail == "farm" else args.detail) / "src"
        OUT = bench.CACHE / f"runtime-ward-detail-{args.detail}"
        PROJECT = OUT / "diagnostic"
        WASM = PROJECT / "bot.wasm"
        RESULT = f"RUNTIME_WARD_DETAIL_{args.detail.upper()}.json"
    if args.rebuild_prepared:
        assert (PROJECT / "src").is_dir() and not (OUT / "games").exists()
        build()
    else:
        prepare()
    bench.OUT = OUT
    for name in OPPONENTS:
        path, expected = bench.OPPS[name]
        assert bench.digest(bench.CACHE / path) == expected
    maps = sorted((bench.CACHE / "jd-sets/conf").glob("*.map26a"))
    assert len(maps) == 16
    assert bench.sha256("\n".join(f"{bench.digest(p)} {p.name}" for p in maps).encode()).hexdigest() == "94b6b4b43167ba179171f6ff3d616d802531c5cd632704412126cc3a21506852"
    (OUT / "games").mkdir()
    jobs = [("profile",0,opp,mp,side,WASM) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    totals = Counter()
    for row in rows:
        totals.update(row["spans"])
    assert totals and any(r["stdout_bytes"] for r in rows)
    examples = {}
    for row in rows:
        for span, trail in row.pop("examples").items():
            examples.setdefault(span, {"map":row["map"],"opponent":row["opponent"],"side":row["side"],"trail":trail})
    result = {"engine":bench.ENGINE,"fixture_sha256":bench.digest(WASM),"cells":len(rows),
              "native_fuel_outs":sum(r["fuel_outs"] for r in rows),"traced_crossings":sum(totals.values()),
              "crossings":dict(totals.most_common()),"examples":examples,"rows":rows}
    target = bench.ROOT / "research/codex-ishan" / RESULT
    with target.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result,out,indent=2)
        out.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("examples","rows")},indent=2),flush=True)

if __name__ == "__main__":
    main()
