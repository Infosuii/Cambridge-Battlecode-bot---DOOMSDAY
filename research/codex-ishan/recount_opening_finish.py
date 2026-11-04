"""Recount opening-finish prototype clears from official native event records."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "artifacts/codex-p0/opening-finish-prototype/games"


def main():
    fixture = json.loads((HERE / "OPENING_FINISH_PROTOTYPE.json").read_bytes())
    confirmed = []
    for cell in fixture["rows"]:
        if not cell["differences"]:
            continue
        game = OUT / f"finish-0-{cell['opponent']}-{cell['map']}-{cell['side']}"
        native = json.loads((game / "native.json").read_bytes())
        assert native["diagnostics"]["detailedCaptureComplete"]
        assert native["match"]["engineBuildHash"] == fixture["engine"]
        team = "team" + cell["side"]
        roster = sorted(c["id"] for c in native["roster"]["champions"] if c["team"] == team)
        events = {(e["owner"]["id"], x["timestamp"]["round"], x["target"]["id"])
                  for e in native["events"] if e["kind"] == "campClear" and e["owner"]["team"] == team
                  for x in e["entries"] if x["target"]["kind"] == "campGroup"}
        for round_no, slot, group, camp, direct in cell["differences"]:
            actor = roster[slot]
            confirmed.append({"map": cell["map"], "opponent": cell["opponent"], "side": cell["side"],
                              "round": round_no, "actor": actor, "group": group, "camp": camp,
                              "direct_sdk_zero_health": bool(direct),
                              "native_clear": (actor, round_no, group) in events})
    result = {"cells": fixture["cells"], "faults": fixture["faults"], "confirmed_rows": confirmed,
              "clear_maps": sorted({r["map"] for r in confirmed if r["native_clear"]}),
              "native_clears": sum(r["native_clear"] for r in confirmed)}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
