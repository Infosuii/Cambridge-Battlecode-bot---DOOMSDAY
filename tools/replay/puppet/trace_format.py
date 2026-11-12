"""Decode numeric trace records; private binary logs remain in local-only artifacts."""
import re
import struct
from deep_preflight import ROOT
FIELDS={
1:('TUNE','carry:i shop:i goldw:f aggression:f retreat:f danger:f stand2:i tsearch:i ranged_flee:i lone:f bag:i race:f gate:i mapknobs:i lab:i act:i survive:i group:i'),
3:('TURN','dead:i group:i'),4:('SELF','x:i y:i hp:f maxhp:f bag:i gold:i range:i melee:i home:i group:i'),
5:('ENTER_HANDLE','enemies:i'),6:('GUARD_IN','win:i danger:i nearest:i nd:i erange:i target:i ttk:f ttd:f risk:f'),
7:('GUARD_COUNT','friends4:i enemy_hp6:f self_hp:f'),8:('GUARD_OUT','win:i danger:i target:i ttk:f'),
9:('BANK_CHECK','bag:i no_bank:i gated:i off_until:i force:i carry:i'),10:('BANK_ROUTE','dist:i safe:i'),
11:('END','mode:u x:i y:i hp:f bag:i walked:i cast:i home:i group:i force:i'),12:('ENTER_ACT','enemies:i walked:i cast:i'),
13:('ENTER_SURVIVE','enemies:i'),14:('SURVIVE_EVAL','nd:i nearest:i bag_panic:i immediate:i hostile:f friendly:f'),15:('SURVIVE_MOVE','dashed:i moved:i'),
16:('CANCEL_WIN_RECALL','bag:i own_score:i enemy_score:i no_bank:i gated:i off_until:i hp:f maxhp:f danger:f'),
17:('BANK_CONTEXT','own_score:i enemy_score:i no_bank:i gated:i off_until:i hp:f maxhp:f bag:i danger:f channel_guard:f recalling:i banking:i carry:i force:i')}


def fnv(s):
    h=2166136261
    for c in s.encode():h=((h^c)*16777619)&0xffffffff
    return h


def decode(raw):
    modes={fnv(s):s for p in (ROOT/'bots/live-69/src').glob('*.cpp') for s in re.findall(r'"([a-z][a-z0-9-]{1,32})"',p.read_text(encoding='utf-8'))}
    magics=[struct.pack('<I',v) for v in (0x44545233,0x44545234)];size=69*4;pos=0;rows=[]
    while True:
        hits=[i for m in magics if (i:=raw.find(m,pos))>=0]
        if not hits:break
        i=min(hits)
        if i+size>len(raw):raise ValueError('Truncated numeric trace')
        words=struct.unpack_from('<69I',raw,i);_,r,actor,stage,n=words[:5]
        if not(0<=r<=2000 and actor<32 and 1<=stage<=17 and n<=64):raise ValueError('Bad numeric trace header')
        if stage==2:
            assert n==48;name='KNOBS';data={str(k):struct.unpack('<f',struct.pack('<I',v))[0] for k,v in enumerate(words[5:53])}
        else:
            name,spec=FIELDS[stage];fields=spec.split();assert len(fields)==n,(stage,n)
            data={}
            for field,v in zip(fields,words[5:5+n]):
                label,kind=field.split(':');value=struct.unpack('<f' if kind=='f' else '<i' if kind=='i' else '<I',struct.pack('<I',v))[0]
                data[label]=modes.get(value,str(value)) if label=='mode' else value
        rows.append({'r':r,'emitted_round':words[68] if words[0]==0x44545234 else None,'actor':actor,'stage':name,'values':data});pos=i+size
    return rows
