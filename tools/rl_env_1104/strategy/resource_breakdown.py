"""Resource breakdown of match outcomes from official gem events (JOHNDOE #170).

Gem accounting per team (engine events; exact): banked = camp + fight_in - fight_out - camp_loss - held_at_end, where
  camp       gemCollection context campGroup     (camp production)
  fight_in   gemCollection context champion      (bags taken from enemy champions)
  fight_out  gemLoss context champion            (our bags taken by enemy champions)
  camp_loss  gemLoss context camp                (bags lost to camps)
  held       gems still carried at the end       (carry not converted)
The final margin (our banked - their banked) therefore splits exactly into
  production  = our camp - their camp
  fights      = 2 x our net fight transfer (fight_in - fight_out; a transfer moves gems between the two teams)
  camp losses = their camp_loss - our camp_loss
  conversion  = their held - our held
Also counts camps cleared (campClear). Per candidate: outcome-conditioned means, plus a matched-cell comparison
against a reference candidate on the same map/side/opponent.

usage: python -I tools/rl_env_1104/strategy/resource_breakdown.py <run_eval dir> --cand v111 --ref v109 [--out f.json]
"""
import argparse
import collections
import json
import os
import statistics


def team_ledger(s: dict) -> dict:
    led = {t: collections.Counter() for t in ("teamA", "teamB")}
    for e in s["events"]:
        t = e["owner"].get("team")
        if t not in led:
            continue
        for x in e["entries"]:
            v = float(x["value"])
            if e["kind"] == "gemCollection":
                led[t]["camp" if x["context"] == "campGroup" else "fight_in"] += v
            elif e["kind"] == "gemLoss":
                led[t]["fight_out" if x["context"] == "champion" else "camp_loss"] += v
            elif e["kind"] == "gemSubmission":
                led[t]["banked"] += v
            elif e["kind"] == "campClear":
                led[t]["clears"] += 1
    for t in led:
        L = led[t]
        L["held"] = L["camp"] + L["fight_in"] - L["fight_out"] - L["camp_loss"] - L["banked"]
    return led


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--cand", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    rep = json.load(open(os.path.join(a.run, "report.json"), encoding="utf-8"))
    norm = lambda p: os.path.abspath(p).replace("\\", "/").lower()
    cands = {norm(v): k for k, v in rep["candidates"].items()}
    opps = {norm(v): k for k, v in rep["opponents"].items()}
    work = os.path.join(a.run, "work")
    rows = []
    for i, line in enumerate(open(os.path.join(work, "batch.txt"), encoding="utf-8")):
        q = line.split()
        pa, pb = q[0].lower(), q[1].lower()
        if pa in cands and pb in opps:
            c, o, our = cands[pa], opps[pb], "teamA"
        elif pb in cands and pa in opps:
            c, o, our = cands[pb], opps[pa], "teamB"
        else:
            continue
        s = json.load(open(os.path.join(work, f"g{i}.json"), encoding="utf-8"))
        th = "teamB" if our == "teamA" else "teamA"
        led = team_ledger(s)
        U, T = led[our], led[th]
        sc = {t["team"]: float(t["submittedGems"]) for t in s["teams"]}
        assert abs(U["banked"] - sc[our]) < 1e-6 and abs(T["banked"] - sc[th]) < 1e-6
        margin = U["banked"] - T["banked"]
        comp = dict(production=U["camp"] - T["camp"], fights=(U["fight_in"] - U["fight_out"]) - (T["fight_in"] - T["fight_out"]),
                    camp_losses=T["camp_loss"] - U["camp_loss"], conversion=T["held"] - U["held"])
        assert abs(sum(comp.values()) - margin) < 1e-6
        rows.append(dict(cand=c, opp=o, map=q[2].split("/")[-1], side="A" if our == "teamA" else "B",
                         win=s["match"]["outcome"] == our, lose=s["match"]["outcome"] == th, margin=margin,
                         our_clears=U["clears"], their_clears=T["clears"], our_camp=U["camp"], their_camp=T["camp"],
                         our_held=U["held"], their_held=T["held"], **comp))
    keys = ["margin", "production", "fights", "camp_losses", "conversion", "our_clears", "their_clears", "our_held", "their_held"]
    out = {}

    def summ(rs):
        return {k: round(statistics.mean(r[k] for r in rs), 1) for k in keys} | dict(n=len(rs))

    for c in (a.cand, a.ref):
        for res, f in (("losses", lambda r: r["lose"]), ("wins", lambda r: r["win"])):
            rs = [r for r in rows if r["cand"] == c and f(r)]
            if rs:
                out[f"{c} {res}"] = summ(rs)
    # matched cells: candidate minus reference on the same map/side/opponent
    idx = {(r["cand"], r["opp"], r["map"], r["side"]): r for r in rows}
    pairs = [(idx[(a.cand, o, m, sd)], r) for (cc, o, m, sd), r in idx.items() if cc == a.ref and (a.cand, o, m, sd) in idx]
    for label, sel in (("all cells", lambda x, y: True), ("cand lost", lambda x, y: x["lose"]),
                       ("cand lost, ref won", lambda x, y: x["lose"] and y["win"]), ("cand won, ref lost", lambda x, y: x["win"] and y["lose"])):
        ps = [(x, y) for x, y in pairs if sel(x, y)]
        if ps:
            out[f"matched {label}: {a.cand} - {a.ref}"] = {k: round(statistics.mean(x[k] - y[k] for x, y in ps), 1) for k in keys} | dict(n=len(ps))
    # in candidate losses: which component carries the deficit?
    lost = [r for r in rows if r["cand"] == a.cand and r["lose"]]
    dom = collections.Counter(min(("production", "fights", "camp_losses", "conversion"), key=lambda k: r[k]) for r in lost)
    out[f"{a.cand} losses: most negative component"] = dict(dom)
    out[f"{a.cand} losses: held >= |margin|"] = sum(r["our_held"] >= -r["margin"] for r in lost)
    for k, v in out.items():
        print(k, v)
    if a.out:
        json.dump(dict(run=a.run, summary=out, rows=rows), open(a.out, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
