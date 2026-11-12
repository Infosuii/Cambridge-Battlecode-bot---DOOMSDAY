"""Measure early spending in exact v112/v114 archives under matched v92 controls."""
from math import isclose
from statistics import mean, median

from audit_uploaded_112_114 import write
from audit_uploaded_112_114_pool import RUN
from discovery_metrics import timeline
from engine3_pool import HERE, bench, read
from resource_live111d_discovery import ledger

POOL = HERE / "UPLOADED_112_114_POOL_RESULT.json"
ROUNDS = (50, 100, 150, 300)
METRICS = ("spentGold", "earnedGold", "gold", "deaths")


def read_match(row):
    native = RUN / f'{row["map"]}-{row["side"]}-{row["arm"]}' / "native.json"
    assert bench.digest(native) == row["native_sha256"]
    doc = read(native)
    assert doc["match"]["roundsCompleted"] >= max(ROUNDS)
    team = "team" + row["side"]
    metrics = {name: {str(r): timeline(doc, team, name, r) for r in ROUNDS} for name in METRICS}
    for name in METRICS:
        observed = sum(float(c["metrics"][name]) for c in doc["champions"] if c["team"] == team)
        assert isclose(observed, timeline(doc, team, name, doc["match"]["roundsStarted"] + 1), abs_tol=1e-3)
    buys = [e["timestamp"]["round"] for kind in doc["events"]
            if kind["kind"] in ("buyItem", "buyConsumable") and kind["owner"]["team"] == team
            for e in kind["entries"]]
    metrics["first_purchase"] = min(buys) if buys else None
    metrics["score_context"] = row["score"]
    metrics["fuel"] = row["fuel_outs"]
    for name in ("camp", "banked"):
        metrics[name] = {str(r): ledger(doc, team, r)[name] for r in ROUNDS}
    return metrics


def comparison(a, b):
    deltas = [v - u for u, v in zip(a, b, strict=True)]
    assert deltas
    return {"n": len(deltas), "mean_v112_v114": [mean(a), mean(b)], "mean_delta": mean(deltas),
            "median_delta": median(deltas), "higher": sum(x > 0 for x in deltas),
            "tied": sum(x == 0 for x in deltas), "lower": sum(x < 0 for x in deltas)}


def main():
    pool = read(POOL)
    results = {}
    for row in pool["rows"]:
        if row["arm"] in ("v112", "v114"):
            cell = (row["map"], row["side"])
            results.setdefault(cell, {})[row["arm"]] = read_match(row)
    assert len(results) == 172 and all(set(arms) == {"v112", "v114"} for arms in results.values())
    phases = {}
    for rnd in map(str, ROUNDS):
        phases[rnd] = {}
        for name in (*METRICS, "camp", "banked"):
            phases[rnd][name] = comparison(*[[cell[arm][name][rnd] for cell in results.values()] for arm in ("v112", "v114")])
    first = [[cell[arm]["first_purchase"] for cell in results.values()
              if all(cell[version]["first_purchase"] is not None for version in ("v112", "v114"))] for arm in ("v112", "v114")]
    write(HERE / "UPLOADED_V114_EARLY_ECONOMY.json",
          {"pool_sha256": bench.digest(POOL), "phases": phases, "first_purchase_round": comparison(*first),
           "first_purchase_unavailable": {arm: sum(c[arm]["first_purchase"] is None for c in results.values()) for arm in ("v112", "v114")},
           "rows": [{"map": key[0], "side": key[1], **value} for key, value in results.items()],
           "limits": "Exact v114 bundle changes early shop and map profiles. Fixed games against the same v92 control do not isolate either change or provide noisy strength evidence."})
    for r, table in phases.items():
        print(r, {k: v for k, v in table.items() if k in ("spentGold", "camp", "banked")}, flush=True)


if __name__ == "__main__":
    main()
