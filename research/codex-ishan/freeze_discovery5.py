"""Freeze 16 discovery and eight confirmation losses outside all earlier samples."""
from collections import Counter
import argparse
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE.parents[1] / "artifacts/codex-p0"
RAW = CACHE / "discovery5"
TEAM = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"
RIVALS = {"QS2isLaw", "0xDEADBEEF", "bentheboss"}


def read(path):
    return json.loads(path.read_bytes())


def key(m):
    return m["opponent"], m["map"], m["side"], tuple(m["our_draft"] or ()), tuple(m["their_draft"] or ())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wave", type=int, choices=(5, 6, 7), default=5)
    wave = parser.parse_args().wave
    raw = CACHE / f"discovery{wave}"
    as_of = datetime.fromisoformat((raw / "as-of.txt").read_text().strip())
    teams = read(raw / "ladder.json")["teams"]
    ours = next(t for t in teams if t["teamId"] == TEAM)
    above = {t["teamId"]: t for t in teams if t["rank"] < ours["rank"] or t["name"] in RIVALS}
    assert sum(t["rank"] < ours["rank"] for t in above.values()) == ours["rank"] - 1
    prior_paths = [HERE / "DISCOVERY_SAMPLE.json", *(HERE / f"discovery{i}/DISCOVERY_SAMPLE.json" for i in (2, 3, 4))]
    prior_paths.extend(HERE / f"DISCOVERY{i}_SAMPLE.json" for i in range(5, wave))
    prior = [m for f in prior_paths for m in read(f)["matches"]]
    targeted = read(HERE / "uk-rivals/SAMPLE.json")["matches"]
    excluded = {m["groupId"] or m["matchId"] for m in prior} | {m["group"] for m in targeted}
    cells = {key(m) for m in prior} | {(m["opponent"], m["map"], m["side"], tuple(m["draft"]), tuple(m["opponent_draft"]))
                                       for m in targeted}
    paths = [*sorted((CACHE / "discovery48/raw").glob("ranked-*.json")), CACHE / "ranked-resume-1.json",
             *(CACHE / f"discovery{i}/matches.json" for i in range(3, wave + 1))]
    if wave == 7:
        paths.extend(sorted(raw.glob("ranked-page-*.json")))
    census = {m["matchId"]: m for f in paths for m in read(f)["matches"]}
    losses = []
    for m in census.values():
        if m["status"] != "finished" or not as_of - timedelta(hours=48) <= datetime.fromisoformat(m["createdAt"]) < as_of:
            continue
        if len(m["teams"]) != 2 or any(t["engineVersion"] != "2.0.0" for t in m["teams"]):
            continue
        us, opp = sorted(m["teams"], key=lambda t: t["teamId"] != TEAM)
        if us["teamId"] != TEAM or us["result"] != "loss" or opp["teamId"] not in above:
            continue
        rank = above[opp["teamId"]]
        row = dict(matchId=m["matchId"], groupId=m["groupId"], createdAt=m["createdAt"], map=m["map"], side=us["side"],
                   opponent=opp["name"], opp_team_id=opp["teamId"], opp_rank=rank["rank"], opp_rating=rank["rating"],
                   our_draft=us["draftPicks"], their_draft=opp["draftPicks"])
        if (row["groupId"] or row["matchId"]) not in excluded and key(row) not in cells:
            losses.append(row)
    counts = Counter()
    chosen = []
    ordered = sorted(losses, key=lambda r: sha256(f"discovery{wave}-1104:{r['matchId']}".encode()).digest())
    for row in ordered:
        group = row["groupId"] or row["matchId"]
        if group in excluded or key(row) in cells or counts[row["opp_team_id"]] >= 4:
            continue
        counts[row["opp_team_id"]] += 1
        excluded.add(group)
        cells.add(key(row))
        chosen.append({**row, "partition": "confirm" if len(chosen) % 3 == 2 else "discovery"})
        if len(chosen) == 24:
            break
    expected = 11 if wave == 7 else 24
    assert len(chosen) == expected, (len(chosen), len(losses), counts)
    result = {"as_of": as_of.isoformat(), "our_rank": ours["rank"], "ranked_census": len(census),
              "eligible_fresh_losses": len(losses), "source_sha256": {p.relative_to(CACHE).as_posix(): sha256(p.read_bytes()).hexdigest()
              for p in [*paths, raw / "ladder.json"]}, "matches": chosen}
    with (HERE / f"DISCOVERY{wave}_SAMPLE.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("Froze", len(chosen), "of", len(losses), "eligible losses at rank", ours["rank"], flush=True)


if __name__ == "__main__":
    main()
