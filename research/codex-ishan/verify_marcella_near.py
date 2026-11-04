"""Check whether the identical greedy edit removes the independent Marcella continuation."""
import json

from cpg_greedy_near import apply_nearby
from large_roster_stress import HERE, OUT as GENERATED, bench, native_fuel, read
from pg_dash_followup import read_turn
from pg_travel_scan import prepare
from probe_continuation_farm import CASES
from qualify_local import build


def main():
    _, rnd, actor, side, name, opponent, seed = CASES[1]
    root = bench.CACHE / "marcella-greedy-near"
    bench.OUT = root
    (root / "games").mkdir(parents=True)
    archive = bench.CACHE / "travel-scan-roster-noise"
    report = read(HERE / "TRAVEL_SCAN_ROSTER_NOISE.json")
    reference_hash = report["binaries"][str(seed)]
    mp = GENERATED / "maps" / f"{name}.map26a"
    assert bench.digest(mp) == read(HERE / "LARGE_ROSTER_MAPS.json")["maps"][mp.name]
    file, expected = bench.OPPS[opponent]
    assert bench.digest(bench.CACHE / file) == expected
    binaries = {}
    for enabled in (False, True):
        arm = "near" if enabled else "off"
        src = root / arm / "src"
        prepare(src, True)
        apply_nearby(src, enabled)
        binaries[arm] = build(src, root / f"{arm}-{seed}", seed)
    assert bench.digest(binaries["off"]) == reference_hash
    row = bench.one(("near", seed, opponent, mp, side, binaries["near"]), fuel=100000)
    original = archive / "games" / f"stress-{seed}-{opponent}-{name}-{side}"
    current = root / "games" / f"near-{seed}-{opponent}-{name}-{side}"
    a, b = (read(p / "native.json") for p in (original, current))
    assert all(a["match"][k] == b["match"][k] for k in ("seed", "mapHash", "engineBuildHash"))
    base, candidate = (read_turn(p, rnd, side, actor) for p in (original, current))
    same_input = bool(base and candidate and base["observation"] == candidate["observation"])
    before, after = ([a for a in t["executed_actions"] if a["kind"] not in (3, 26)] if t else []
                     for t in (base, candidate))
    same_prefix = bool(base and candidate and before == after[:len(before)])
    events = native_fuel(row, root)
    removed = not any(e["timestamp"]["round"] == rnd and e["owner"]["id"] == actor for e in events)
    same_draft = a["roster"]["draft"] == b["roster"]["draft"]
    errors = bool(b["diagnostics"]["codes"] or any(b["diagnostics"]["botFaults"].values()))
    result = {"engine": bench.ENGINE, "reference": reference_hash, "candidate": bench.digest(binaries["near"]),
              "round": rnd, "actor": actor, "same_input": same_input, "same_action_prefix": same_prefix,
              "same_draft": same_draft, "native_event_removed": removed, "errors": errors,
              "pass": same_input and same_prefix and same_draft and removed and not events and not errors,
              "row": row, "events": events}
    with (HERE / "MARCELLA_GREEDY_NEAR.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "base_turn": base, "candidate_turn": candidate}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
