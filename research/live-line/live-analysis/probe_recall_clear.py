"""Count one-hit camp checks at the point where a voluntary recall starts."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from probe_wait_payout import OPPONENTS, bench, partition

OUT = bench.CACHE / "recall-clear-dev"


def prepare(src):
    copytree(bench.ROOT / "bots/v92/src", src)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"bool Bot::go_home_if_needed() {")
    end = data.index(b"bool Bot::tribute_if_needed() {", start)
    block = data[start:end]
    for old, new in (
        ("    heading_home = true;", """    const bool new_shopping_trip = rich && !low && !heading_home;
    heading_home = true;"""),
        ("        try {\n            me.recall();\n            return true;", """        int clear_camp = -1;
        if (new_shopping_trip && round <= 300 && hp >= 0.65f * max_hp && w.enemies.empty() &&
            target_group >= 0 && target_group < static_cast<int>(w.groups.size()) &&
            bc::fuel_remaining() > rb::kTailReserve && me.can_attack()) {
            const auto& pending = w.groups[target_group];
            if (pending.state == GroupState::alive && bit(pending.tiles, pos)) {
                int alive = 0;
                for (int ci : pending.camps) {
                    const auto& c = w.camps[ci];
                    if (c.dead) continue;
                    ++alive;
                    if (bit(w.visible, c.pos) && cheb(c.pos, pos) <= range && c.hp <= strength * camp_dealt_mult)
                        clear_camp = ci;
                }
                if (alive != 1) clear_camp = -1;
            }
        }
        try {
            me.recall();
            if (clear_camp >= 0)
                std::printf("CODEX_RECALL_CLEAR R%d S%d G%d C%d\\n", round, slot, target_group, clear_camp);
            return true;"""),
    ):
        original = old.encode().replace(b"\n", nl)
        assert block.count(original) == 1
        block = block.replace(original, new.encode().replace(b"\n", nl))
    bot.write_bytes(data[:start] + block + data[end:])
    apply(src / "main.cpp", (("                play_draft();", """                static bool capture_announced = false;
                if (!capture_announced) { std::puts("CODEX_RECALL_CLEAR_CAPTURE"); capture_announced = true; }
                play_draft();"""),))


def play(job):
    row = bench.one(job, log_limit=1048576)
    case = OUT / "games" / f"probe-0-{row['opponent']}-{row['map']}-{row['side']}"
    with ZipFile(next(case.glob("*.repl26a"))) as bundle:
        log = bundle.read(f"team-{row['side'].lower()}.stdout")
    assert len(log) < 1048576 and b"CODEX_RECALL_CLEAR_CAPTURE" in log
    rows = [tuple(map(int, m)) for m in re.findall(rb"CODEX_RECALL_CLEAR R(\d+) S(\d+) G(\d+) C(\d+)", log)]
    assert all(1 <= r <= 300 for r, _, _, _ in rows)
    return {**row, "opportunities": rows}


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
    with (bench.ROOT / "research/codex-ishan/RECALL_CLEAR_PROBE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "rows": rows}, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
