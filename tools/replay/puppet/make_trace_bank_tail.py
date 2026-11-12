"""Bank eligibility snapshot only at the unchanged decision tail; no mid-function probe."""
import hashlib
import json
import re
from pathlib import Path
from make_trace_tail import make as tail_make


def make(case,destination):
    destination=Path(destination);base=destination.parent/(case['card_id']+'-tail-base')
    selected=tail_make(case,base)
    contents={p.relative_to(base/'src').as_posix():p.read_bytes() for p in (base/'src').rglob('*') if p.is_file()}
    pattern=rb'    DT3\(1,[^\r\n]+\);\r\n'
    assert len(re.findall(pattern,contents['bot.cpp']))==1
    line=b'    DT3(17,ally_score,enemy_score,w.no_bank,w.altar_gated,tribute_off_until,hp,max_hp,gems,tune::kDangerHp,tune::kChannelGuard,state.contains(bc::champion_state::recalling),state.contains(bc::champion_state::submitting_gems),tune::kTributeCarry,force_tribute);\r\n'
    contents['bot.cpp']=re.sub(pattern,lambda m:line,contents['bot.cpp'])
    for name,data in contents.items():
        p=destination/'src'/name;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists():assert p.read_bytes()==data,'Use a fresh bank-context trace directory'
        p.write_bytes(data)
    result=selected|{'format':'bank-tail-numeric-v4','source_hashes':{n:hashlib.sha256(b).hexdigest() for n,b in contents.items()},
                     'limits':'Cached end-of-turn eligibility context; infer executed calls separately from exact input script, never from an unfaithful logging run.'}
    (destination/'trace-identity.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());return result
