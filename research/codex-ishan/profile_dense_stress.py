"""Join dense stress native turns to narrow camp-strike and dash boundaries."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from dash_low_fuel_stress import instrument
from large_roster_stress import DENSE_OUT as RAW, HERE, bench, native_fuel, read
from pg_siege_resume import prepare
from profile_roster_stress import play_scoped, prepare_coarse

OUT = bench.CACHE / "dense-roster-profile"
STAGES = ("world", "wardrev", "ambush", "enemies", "farmsel", "c_safe", "camp_dash_enter", "camp_dash_done", "c_cast", "decide", "tail")


def main():
    affected = read(HERE / "DENSE_ROSTER_STRESS.json")["affected"]
    exact = read(RAW / "rows.json")
    maps_seen = {r["map"] for r in affected}
    controls = []
    for r in sorted(exact, key=lambda r: sha256(f"exp064:{r['map']}:{r['opponent']}:{r['side']}".encode()).digest()):
        if r["map"] in maps_seen or r["fuel_outs"]:
            continue
        maps_seen.add(r["map"])
        controls.append(r)
        if len(controls) == 6:
            break
    assert len(affected) == 7 and len(controls) == 6
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    project = OUT / "diagnostic"
    src = project / "src"
    prepare(src, True)
    apply(src / "bot.cpp", (
        ("        int best_hits = 0, best_home = kUnreach;", '        PROF_CHECK("camp_dash_enter");\n        int best_hits = 0, best_home = kUnreach;'),
        ("        if (best.x < 0 || best_hits <= 0) return false;", '        PROF_CHECK("camp_dash_done");\n        if (best.x < 0 || best_hits <= 0) return false;'),
    ))
    prepare_coarse(src, {e["timestamp"]["round"] for row in affected for e in row["events"]}, STAGES)
    instrument(src, "round == 26 && type == bc::champion_type::issac")
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    manifest = read(HERE / "DENSE_ROSTER_MAPS.json")["maps"]
    maps = {p.stem: p for p in (RAW / "maps").glob("*.map26a")}
    for row in affected + controls:
        mp = maps[row["map"]]
        assert bench.digest(mp) == manifest[mp.name]
        file, expected = bench.OPPS[row["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
    jobs = [("profile", 0, r["opponent"], maps[r["map"]], r["side"], wasm) for r in affected + controls]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(play_scoped, jobs))
    joins = []
    for base, row in zip(affected + controls, rows, strict=True):
        assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "side", "opponent"))
        exact_events = {(e["owner"]["name"], e["timestamp"]["round"]) for e in base.get("events", [])}
        matched = exact_events & {(e["owner"]["name"], e["timestamp"]["round"]) for e in native_fuel(row, OUT)}
        case = OUT / "games" / f"profile-0-{row['opponent']}-{row['map']}-{row['side']}"
        with ZipFile(next(case.glob("*.repl26a"))) as bundle:
            raw = bundle.read(f"team-{row['side'].lower()}.stdout")
        row["dash"] = [v.decode("ascii") for v in re.findall(rb"CODEX_DASH_STRESS [^\n]+", raw)]
        if matched:
            rounds = {r for _, r in matched}
            phases = [p for p, line in row["examples"].items() if int(re.search(r" R(\d+)", line).group(1)) in rounds]
            joins.append({"map": row["map"], "opponent": row["opponent"], "side": row["side"],
                          "matched_native": sorted(matched), "phases": phases, "dash": row["dash"]})
    result = {"wasm": bench.digest(wasm), "n": len(rows), "matches": joins, "fuel": sum(r["fuel_outs"] for r in rows),
              "errors": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows)}
    with (HERE / "DENSE_ROSTER_PROFILE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
