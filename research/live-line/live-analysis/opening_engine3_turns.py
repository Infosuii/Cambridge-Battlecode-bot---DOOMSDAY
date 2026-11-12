"""Freeze and inspect same-champion own-view turns in three current-engine rival losses."""
from hashlib import sha256
import importlib.util
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from discovery_metrics import timeline
from engine3_pool import CLI, HERE, read
from freeze_engine3_discovery import OUT, write


def main():
    selected = []
    discovery = read(HERE / "LIVE109_NATIVE_DISCOVERY.json")["rows"]
    index = {r["matchId"]: r for r in read(HERE / "LIVE109_DISCOVERY_SPLIT.json")["matches"]}
    for rival in ("QS2isLaw", "0xDEADBEEF", "bentheboss"):
        eligible = [r for r in discovery if r["opponent"] == rival and r["patterns"]["early_income_without_deaths"] and r["first_sustained_gold_lead"] is not None]
        assert eligible, rival
        row = min(eligible, key=lambda r: sha256(r["id"].encode()).hexdigest())
        native = read(OUT / "summaries" / (row["id"] + ".json"))
        ours = "team" + index[row["id"]]["side"].upper()
        theirs = "teamB" if ours == "teamA" else "teamA"
        champion = next(name for name in ("Marcella", "Vendetta", "Varg", "Heart of Ruin") if all(
            any(c["name"] == name and c["team"] == team for c in native["roster"]["champions"]) for team in (ours, theirs)))
        actors = {label: next(c["id"] for c in native["roster"]["champions"] if c["team"] == team and c["name"] == champion)
                  for label, team in (("ours", ours), ("rival", theirs))}
        selected.append({**index[row["id"]], "round": row["first_sustained_gold_lead"], "champion": champion,
                         "actors": actors, "native_sha256": bench.digest(OUT / "summaries" / (row["id"] + ".json"))})
    write(HERE / "LIVE109_OPENING_TURNS_PLAN.json", {"protocol": "One discovery loss per named rival with frozen early-income-without-deaths and a sustained lead; select minimum match-ID SHA, compare the same champion at the first sustained lead round. Before reading those own views. Source interval inferred, private policy unavailable.", "cases": selected})
    output = OUT / "opening-turns"
    output.mkdir()
    old_path = HERE / "uk-rivals/turns/7c64f1a2-96c7-4807-a2e2-2722e17c436c-50-0.json"
    old = read(old_path)
    old_replay = bench.CACHE / "uk-targets-1104/replays/rep/7c64f1a2-96c7-4807-a2e2-2722e17c436c.repl26a"
    env = {**os.environ, "NFS_REPLAY_ENGINE": "2.0.0"}
    control = output / "engine2-control.json"
    subprocess.run(["node", HERE / "trace_turn.mjs", old_replay, str(old["round"]), str(old["team"]), str(old["actor"]), control], cwd=bench.ROOT, env=env, check=True)
    assert control.read_bytes() == old_path.read_bytes()
    spec = importlib.util.spec_from_file_location("losses_recent", bench.ROOT / "tools/ladder/losses_recent.py")
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    collector.CLI = str(CLI)
    env["NFS_REPLAY_ENGINE"] = "3.0.0"
    reports = []
    for case in selected:
        mid = case["matchId"]
        archive = OUT / "replays" / (mid + ".zip")
        assert collector.fetch(["matches", "download", mid], archive)
        replay = output / (mid + ".repl26a")
        with ZipFile(archive) as bundle:
            with replay.open("xb") as out:
                out.write(bundle.read("replay.repl26a"))
        native = read(OUT / "summaries" / (mid + ".json"))
        measured = {**case, "archive_sha256": bench.digest(archive), "observations": {}}
        for label, actor in case["actors"].items():
            team = int(case["side"].upper() == "B") if label == "ours" else int(case["side"].upper() != "B")
            destination = output / f"{mid}-{label}.json"
            subprocess.run(["node", HERE / "trace_turn.mjs", replay, str(case["round"]), str(team), str(actor), destination], cwd=bench.ROOT, env=env, check=True)
            turn = read(destination)
            assert turn["observation"]["actor"]["id"] == actor and turn["observation"]["actor"]["team"] == team
            one = {"championTimelines": [r for r in native["championTimelines"] if r["owner"]["id"] == actor]}
            measured["observations"][label] = {"trace": destination.relative_to(bench.ROOT).as_posix(), "sha256": bench.digest(destination),
                "native_boundary_gold": [timeline(one, "team" + "AB"[team], "gold", r) for r in (case["round"] - 1, case["round"])],
                "native_boundary_gems": [timeline(one, "team" + "AB"[team], "gems", r) for r in (case["round"] - 1, case["round"])],
                "actor": turn["observation"]["actor"], "visible_enemies": len(turn["observation"]["visible_enemies"]), "visible_camps": len(turn["observation"]["visible_camps"]), "actions": turn["executed_actions"]}
        reports.append(measured)
    write(HERE / "LIVE109_OPENING_TURNS.json", {"engine2_control_bytes_identical": True, "engine3_actor_ids_teams_verified": True,
          "limits": "Native timeline values bracket round boundaries; observed inputs precede the actor's actions. No inference of historical private source state from these views.", "cases": reports})
    print({"cases": len(reports), "engine2_byte_control": True}, flush=True)


if __name__ == "__main__":
    main()
