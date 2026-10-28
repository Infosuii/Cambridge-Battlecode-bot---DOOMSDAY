"""Build a separate coherent combat/coordination/raw-stat prototype from the corrected core.

The active v67 portfolio stays unchanged; this is an independent mechanism experiment.
"""
import argparse
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--variant', choices=['responsive','lifecycle','symmetric','crews','productive','vision','entry','cohort'], default='lifecycle')
ap.add_argument('--legacy-combat',action='store_true',help='Paired cohort control using the established fight executor')
args=ap.parse_args()
lifecycle=args.variant!='responsive'
assert not args.legacy_combat or args.variant=='cohort'
version={'responsive':2,'lifecycle':3,'symmetric':4,'crews':5,'productive':6,'vision':7,'entry':8,'cohort':9}[args.variant]
if args.legacy_combat:version=10
out=ROOT/f'artifacts/tmp/v67/combat-package-v{version}'
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
for name,value in {'V67_TEAMPLAY':'3' if lifecycle else '2','V67_META':'3','V67_OPENING':'0','V67_BUILD':'3','V67_FIGHT':'0','V67_COORD':'1','V67_CAMP_STATE':'1'}.items():
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
if lifecycle:
    # Preserve the mature lifecycle: priorities, death/job cleanup, field warmup,
    # claim tenure and race/banking bookkeeping. Only the contact decision is
    # replaced; legacy hunt cannot override a rejected fight.
    p=src/'bot.cpp';s=p.read_bytes().decode();end='\r\n' if '\r\n' in s else '\n'
    start=s.index('    const bool fought ='+end)
    stop=s.index('#if A2_SHIELDLATE',start)
    controller='handle_enemies()' if args.legacy_combat else 'v67_team_combat()'
    s=s[:start]+'    const bool fought = '+controller+';'+end+s[stop:]
    assert s.count('} else if (hunt()) {')==1
    s=s.replace('} else if (hunt()) {','} else if (false) { // all contact decisions belong to v67_team_combat')
    p.write_bytes(s.encode())
p=src/'bot.h';s=p.read_bytes().decode();e='\r\n' if '\r\n' in s else '\n'
s=s.replace('    bool v67_team_combat();','    bool v67_team_combat();'+e+'    int v67_capture_owner(const GroupRec& g) const;'+e+'    int v67_buddy_job() const;'+e+'    int contact67_=-1000;')
if args.variant in ('productive','vision','entry','cohort'):
    assert s.count('    int contact67_=-1000;')==1
    s=s.replace('    int contact67_=-1000;','    int contact67_=-1000;'+e+
        '    int crew_progress_job67_=-1,crew_progress_round67_=0;'+e+'    float crew_progress_hp67_=0;')
