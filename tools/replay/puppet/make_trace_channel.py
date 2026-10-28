"""Focused bank/recall trace added after an exact tail trace exposed channel churn."""
import hashlib
import json
from pathlib import Path
from make_trace_tail import make as tail_make


def make(case,destination):
    destination=Path(destination)
    selected=tail_make(case,destination.parent/(case['card_id']+'-tail-base'))
    base=destination.parent/(case['card_id']+'-tail-base')
    contents={p.relative_to(base/'src').as_posix():p.read_bytes() for p in (base/'src').rglob('*') if p.is_file()}
    def ins(needle,code,after=False):
        b=contents['bot.cpp'];n=needle.encode();assert b.count(n)==1
        e=code.replace('\n','\r\n').encode()+b'\r\n';contents['bot.cpp']=b.replace(n,n+e if after else e+n,1)
    ins('bool Bot::tribute_if_needed() {\r\n','    DT3(9,gems,w.no_bank,w.altar_gated,tribute_off_until,force_tribute,tune::kTributeCarry);',True)
    ins('    if (dist == kUnreach) return false;\r\n    const bool wins = ally_score + gems','    DT3(10,dist,use_safe);')
    ins('    if (state.contains(bc::champion_state::recalling) && win_now() && hp >= max_hp * tune::kDangerHp) {\r\n','        DT3(16,gems,ally_score,enemy_score,w.no_bank,w.altar_gated,tribute_off_until,hp,max_hp,tune::kDangerHp);',True)
    for name,data in contents.items():
        p=destination/'src'/name;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists():assert p.read_bytes()==data,'Use a fresh focused trace directory'
        p.write_bytes(data)
    result=selected|{'format':'channel-numeric-v4','source_hashes':{n:hashlib.sha256(b).hexdigest() for n,b in contents.items()},
                     'limits':'Focused exploratory probe after recall churn observation. Verify prefix and retain the prior failed probes.'}
    (destination/'trace-identity.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    return result
