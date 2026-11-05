"""Account for confirmed observed deficits in their original units, without a causal claim."""
from statistics import mean

from engine3_pool import HERE, read
from freeze_engine3_discovery import write


def account(rows, eligible, affected, gap, unit):
    selected = [r for r in rows if eligible(r)]
    values = [gap(r) for r in selected if affected(r)]
    assert all(v > 0 for v in values)
    return {"unit":unit,"eligible_games":len(selected),"affected_games":len(values),
            "mean_positive_gap":mean(values) if values else None,
            "frequency_times_mean_gap":sum(values)/len(selected) if selected else None}


if __name__ == "__main__":
    result = {"limits":"Overlapping observed deficits in source-interval-inferred, outcome-selected cases. Frequency times gap is descriptive accounting per eligible game, not attributable/recoverable improvement or a win-rate ceiling."}
    metric = lambda r,side,name,round:r[side]["metrics"][name][str(round)]
    for part in ("discovery","confirm","control"):
        native = read(HERE/f"LIVE111_NATIVE_{part.upper()}.json")["rows"]
        replay = read(HERE/f"LIVE111_REPLAY_{part.upper()}.json")["rows"]
        definitions = (
            ("early_gold_without_deaths","early_income_without_deaths",150,("earnedGold",),"gold",lambda r:True),
            ("gem_acquisition300","early_gem_acquisition",300,("collectedGems",),"gems",lambda r:True),
            ("total_gems800","midgame_total_gems_deficit",800,("submittedGems","gems"),"gems",lambda r:not r["ended_before800"]))
        report = {}
        for name,pattern,round,names,unit,eligible in definitions:
            def gap(r): return sum(metric(r,"rival",n,round)-metric(r,"ours",n,round) for n in names)
            report[name] = account(native,eligible,lambda r:r["patterns"][pattern],gap,unit)
        for name,key,positive,unit in (("inferred_capture_gold300","inferred_capture_gold300",1,"inferred gold"),
                                       ("excess_no_hit_deaths600","no_pvp_basic_or_cast_deaths600",-1,"deaths")):
            gap = lambda r:positive*(r["rival"][key]-r["ours"][key])
            report[name]=account(replay,lambda r:True,lambda r:gap(r)>0,gap,unit)
        result[part]=report
    write(HERE/"LIVE111_DISCOVERY_ERROR_TABLE.json",result)
    print(result,flush=True)
