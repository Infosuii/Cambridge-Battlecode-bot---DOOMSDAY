"""Compile intact tested policies into isolated namespaces with a per-map selector.

This generates a new bot for fresh evaluation; retrospective selected scores are
only a prediction. Source snapshots are the benchmark builder's exact copies.
"""
import argparse
from collections import defaultdict, Counter
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
HEADERS=['algorithm','array','cambc.h','cmath','cstdint','cstdio','cstring','iostream','memory','optional','span','string','string_view','tuple','variant','vector']


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',required=True)
    ap.add_argument('--runs',nargs='*')
    ap.add_argument('--force',help='Use one named policy on all maps, for equivalence diagnostics')
    a=ap.parse_args()
    out=(ROOT/a.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT): raise SystemExit('fresh workspace output directory required')
    records=[json.loads(s) for s in (ROOT/'research/v67/RESULTS.jsonl').read_text().splitlines() if s]
    eligible={r['run']:r for r in records if r['opponent']=='v65' and r['seeds']==[1,2] and not r['holdout']}
    if a.runs: eligible={r:eligible[r] for r in a.runs}
    table=defaultdict(list)
    for run,r in eligible.items():
        for m,v in r['per_map'].items(): table[m].append((run,v))
    chosen={m:max(v,key=lambda pair:(pair[1]['wins'],pair[1]['margin']))[0] for m,v in table.items()}
    if a.force: chosen={m:a.force for m in table}
    names=sorted(set(chosen.values()))
    src=out/'src'; src.mkdir(parents=True)
    seed='#pragma once\n#define NOVA_SEED 1\ninline constexpr int v67_eval_seed=NOVA_SEED;\n'
    (src/'common.h').write_text(seed,encoding='utf8',newline='\n')
    # Every standard/SDK header is parsed in global scope before namespace wrapping.
    prelude='#include "common.h"\n#undef NOVA_SEED\n'+''.join('#include <'+h+'>\n' for h in HEADERS)+'namespace bc=cambc;\n'
    manifest=[]
    for k,run in enumerate(names):
        source=ROOT/'artifacts/evaluations/v67'/run/'build/src-bot-s1/src'
        if not source.is_dir(): raise SystemExit('missing source snapshot '+run)
        arm=src/'policies'/f'p{k}'; arm.mkdir(parents=True)
        hashes={}
        for p in source.iterdir():
            if not p.is_file() or p.name=='main.cpp': continue
            if p.suffix not in ('.h','.cpp','.inc'): continue
            text=p.read_bytes().decode('utf8')
            hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
            if p.name=='common.h':
                text=re.sub(r'^#define NOVA_SEED 1\r?$', '#define NOVA_SEED (::v67_eval_seed)',text,flags=re.M)
            target=p.stem+'.inc' if p.suffix=='.cpp' else p.name
            (arm/target).write_bytes(text.encode())
            if p.suffix=='.cpp':
                wrapper=prelude+f'namespace policy{k} {{\n#include "policies/p{k}/{target}"\n}}\n'
                (src/f'p{k}_{p.stem}.cpp').write_text(wrapper,encoding='utf8',newline='\n')
        entry=prelude+f'''namespace policy{k} {{
#include "policies/p{k}/bot.h"
#include "policies/p{k}/draft.h"
void turn() {{
    static Bot bot;
    if(bc::is_draft()) {{
        play_draft();
#if V58_DIRECTOR
        economy_record_roster();
#endif
    }} else bot.play_turn();
}}
}}
'''
        (src/f'p{k}_entry.cpp').write_text(entry,encoding='utf8',newline='\n')
        manifest.append(dict(index=k,run=run,source_sha256=hashes))
    keys=json.loads((ROOT/'research/proxy/map_keys.json').read_text())
    keys={m.replace('_','-'):v['key'] for m,v in keys.items()}
    maincode=prelude+''.join(f'namespace policy{i} {{ void turn(); }}\n' for i in range(len(names)))
    maincode+='''namespace {
unsigned map_key() {
    namespace d=cambc::detail;
    unsigned hash=2166136261u;
    auto mix=[&](std::int64_t value) { for(int b=0;b<4;++b) { hash^=unsigned((value>>(8*b))&255); hash*=16777619u; } };
    mix(bc::map::width()); mix(bc::map::height()); mix(bc::draft::team_size());
    std::uint32_t n=0; d::check(d::sdk_map_num_camp_groups(&n));
    std::vector<std::uint32_t> groups(n); d::check(d::sdk_map_camp_groups(groups.data(),n,&n)); mix(n);
    for(auto g:groups) {
        d::camp_group_info info{}; d::check(d::sdk_map_camp_group(g,&info)); mix(info.gold); mix(info.gems);
        std::uint32_t count=0; d::check(d::sdk_map_camp_group_num_camps(g,&count));
        std::vector<std::uint32_t> camps(count); d::check(d::sdk_map_camp_group_camps(g,camps.data(),count,&count));
        for(auto c:camps) { d::camp_info spec{}; d::check(d::sdk_map_camp_info(c,&spec)); mix(spec.x); mix(spec.y); mix(spec.type); }
    }
    return hash;
}
int choose() {
    switch(map_key()) {
'''
    for m,run in sorted(chosen.items()):
        maincode+=f'    case {keys[m.replace("_","-")]}u: return {names.index(run)}; // {m}: {run}\n'
    fallback=names.index('b06-life15') if 'b06-life15' in names else 0
    maincode+=f'    default: return {fallback};\n    }}\n}}\n}}\nint main() {{\n    int selected=-1;\n    while(true) {{\n        try {{\n            if(selected<0) selected=choose();\n            switch(selected) {{\n'
    maincode+=''.join(f'            case {i}: policy{i}::turn(); break;\n' for i in range(len(names)))
    maincode+='''            }
        } catch(const std::exception& e) { std::printf("bot error: %s\\n",e.what()); }
        catch(...) { std::printf("bot error: unknown exception\\n"); }
        bc::end_turn();
    }
}
'''
    (src/'main.cpp').write_text(maincode,encoding='utf8',newline='\n')
    predicted=sum(eligible[run]['per_map'][m]['wins'] for m,run in chosen.items())
    report=dict(source='training benchmark seeds1/2 only; requires a fresh full run',predicted_wins=predicted,
                maps=chosen,policies=manifest)
    (src/'selection.json').write_text(json.dumps(report,indent=1)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(dict(out=str(out),policies=len(names),predicted_only=predicted,counts=dict(Counter(chosen.values()))),indent=2))


if __name__=='__main__': main()
