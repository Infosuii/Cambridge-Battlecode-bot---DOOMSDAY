"""Read-only Phase 0 evidence from captured CLI responses and frozen Git records."""
from collections import Counter, defaultdict
from random import Random

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "artifacts/codex-p0"
OUT = Path(__file__).resolve().parent
OUR_ID = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"
JD = "cb8d0105e4047f75924556268f23053eb634699a"
HANDOVER = "33c16873bae27d68d0076c730b025dda3e9cd898"

def read(name):
    return json.loads((CACHE / name).read_text(encoding="utf-8-sig"))

def git_json(ref, path):
    return json.loads(subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT))

def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")

def our_game(match):
    us, opp = sorted(match["teams"], key=lambda x: x["teamId"] != OUR_ID)
    assert us["teamId"] == OUR_ID
    return (opp["teamId"], match["map"], us["side"], us["result"])

def group_key(games):
    return tuple(our_game(m)[:3] for m in sorted(games, key=lambda m: m["position"]))

def expected_key(group):
    return tuple(zip([group["opponentId"]] * 5, group["maps"], group["sides"]))

def main():
    subs = read("submissions-list---json.json")
    old = read("submissions-list---before-86---json.json")
    versions = sorted(subs["submissions"] + old["submissions"], key=lambda s:s["version"])
    write("SUBMISSIONS.json", {
        "active": subs["active"]["version"], "selected": subs["selected"]["version"],
        "pinned": subs["pinned"], "frozen": subs["frozen"], "upcomingTournament": subs["upcomingTournament"],
        "versions": [{k:s[k] for k in ("version", "createdAt", "statusAt", "status", "note", "fileName", "size")} for s in versions if s["version"] >= 80]
    })
    ladder = read("ladder---page-1---limit-100---json.json")["teams"]
    us = next(t for t in ladder if t["teamId"] == OUR_ID)
    above = [t for t in ladder if t["rating"] > us["rating"]]
    write("LADDER.json", {"team": us, "top10": ladder[:10], "above": above})
    cpg = next(s for s in versions if s["version"] == 105)
    plan = git_json(HANDOVER, "research/x3/duel/duel_20261103c.json")
    signatures = {expected_key(g): i for i,g in enumerate(plan["groups"])}
    periods = {}
    window_groups = defaultdict(list)
    for kind in ("ranked", "unranked"):
        rows = read(f"matches-list---team-me---kind-{kind}---limit-100---json.json")["matches"]
        windows = {}
        for label, lo, hi in (
            ("before-v105-upload", "", cpg["createdAt"]),
            ("upload-to-inactive", cpg["createdAt"], cpg["statusAt"]),
            ("inactive-to-v80-status", cpg["statusAt"], subs["active"]["statusAt"]),
            ("after-v80-status", subs["active"]["statusAt"], "9999"),
        ):
            subset = [m for m in rows if lo <= m["createdAt"] < hi and m["status"] == "finished"]
            windows[label] = {"results": dict(Counter(our_game(m)[3] for m in subset)),
                              "unique_opponents": len({our_game(m)[0] for m in subset})}
            if kind == "unranked" and label == "upload-to-inactive":
                for m in subset:
                    window_groups[m["groupId"]].append(m)
        periods[kind] = {"earliest": rows[-1]["createdAt"], "latest": rows[0]["createdAt"], "windows": windows}
    matches = [{"groupId": gid, "planIndex": signatures.get(group_key(rows)), "games": len(rows),
                "createdAt": min(r["createdAt"] for r in rows), "results": dict(Counter(our_game(r)[3] for r in rows))}
               for gid, rows in sorted(window_groups.items())]
    write("CPG_WINDOW.json", {"warning": "Times are not match version assignments. Neither endpoint exposes own or opponent submission ID or source-group lineage.", "periods": periods, "unranked_groups": matches,
                             "archived_plan_c_arms": {k: {"version":v["version"],"groups":len(v["groups"]), "contaminated":v.get("contaminated")} for k,v in plan["arms"].items()}})
    pool = git_json(JD, "research/jd-g5070-resume-0715/runs/final-cpg-pool-01.json")
    fresh = git_json(JD, "research/jd-g5070-resume-0715/runs/final-cpg-fresh51104-01.json")
    def interval(rows):
        by_map = defaultdict(list)
        for row in rows:
            by_map[row[1]].append(row[3] - row[4])
        groups = [(sum(by_map[k]), len(by_map[k])) for k in sorted(by_map)]
        rng = Random(1104)
        draws = []
        for _ in range(2000):
            sample = [groups[rng.randrange(len(groups))] for _ in groups]
            draws.append(100 * sum(n for n, _ in sample) / sum(d for _, d in sample))
        draws.sort()
        return [round(draws[i], 3) for i in (50, 1949)]

    def counts(d):
        rows = d["cells"]
        return {"n": len(rows), "base_wins": sum(x[4] for x in rows), "candidate_wins": sum(x[3] for x in rows),
                "b": sum(x[3] > x[4] for x in rows), "c": sum(x[4] > x[3] for x in rows),
                "fuel": {arm: d["arms"][arm]["fuel_outs"] for arm in ("base", "cand")},
                "faults": {arm: d["arms"][arm]["faults"] for arm in ("base", "cand")}, "map_cluster_95_ci_pp": interval(rows)}
    write("CPG_LOCAL.json", {"pool": counts(pool), "fresh51104": counts(fresh), "combined_ci_pp": interval(pool["cells"] + fresh["cells"]), "source_commit": JD})
    print(us["rank"], us["rating"], len(above), "teams above")
    print("Window coverage", periods)
    print("Plan C signature matches in v105 upload-to-inactive window", sum(m["planIndex"] is not None for m in matches), "/", len(matches))
    print("CPG local", counts(pool), counts(fresh))

if __name__ == "__main__":
    main()
