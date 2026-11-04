"""Localize the three standard-budget events from the frozen seed-14107 stress run."""
from concurrent.futures import ThreadPoolExecutor
import json

from bounded_verdict import apply
from cpg_heart_cast_path import prepare
from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from pg_dash_followup import read_turn
from profile_roster_stress import prepare_coarse, summarize_scoped
from qualify_local import build
from stress_heart_cast_path import OUT as RAW, SEED

OUT = bench.CACHE / "heart-cast-path-stress-profile-14107"
STAGES = ("world", "support", "wardrev", "ambush", "e_in", "e_td", "enemies", "farm0",
          "farmsel", "d_farm", "decide", "tail", "fields", "bushpre")


def play(item):
    base, mp, wasm = item
    opponent, side = base["opponent"], base["side"]
    row = bench.one(("profile", SEED, opponent, mp, side, wasm), fuel=100000, log_limit=1048576)
    assert all(base[k] == row[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    key = f"{SEED}-{opponent}-{mp.stem}-{side}"
    old, new = RAW / "games" / f"path-{key}", OUT / "games" / f"profile-{key}"
    row = summarize_scoped(row, new)
    a, b = (read(p / "native.json") for p in (old, new))
    same_draft = a["roster"]["draft"] == b["roster"]["draft"]
    errors = bool(b["diagnostics"]["codes"] or any(b["diagnostics"]["botFaults"].values()))
    observed = native_fuel(row, OUT)
    checks = []
    for event in base["events"]:
        actor, rnd = event["owner"]["id"], event["timestamp"]["round"]
        old_turn, new_turn = (read_turn(p, rnd, side, actor) for p in (old, new))
        actions = [[a for a in t["executed_actions"] if a["kind"] not in (3, 26)] if t else []
                   for t in (old_turn, new_turn)]
        native_match = any(e["owner"] == event["owner"] and e["timestamp"]["round"] == rnd for e in observed)
        same_input = bool(old_turn and new_turn and old_turn["observation"] == new_turn["observation"])
        same_actions = bool(old_turn and new_turn and actions[0] == actions[1])
        phases = [phase for phase, marker in row["examples"].items() if f" R{rnd} " in marker]
        checks.append({"round": rnd, "actor": actor, "same_input": same_input, "same_actions": same_actions,
                       "same_event": native_match, "phases": phases,
                       "matched": same_draft and not errors and native_match and same_input and same_actions,
                       "base_turn": old_turn, "diagnostic_turn": new_turn})
    return {"base": base, "diagnostic": row, "same_draft": same_draft, "errors": errors,
            "observed": observed, "checks": checks}


def main():
    frozen = read(HERE / "CPG_HEART_CAST_PATH_STRESS.json")
    assert frozen["seed"] == SEED and frozen["n"] == 800
    cases = frozen["affected"]
    events = [(e["timestamp"]["round"], e["owner"]["name"].lower()) for r in cases for e in r["events"]]
    assert events == [(321, "cassi"), (334, "cassi"), (566, "issac")]
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    src = OUT / "source/src"
    prepare(src, True)
    rounds = sorted({rnd for rnd, _ in events})
    prepare_coarse(src, rounds, STAGES)
    initial = " || ".join(f"round == {rnd}" for rnd in rounds)
    condition = " || ".join(f"(round == {rnd} && type == bc::champion_type::{champion})" for rnd, champion in events)
    apply(src / "bot.cpp", ((f"    codex_stress_trace = {initial};", f"    codex_stress_trace = {condition};"),))
    wasm = build(src, OUT / "diagnostic", SEED)
    jobs = []
    for row in cases:
        mp = STRESS / "maps" / f"{row['map']}.map26a"
        assert bench.digest(mp) == row["map_hash"]
        file, expected = bench.OPPS[row["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
        jobs.append((row, mp, wasm))
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(play, jobs))
    matches = {r["round"]: r["phases"] for cell in rows for r in cell["checks"] if r["matched"]}
    result = {"engine": bench.ENGINE, "reference": frozen["wasm"], "diagnostic": bench.digest(wasm),
              "seed": SEED, "matches": matches, "n": len(rows)}
    with (HERE / "CPG_HEART_CAST_PATH_STRESS_TRACE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
