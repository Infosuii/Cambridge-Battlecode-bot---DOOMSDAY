"""Measure late redundant arrivals in already-scored opening routes."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from qualify_local import partition

OUT = bench.CACHE / "redundant-arrival-dev"
OPPONENTS = ("x3inv", "public-khiri")

OBSERVE = r'''    if (round <= 150 && best >= 0 && w.enemies.empty() && w.has_field(best) && n_top >= 2 &&
        bc::fuel_remaining() >= static_cast<std::uint64_t>(tune::kDetSafety) + 10000) {
        const auto& job = w.groups[best];
        const int distance = w.group_distance(best, pos);
        if (job.state == GroupState::alive && distance < kUnreach && distance > range + 3) {
            const int my_eta = distance - range;
            const float left = job.hp_left(w.camps);
            bool redundant = false;
            for (const auto& ally : w.allies) {
                if (ally.id == my_id || ally.hp < 0.75f * ally.max_hp) continue;
                const auto it = std::find(ally_handle.begin(), ally_handle.end(), ally.id);
                if (it == ally_handle.end() || it - ally_handle.begin() >= kClaimSlots ||
                    claim_of(static_cast<int>(it - ally_handle.begin())) != best) continue;
                const int ally_dist = w.group_distance(best, ally.pos);
                if (ally_dist == kUnreach) continue;
                const float dps = std::max(1.0f, ally.strength + 0.25f * ally.focus);
                const float kill = left / dps;
                if (kill * job.strength >= 0.75f * ally.hp) continue;
                if (static_cast<float>(std::max(0, ally_dist - ally.range)) + kill + capture_time <= my_eta) {
                    redundant = true;
                    break;
                }
            }
            if (redundant) for (int i = 0; i < n_top; ++i) {
                const int alt = top[i].gi;
                if (alt == best || top[i].need != 1 || claim_count(alt) != 0 || w.groups[alt].gems == 0 ||
                    w.groups[alt].state == GroupState::respawning) continue;
                std::printf("CODEX_REDUNDANT R%d S%d G%d A%d\n", round, slot, best, alt);
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
    assert len(raw) < 1048576 and b"CODEX_REDUNDANT_CAPTURE" in raw
    pattern = rb"CODEX_REDUNDANT R(\d+) S(\d+) G(\d+) A(\d+)"
    events = [tuple(int(v) for v in m) for m in re.findall(pattern, raw)]
    assert all(r <= 150 and g != a for r, _, g, a in events)
    return {**row, "opportunities": events}


def main():
    bench.OUT = OUT
    project = OUT / "diagnostic"
    src = project / "src"
    copytree(bench.ROOT / "bots/v92/src", src)
    apply(src / "bot.cpp", (("    return best;\n}\n\n// Follow-up table for one champion alone", OBSERVE +
                             "    return best;\n}\n\n// Follow-up table for one champion alone"),))
    apply(src / "main.cpp", (("                play_draft();", """                static bool observed = false;
                if (!observed) { std::puts("CODEX_REDUNDANT_CAPTURE"); observed = true; }
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
    count = sum(len({tuple(v[1:]) for v in r["opportunities"]}) for r in rows)
    report = {"engine": bench.ENGINE, "wasm": bench.digest(wasm), "n": len(rows), "events": count,
              "affected_maps": maps, "affected_opponents": opponents, "errors": errors,
              "pass": len(maps) >= 2 and len(opponents) == 2 and not errors}
    with (bench.ROOT / "research/codex-ishan/REDUNDANT_ARRIVAL_PROBE.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump({**report, "rows": rows}, f, indent=2)
        f.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
