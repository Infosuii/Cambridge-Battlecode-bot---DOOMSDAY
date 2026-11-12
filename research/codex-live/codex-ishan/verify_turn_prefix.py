"""Demonstrate the turn-end false negative and recount saved diagnostic controls."""
from pathlib import Path
import re

import ablate_dev as bench
from engine3_pool import HERE, read
from freeze_engine3_discovery import write
from turn_prefix import action_prefix


def old_prefix(doc):
    result = []
    for action in doc["executed_actions"]:
        if action["kind"] == 26: break
        result.append(action)
    return result


if __name__ == "__main__":
    root = Path("C:/Users/ishan/AppData/Local/cambc/assets")
    panel = next(root.glob("*/visualiser/assets/PanelChrome-DRtW3oWL.js"))
    assert bench.digest(panel) == "f4d42ccf4a3cc2ed5da94b496a2dc4da286e3e1d034fc95265be92a86e67a9fa"
    text = panel.read_text(encoding="utf8")
    enum = re.search(r"\w+=e=>e.kind===8\|\|e.kind===26\|\|e.kind===27", text)
    assert enum
    controls = []
    for report in HERE.glob("LIVE109_RUNTIME_TARGET_*.json"):
        for row in read(report)["rows"]:
            case = row["case"]
            before = read(bench.ROOT / case["traces"]["base"]["path"])
            after = read(bench.ROOT / row["directory"] / "turn.json")
            old = old_prefix(before) == old_prefix(after)
            new = action_prefix(before) == action_prefix(after)
            assert old == new == row["same_action_prefix"], (report, case["stage"])
            controls.append({"report": report.name, "stage": case["stage"], "old": old, "new": new})
    case = read(HERE / "LIVE111_FIRST_TURN_PLAN.json")["case"]
    before = read(bench.ROOT / case["traces"]["base"]["path"])
    after = read(bench.CACHE / "live111-field-prepare/public-khiri/pf_pool_77041-A-prepare/turn.json")
    assert old_prefix(before) != old_prefix(after)
    assert action_prefix(before) == action_prefix(after) == []
    a = {"executed_actions": [{"kind": 4, "to": 1}, {"kind": 26}]}
    b = {"executed_actions": [{"kind": 4, "to": 2}, {"kind": 8}]}
    assert action_prefix(a) != action_prefix(b)
    write(HERE / "TURN_PREFIX_REPAIR_CONTROLS.json", {"official_panel_sha256": bench.digest(panel), "official_turn_end_predicate": enum.group(),
        "false_negative_reproduced": True, "corrected_prefixes_empty": True, "gameplay_difference_detected": True,
        "historical_labels_unchanged": True, "controls": controls})
    print({"historical_controls": len(controls), "all_labels_unchanged": True, "false_negative_reproduced": True}, flush=True)
