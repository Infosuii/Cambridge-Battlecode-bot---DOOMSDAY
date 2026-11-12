"""Low-overhead numeric trace: cache words, write once after the decision completes."""
import hashlib
import json
from pathlib import Path
from make_trace import make as verbose_make

HEADER = r'''// Diagnostic numeric trace; dumps after play_turn, never an SDK decision input.
#pragma once
#include <bit>
#include <cstdint>
#include <cstdio>
namespace deeptrace {
struct Record { std::uint32_t magic,round,actor,stage,count,data[64]; };
inline Record records[24]{};
inline unsigned n=0;
inline std::uint32_t word(float v){return std::bit_cast<std::uint32_t>(v);}
inline std::uint32_t word(double v){return word(float(v));}
template<class T> inline std::uint32_t word(T v){return std::uint32_t(v);}
template<class... T> inline void add(unsigned r,unsigned id,unsigned stage,T... a){
 if(n==24)return;
 auto &v=records[n++];v.magic=0x44545234;v.round=r;v.actor=id;v.stage=stage;v.count=sizeof...(a);
 const std::uint32_t words[]={word(a)...};for(unsigned i=0;i<sizeof...(a);++i)v.data[i]=words[i];
}
inline unsigned mode_id(const char* p){unsigned h=2166136261u;while(*p){h=(h^static_cast<unsigned char>(*p++))*16777619u;}return h;}
inline void flush(unsigned engine_round){if(n){for(unsigned i=0;i<n;++i)records[i].data[63]=engine_round;std::fwrite(records,sizeof(Record),n,stdout);n=0;}}
}
#define DT3(stage, ...) do {if(round>=DT_FROM && round<=DT_UNTIL && my_id==DT_ACTOR) deeptrace::add(round,my_id,stage,__VA_ARGS__);}while(0)
'''


