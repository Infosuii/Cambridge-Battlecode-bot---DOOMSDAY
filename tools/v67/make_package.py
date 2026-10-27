"""Build a separate coherent combat/coordination/raw-stat prototype from the corrected core.

The active v67 portfolio stays unchanged; this is an independent mechanism experiment.
"""
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'artifacts/tmp/v67/combat-package-v2'
assert not out.exists()
src=out/'src';src.mkdir(parents=True)
source=ROOT/'bots/v67/src/policies/p15'
cpp_stems={p.stem[4:] for p in (ROOT/'bots/v67/src').glob('p15_*.cpp') if p.stem!='p15_entry'}
for p in source.iterdir():
    if p.is_file():
        name=p.stem+'.cpp' if p.suffix=='.inc' and p.stem in cpp_stems else p.name
        shutil.copyfile(p,src/name)
shutil.copyfile(ROOT/'artifacts/tmp/v67/controller-v21/main.cpp',src/'main.cpp')
p=src/'common.h';s=p.read_bytes().decode();s=s.replace('#define NOVA_SEED (::v67_eval_seed)','#define NOVA_SEED 1')
for name,value in {'V67_TEAMPLAY':'2','V67_META':'3','V67_OPENING':'0','V67_BUILD':'3','V67_FIGHT':'0','V67_COORD':'1','V67_CAMP_STATE':'1'}.items():
    s=re.sub(r'(^#define '+name+r' )[^\r\n]*',lambda m:m[1]+value,s,flags=re.M)
p.write_bytes(s.encode())
p=src/'bot.cpp';s=p.read_bytes().decode();e='\r\n' if '\r\n' in s else '\n'
s=s.replace('#include "v67_meta_build.inc"'+e+'#include "v67_build.inc"','#include "v67_build.inc"'+e+'#include "v67_meta_build.inc"',1)
s=s.replace('bool Bot::group_capture_covered(const GroupRec& g) const {','bool Bot::group_capture_covered(const GroupRec& g) const {'+e+'    if (const int owner=v67_capture_owner(g); owner>=0) return owner!=slot;',1)
s=s.replace('int Bot::score_groups(int participants_hint, int& best_need, float& best_score) {',
'''int Bot::score_groups(int participants_hint, int& best_need, float& best_score) {
    if (const int follow=v67_buddy_job(); follow>=0) {best_need=1;best_score=1e9f;return follow;}
    if(battle_target67_>=0 || round-contact67_<=20) {
        if(type==bc::champion_type::heart_of_ruin)participants_hint=std::max(participants_hint,std::min(3,team_size));
        if(type==bc::champion_type::varg)participants_hint=std::max(participants_hint,2);
    }'''.replace('\n',e),1)
p.write_bytes(s.encode())
p=src/'bot.h';s=p.read_bytes().decode();e='\r\n' if '\r\n' in s else '\n'
s=s.replace('    bool v67_team_combat();','    bool v67_team_combat();'+e+'    int v67_capture_owner(const GroupRec& g) const;'+e+'    int v67_buddy_job() const;'+e+'    int contact67_=-1000;')
p.write_bytes(s.encode())
p=src/'v67_meta.cpp';s=p.read_text(encoding='utf8');s=s.replace('    const auto& team = selected();','''    constexpr bc::champion_draft package[]={bc::champion_draft::vesper_vale,bc::champion_draft::heart_of_ruin,
        bc::champion_draft::vendetta,bc::champion_draft::varg,bc::champion_draft::marcella,bc::champion_draft::ryth};
    for(auto hero:package) if(std::find(chosen.begin(),chosen.end(),hero)==chosen.end()) {
        bc::draft::pick(hero); return true;
    }
    const auto& team = selected();''',1);p.write_text(s,encoding='utf8',newline='\n')
(src/'v67_build.inc').write_text('''#if V67_BUILD == 3
{
    using ct=bc::champion_type;
    const bool focus_user=t==ct::heart_of_ruin||t==ct::cassi||t==ct::stellar||t==ct::prism||t==ct::marcella||t==ct::willow;
    const it main=focus_user?it::bruiser_shard_of_focus:it::bruiser_shard_of_strength;
    std::vector<BuildStep> plan;
    if(t==ct::vesper_vale) {
        plan.push_back({it::treasure_shard_of_strength,5});
        plan.push_back({main,5});
        plan.push_back({it::jungle_shard_of_health,5});
    } else {
        plan.push_back({it::jungle_shard_of_health,5});
        plan.push_back({main,5});
    }
    for(int n=10;n<=150;n+=5) plan.push_back({main,n});
    return plan;
}
#endif
''',encoding='utf8',newline='\n')
p=src/'v67_team.cpp';s=p.read_text(encoding='utf8')
a=s.index('bool Bot::v67_team_combat() {');b=s.index('bool Bot::v67_team_home()',a)
s=s[:a]+s[b:]
s=s.replace('hp>=max_hp*0.65f&&!heading_home&&friends>=foes','hp>=max_hp*0.2f')
s=s.replace('hp<max_hp*0.75f || gems>=30','hp<max_hp*0.6f || gems>=50')
s=s.replace('    cast_done = walked = keep_channel = false;','    cast_done = walked = keep_channel = false;\n    force_tribute=false;')
s=s.replace('            bot->v67_team_publish(true);','            bot->v67_team_after_turn();')
s=s.replace('''    if (state.contains(bc::champion_state::recalling) || state.contains(bc::champion_state::submitting_gems) ||
        state.contains(bc::champion_state::teleporting)) return;
    v67_team_plan();''','''    if(state.contains(bc::champion_state::teleporting)) return;
    if(state.contains(bc::champion_state::recalling)||state.contains(bc::champion_state::submitting_gems)) {
        float incoming=0;
        for(const auto& e:w.enemies) if(cheb(pos,e.pos)<=e.range+2) incoming+=e.strength+e.focus*0.3f;
        std::int32_t left=0; cambc::detail::sdk_champion_channel_time(my_id,&left);
        if(incoming*(left+1)<hp*0.8f) return;
        try {
            if(state.contains(bc::champion_state::recalling)) me.cancel_recall(); else me.cancel_submit_gems();
        } catch(...) {return;}
        refresh_self(); w.update(round); v67_team_sync();
    }
    if(ward_reveal()) {w.update(round);v67_team_sync();}
    if(counter_ambush()) {w.update(round);v67_team_sync();}''')
s=s.replace('''        if (!v67_team_home() && !v67_team_bank()) {
#if V67_TEAMPLAY == 2
            farm();
#else
            v67_team_farm();
#endif
        }''','''        if(gems>=50 && battle_target67_>=0) force_tribute=true;
        if(!go_home_if_needed() && !tribute_if_needed() && !v67_team_join()) {
            farm(); opportunistic_attack();
        }''')
p.write_text(s,encoding='utf8',newline='\n')
package=(ROOT/'tools/v67/package_combat.cpp').read_text(encoding='utf8')
a=package.index('int Bot::v67_capture_owner');b=package.index('int Bot::v67_buddy_job',a)
capture=package[a:b]
p=src/'bot.cpp';original=p.read_bytes().decode();end='\r\n' if '\r\n' in original else '\n'
p.write_bytes((original+end+capture.replace('\n',end)).encode())
(src/'package_combat.cpp').write_text(package[:a]+package[b:],encoding='utf8',newline='\n')
print('prepared',out)
