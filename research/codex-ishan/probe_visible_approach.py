"""Measure equal-length steps that bring the current visible camp into basic range."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from qualify_local import partition

OUT = bench.CACHE / "visible-approach-dev"
OPPONENTS = ("x3inv", "public-khiri")

OBSERVE = r'''    if (round <= 150 && melee && hp >= 0.75f * max_hp && n >= 2 && w.enemies.empty() &&
        target_group >= 0 && target_group < static_cast<int>(w.groups.size()) && std::string_view(mode) == "approach" &&
        bc::fuel_remaining() >= rb::kTailReserve + 8000) {
        const auto& group = w.groups[target_group];
        if (group.state == GroupState::alive) {
            const auto can_hit = [&](vec2 q) {
                for (int ci : group.camps) {
                    const auto& camp = w.camps[ci];
                    if (!camp.dead && bit(w.visible, camp.pos) && cheb(q, camp.pos) <= range) return true;
                }
                return false;
            };
            if (!can_hit(cands[0].p)) for (int i = 1; i < n && cands[i].score / 4 == cands[0].score / 4; ++i) {
                if (bit(w.hot_zone, cands[i].p) || !can_hit(cands[i].p)) continue;
                std::printf("CODEX_VISIBLE_STEP R%d S%d G%d x%d y%d ax%d ay%d\n", round, slot, target_group,
                            cands[0].p.x, cands[0].p.y, cands[i].p.x, cands[i].p.y);
                break;
            }
        }
    }
'''


def play(job):
    row = bench.one(job, log_limit=1048576)
    case = OUT / "games" / f"probe-0-{row['opponent']}-{row['map']}-{row['side']}"
    with ZipFile(next(case.glob("*.repl26a"))) as bundle:
        raw = bundle.read(f"team-{row['side'].lower()}.stdout")
    assert len(raw) < 1048576 and b"CODEX_VISIBLE_CAPTURE" in raw
    pattern = rb"CODEX_VISIBLE_STEP R(\d+) S(\d+) G(\d+) x(\d+) y(\d+) ax(\d+) ay(\d+)"
    observations = [tuple(int(x) for x in m) for m in re.findall(pattern, raw)]
    assert all(1 <= r <= 150 and (x, y) != (ax, ay) for r, _, _, x, y, ax, ay in observations)
    return {**row, "opportunities": observations}


def main():
    bench.OUT = OUT
    project = OUT / "diagnostic"
    src = project / "src"
    copytree(bench.ROOT / "bots/v92/src", src)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"bool Bot::follow_field(")
    anchor = data.index(b"#if A2_BRIDGES", start)
    assert anchor < data.index(b"bool Bot::walk_toward(", start)
    bot.write_bytes(data[:anchor] + OBSERVE.encode().replace(b"\n", nl) + data[anchor:])
    apply(src / "main.cpp", (("                play_draft();", """                static bool observed = false;
                if (!observed) { std::puts("CODEX_VISIBLE_CAPTURE"); observed = true; }
                play_draft();"""),))
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for o in OPPONENTS:
        file, expected = bench.OPPS[o]
        assert bench.digest(bench.CACHE / file) == expected
    (OUT / "games").mkdir()
    jobs = [("probe", 0, o, m, s, wasm) for m in partition("conf") for o in OPPONENTS for s in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(play, jobs))
    maps = sorted({r["map"] for r in rows if r["opportunities"]})
    opponents = sorted({r["opponent"] for r in rows if r["opportunities"]})
    errors = sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows)
    result = {"engine": bench.ENGINE, "wasm": bench.digest(wasm), "n": len(rows),
              "events": sum(len(r["opportunities"]) for r in rows), "affected_maps": maps, "affected_opponents": opponents,
              "error_cells": errors, "pass": len(maps) >= 2 and len(opponents) == 2 and not errors}
    with (bench.ROOT / "research/codex-ishan/VISIBLE_APPROACH_PROBE.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump({**result, "rows": rows}, f, indent=2)
        f.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
