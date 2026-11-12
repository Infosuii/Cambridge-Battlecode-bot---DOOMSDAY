"""Count missing wards that still suppress the active proactive branch."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from probe_wait_payout import OPPONENTS, bench, partition

OUT = bench.CACHE / "ward-expiry-dev"


def prepare(src):
    copytree(bench.ROOT / "bots/v92/src", src)
    apply(src / "bot.cpp", (
        ("bool Bot::ward_ahead() {", """static int codex_ward_round = -1, codex_expiry_sampled = -1;

bool Bot::ward_ahead() {"""),
        ("""    if (ward_pos.x >= 0 && cheb(ward_pos, pos) <= NOVA_WARD_AHEAD + static_cast<int>(std::lround(2.0f * LABK(39)))) return false; // our ward still covers this area""",
         """    if (ward_pos.x >= 0 && cheb(ward_pos, pos) <= NOVA_WARD_AHEAD + static_cast<int>(std::lround(2.0f * LABK(39)))) {
        if (round <= 600 && codex_ward_round >= 0 && codex_expiry_sampled != codex_ward_round &&
            round - codex_ward_round > bc::constants::ward_lifetime && target_group >= 0 &&
            target_group < static_cast<int>(w.groups.size()) &&
            w.groups[target_group].state == GroupState::alive && bc::fuel_remaining() > rb::kTailReserve &&
            bc::self().ward_cooldown() == 0) {
            std::uint32_t ward = 0;
            if (d::sdk_ally_ward_at(ward_pos.x, ward_pos.y, &ward) ==
                static_cast<int>(bc::error_code::api_not_found)) {
                codex_expiry_sampled = codex_ward_round;
                std::printf("CODEX_WARD_EXPIRY R%d S%d G%d placed%d life%d x%d y%d\\n", round, slot, target_group,
                            codex_ward_round, bc::constants::ward_lifetime, ward_pos.x, ward_pos.y);
            }
        }
        return false;
    }"""),
        ("            ward_pos = best;", "            ward_pos = best;\n            codex_ward_round = round;"),
        ("                ward_pos = cands[i].p;", "                ward_pos = cands[i].p;\n                codex_ward_round = round;"),
        ("        if (me.place_ward(at)) ward_pos = at;", """        if (me.place_ward(at)) {
            ward_pos = at;
            codex_ward_round = round;
        }"""),
        ("                        ward_pos = q;", "                        ward_pos = q;\n                        codex_ward_round = round;"),
    ))
    apply(src / "main.cpp", (("                play_draft();", """                static bool capture_announced = false;
                if (!capture_announced) { std::puts("CODEX_WARD_EXPIRY_CAPTURE"); capture_announced = true; }
                play_draft();"""),))


def play(job):
    row = bench.one(job, log_limit=1048576)
    case = OUT / "games" / f"probe-0-{row['opponent']}-{row['map']}-{row['side']}"
    with ZipFile(next(case.glob("*.repl26a"))) as bundle:
        log = bundle.read(f"team-{row['side'].lower()}.stdout")
    assert len(log) < 1048576 and b"CODEX_WARD_EXPIRY_CAPTURE" in log
    pattern = rb"CODEX_WARD_EXPIRY R(\d+) S(\d+) G(\d+) placed(\d+) life(\d+) x(\d+) y(\d+)"
    events = [tuple(map(int, values)) for values in re.findall(pattern, log)]
    assert all(r <= 600 and r > placed + lifetime for r, _, _, placed, lifetime, _, _ in events)
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
    with (bench.ROOT / "research/codex-ishan/WARD_EXPIRY_PROBE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "rows": rows}, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
