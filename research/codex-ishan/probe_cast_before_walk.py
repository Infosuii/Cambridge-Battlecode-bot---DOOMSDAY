"""Count existing camp approaches with a safe one-cast clear before walking."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from probe_wait_payout import OPPONENTS, bench, partition

OUT = bench.CACHE / "cast-before-walk-dev"


def prepare(src):
    copytree(bench.ROOT / "bots/v92/src", src)
    apply(src / "bot.cpp", (
        ('        mode = "approach";\n#if A2_APPROACHFIX', '''        mode = "approach";
        int codex_clear_slot = -1, codex_clear_camp = -1;
        if (round <= 300 && !walked && !cast_done && hp >= 0.65f * max_hp && w.enemies.empty() &&
            bc::fuel_remaining() > rb::kTailReserve) {
            bool threat = false;
            for (const auto& seen : w.sightings)
                if (round - seen.round <= 3 && cheb(seen.pos, pos) <= 6) { threat = true; break; }
            int remaining = 0;
            if (!threat) for (int ci : g.camps) {
                const auto& c = w.camps[ci];
                if (c.dead) continue;
                ++remaining;
                const int dist = cheb(pos, c.pos);
                if (!bit(w.visible, c.pos) || dist <= range) continue;
                for (int s = 0; s < 2; ++s) {
                    const auto& sp = spells[s];
                    if (spell_ready(s) && sp.excludes_walk && sp.camps && sp.kind == bc::ability_kind::damage &&
                        dist <= static_cast<int>(sp.range) && sp.modifier * focus * camp_dealt_mult >= c.hp) {
                        codex_clear_camp = ci;
                        codex_clear_slot = s;
                        break;
                    }
                }
            }
            if (remaining != 1) codex_clear_slot = -1;
        }
#if A2_APPROACHFIX'''),
        ('        PROF_CHECK("c_walked"); if (!melee) {', '''        if (codex_clear_slot >= 0 && walked)
            std::printf("CODEX_CAST_BEFORE_WALK R%d S%d C%d A%d\\n", round, slot, codex_clear_camp, codex_clear_slot);
        PROF_CHECK("c_walked"); if (!melee) {'''),
    ))
    apply(src / "main.cpp", (("                play_draft();", """                static bool capture_announced = false;
                if (!capture_announced) { std::puts("CODEX_CAST_BEFORE_WALK_CAPTURE"); capture_announced = true; }
                play_draft();"""),))


def play(job):
    row = bench.one(job, log_limit=1048576)
    case = OUT / "games" / f"probe-0-{row['opponent']}-{row['map']}-{row['side']}"
    with ZipFile(next(case.glob("*.repl26a"))) as bundle:
        log = bundle.read(f"team-{row['side'].lower()}.stdout")
    assert len(log) < 1048576 and b"CODEX_CAST_BEFORE_WALK_CAPTURE" in log
    pattern = rb"CODEX_CAST_BEFORE_WALK R(\d+) S(\d+) C(\d+) A(\d+)"
    events = [tuple(map(int, values)) for values in re.findall(pattern, log)]
    assert all(r <= 300 and ability in (0, 1) for r, _, _, ability in events)
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
    with (bench.ROOT / "research/codex-ishan/CAST_BEFORE_WALK_PROBE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "rows": rows}, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
