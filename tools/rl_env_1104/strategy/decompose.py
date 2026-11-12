"""Where are games won and lost? Score-margin decomposition over local match statistics (strategy lead, JOHNDOE #118).

Per team of every finished game (official engine statistics JSON, --statistics --json):
    submitted = collected_camp + collected_champion - lost_camp - lost_champion - held_at_end      (checked exactly)
so a game's margin (ours - theirs) splits into Δcamp collection, Δchampion-kill collection, Δdeath losses and Δgems
still held at the end. Also per team: deaths, kills, camp clears, earned gold, monster damage, gold per clear,
first submission round. Reports the share of margin variance each component carries, and for decided games the mean
component difference winner - loser, split by map split (training / development / unknown) so nothing is fit to the
reserved confirmation maps (those files are skipped).

usage (repo root): python tools/rl_env_1104/strategy/decompose.py [--glob 'runs/rl_env_1104/eval/*/work/g*.json' ...]
       [--manifest artifacts/tmp/rl_env_1104/eval_manifest.json] [--out research/rl_env_1104/strategy/decomposition.json]
"""
import argparse
import collections
import glob
import hashlib
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DEFAULT_GLOBS = ["runs/rl_env_1104/eval/*/work/g*.json", "artifacts/tmp/rl_env_1104/*/g*.json"]
COMP = ("collected_camp", "collected_champion", "lost_camp", "lost_champion", "held_at_end")