if args.variant=='cohort':
    s=s.replace('    int contact67_=-1000;','    int contact67_=-1000;'+e+'    float v67_item_investment(int s) const;')
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
if args.variant in ('productive','vision','entry','cohort'):
    p=src/'v67_build.inc';s=p.read_text(encoding='utf8')
    s=s.replace('    std::vector<BuildStep> plan;','    const it jungle=focus_user?it::jungle_shard_of_focus:it::jungle_shard_of_strength;\n    std::vector<BuildStep> plan;')
    s=s.replace('plan.push_back({it::jungle_shard_of_health,5});','plan.push_back({jungle,5});')
    s=s.replace('''    } else {
        plan.push_back({jungle,5});
        plan.push_back({main,5});
    }''','''    } else {
        plan.push_back({main,5});
        plan.push_back({jungle,5});
    }''')
    p.write_text(s,encoding='utf8',newline='\n')
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
if args.variant in ('crews','productive','vision','entry','cohort'):
    p=src/'v67_team.cpp';s=p.read_text(encoding='utf8')
    start=s.index('bool Bot::v67_team_farm() {');stop=s.index('void Bot::v67_team_turn()',start)
    s=s[:start]+s[stop:];p.write_text(s,encoding='utf8',newline='\n')
    p=src/'bot.cpp';s=p.read_bytes().decode()
    assert s.count('if (!farm()) mode = "nofarm";')==1
    s=s.replace('if (!farm()) mode = "nofarm";','if (!v67_team_farm()) mode = "nofarm";')
    p.write_bytes(s.encode())
    farm=(ROOT/'tools/v67/package_farm.cpp').read_text(encoding='utf8')
    if args.variant in ('productive','vision','entry','cohort'):
        farm=farm.replace('''            if(!a.alive||!a.exact||!bit(g.tiles,a.pos))continue;''','''            if(!a.alive||!a.exact)continue;
            bool ready=bit(g.tiles,a.pos);
            if(slot_type[s]==ct::vesper_vale&&a.job==gi&&a.hp>=a.max_hp*0.4f&&w.enemies.empty())
                for(int ci:g.camps)ready|=cheb(a.pos,w.camps[ci].pos)<=2;
            if(!ready)continue;''')
        farm=farm.replace('''    int job=-1;''','''    if(valid(target_group)) {
        const auto& g=w.groups[target_group];const float remaining=g.hp_left(w.camps);
        if(crew_progress_job67_!=target_group||g.state!=GroupState::alive||distance_to(target_group,pos)>8) {
            crew_progress_job67_=target_group;crew_progress_hp67_=remaining;crew_progress_round67_=round;
        } else if(round-crew_progress_round67_>=40) {
            if(crew_progress_hp67_-remaining<std::max(100.0f,g.max_hp*0.1f))avoid_until[target_group]=round+30;
            crew_progress_hp67_=remaining;crew_progress_round67_=round;
        }
    }
    int job=-1;''',1)
        farm=farm.replace('''            value/=1+loss/std::max(1.0f,pool)*0.5f;''','''            bool other_crew=false;
            for(int s=0;s<std::min(team_size,6);++s) {
                const auto& a=team67_[s];
                other_crew|=a.alive&&crew(s)!=mine&&a.job==gi&&round-a.job_seen<=4;
            }
            if(other_crew)value*=0.6f;
            value/=1+loss/std::max(1.0f,pool)*0.5f;''')
    if args.variant=='cohort':
        farm=farm.replace('if(team_size<=3)return 0;','if(team_size<=3||round<150)return 0;')
        farm=farm.replace('''        int owner=-1;
        for(int s=0;s<std::min(team_size,6);++s) {''','''        int owner=-1;float investment=1e30f;
        const int preferred=v67_capture_owner(g);
        for(int s=0;s<std::min(team_size,6);++s) {''',1)
        farm=farm.replace('if(slot_type[s]==ct::vesper_vale&&a.job==gi&&a.hp>=a.max_hp*0.4f&&w.enemies.empty())',
            'if(s==preferred&&a.job==gi&&a.hp>=a.max_hp*0.4f&&w.enemies.empty())')
        farm=farm.replace('''            if(owner<0||slot_type[s]==ct::vesper_vale)owner=s;''','''            if(s==preferred)return s;
            const float amount=v67_item_investment(s);
            if(amount<investment)owner=s,investment=amount;''')
        farm=farm.replace('''    auto& g=w.groups[job];''','''    auto& g=w.groups[job];
    if(g.state==GroupState::alive&&type==ct::heart_of_ruin) {
        for(int ci:g.camps)if(!w.camps[ci].dead&&bit(w.visible,w.camps[ci].pos)&&cheb(pos,w.camps[ci].pos)<=3)
            if(cast_camp_strike(ci)) {w.update(round);break;}
    }''',1)
    (src/'package_farm.cpp').write_text(farm,encoding='utf8',newline='\n')
package=(ROOT/'tools/v67/package_combat.cpp').read_text(encoding='utf8')
if args.variant=='symmetric':
    helper=(ROOT/'tools/v67/package_power.h').read_text(encoding='utf8')
    package=package.replace('#include "team_memory.h"','#include "team_memory.h"\n'+helper,1)
    package=package.replace('float our_hp=hp,our_dps=my_dps(nullptr),their_hp=0,their_dps=0,immediate=0;',
        'const float self_weight=contact_weight67(distance,range,ready_gap67(my_id,type));\n'
        '    float our_hp=hp*self_weight,our_dps=my_dps(nullptr)*self_weight,their_hp=0,their_dps=0,immediate=0;')
    package=package.replace('const int eta=std::max(0,cheb(a.pos,target->pos)-a.range);',
        'const int eta=std::max(0,cheb(a.pos,target->pos)-a.range-ready_gap67(a.id,a.type));')
    package=package.replace('''        their_hp+=e.hp;their_dps+=e.strength+kit.nuke*(kit.two_spells?0.25f:0.125f);++foes;''',
        '''        const int eta=std::max(0,d-e.range-ready_gap67(e.id,e.type));
        const float weight=contact_weight67(d,e.range,ready_gap67(e.id,e.type));
        their_hp+=e.hp*weight;
        their_dps+=(e.strength+kit.nuke*(kit.two_spells?0.25f:0.125f))*weight;
        foes+=eta<=1;''')
a=package.index('int Bot::v67_capture_owner');b=package.index('int Bot::v67_buddy_job',a)
capture=package[a:b]
if args.variant=='cohort':
    capture+='''float Bot::v67_item_investment(int s) const {
    const auto& a=team67_[s];
    return items_of(slot_type[s],a.max_hp,a.strength,a.focus);
}
'''
p=src/'bot.cpp';original=p.read_bytes().decode();end='\r\n' if '\r\n' in original else '\n'
p.write_bytes((original+end+capture.replace('\n',end)).encode())
(src/'package_combat.cpp').write_text(package[:a]+package[b:],encoding='utf8',newline='\n')
if args.variant in ('vision','entry','cohort'):
    from vision_patch import patch_folder
    patch_folder(src,persistent=args.variant!='vision')
print('prepared',out)
