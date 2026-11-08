"""Ladder-game breakdown for our live bot from downloaded platform match summaries (cambc matches summary --json).

Per game (our side from the match index): outcome, opponent and rating, the exact margin split
(production / fights / camp losses / conversion, as resource_breakdown.py), deaths, kills, fuel-outs, camps cleared,
gems collected and banked by round 300/500/1000, and our draft. Aggregates by result and by opponent rating band,
plus per-champion death/kill/collection rates.

usage: python -I tools/rl_env_1104/strategy/ladder_breakdown.py data/ladder/live_v112_20261108 [--ladder ladder.jsonl] [--out f.json]
"""
import argparse
import collections
import json
import os
import statistics

ME = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"


def series(runs):
    v = []
    for r in runs:
        v.extend([float(r["value"])] * int(r["duration"]))
    return v


def at(v, r):
    return v[min(r, len(v) - 1)] if v else 0.0


def game_row(s, our):
    th = "teamB" if our == "teamA" else "teamA"
    led = {t: collections.Counter() for t in ("teamA", "teamB")}
    deaths = collections.Counter(); kills = collections.Counter(); fuel = collections.Counter()
    champ_team = {c["id"]: c["team"] for c in s["roster"]["champions"]}
    champ_name = {c["id"]: c["name"] for c in s["roster"]["champions"]}
    per_champ = collections.defaultdict(collections.Counter)
    first_death = {}
    for e in s["events"]:
        t = e["owner"].get("team"); oid = e["owner"].get("id")
        for x in e["entries"]:
            v = float(x["value"]) if e["kind"] in ("gemCollection", "gemLoss", "gemSubmission") else 1.0
            if e["kind"] == "gemCollection":
                led[t]["camp" if x["context"] == "campGroup" else "fight_in"] += v
                if t == our and x["context"] == "campGroup": per_champ[champ_name[oid]]["camp_gems"] += v
            elif e["kind"] == "gemLoss":
                led[t]["fight_out" if x["context"] == "champion" else "camp_loss"] += v
            elif e["kind"] == "gemSubmission":
                led[t]["banked"] += v
            elif e["kind"] == "campClear":
                led[t]["clears"] += 1
            elif e["kind"] == "death":
                deaths[t] += 1
                rd = x["timestamp"]["round"]
                first_death.setdefault(t, rd)
                if t == our: per_champ[champ_name[oid]]["deaths"] += 1
                if rd <= 300: deaths[t + "_300"] += 1
            elif e["kind"] == "kill":
                kills[t] += 1
            elif e["kind"] == "fuelExhausted":
                fuel[t] += 1
    for t in led:
        L = led[t]
        L["held"] = L["camp"] + L["fight_in"] - L["fight_out"] - L["camp_loss"] - L["banked"]
    U, T = led[our], led[th]
    sub = {x["owner"]: series(x["runs"]) for x in s["teamTimelines"] if x["metric"] == "submittedGems"}
    gold = collections.defaultdict(float)
    gems_tl = collections.defaultdict(float)
    for x in s["championTimelines"]:
        tm = champ_team.get(x["owner"]["id"])
        if x["metric"] == "earnedGold":
            gold[(tm, 300)] += at(series(x["runs"]), 300); gold[(tm, 1000)] += at(series(x["runs"]), 10 ** 6)
    row = dict(
        rounds=s["match"]["roundsCompleted"], win=s["match"]["outcome"] == our, lose=s["match"]["outcome"] == th,
        margin=U["banked"] - T["banked"], ours=U["banked"], theirs=T["banked"],
        production=U["camp"] - T["camp"], fights=(U["fight_in"] - U["fight_out"]) - (T["fight_in"] - T["fight_out"]),
        camp_losses=T["camp_loss"] - U["camp_loss"], conversion=T["held"] - U["held"],
        our_camp=U["camp"], their_camp=T["camp"], our_clears=U["clears"], their_clears=T["clears"],
        our_held=U["held"], their_held=T["held"], our_deaths=deaths[our], their_deaths=deaths[th],
        our_deaths300=deaths[our + "_300"], their_deaths300=deaths[th + "_300"],
        our_fuel=fuel[our], their_fuel=fuel[th], our_first_death=first_death.get(our, 9999), their_first_death=first_death.get(th, 9999),
        bank300=at(sub.get(our, []), 300), their_bank300=at(sub.get(th, []), 300),
        bank500=at(sub.get(our, []), 500), their_bank500=at(sub.get(th, []), 500),
        gold300=gold[(our, 300)], their_gold300=gold[(th, 300)], gold_end=gold[(our, 1000)], their_gold_end=gold[(th, 1000)],
        our_draft=[c["name"] for c in sorted(s["roster"]["champions"], key=lambda c: c["draftPick"]) if c["team"] == our],
        their_draft=[c["name"] for c in sorted(s["roster"]["champions"], key=lambda c: c["draftPick"]) if c["team"] == th],
        per_champ={k: dict(v) for k, v in per_champ.items()})
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--ladder")
    ap.add_argument("--out")
    a = ap.parse_args()
    idx = json.load(open(os.path.join(a.dir, "match_index.json"), encoding="utf-8"))
    rating = {}
    if a.ladder:
        for l in open(a.ladder, encoding="utf-8"):
            l = l.strip()
            if l:
                d = json.loads(l)
                for r in (d if isinstance(d, list) else (d.get("entries") or d.get("teams") or list(d.values())[0])):
                    rating[r["teamId"]] = r["rating"]
    rows = []
    for m in idx:
        f = os.path.join(a.dir, "summaries", m["matchId"] + ".json")
        if not os.path.exists(f) or os.path.getsize(f) < 1000:
            continue
        me = [t for t in m["teams"] if t["teamId"] == ME][0]; op = [t for t in m["teams"] if t["teamId"] != ME][0]
        s = json.load(open(f, encoding="utf-8"))
        r = game_row(s, "teamA" if me["side"] == "a" else "teamB")
        r.update(match=m["matchId"], map=m["map"], opp=op["name"], opp_rating=rating.get(op["teamId"]), created=m["createdAt"])
        rows.append(r)
    keys = ["margin", "production", "fights", "camp_losses", "conversion", "our_clears", "their_clears", "our_deaths",
            "their_deaths", "our_deaths300", "their_deaths300", "our_fuel", "our_first_death", "their_first_death",
            "bank300", "their_bank300", "bank500", "their_bank500", "gold300", "their_gold300", "gold_end", "their_gold_end",
            "our_held", "their_held"]
    out = dict(n=len(rows))
    for lab, sel in (("losses", lambda r: r["lose"]), ("wins", lambda r: r["win"]),
                     ("losses vs 2150+", lambda r: r["lose"] and (r["opp_rating"] or 0) >= 2150),
                     ("wins vs 2150+", lambda r: r["win"] and (r["opp_rating"] or 0) >= 2150)):
        rs = [r for r in rows if sel(r)]
        if rs:
            out[lab] = {k: round(statistics.mean(r[k] for r in rs), 1) for k in keys} | dict(n=len(rs))
    lost = [r for r in rows if r["lose"]]
    out["loss dominant component"] = dict(collections.Counter(min(("production", "fights", "camp_losses", "conversion"), key=lambda k: r[k]) for r in lost))
    out["losses where held >= deficit"] = sum(r["our_held"] >= -r["margin"] for r in lost)
    pc = collections.defaultdict(collections.Counter)
    for r in rows:
        for name, c in r["per_champ"].items():
            pc[name]["games"] += 1; pc[name]["wins"] += r["win"]
            for k, v in c.items():
                pc[name][k] += v
    out["per champion"] = {k: dict(games=v["games"], winrate=round(v["wins"] / v["games"], 2), deaths=round(v["deaths"] / v["games"], 2),
                                   camp_gems=round(v["camp_gems"] / v["games"], 1)) for k, v in sorted(pc.items(), key=lambda kv: -kv[1]["games"])}
    for k, v in out.items():
        print(k, v)
    if a.out:
        json.dump(dict(summary=out, rows=rows), open(a.out, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
