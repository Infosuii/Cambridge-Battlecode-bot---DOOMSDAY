"""Recount every frozen 0xDEADBEEF replay, retaining repeat and deduplicated results."""
from collections import defaultdict
from zipfile import ZipFile
import os
import subprocess

from attribute_live111b_camps import audit
from audit_ranked_112_114_transition import OUT, PLAN, RIVALS
from audit_uploaded_112_114 import write
from engine3_pool import ENGINE, HERE, bench, read
from resource_live111d_discovery import ledger

DECODER = HERE / "extract_runtime_camps.mjs"
PROOF = HERE / "RUNTIME_CAMP_METADATA_PROOF.json"
ROOT = OUT / "0x-analysis"
NATIVE = HERE / "RANKED_112_114_TRANSITION_RESULT.json"
RIVAL = next(team for team, name in RIVALS.items() if name == "0xDEADBEEF")
WINDOWS = {"150": (0, 150), "300": (0, 300), "600": (0, 600), "800": (0, 800),
           "post300": (300, None), "terminal": (0, None)}
KEYS = ("packets", "clears", "actual", "base", "residual", "cross_packets", "cross_base", "unmatched")


def phase(rows, low, high):
    return [r for r in rows if r["round"] > low and (high is None or r["round"] <= high)]


def measures(caps, clears, groups):
    actual = sum(c["gems"] for c in caps)
    base = sum(groups[c["group"]]["gems"] for c in caps)
    cross = [c for c in caps if c["clear"] is not None and c["clear"]["team"] != c["team"]]
    return {"packets": len(caps), "clears": len(clears), "actual": actual, "base": base, "residual": actual - base,
            "cross_packets": len(cross), "cross_base": sum(groups[c["group"]]["gems"] for c in cross),
            "unmatched": sum(c["clear"] is None for c in caps)}


def report(rows):
    reports = {}
    for stage in WINDOWS:
        cohort = [r for r in rows if stage in r["phases"]]
        result = {"games": len(cohort)}
        for side in ("ours", "rival"):
            sums = {k: sum(r["phases"][stage][side][k] for r in cohort) for k in KEYS}
            sums["base_per_packet"] = sums["base"] / sums["packets"] if sums["packets"] else None
            result[side] = sums
        result["ours_minus_rival"] = {k: result["ours"][k] - result["rival"][k] for k in KEYS}
        gap = result["ours_minus_rival"]
        assert gap["actual"] == gap["base"] + gap["residual"]
        reports[stage] = result
    return reports


