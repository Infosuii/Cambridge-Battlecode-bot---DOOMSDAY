"""Find observed reachable rewards during a safe early respawn wait."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply
from qualify_local import partition

OUT = bench.CACHE / "wait-payout-dev"
OPPONENTS = ("x3inv", "public-khiri")

OBSERVE = r'''        if (round <= 150 && w.enemies.empty() && hp >= 0.75f * max_hp && w.has_field(best) &&
            w.group_distance(best, pos) <= range + 1 && !bit(g.tiles, pos) &&
            bc::fuel_remaining() >= static_cast<std::uint64_t>(tune::kDetSafety) + 12000) {
            int payout = -1, best_trip = g.respawn_round - round;
            for (int i = 0; i < static_cast<int>(w.groups.size()); ++i) {
                const auto& reward = w.groups[i];
                if (reward.state != GroupState::reward || reward.seen_round != round || reward.gems == 0 ||
                    !w.has_field(i) || claim_count(i) != 0) continue;
                const int there = w.group_distance(i, pos);
                if (there > 8) continue;
                int back = 0;
                for (int ci : reward.camps) back = std::max(back, w.group_distance(best, w.camps[ci].pos));
                const int trip = there + back + capture_time + 2;
                if (trip < best_trip) payout = i, best_trip = trip;
            }
            if (payout >= 0)
                std::printf("CODEX_WAIT_PAYOUT R%d S%d G%d P%d trip%d wait%d\n",
                            round, slot, best, payout, best_trip, g.respawn_round - round);
        }
'''


def play(job):
    row = bench.one(job, log_limit=1048576)
    case = OUT / "games" / f"probe-0-{row['opponent']}-{row['map']}-{row['side']}"
    with ZipFile(next(case.glob("*.repl26a"))) as bundle:
        raw = bundle.read(f"team-{row['side'].lower()}.stdout")
    assert len(raw) < 1048576 and b"CODEX_WAIT_CAPTURE" in raw
    pattern = rb"CODEX_WAIT_PAYOUT R(\d+) S(\d+) G(\d+) P(\d+) trip(\d+) wait(\d+)"
    matches = [tuple(int(v) for v in m) for m in re.findall(pattern, raw)]
    assert all(r <= 150 and g != p and trip < wait for r, _, g, p, trip, wait in matches)
    return {**row, "opportunities": matches}


def main():
    bench.OUT = OUT
    project = OUT / "diagnostic"
    src = project / "src"
    copytree(bench.ROOT / "bots/v92/src", src)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"    case GroupState::respawning: {", data.index(b"bool Bot::farm()"))
    anchor = data.index(b"        bc::bitboard goal;", data.index(b"        if (tune::kUseWaits) {", start))
    bot.write_bytes(data[:anchor] + OBSERVE.encode().replace(b"\n", nl) + data[anchor:])
    apply(src / "main.cpp", (("                play_draft();", """                static bool observed = false;
                if (!observed) { std::puts("CODEX_WAIT_CAPTURE"); observed = true; }
                play_draft();"""),))
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
    maps = sorted({r["map"] for r in rows if r["opportunities"]})
    opponents = sorted({r["opponent"] for r in rows if r["opportunities"]})
    errors = sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows)
    report = {"engine": bench.ENGINE, "wasm": bench.digest(wasm), "n": len(rows), "affected_maps": maps,
              "affected_opponents": opponents, "errors": errors, "events": sum(len(r["opportunities"]) for r in rows),
              "pass": len(maps) >= 2 and len(opponents) == 2 and not errors}
    with (bench.ROOT / "research/codex-ishan/WAIT_PAYOUT_PROBE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "rows": rows}, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