def make(case, destination):
    # Reuse only the frozen case/actor selection from the verbose builder; no
    # verbose instrumented source is used in this build.
    from deep_preflight import ROOT
    selector = Path(destination).parent / (case['card_id'] + '-selection')
    selected = verbose_make(case, selector)
    start, end, actor = (selected[k] for k in ('trace_from', 'trace_until', 'trace_actor'))
    source = ROOT / 'bots/live-69/src'
    contents = {p.relative_to(source).as_posix(): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    changes=[]
    def ins(file,needle,extra,after=False):
        b=contents[file];n=needle.encode();assert b.count(n)==1,(file,needle[:60],b.count(n))
        e=extra.rstrip('\n').replace('\n','\r\n').encode()+b'\r\n'
        contents[file]=b.replace(n,n+e if after else e+n,1);changes.append({'file':file,'anchor':needle[:80]})
    contents['deep_trace.h']=(f'#define DT_FROM {start}\n#define DT_UNTIL {end}\n#define DT_ACTOR {actor}u\n'+HEADER).replace('\n','\r\n').encode()
    contents['common.h']=b'#include "deep_trace.h"\r\n'+contents['common.h']
    ins('main.cpp','        bc::end_turn();','        if(deeptrace::n) deeptrace::flush(bc::round_number());')
    ins('bot.cpp','    cast_done = false;\r\n    keep_channel = false;', '''    DT3(1,tune::kTributeCarry,tune::kShopGold,tune::kGoldWeight,tune::kAggression,tune::kRetreatHp,tune::kDangerHp,tune::kStand2,tune::kTSearch,tune::kRangedFlee,float(V75_LONE),V75_BAG,float(V75_RACE),V75_GATE,V71_MAP_KNOBS,A2_LAB,V58_ACT,V58_SURVIVE,target_group);
    if(round==DT_FROM && my_id==DT_ACTOR) deeptrace::add(round,my_id,2,lab::knobs[0],lab::knobs[1],lab::knobs[2],lab::knobs[3],lab::knobs[4],lab::knobs[5],lab::knobs[6],lab::knobs[7],lab::knobs[8],lab::knobs[9],lab::knobs[10],lab::knobs[11],lab::knobs[12],lab::knobs[13],lab::knobs[14],lab::knobs[15],lab::knobs[16],lab::knobs[17],lab::knobs[18],lab::knobs[19],lab::knobs[20],lab::knobs[21],lab::knobs[22],lab::knobs[23],lab::knobs[24],lab::knobs[25],lab::knobs[26],lab::knobs[27],lab::knobs[28],lab::knobs[29],lab::knobs[30],lab::knobs[31],lab::knobs[32],lab::knobs[33],lab::knobs[34],lab::knobs[35],lab::knobs[36],lab::knobs[37],lab::knobs[38],lab::knobs[39],lab::knobs[40],lab::knobs[41],lab::knobs[42],lab::knobs[43],lab::knobs[44],lab::knobs[45],lab::knobs[46],lab::knobs[47]);''')
    ins('bot.cpp','    if (state.is_dead()) {\r\n        episode_tick(true);','    DT3(3,state.is_dead(),target_group);')
    ins('bot.cpp','    // A recall started before a capture landed:','    DT3(4,pos.x,pos.y,hp,max_hp,gems,gold,range,melee,heading_home,target_group);')
    ins('bot.cpp','bool Bot::handle_enemies() {\r\n','    DT3(5,int(w.enemies.size()));',True)
    ins('bot.cpp','    // V75_LONE = r (0 = off):','    DT3(6,winning,in_danger,nearest?int(nearest->id):-1,nearest_d,nearest?nearest->range:-1,target?int(target->id):-1,target_ttk,ttd,risk);')
    ins('bot.cpp','        if (friends == 0 && theirs >= V75_LONE * hp) {','        DT3(7,friends,theirs,hp);')
    ins('bot.cpp','    if (tune::kTribDeny & 2) {','    DT3(8,winning,in_danger,target?int(target->id):-1,target_ttk);')
    ins('bot.cpp','bool Bot::tribute_if_needed() {\r\n','    DT3(9,gems,w.no_bank,w.altar_gated,tribute_off_until,force_tribute,tune::kTributeCarry);',True)
    ins('bot.cpp','    if (dist == kUnreach) return false;\r\n    const bool wins = ally_score + gems','    DT3(10,dist,use_safe);')
    ins('bot.cpp','    PROF_CHECK("tail");\r\n    build_fields();','    DT3(11,deeptrace::mode_id(mode),pos.x,pos.y,hp,gems,walked,cast_done,heading_home,target_group,force_tribute);')
    ins('tactics.cpp','bool Bot::act_enemy_before_walk() {\r\n','    DT3(12,int(w.enemies.size()),walked,cast_done);',True)
    ins('tactics.cpp','bool Bot::survive_contact() {\r\n','    DT3(13,int(w.enemies.size()));',True)
    ins('tactics.cpp','    if (!bag_panic && (immediate_finish || hostile < 1.65f * friendly)) return false;','    DT3(14,distance,int(nearest->id),bag_panic,immediate_finish,hostile,friendly);')
    ins('tactics.cpp','    if (!moved) return false;\r\n    if (bag_panic || hp < 0.45f * max_hp)','    DT3(15,dashed,moved);')
    destination=Path(destination).resolve();assert destination.is_relative_to(ROOT/'artifacts')
    for name,data in contents.items():
        p=destination/'src'/name;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists():assert p.read_bytes()==data,'Use a fresh trace directory'
        p.write_bytes(data)
    result=case|{'trace_actor':actor,'trace_from':start,'trace_until':end,'format':'numeric-v4','changes':changes,
                 'source_hashes':{n:hashlib.sha256(b).hexdigest() for n,b in contents.items()},
                 'interpretation':'numeric snapshots buffered without formatting; dump after decision; still verify prefix and stop at divergence'}
    (destination/'trace-identity.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    return result
