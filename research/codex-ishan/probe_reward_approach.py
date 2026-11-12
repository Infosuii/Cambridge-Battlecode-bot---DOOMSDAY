"""Find equal-length approach moves that would end on a camp reward tile."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from probe_wait_payout import OPPONENTS, bench, partition

OUT = bench.CACHE / "reward-approach-dev"


def prepare(src):
    copytree(bench.ROOT / "bots/v92/src", src)
    apply(src / "bot.cpp", (
        ("        if (!walk_toward(goal) && !bit(goal, pos)) {",
         """        const vec2 codex_approach_start = pos;
        if (!walk_toward(goal) && !bit(goal, pos)) {"""),
        ("        if (!melee) {\n#if V58_ACT & 12", """        if (round <= 300 && walked && cheb(codex_approach_start, pos) == 1 && bit(goal, pos) &&
            !bit(g.tiles, pos) && w.enemies.empty() && hp >= 0.65f * max_hp &&
            bc::fuel_remaining() > rb::kTailReserve) {
            int remaining = 0, last = -1;
            for (int ci : g.camps) {
                const auto& c = w.camps[ci];
                if (c.dead) continue;
                ++remaining;
                if (bit(w.visible, c.pos) && c.hp <= strength * camp_dealt_mult) last = ci;
            }
            if (remaining == 1 && last >= 0) {
                const auto& camp = w.camps[last];
                const int distance = cheb(pos, camp.pos);
                for (vec2 dir : kDirs) {
                    const vec2 alternative = codex_approach_start + dir;
                    if (!in_bounds(alternative, w.width, w.height) || !bit(goal, alternative) ||
                        !bit(g.tiles, alternative) || bit(w.static_blocked, alternative) ||
                        bit(w.unit_tiles, alternative) || cheb(alternative, camp.pos) > distance ||
                        (bit(w.hot_zone, alternative) && !bit(w.hot_zone, pos))) continue;
                    std::printf("CODEX_REWARD_APPROACH R%d S%d C%d x%d y%d\\n",
                                round, slot, last, alternative.x, alternative.y);
                    break;
                }
            }
        }
        if (!melee) {
#if V58_ACT & 12"""),
    ))
    apply(src / "main.cpp", (("                play_draft();", """                static bool capture_announced = false;
                if (!capture_announced) { std::puts("CODEX_REWARD_APPROACH_CAPTURE"); capture_announced = true; }
                play_draft();"""),))


def play(job):
    row = bench.one(job, log_limit=1048576)
    case = OUT / "games" / f"probe-0-{row['opponent']}-{row['map']}-{row['side']}"
    with ZipFile(next(case.glob("*.repl26a"))) as bundle:
        log = bundle.read(f"team-{row['side'].lower()}.stdout")
    assert len(log) < 1048576 and b"CODEX_REWARD_APPROACH_CAPTURE" in log
    pattern = rb"CODEX_REWARD_APPROACH R(\d+) S(\d+) C(\d+) x(\d+) y(\d+)"
    events = [tuple(map(int, values)) for values in re.findall(pattern, log)]
    assert all(r <= 300 for r, _, _, _, _ in events)
    return {**row, "opportunities": events}


def main():
    bench.OUT = OUT
    project = OUT / "diagnostic"
    prepare(project / "src")
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for opponent in OPPONENTS:
        file, digest = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == digest
    (OUT / "games").mkdir()
    jobs = [("probe", 0, o, m, s, wasm) for m in partition("conf") for o in OPPONENTS for s in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(play, jobs))
    affected = [r for r in rows if r["opportunities"]]
    maps = sorted({r["map"] for r in affected})
    opponents = sorted({r["opponent"] for r in affected})
    errors = sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows)
    report = {"engine": bench.ENGINE, "wasm": bench.digest(wasm), "n": len(rows), "maps": maps, "opponents": opponents,
              "errors": errors, "events": sum(len(r["opportunities"]) for r in affected),
              "pass": len(maps) >= 2 and len(opponents) == 2 and not errors}
    with (bench.ROOT / "research/codex-ishan/REWARD_APPROACH_PROBE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "rows": rows}, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
