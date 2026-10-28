"""Minimal end-of-decision trace for cases sensitive to mid-function probes."""
import hashlib
import json
from pathlib import Path
from make_trace import make as select_case
from make_trace_binary import HEADER
from deep_preflight import ROOT


def make(case,destination):
    destination=Path(destination).resolve();assert destination.is_relative_to(ROOT/'artifacts')
    selection=select_case(case,destination.parent/(case['card_id']+'-selection'))
    start,end,actor=(selection[k] for k in ('trace_from','trace_until','trace_actor'))
    source=ROOT/'bots/live-69/src'
    contents={p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*') if p.is_file()}
    contents['deep_trace.h']=(f'#define DT_FROM {start}\n#define DT_UNTIL {end}\n#define DT_ACTOR {actor}u\n'+HEADER).replace('\n','\r\n').encode()
    contents['common.h']=b'#include "deep_trace.h"\r\n'+contents['common.h']
    needle=b'        bc::end_turn();';assert contents['main.cpp'].count(needle)==1
    contents['main.cpp']=contents['main.cpp'].replace(needle,b'        if(deeptrace::n) deeptrace::flush(bc::round_number());\r\n'+needle)
    needle=b'    debug_block({ std::printf("M %d %u %s %d\\n", round, my_id, mode, target_group); });'
    assert contents['bot.cpp'].count(needle)==1
    code='''    DT3(1,tune::kTributeCarry,tune::kShopGold,tune::kGoldWeight,tune::kAggression,tune::kRetreatHp,tune::kDangerHp,tune::kStand2,tune::kTSearch,tune::kRangedFlee,float(V75_LONE),V75_BAG,float(V75_RACE),V75_GATE,V71_MAP_KNOBS,A2_LAB,V58_ACT,V58_SURVIVE,target_group);
    DT3(11,deeptrace::mode_id(mode),pos.x,pos.y,hp,gems,walked,cast_done,heading_home,target_group,force_tribute);
'''.replace('\n','\r\n').encode()
    contents['bot.cpp']=contents['bot.cpp'].replace(needle,code+needle)
    for name,data in contents.items():
        p=destination/'src'/name;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists():assert p.read_bytes()==data,'Use a fresh trace output directory'
        p.write_bytes(data)
    result=case|{'trace_actor':actor,'trace_from':start,'trace_until':end,'format':'tail-numeric-v4',
                 'source_hashes':{n:hashlib.sha256(b).hexdigest() for n,b in contents.items()},
                 'limits':'Only final mode/effective tuning on turns reaching normal play_turn tail. No channel/dead early return or mid-guard telemetry; validate exact prefix.'}
    (destination/'trace-identity.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    return result