def main():
    frozen = read(PLAN)
    assert bench.digest(PLAN) == read(NATIVE)["plan_sha256"]
    native_index = {r["match"]: r for r in read(NATIVE)["native_rows"]}
    selected = [r for r in frozen["cells"] if r["rival_id"] == RIVAL]
    assert len(selected) == 20 and all(r["native_requested"] for r in selected)
    proof = read(PROOF)
    assert proof["pass"] and proof["games"] == 90 and proof["decoder_sha256"] == bench.digest(DECODER)
    ROOT.mkdir()
    jobs = []
    for row in selected:
        mid = row["match"]
        native = OUT / "native" / (mid + ".json")
        assert bench.digest(native) == native_index[mid]["native_sha256"]
        archive = OUT / "0x-replays" / (mid + ".zip")
        replay = ROOT / (mid + ".repl26a")
        with ZipFile(archive) as zipped, replay.open("xb") as out:
            out.write(zipped.read("replay.repl26a"))
        jobs.append({"matchId": mid, "replay": str(replay), "replay_sha256": bench.digest(replay),
                     "archive_sha256": bench.digest(archive), "native_sha256": native_index[mid]["native_sha256"],
                     "map_sha256": native_index[mid]["map_sha256"]})
    write(ROOT / "jobs.json", jobs)
    subprocess.run(["node", DECODER, ROOT / "jobs.json", ROOT / "decoded.json"], cwd=bench.ROOT,
                   env={**os.environ, "NFS_REPLAY_ENGINE": "3.0.0"}, check=True)
    decoded = read(ROOT / "decoded.json")
    assert decoded["games"] == 20
    metadata = {r["matchId"]: r for r in decoded["rows"]}
    assert len(metadata) == 20
    rows = []
    repeats = defaultdict(list)
    for item in selected:
        mid = item["match"]
        mapping = metadata[mid]
        assert mapping["initial_snapshot_camps_match"]
        native = OUT / "native" / (mid + ".json")
        assert bench.digest(native) == mapping["native_sha256"]
        doc = read(native)
        assert doc["match"]["engineBuildHash"] == ENGINE and doc["match"]["mapHash"] == mapping["map_sha256"]
        assert doc["diagnostics"]["detailedCaptureComplete"]
        groups = {g["handle"]: g for g in mapping["groups"]}
        assert len(groups) == len(mapping["groups"])
        clears, caps = audit(doc)
        assert all(r["group"] in groups for r in (*clears, *caps))
        for cap in caps:
            assert sum(r["gems"] for r in cap["shares"]) == cap["gems"]
        own = "team" + item["side"].upper()
        teams = {"ours": own, "rival": "teamB" if own == "teamA" else "teamA"}
        row = {k: item[k] for k in ("match", "group", "map", "map_id", "side", "result")}
        row.update({k: mapping[k] for k in ("native_sha256", "archive_sha256", "replay_sha256")})
        row["rounds_completed"] = doc["match"]["roundsCompleted"]
        row["phases"] = {}
        for stage, (low, high) in WINDOWS.items():
            if max(low, high or 0) > row["rounds_completed"]:
                continue
            row["phases"][stage] = {}
            for tag, team in teams.items():
                hits = phase([c for c in caps if c["team"] == team], low, high)
                done = phase([c for c in clears if c["team"] == team], low, high)
                part = measures(hits, done, groups)
                independently = ledger(doc, team, high)
                previous = ledger(doc, team, low) if low else {"camp": 0, "clears": 0}
                assert part["actual"] == independently["camp"] - previous["camp"]
                assert part["clears"] == independently["clears"] - previous["clears"]
                row["phases"][stage][tag] = part

        later = defaultdict(lambda: {"ours": [], "rival": []})
        for c in phase(caps, 300, None):
            label = "ours" if c["team"] == own else "rival"
            later[c["group"]][label].append(c)
        deficits = []
        for gid, pair in later.items():
            group = groups[gid]
            delta = group["gems"] * (len(pair["ours"]) - len(pair["rival"]))
            if delta < 0:
                deficits.append({"group_handle": gid, "base": group["gems"], "camp_types": [c["type"] for c in group["camps"]],
                                 "positions": [[c["x"], c["y"]] for c in group["camps"]], "base_gap": delta,
                                 "captures": {k: [{name: cap[name] for name in ("round", "input", "clear", "gems", "shares")} for cap in v]
                                              for k, v in pair.items()}})
        row["largest_later_group_deficits"] = sorted(deficits, key=lambda g: (g["base_gap"], g["group_handle"]))[:3]
        repeats[(row["native_sha256"], row["map_id"], row["side"], row["result"])].append(row)
        rows.append(row)
    unique = [duplicates[0] for duplicates in repeats.values()]
    duplicates = [[{k: r[k] for k in ("match", "map", "side", "result", "native_sha256", "replay_sha256")}
                   for r in group] for group in repeats.values() if len(group) > 1]
    reports = {scope: {outcome: report([r for r in cohort if r["result"] == outcome]) for outcome in ("win", "loss")}
               for scope, cohort in (("all", rows), ("unique_native", unique))}
    write(HERE / "RANKED_0XDEADBEEF_REWARD_AUDIT.json",
          {"match_plan_sha256": bench.digest(PLAN), "native_result_sha256": bench.digest(NATIVE),
           "decoded_sha256": bench.digest(ROOT / "decoded.json"), "decoder_sha256": bench.digest(DECODER),
           "rows": rows, "duplicate_groups": duplicates, "reports": reports,
           "scope": "Runtime base rewards and native gem packets. Final-clear association does not establish ownership or exclusive damage. Phase cutoffs exclude games ending earlier."})
    for scope, report_data in reports.items():
        for outcome, phases in report_data.items():
            print(scope, outcome, {stage: (p["games"], p["ours_minus_rival"]) for stage, p in phases.items()}, flush=True)


if __name__ == "__main__":
    main()
