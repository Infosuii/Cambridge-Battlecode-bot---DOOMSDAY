"""Check exact camp exclusions against the original square walk in the SDK."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from cpg_heart_camp_mask import prepare
from large_roster_stress import HERE, bench, read
from qualify_local import partition

OUT = bench.CACHE / "cpg-heart-camp-mask-proof"


def instrument(src):
    apply(src / "bot.cpp", (
        ("void Bot::play_turn() {", """static void verify_camp_mask(World& world) {
    const auto allies = bc::champions(bc::team::ally);
    if (allies.empty() || !(allies.front() == bc::self())) return;
    int tests = 0, differences = 0, exclusions = 0;
    const auto check = [&](int group, vec2 target, int radius) {
        const auto foreign = live_foreign_camps(world, group, target, radius);
        for (int dx = -radius; dx <= radius; ++dx) for (int dy = -radius; dy <= radius; ++dy) {
            const vec2 q{target.x + dx, target.y + dy};
            if (!in_bounds(q, world.width, world.height)) continue;
            bool old = false;
            for (int x = -radius; x <= radius; ++x) for (int y = -radius; y <= radius; ++y) {
                const int other = world.group_of_camp_tile({q.x + x, q.y + y});
                if (other >= 0 && other != group && world.groups[static_cast<std::size_t>(other)].state == GroupState::alive)
                    old = true;
            }
            const bool next = std::any_of(foreign.begin(), foreign.end(), [&](vec2 p) { return cheb(p, q) <= radius; });
            ++tests;
            exclusions += old;
            differences += old != next;
        }
    };
    const auto stride = std::max<std::size_t>(1, (world.groups.size() + 11) / 12);
    for (int state = 0; state < 2; ++state) {
        for (std::size_t gi = 0; gi < world.groups.size(); gi += stride) {
            const auto& g = world.groups[gi];
            if (g.camps.empty()) continue;
            for (int radius : {1, 2, 3}) check(static_cast<int>(gi), world.camps[g.camps.front()].pos, radius);
        }
        for (vec2 edge : {vec2{0, 0}, vec2{world.width - 1, world.height - 1},
                         vec2{world.width / 2, 0}, vec2{0, world.height / 2}}) check(-1, edge, 2);
        for (std::size_t i = 0; i < world.groups.size(); i += 2)
            world.groups[i].state = i % 4 == 0 ? GroupState::reward : GroupState::respawning;
    }
    std::printf("CODEX_HEART_MASK %d %d %d\\n", tests, differences, exclusions);
    bc::resign();
}

void Bot::play_turn() {"""),
        ('        PROF_CHECK("init");', '        PROF_CHECK("init");\n        verify_camp_mask(w);'),
    ))


def play(job):
    row = bench.one(job, fuel=10000000, log_limit=1048576)
    case = OUT / "games" / f"proof-0-v92-{row['map']}-{row['side']}"
    (archive,) = case.glob("*.repl26a")
    with ZipFile(archive) as z:
        log = z.read(f"team-{row['side'].lower()}.stdout")
    (match,) = re.findall(rb"CODEX_HEART_MASK (\d+) (\d+) (\d+)", log)
    tests, differences, exclusions = map(int, match)
    native = read(case / "native.json")
    errors = bool(native["diagnostics"]["codes"] or any(native["diagnostics"]["botFaults"].values()))
    return {**row, "tests": tests, "differences": differences, "exclusions": exclusions, "errors": errors}


def main():
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    project = OUT / "diagnostic"
    prepare(project / "src", True)
    instrument(project / "src")
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    file, expected = bench.OPPS["v92"]
    assert bench.digest(bench.CACHE / file) == expected
    jobs = [("proof", 0, "v92", mp, side, wasm) for mp in partition("conf") for side in "AB"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    errors = sum(bool(r["errors"] or r["fuel_outs"]) for r in rows)
    tests = sum(r["tests"] for r in rows)
    differences = sum(r["differences"] for r in rows)
    exclusions = sum(r["exclusions"] for r in rows)
    result = {"engine": bench.ENGINE, "diagnostic": bench.digest(wasm), "n": len(rows), "tests": tests,
              "differences": differences, "exclusions": exclusions, "errors": errors,
              "pass": len(rows) == 32 and exclusions > 0 and not differences and not errors}
    with (HERE / "CPG_HEART_CAMP_MASK_PROOF.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
