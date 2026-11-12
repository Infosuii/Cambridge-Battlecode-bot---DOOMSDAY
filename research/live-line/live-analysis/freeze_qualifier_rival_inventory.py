"""Read-only inventory of all visible matches against the three requested qualifier rivals."""
from collections import Counter, defaultdict

from audit_ranked_112_114_transition import RIVALS, TEAM, time
from audit_uploaded_112_114 import write
from engine3_pool import HERE, bench, read

OUT = bench.CACHE / "qualifier-rival-inventory-20261109"
BASE = HERE / "RANKED_112_114_TRANSITION_PLAN.json"
PLAN = HERE / "QUALIFIER_RIVAL_INVENTORY_20261109.json"
CUTOFF = "2026-11-06T08:45:00Z"


def main():
    pages = {}
    records = {}
    for kind in ("ranked", "unranked"):
        files = sorted(OUT.glob(f"{kind}-*.json"))
        assert files and (OUT / "finished-utc.txt").is_file()
        rows = []
        for i, path in enumerate(files, 1):
            assert path.name == f"{kind}-{i:02}.json"
            doc = read(path)
            pages[path.name] = bench.digest(path)
            rows.extend(doc["matches"])
        assert rows and all(row["kind"] == kind for row in rows)
        assert len({r["matchId"] for r in rows}) == len(rows)
        assert all(time(a["createdAt"]) >= time(b["createdAt"]) for a, b in zip(rows, rows[1:]))
        assert time(rows[-1]["createdAt"]) < time(CUTOFF) or not doc["nextCursor"]
        records[kind] = [row for row in rows if time(row["createdAt"]) >= time(CUTOFF)]
    prior = {r["match"] for r in read(BASE)["cells"] if r["native_requested"]}
    by_rival = defaultdict(list)
    named = []
    for kind, rows in records.items():
        for row in rows:
            if row["status"] != "finished":
                continue
            own, = (team for team in row["teams"] if team["teamId"] == TEAM)
            rival, = (team for team in row["teams"] if team["teamId"] != TEAM)
            if rival["teamId"] not in RIVALS:
                continue
            match = {"id": row["matchId"], "group": row["groupId"], "position": row["position"],
                     "rival_id": rival["teamId"], "name": RIVALS[rival["teamId"]], "created": row["createdAt"],
                     "kind": kind, "map": row["map"], "map_id": row["mapId"], "side": own["side"],
                     "result": own["result"], "prior_native": row["matchId"] in prior}
            named.append(match)
            by_rival[kind, match["name"]].append(match)
    buckets = {}
    for (kind, rival), rows in sorted(by_rival.items()):
        groups = defaultdict(list)
        for row in rows:
            groups[row["group"]].append(row)
        full = [group for group in groups.values() if len(group) == 5 and len({r["position"] for r in group}) == 5]
        full.sort(key=lambda group: (min(time(row["created"]) for row in group), group[0]["group"]))
        if kind == "unranked" and rival == "QS2isLaw":
            subset = full
        elif kind == "unranked" and rival == "bentheboss":
            # Cover the time window without choosing by result or map.
            n = min(8, len(full))
            subset = [full[((2 * i + 1) * len(full)) // (2 * n)] for i in range(n)]
        elif kind == "ranked" and rival == "0xDEADBEEF":
            subset = full
        else:
            subset = []
        selected = {row["id"] for group in subset for row in group}
        for row in rows:
            row["native_requested"] = row["id"] in selected
        buckets[kind + "/" + rival] = {"games": len(rows), "groups": len(groups), "complete_groups": len(full),
                                       "record": dict(Counter(row["result"] for row in rows)),
                                       "selected_native": len(selected),
                                       "new_native": sum(row["native_requested"] and not row["prior_native"] for row in rows)}
    named.sort(key=lambda row: (time(row["created"]), row["id"]))
    write(PLAN, {"cutoff": CUTOFF, "listed_utc": (OUT / "finished-utc.txt").read_text().strip(),
                 "page_sha256": pages, "prior_plan_sha256": bench.digest(BASE),
                 "inventory": {kind: dict(Counter(row["status"] for row in rows)) for kind, rows in records.items()},
                 "buckets": buckets, "named": named,
                 "selection": "All complete unranked QS2isLaw groups, eight evenly spaced complete unranked bentheboss groups, all complete ranked 0xDEADBEEF groups. No result, map or draft selection. Reuse exact previous native pins when present.",
                 "limits": "Unranked is mixed origin and may use pinned or older opponents. These records lack submission IDs. Snapshot counts provide matchup coverage, not current release strength."})
    print(buckets, flush=True)


if __name__ == "__main__":
    main()
