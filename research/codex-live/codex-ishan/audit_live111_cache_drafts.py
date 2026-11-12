"""Recount exact release draft parity on every already played large-development case."""
import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write


if __name__ == "__main__":
    data=read(HERE/"LIVE111_DRAFT_CACHE_RELEASE_LARGE.json")
    rows=[]
    for base,cand in data["pairs"]:
        first=bench.CACHE/"live111-large-development"/base["opponent"]/f"{base['map']}-{base['side']}-stock111/native.json"
        second=bench.CACHE/"live111-draft-cache-release"/cand["opponent"]/f"{cand['map']}-{cand['side']}-draft-cache-release/native.json"
        a,b=read(first),read(second)
        assert all(a["match"][k]==b["match"][k] for k in ("engineBuildHash","mapHash","seed"))
        rows.append({"map":base["map"],"side":base["side"],"opponent":base["opponent"],"draft_equal":a["roster"]["draft"]==b["roster"]["draft"],"source_native_sha256":bench.digest(first),"candidate_native_sha256":bench.digest(second)})
    result={"n":len(rows),"drafts_equal":sum(r["draft_equal"] for r in rows),"safety_pass":data["pass"],"pass":data["pass"] and all(r["draft_equal"] for r in rows),"rows":rows}
    write(HERE/"LIVE111_DRAFT_CACHE_RELEASE_DRAFT_AUDIT.json",result)
    print({k:v for k,v in result.items() if k!='rows'},flush=True)
