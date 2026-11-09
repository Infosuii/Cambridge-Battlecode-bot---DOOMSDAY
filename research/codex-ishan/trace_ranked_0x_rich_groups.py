"""Explain observed rich-group access in two losses and one fixed win control."""
from collections import Counter, defaultdict
import os
import subprocess

from attribute_live111b_camps import audit
from audit_ranked_0x_rewards import ROOT, OUT
from audit_uploaded_112_114 import write
from discovery_metrics import timeline
from engine3_pool import HERE, bench, read

PARENT = HERE / "RANKED_0XDEADBEEF_REWARD_AUDIT.json"
TOOL = HERE / "trace_ranked_0x_rich_groups.mjs"
RESULTS = OUT / "0x-rich-group-trace-r2"
PLAN = HERE / "RANKED_0XDEADBEEF_RICH_GROUP_R2_PLAN.json"


def base_gap(row, phase):
    phases = row["phases"][phase]
    return phases["ours"]["base"] - phases["rival"]["base"]


def main():
    audit_result = read(PARENT)
    decoded = ROOT / "decoded.json"
    assert bench.digest(decoded) == audit_result["decoded_sha256"]
    metadata = {r["matchId"]: r["groups"] for r in read(decoded)["rows"]}
    unique = {}
    for row in audit_result["rows"]:
        unique.setdefault((row["native_sha256"], row["map_id"], row["side"], row["result"]), row)
    losses = sorted((r for r in unique.values() if r["result"] == "loss"), key=lambda r: (base_gap(r, "post300"), r["match"]))
    wins = sorted((r for r in unique.values() if r["result"] == "win"), key=lambda r: (-base_gap(r, "terminal"), r["match"]))
    jobs = []
    for row in (*losses[:2], wins[0]):
        mid = row["match"]
        native_path = OUT / "native" / f"{mid}.json"
        replay = ROOT / f"{mid}.repl26a"
        assert bench.digest(native_path) == row["native_sha256"] and bench.digest(replay) == row["replay_sha256"]
        doc = read(native_path)
        _, packets = audit(doc)
        groups = {g["handle"]: g for g in metadata[mid]}
        own = "team" + row["side"].upper()
        if row["result"] == "loss":
            gid = row["largest_later_group_deficits"][0]["group_handle"]
            selected = [c for c in packets if c["team"] != own and c["group"] == gid and c["round"] > 300]
        else:
            values = Counter()
            for cap in packets:
                values[cap["group"]] += groups[cap["group"]]["gems"] * (1 if cap["team"] == own else -1)
            gid = max(values, key=lambda group: (values[group], -group))
            selected = [c for c in packets if c["team"] == own and c["group"] == gid]
        selected.sort(key=lambda cap: (cap["round"], cap["ordinal"]))
        capture_jobs = selected[:4]
        rounds = set()
        for cap in capture_jobs:
            assert cap["clear"] is not None
            clear, capture = cap["clear"]["round"], cap["round"]
            rounds.update((max(1, clear - 10), clear, capture, capture + 1))
        jobs.append({"match": mid, "map": row["map"], "result": row["result"], "side": row["side"],
                     "group": gid, "base_gems": groups[gid]["gems"], "respawn": groups[gid]["respawn"],
                     "camps": groups[gid]["camps"], "replay": str(replay), "replay_sha256": row["replay_sha256"],
                     "native_sha256": row["native_sha256"], "rounds": sorted(rounds), "captures": capture_jobs})
    RESULTS.mkdir()
    plan = {"source_sha256": bench.digest(PARENT), "tool_sha256": bench.digest(TOOL), "jobs": jobs,
            "selection": "Two distinct losses with largest post-300 base deficit and their largest lost groups. One distinct win with largest terminal base lead and its highest net group. First four relevant captures in each."}
    original = HERE / "RANKED_0XDEADBEEF_RICH_GROUP_PLAN.json"
    attempt = read(HERE / "RANKED_0XDEADBEEF_RICH_GROUP_ATTEMPT.json")
    assert bench.digest(original) == attempt["plan_sha256"] and jobs == read(original)["jobs"]
    plan["original_plan_sha256"] = attempt["plan_sha256"]
    write(PLAN, plan)
    write(RESULTS / "jobs.json", jobs)
    subprocess.run(["node", TOOL, RESULTS / "jobs.json", RESULTS / "snapshots.json"], cwd=bench.ROOT,
                   env={**os.environ, "NFS_REPLAY_ENGINE": "3.0.0"}, check=True)
    observed = {row["match"]: row for row in read(RESULTS / "snapshots.json")}
    result = []
    for job in jobs:
        trace = observed[job["match"]]
        assert trace["group"] == job["group"]
        doc = read(OUT / "native" / (job["match"] + ".json"))
        own = int(job["side"] == "b")
        matched = defaultdict(dict)
        for sample in trace["snapshots"]:
            rnd = sample["round"]
            assert rnd in job["rounds"]
            for unit in sample["actors"]:
                side = "team" + "AB"[unit["team"]]
                unit_doc = {"championTimelines": [r for r in doc["championTimelines"] if r["owner"]["id"] == unit["id"]]}
                for metric in ("gems", "gold"):
                    boundaries = [timeline(unit_doc, side, metric, t) for t in (rnd - 1, rnd)]
                    assert min(boundaries) <= unit[metric] <= max(boundaries), (job["match"], rnd, unit, metric, boundaries)
                key = "ours" if unit["team"] == own else "rival"
                record = matched[rnd].setdefault(key, {"nearest": None, "within_four": 0, "on": 0})
                record["on"] += unit["chebyshev"] == 0
                record["within_four"] += unit["chebyshev"] <= 4
                if record["nearest"] is None or unit["chebyshev"] < record["nearest"]["chebyshev"]:
                    record["nearest"] = unit
        for cap in job["captures"]:
            cap["sample_at_clear"] = matched.get(cap["clear"]["round"])
            cap["sample_at_capture"] = matched.get(cap["round"])
        result.append({"match": job["match"], "map": job["map"], "result": job["result"],
                       "group": job["group"], "base_gems": job["base_gems"], "respawn": job["respawn"],
                       "captures": job["captures"], "trace": trace})
        print(job["map"], job["group"], [(cap["round"], cap["sample_at_capture"]) for cap in job["captures"]], flush=True)
    write(HERE / "RANKED_0XDEADBEEF_RICH_GROUP_R2_TRACE.json",
          {"plan_sha256": bench.digest(PLAN),
           "raw_trace_sha256": bench.digest(RESULTS / "snapshots.json"), "rows": result,
           "limits": "First champion phase, before ordinary actions of the recorded round. Chebyshev proximity ignores obstacles, threat and private target. Reported actors and camp states are public replay observations, not a legal path or ownership counterfactual."})


if __name__ == "__main__":
    main()
