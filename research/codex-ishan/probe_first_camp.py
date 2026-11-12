"""Measure early opportunities to reinforce a visible tank with a higher-value camp."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile
import json
import re
import subprocess

import ablate_dev as bench

OUT = bench.CACHE / "first-camp-probe"
PROJECT = OUT / "diagnostic"
WASM = PROJECT / "bot.wasm"
OPPONENTS = ("x3inv", "public-khiri")
LOG_LIMIT = 1048576

OBSERVE = r"""    if (round <= 150 && !low_fuel && !in_role_pack && best >= 0 && best_need == 1 &&
        best_score > 0.0f && hp >= 0.65f * max_hp && w.enemies.empty() && claim_count(best) == 0 &&
        bc::fuel_remaining() > static_cast<std::uint64_t>(tune::kDetSafety) + 12000) {
        const float gold = gold_weight();
        const auto worth = [&](const GroupRec& group) {
            return static_cast<float>(group.gems) + gold * static_cast<float>(group.gold);
        };
        for (const auto& ally : w.allies) {
            if (ally.range > 1 || ally.hp < 0.8f * ally.max_hp) continue;
            const auto handle = std::find(ally_handle.begin(), ally_handle.end(), ally.id);
            if (handle == ally_handle.end() || handle - ally_handle.begin() >= kClaimSlots) continue;
            const int tank = claim_of(static_cast<int>(handle - ally_handle.begin()));
            if (tank < 0 || tank >= static_cast<int>(w.groups.size()) || tank == best || tank == target_group ||
                avoid_until[tank] > round || !w.has_field(tank) || w.group_distance(tank, pos) > 8 ||
                claim_count(tank) != 1) continue;
            const auto& group = w.groups[tank];
            if (group.state != GroupState::alive || worth(group) <= worth(w.groups[best])) continue;
            bool ready = false;
            for (int ci : group.camps) {
                const auto& camp = w.camps[ci];
                if (!camp.dead && bit(w.visible, camp.pos) && cheb(ally.pos, camp.pos) <= ally.range) {
                    ready = true;
                    break;
                }
            }
            if (!ready || champions_needed(group, group.hp_left(w.camps)) != 2) continue;
            for (const auto& other : w.allies) {
                if (other.id == ally.id || other.hp < 0.65f * other.max_hp) continue;
                const auto owner = std::find(ally_handle.begin(), ally_handle.end(), other.id);
                if (owner == ally_handle.end() || owner - ally_handle.begin() >= kClaimSlots) continue;
                const int job = claim_of(static_cast<int>(owner - ally_handle.begin()));
                if (job < 0 || job >= static_cast<int>(w.groups.size()) || job == tank || job == best) continue;
                if (w.groups[job].state != GroupState::alive || worth(w.groups[job]) >= worth(group)) continue;
                std::printf("CODEX_FIRSTCAMP_DELTA R%d S%d G%d T%d J%d\n", round, slot, best, tank, job);
                break;
            }
        }
    }
"""


def prepare():
    src = PROJECT / "src"
    copytree(bench.ROOT / "bots/v92/src", src)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"bool Bot::farm()")
    end = data.index(b"void Bot::opportunistic_attack()", start)
    body = data[start:end]
    anchor = b"    if (best != target_group) {"
    assert body.count(anchor) == 1
    body = body.replace(anchor, OBSERVE.encode().replace(b"\n", nl) + anchor, 1)
    data = data[:start] + body + data[end:]
    bot.write_bytes(data)
    main = src / "main.cpp"
    data = main.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    draft = b"                play_draft();"
    assert data.count(draft) == 1
    main.write_bytes(data.replace(draft, nl.join([
        b"                static bool capture_announced = false;",
        b'                if (!capture_announced) { std::puts("CODEX_FIRSTCAMP_CAPTURE"); capture_announced = true; }',
        draft,
    ]), 1))
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", PROJECT, "--release", "--output", WASM], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)

def run(job):
    row = bench.one(job, log_limit=LOG_LIMIT)
    arm, seed, opp, mp, side, _ = job
    case = OUT / "games" / f"{arm}-{seed}-{opp}-{mp.stem}-{side}"
    (path,) = case.glob("*.repl26a")
    with ZipFile(path) as archive:
        log = archive.read(f"team-{side.lower()}.stdout").replace(b"\0", b"")
    assert len(log) < LOG_LIMIT and b"CODEX_FIRSTCAMP_CAPTURE" in log
    observations = [[int(x) for x in m] for m in re.findall(rb"CODEX_FIRSTCAMP_DELTA R(\d+) S(\d+) G(\d+) T(\d+) J(\d+)", log)]
    assert all(1 <= r <= 150 and len({g, tank, job}) == 3 for r, _, g, tank, job in observations)
    return {**row, "differences":observations}


def main():
    prepare()
    bench.OUT = OUT
    for name in OPPONENTS:
        file, expected = bench.OPPS[name]
        assert bench.digest(bench.CACHE / file) == expected
    maps = sorted((bench.CACHE / "jd-sets/conf").glob("*.map26a"))
    assert len(maps) == 16
    digest = bench.sha256("\n".join(f"{bench.digest(p)} {p.name}" for p in maps).encode()).hexdigest()
    assert digest == "94b6b4b43167ba179171f6ff3d616d802531c5cd632704412126cc3a21506852"
    (OUT / "games").mkdir()
    jobs = [("first-camp",0,opp,mp,side,WASM) for mp in maps for opp in OPPONENTS for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    matched = sum(len({tuple(x[:4]) for x in r["differences"]}) for r in rows)
    affected = sorted({r["map"] for r in rows if r["differences"]})
    result = dict(engine=bench.ENGINE, fixture_sha256=bench.digest(WASM), cells=len(rows),
                  affected_maps=affected,
                  unique_decisions=matched, raw_calls=sum(len(r["differences"]) for r in rows),
                  faults=sum(r["faults"] for r in rows), rows=rows)
    path = Path(__file__).with_name("FIRST_CAMP_PROBE.json")
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k:v for k,v in result.items() if k!="rows"}, flush=True)

if __name__ == "__main__":
    main()
