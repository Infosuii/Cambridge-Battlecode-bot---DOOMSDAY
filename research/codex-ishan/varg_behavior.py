"""Recount the missing-Varg mechanism and freeze paired development fuel fixtures."""
from collections import Counter
import json

import ablate_dev as bench
from discovery_metrics import timeline
from engine3_pool import HERE, read
from freeze_engine3_discovery import write


def measure(row, output):
    directory = output / f"{row['noise_seed']}-{row['opponent']}" / f"{row['map']}-{row['side']}-{row['arm']}"
    doc = read(directory / "native.json")
    ours = "team" + row["side"]
    roster = [p["champion"] for p in doc["roster"]["draft"] if p["team"] == ours]
    varg = {"championTimelines": [r for r in doc["championTimelines"] if r["owner"]["team"] == ours and r["owner"]["name"] == "Varg"]}
    strength = sum(int(entry["value"]) for event in doc["events"] if event["kind"] == "buyItem" and event["owner"]["team"] == ours and event["owner"]["name"] == "Varg"
                   for entry in event["entries"] if "Strength" in entry["target"]["name"] and entry["timestamp"]["round"] <= 300)
    fuel = [{"champion": event["owner"]["name"], "round": entry["timestamp"]["round"]} for event in doc["events"] if event["kind"] == "fuelExhausted" and event["owner"]["team"] == ours for entry in event["entries"]]
    values = {"varg_picks": roster.count("Varg"), "marcella_picks": roster.count("Marcella"), "varg_strength_purchases300": strength,
              "varg_monster_damage300": timeline(varg, ours, "monsterDamageDone", 300) if varg["championTimelines"] else 0,
              **{f"team_{metric}_{r}": timeline(doc, ours, metric, r) for metric in ("monsterDamageDone", "earnedGold", "collectedGems", "deaths") for r in (150, 300)}}
    return roster, values, fuel, directory


def main():
    output = bench.CACHE / "engine3-live109-varg"
    rows = read(output / "rows.json")
    report = read(HERE / "ENGINE3_LIVE109_VARG_DEV.json")
    totals = {arm: Counter() for arm in ("base", "candidate")}
    changes, fixtures = Counter(), []
    used = set()
    for base, candidate in zip(rows[::2], rows[1::2], strict=True):
        before, bv, bf, bd = measure(base, output)
        after, cv, cf, cd = measure(candidate, output)
        totals["base"].update(bv)
        totals["candidate"].update(cv)
        changes["changed_rosters"] += sorted(before) != sorted(after)
        changes["added_varg_rosters"] += "Varg" not in before and "Varg" in after
        changes["removed_marcella_rosters"] += "Marcella" in before and "Marcella" not in after
        if not bf and cf and base["opponent"] not in used:
            used.add(base["opponent"])
            fixtures.append({k: base[k] for k in ("noise_seed", "opponent", "map", "map_hash", "engine_seed", "side", "category")})
            fixtures[-1].update({"base_roster": before, "candidate_roster": after, "base_events": bf, "candidate_events": cf,
                                 "base_directory": bd.relative_to(bench.ROOT).as_posix(), "candidate_directory": cd.relative_to(bench.ROOT).as_posix(),
                                 "base_binary": report["binaries"][f"base-{base['noise_seed']}"], "candidate_binary": report["binaries"][f"candidate-{candidate['noise_seed']}"]})
    moved = totals["candidate"]["varg_picks"] > totals["base"]["varg_picks"] and totals["candidate"]["varg_strength_purchases300"] > 0
    result = {"candidate_release": report["candidate_release"], "reference_release": report["reference_release"], "n_pairs": len(rows)//2,
              "mechanism_moved": moved, "totals": totals, "roster_changes": changes, "strength_filter_pass": report["pass"],
              "safety_failed": report["overall"]["fuel"][1] > report["overall"]["fuel"][0] or bool(report["overall"]["per_cell_fuel_regressions"])}
    write(HERE / "LIVE109_VARG_BEHAVIOR.json", result)
    write(HERE / "LIVE109_VARG_FUEL_FIXTURES.json", {"protocol": "First preregistered dev-cell order zero-to-nonzero fuel fixture per opponent; diagnosis only, no safety-pool or holdout identity. Reproduce with frozen paired noisy binaries, normal100k/log-limit0/engine3, map SHA verified.", "fixtures": fixtures})
    print(json.dumps(result, indent=2), flush=True)
    print("Native zero-to-nonzero fixture count", len(fixtures), flush=True)


if __name__ == "__main__":
    main()
