"""Freeze and recount a read-only ranked transition sample without inferring bot pins."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import mean

from audit_uploaded_112_114 import write
from engine3_pool import ENGINE, HERE, bench, read

OUT = bench.CACHE / "late-qualifier-ranked-20261108"
TEAM = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"
RIVALS = {
    "6bbc4925-89d1-4523-beac-b651d41bf945": "QS2isLaw",
    "a4247250-fa1e-4d33-811d-d94667bf7a2b": "bentheboss",
    "f92d0bbd-519e-4f8b-b8bd-0d909f4ca0ee": "0xDEADBEEF",
}
PLAN = HERE / "RANKED_112_114_TRANSITION_PLAN.json"
FIRST = "2026-11-08T05:30:00Z"
V113_CUTOFF = "2026-11-08T22:08:01.621Z"
V114_UPLOADED = "2026-11-08T23:08:16.270Z"
V114_ACTIVE_READ = "2026-11-08T23:40:34.375Z"
V114_SAMPLE_END = "2026-11-08T23:50:59Z"


def time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def interval(created):
    t = time(created)
    for boundary, label in (
        (FIRST, "pre-window"),
        (V113_CUTOFF, "before_v113_switch"),
        (V114_UPLOADED, "v113_time_window"),
        (V114_ACTIVE_READ, "v114_transition"),
        (V114_SAMPLE_END, "after_v114_active_timestamp"),
    ):
        if t < time(boundary):
            return label
    return "after-sample"


def collect():
    files = sorted(OUT.glob("ranked-[0-9][0-9].json")) + [OUT / "ranked-refresh.json"]
    rows = {}
    for path in files:
        for row in read(path)["matches"]:
            assert row["kind"] == "ranked"
            if row["matchId"] in rows:
                prior = rows[row["matchId"]]
                assert all(prior[k] == row[k] for k in ("createdAt", "kind", "groupId", "position", "mapId"))
                if prior["status"] == "finished":
                    assert prior == row or row["status"] != "finished"
                    continue
            rows[row["matchId"]] = row
    assert min(time(row["createdAt"]) for row in rows.values()) < time(FIRST)
    return rows, files


def freeze():
    rows, files = collect()
    groups = defaultdict(list)
    for row in rows.values():
        groups[row["groupId"]].append(row)
    cells = []
    incomplete = []
    for gid, group in groups.items():
        labels = {interval(row["createdAt"]) for row in group}
        assert len(labels) == 1
        label = labels.pop()
        if label in ("pre-window", "after-sample"):
            continue
        if len(group) != 5 or len({r["position"] for r in group}) != 5 or any(r["status"] != "finished" for r in group):
            incomplete.append({"group": gid, "window": label, "listed": len(group), "statuses": dict(Counter(r["status"] for r in group))})
            continue
        for row in group:
            ours, = (t for t in row["teams"] if t["teamId"] == TEAM)
            rival, = (t for t in row["teams"] if t["teamId"] != TEAM)
            cells.append({"match": row["matchId"], "group": gid, "window": label, "created": row["createdAt"],
                          "map": row["map"], "map_id": row["mapId"], "side": ours["side"], "result": ours["result"],
                          "rival": rival["name"], "rival_id": rival["teamId"],
                          "native_requested": time(row["createdAt"]) >= time("2026-11-08T21:30:00Z") or rival["teamId"] in RIVALS})
    cells.sort(key=lambda row: (time(row["created"]), row["match"]))
    manifest = {"captured": datetime.now(timezone.utc).isoformat(), "window_bounds": [FIRST, V113_CUTOFF, V114_UPLOADED, V114_ACTIVE_READ, V114_SAMPLE_END],
                "raw_pages": {p.name: bench.digest(p) for p in files},
                "source_status": {p.name: bench.digest(p) for p in OUT.glob("submissions-*.json")},
                "ladder": bench.digest(OUT / "ladder-top100.json"), "visible_match_ids": len(rows),
                "incomplete": incomplete, "cells": cells,
                "limits": "Ranked time windows, no per-match submission identity; ladder ratings are at capture time. Native sample uses all complete groups from 21:30 and all named-rival cells in the earlier window, independent of outcome."}
    write(PLAN, manifest)
    print(len(cells), sum(r["native_requested"] for r in cells), incomplete, flush=True)


def event_rounds(doc, team, kind):
    return [int(e["timestamp"]["round"]) for group in doc["events"]
            if group["kind"] == kind and group.get("owner", {}).get("team") == team for e in group["entries"]]


def numeric_summary(values):
    if not values:
        return None
    return {"n": len(values), "sum": sum(values), "mean": round(mean(values), 3)}


def recount():
    plan = read(PLAN)
    rows, files = collect()
    assert len(rows) == plan["visible_match_ids"]
    assert {p.name: bench.digest(p) for p in files} == plan["raw_pages"]
    assert {p.name: bench.digest(p) for p in OUT.glob("submissions-*.json")} == plan["source_status"]
    assert bench.digest(OUT / "ladder-top100.json") == plan["ladder"]
    standings = read(OUT / "ladder-top100.json")["teams"]
    ranks = {team["teamId"]: team for team in standings}
    result = {}
    native_rows = []
    for row in plan["cells"]:
        entry = rows[row["match"]]
        assert entry["createdAt"] == row["created"] and interval(entry["createdAt"]) == row["window"]
        assert entry["groupId"] == row["group"] and entry["mapId"] == row["map_id"]
        own = next(t for t in entry["teams"] if t["teamId"] == TEAM)
        opp = next(t for t in entry["teams"] if t["teamId"] != TEAM)
        assert (own["side"], own["result"], opp["teamId"]) == (row["side"], row["result"], row["rival_id"])
        win = result.setdefault(row["window"], defaultdict(list))
        win["all"].append(row)
        win[row["rival_id"]].append(row)
        if not row["native_requested"]:
            continue
        path = OUT / "native" / (row["match"] + ".json")
        doc = read(path)
        match, diag = doc["match"], doc["diagnostics"]
        assert (match["engineVersion"], match["engineBuildHash"]) == ("3.0.0", ENGINE)
        assert diag["detailedCaptureComplete"]
        side = "team" + row["side"].upper()
        rival = "teamB" if side == "teamA" else "teamA"
        assert match["outcome"] == {"win": side, "loss": rival, "draw": "draw"}[row["result"]]
        fuel = event_rounds(doc, side, "fuelExhausted")
        other_fuel = event_rounds(doc, rival, "fuelExhausted")
        native_rows.append({"match": row["match"], "window": row["window"], "rival_id": row["rival_id"],
                            "result": row["result"], "native_sha256": bench.digest(path), "map_sha256": match["mapHash"],
                            "rounds_started": match["roundsStarted"], "fuel": len(fuel), "r1": fuel.count(1),
                            "rival_fuel": len(other_fuel), "rival_r1": other_fuel.count(1),
                            "faults": diag["botFaults"][side], "rival_faults": diag["botFaults"][rival],
                            "codes": diag["codes"]})
    compact = {}
    for label, buckets in result.items():
        compact[label] = {}
        for who, cells in buckets.items():
            identity = "all" if who == "all" else ranks.get(who, {}).get("name", cells[0]["rival"])
            natives = [r for r in native_rows if r["window"] == label and (who == "all" or r["rival_id"] == who)]
            compact[label][who] = {"name": identity, "groups": len({r["group"] for r in cells}),
                                   "record": dict(Counter(r["result"] for r in cells)),
                                   "natives": len(natives), "our_fuel": numeric_summary([r["fuel"] for r in natives]),
                                   "our_r1": sum(r["r1"] for r in natives), "rival_r1": sum(r["rival_r1"] for r in natives),
                                   "rival_fuel": numeric_summary([r["rival_fuel"] for r in natives]),
                                   "our_faults": sum(r["faults"] for r in natives), "rival_faults": sum(r["rival_faults"] for r in natives),
                                   "native_code_cells": sum(bool(r["codes"]) for r in natives)}
    write(HERE / "RANKED_112_114_TRANSITION_RESULT.json",
          {"plan_sha256": bench.digest(PLAN), "standings": {k: ranks.get(k) for k in (TEAM, *RIVALS)},
           "windows": compact, "native_rows": native_rows})
    for label, buckets in compact.items():
        print(label, {v["name"]: (v["record"], v["our_fuel"]) for k, v in buckets.items() if k in ("all", *RIVALS)})


if __name__ == "__main__":
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument("action", choices=("freeze", "recount"))
    if args.parse_args().action == "freeze":
        freeze()
    else:
        recount()
