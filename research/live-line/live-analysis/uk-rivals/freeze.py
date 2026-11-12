"""Freeze direct DOOMSDAY replay cases and controls for the three UK rivals."""
from collections import Counter
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
CACHE = OUT.parents[2] / "artifacts/codex-p0"
RAW = CACHE / "uk-targets-1104"
OUR = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"
TARGETS = {
    "QS2isLaw": "6bbc4925-89d1-4523-beac-b651d41bf945",
    "0xDEADBEEF": "f92d0bbd-519e-4f8b-b8bd-0d909f4ca0ee",
    "bentheboss": "a4247250-fa1e-4d33-811d-d94667bf7a2b",
}


def read(path):
    return json.loads(path.read_bytes())


def game(m, target, source):
    sides = {t["teamId"]: t for t in m["teams"]}
    if set(sides) != {OUR, TARGETS[target]} or m["status"] != "finished":
        return None
    ours, rival = sides[OUR], sides[TARGETS[target]]
    if any(t["engineVersion"] != "2.0.0" for t in sides.values()):
        return None
    return {"id": m["matchId"], "group": m["groupId"] or m["matchId"], "date": m["createdAt"],
            "map": m["map"], "opponent": target, "source": source, "side": ours["side"],
            "result": ours["result"], "draft": ours["draftPicks"], "opponent_draft": rival["draftPicks"]}


def main():
    paths = [*sorted((CACHE / "discovery48/raw").glob("ranked-*.json")), CACHE / "ranked-resume-1.json",
             CACHE / "discovery3/matches.json", CACHE / "discovery4/matches.json", *sorted(RAW.glob("*-ranked.json"))]
    ranked = {m["matchId"]: m for f in paths for m in read(f)["matches"]}
    plan = read(CACHE / "archived-plan-c-readonly.json")
    selected = []
    sizes = {}
    for target in TARGETS:
        if target == "QS2isLaw":
            # The captured recent ranked census has no direct QS matches. Use every
            # match from both pre-existing v92 arms, without filtering on outcome.
            ids = [gid for g, gid in zip(plan["groups"], plan["arms"]["v92"]["groups"], strict=True)
                   if g["opponent"] == target]
            rows = [game(m, target, "archived Plan C v92 unranked")
                    for gid in ids for m in read(CACHE / "duel-group-cache" / f"{gid}.json")["matches"]]
            assert len(rows) == 10 and all(rows)
            selected.extend(rows)
            sizes[target] = dict(Counter(row["result"] for row in rows))
            continue
        direct = [row for m in ranked.values() if (row := game(m, target, "ranked"))]
        sizes[target] = dict(Counter(row["result"] for row in direct))
        for result, limit in (("loss", 6), ("win", 4)):
            per_group = Counter()
            keys = set()
            for row in sorted(direct, key=lambda r: (r["date"], r["id"]), reverse=True):
                key = (row["map"], row["side"], tuple(row["draft"]), tuple(row["opponent_draft"]))
                if row["result"] != result or per_group[row["group"]] >= 2 or key in keys:
                    continue
                selected.append(row)
                per_group[row["group"]] += 1
                keys.add(key)
                if len(keys) == limit:
                    break
    payload = {"protocol": "Direct rivals. Ranked samples are outcome-stratified descriptive cases and controls; "
                           "Plan C historical QS arm includes every case. No rating or causal estimate from the sample.",
               "ranked_inputs": {p.relative_to(CACHE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths}, "direct_rows_in_census": sizes, "matches": selected}
    with (OUT / "SAMPLE.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(sizes, len(selected), flush=True)


if __name__ == "__main__":
    main()