def team_rows(s: dict) -> dict:
    rows = {t["team"]: collections.Counter(submitted=float(t["submittedGems"])) for t in s["teams"]}
    for e in s["events"]:
        team = e["owner"].get("team")
        if team not in rows:
            continue
        r = rows[team]
        for x in e["entries"]:
            v = float(x["value"])
            if e["kind"] == "gemCollection":
                r["collected_" + ("camp" if x["context"] == "campGroup" else "champion")] += v
            elif e["kind"] == "gemLoss":
                r["lost_" + ("camp" if x["context"] == "camp" else "champion")] += v
            elif e["kind"] == "death":
                r["deaths"] += 1
            elif e["kind"] == "kill":
                r["kills"] += 1
            elif e["kind"] == "campClear":
                r["clears"] += 1
            elif e["kind"] == "gemSubmission" and v > 0 and "first_submit" not in r:
                r["first_submit"] = x["timestamp"]["round"]
    for tl in s["championTimelines"]:
        team = tl["owner"].get("team")
        if team in rows and tl["metric"] in ("earnedGold", "monsterDamageDone", "championDamageDone"):
            last = tl["runs"][-1]["value"] if tl["runs"] else "0"
            rows[team][tl["metric"]] += float(last)
    for r in rows.values():
        r["held_at_end"] = r["collected_camp"] + r["collected_champion"] - r["lost_camp"] - r["lost_champion"] - r["submitted"]
        r["gold_per_clear"] = r["earnedGold"] / r["clears"] if r["clears"] else 0.0
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--glob", nargs="+", default=DEFAULT_GLOBS)
    ap.add_argument("--manifest", default="artifacts/tmp/rl_env_1104/eval_manifest.json")
    ap.add_argument("--out", default="research/rl_env_1104/strategy/decomposition.json")
    a = ap.parse_args()
    with open(os.path.join(ROOT, a.manifest), encoding="utf-8") as f:
        man = json.load(f)
    split_of = {m["sha256"]: m["split"] for m in man["maps"]}
    seen, games = set(), []
    for g in a.glob:
        for path in sorted(glob.glob(os.path.join(ROOT, g))):
            try:
                with open(path, encoding="utf-8") as f:
                    s = json.load(f)
                m = s["match"]
            except Exception:
                continue
            if m.get("outcome") not in ("teamA", "teamB", "draw"):
                continue
            key = (m["mapHash"], m.get("seed"), tuple(sorted((t["team"], t["submittedGems"]) for t in s["teams"])),
                   m["roundsCompleted"])
            if key in seen:  # the same deterministic game reached through several runs
                continue
            seen.add(key)
            split = split_of.get(m["mapHash"], "unknown")
            if split == "confirmation_reserved":
                continue
            rows = team_rows(s)
            if set(rows) != {"teamA", "teamB"}:
                continue
            games.append(dict(split=split, outcome=m["outcome"], rounds=m["roundsCompleted"], rows=rows,
                              path=os.path.relpath(path, ROOT).replace(os.sep, "/")))
    out = dict(kind="score-margin decomposition over local statistics (diagnostic; not a policy fit)",
               games=len(games), by_split=dict(collections.Counter(g["split"] for g in games)))
    # exactness of the identity on every team row
    out["identity_max_abs_error"] = max(abs(r["held_at_end"] - (r["collected_camp"] + r["collected_champion"] -
                                            r["lost_camp"] - r["lost_champion"] - r["submitted"]))
                                        for g in games for r in g["rows"].values()) if games else None
    out["held_at_end_negative"] = sum(r["held_at_end"] < -1e-9 for g in games for r in g["rows"].values())
    report = {}
    for split in sorted(set(g["split"] for g in games)) + ["ALL"]:
        gs = [g for g in games if split == "ALL" or g["split"] == split]
        dec = [g for g in gs if g["outcome"] in ("teamA", "teamB")]
        if not dec:
            continue
        # margin = A - B; components with sign: + collection, - loss, - held
        D = {c: np.array([g["rows"]["teamA"][c] - g["rows"]["teamB"][c] for g in gs]) for c in COMP + ("submitted",)}
        signed = {"camp collection": D["collected_camp"], "champion-kill collection": D["collected_champion"],
                  "death losses (camp)": -D["lost_camp"], "death losses (champion)": -D["lost_champion"],
                  "held at end": -D["held_at_end"]}
        margin = D["submitted"]
        var = float(margin.var())
        # covariance share: sum_k cov(x_k, margin) / var(margin) = 1 exactly
        share = {k: round(float(np.cov(v, margin, bias=True)[0, 1]) / var, 4) if var else None for k, v in signed.items()}
        wl = collections.defaultdict(list)
        for g in dec:
            w, l = (g["rows"]["teamA"], g["rows"]["teamB"]) if g["outcome"] == "teamA" else (g["rows"]["teamB"], g["rows"]["teamA"])
            for c in COMP + ("submitted", "deaths", "kills", "clears", "earnedGold", "monsterDamageDone",
                             "championDamageDone", "gold_per_clear", "first_submit"):
                wl[c].append(w.get(c, 0.0) - l.get(c, 0.0))
        report[split] = dict(games=len(gs), decided=len(dec), margin_sd=round(var ** 0.5, 1),
                             margin_variance_share=share,
                             winner_minus_loser_mean={c: round(float(np.mean(v)), 2) for c, v in wl.items()},
                             winner_minus_loser_frac_positive={c: round(float(np.mean(np.array(v) > 0)), 3) for c, v in wl.items()})
    out["report"] = report
    out["sources_sha256"] = hashlib.sha256("|".join(sorted(g["path"] for g in games)).encode()).hexdigest()
    os.makedirs(os.path.dirname(os.path.join(ROOT, a.out)), exist_ok=True)
    with open(os.path.join(ROOT, a.out), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in ("games", "by_split", "identity_max_abs_error", "held_at_end_negative")}))
    for split, r in report.items():
        print(f"\n== {split}: {r['games']} games ({r['decided']} decided), margin sd {r['margin_sd']}")
        print("  share of margin variance:", r["margin_variance_share"])
        print("  winner - loser mean:", r["winner_minus_loser_mean"])
        print("  frac winner > loser:", r["winner_minus_loser_frac_positive"])


if __name__ == "__main__":
    main()
