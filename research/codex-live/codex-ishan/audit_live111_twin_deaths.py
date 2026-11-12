"""Separate known linked-twin events from the existing no-hit descriptive counts."""
from collections import Counter

import ablate_dev as bench
from engine3_pool import HERE, read
from freeze_engine3_discovery import write


if __name__ == "__main__":
    output = bench.CACHE / "live111-discovery-20261105"
    result = {"scope":"Existing descriptive death-window counts; same-round twin coincidence does not identify which twin initiated death. Original metrics unchanged.","partitions":{}}
    for part in ("discovery","confirm","control"):
        rows=read(HERE/f"LIVE111_REPLAY_{part.upper()}.json")["rows"]
        contexts={r["id"]:r["deaths"] for r in read(output/f"analysis-{part}/death_context.json")}
        table={side:Counter() for side in ("ours","rival")}
        cases=[]
        for row in rows:
            deaths=contexts[row["matchId"]]
            for side,team in (("ours",int(row["side"].upper()=="B")),("rival",int(row["side"].upper()!="B"))):
                own=[d for d in deaths if d["team"]==team]
                nohit=[d for d in own if d["pvp_attacks"]==0 and d["casts"]==0]
                assert len(nohit)==row[side]["no_pvp_basic_or_cast_deaths600"]
                c=table[side]
                c["all_deaths"]+=len(own)
                c["no_hit_deaths"]+=len(nohit)
                pairs={}
                for d in nohit:
                    c[f"type_{d['type']}"]+=1
                    other=next((o for o in own if d["type"] in (3,4) and o["type"]==7-d["type"] and o["round"]==d["round"]),None)
                    linked=other is not None
                    c["no_hit_linked_twin" if linked else "no_hit_other"]+=1
                    c["no_hit_zero_nearby_enemies"]+=d["enemies4"]==0
                    c["no_hit_gems_held"]+=d["gems"]
                    if linked: pairs[(d["round"],min(d["id"],other["id"]),max(d["id"],other["id"]))]=True
                    cases.append({"matchId":row["matchId"],"opponent":row["opponent"],"side":side,
                                  "death":d,"same_round_opposite_twin":other})
                c["linked_pair_events_with_nohit_member"]+=len(pairs)
        result["partitions"][part]={"n":len(rows),"totals":{k:dict(v) for k,v in table.items()},"cases":cases}
    write(HERE/"LIVE111_TWIN_DEATH_AUDIT.json",result)
    print({part:data["totals"] for part,data in result["partitions"].items()},flush=True)
