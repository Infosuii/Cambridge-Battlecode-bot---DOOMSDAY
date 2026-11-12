"""Extract and profile the frozen rival replays with the official engine reader."""
from pathlib import Path
import json
import os
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / "artifacts/codex-p0/uk-targets-1104"
sys.path.insert(0, str(HERE.parent / "discovery4"))
from capture_metrics import team_metrics
from metrics import timeline


def read(path):
    return json.loads(path.read_bytes())


def native_profiles(matches):
    extracts = CACHE / "replays/rep"
    extracts.mkdir(exist_ok=True)
    files = []
    for row in matches:
        mid = row["id"]
        f = extracts / f"{mid}.repl26a"
        with ZipFile(CACHE / "replays" / f"{mid}.zip") as z:
            f.write_bytes(z.read("replay.repl26a"))
        files.append(f)
    env = {**os.environ, "NFS_REPLAY_ENGINE": "2.0.0", "NFS_FUNNEL_UNTIL": "300"}
    outputs = {}
    for tool, leading in (("winner_profile", []), ("capture_pressure", []), ("death_context", ["600"])):
        output = CACHE / f"{tool}.json"
        subprocess.run(["node", ROOT / "tools/replay" / f"{tool}.mjs", *leading, output, *files],
                       cwd=ROOT, env=env, check=True)
        outputs[tool] = {Path(row["id"]).stem: row for row in read(output)}
    return outputs


def stats(profiles, m, team):
    mid = m["id"]
    n = read(CACHE / "summaries" / f"{mid}.json")
    expected = "team" + ("AB"[team] if m["result"] == "win" else "AB"[1 - team])
    assert n["match"]["engineVersion"] == "2.0.0" and n["match"]["outcome"] == expected
    snap = profiles["winner_profile"][mid]["teams"][team]
    captures = team_metrics(profiles["capture_pressure"][mid], team)
    deaths = [d for d in profiles["death_context"][mid]["deaths"] if d["team"] == team]
    tag = "team" + "AB"[team]
    return {"gold": {str(r): timeline(n, tag, "earnedGold", r) for r in (50, 100, 150, 200, 250, 300)},
            "banked": {str(r): timeline(n, tag, "submittedGems", r) for r in (150, 300)},
            "r150_grouped": snap["grouped"][0], "workers_together": snap["workers_together"],
            "deaths_before_150": sum(d["round"] < 150 for d in deaths),
            "deaths_no_basic_or_cast_600": sum(d["pvp_attacks"] == 0 and d["casts"] == 0 for d in deaths),
            "camp": captures, "first_contact": snap["first_contact"], "opening_route": snap["route"][:4]}


def main():
    matches = read(HERE / "SAMPLE.json")["matches"]
    profiles = native_profiles(matches)
    rows = []
    for m in matches:
        ours = int(m["side"].upper() == "B")
        # The outcome assertion belongs to the DOOMSDAY side. For the second
        # call invert the result so expected still names the actual winner.
        inverse = {**m, "result": "win" if m["result"] == "loss" else "loss"}
        rows.append({**m, "ours": stats(profiles, m, ours), "rival": stats(profiles, inverse, 1 - ours)})
    with (HERE / "PROFILE.json").open("x", encoding="utf-8", newline="\n") as out:
        json.dump(rows, out, indent=2)
        out.write("\n")


if __name__ == "__main__":
    main()
