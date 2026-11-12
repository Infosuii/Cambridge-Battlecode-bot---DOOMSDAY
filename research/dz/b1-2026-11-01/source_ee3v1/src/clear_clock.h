#pragma once
#include "memory.h"
#include "attack_clock.h"
#include "timed_damage.h"

namespace dz {
struct ResetTiming { unsigned remaining=0,period=0;bool refresh_on_monster=false; };
inline ResetTiming reset_timing() {
    ResetTiming timing;
    auto& me=cambc::self();
    for(auto ability:me.abilities())if(ability.is_attack_reset()&&ability.info()) {
        timing.remaining=static_cast<unsigned>(std::max(0,ability.cooldown()));
        timing.period=static_cast<unsigned>(std::max(0,std::get<cambc::ability_attack_reset>(*ability.info()).max_cooldown));
    }
    timing.refresh_on_monster=me.champion_name()==cambc::champion_type::vendetta;
    return timing;
}
// A timing estimate only: executor-like initial target ordering, fixed damage,
// no internal movement delay, no extra credit for spells or unseen helpers.
inline AttackClock group_attack_clock(const StaticWorld& world,const Memory& mem,
                                      const Observation& obs,int index,float damage,ResetTiming timing,
                                      double* timed_loss=nullptr) {
    const auto& g=world.groups[index];const auto& hp=mem.member_hp[index];
    if(hp.size()>64||hp.size()!=g.tiles.size()||hp.size()!=g.initial_strength.size())return {};
    struct Target { TimedAttackJob job;float strength,hp;int distance; };
    std::array<Target,64> targets;unsigned count=0;
    for(unsigned k=0;k<hp.size();++k) {
        const BasicTarget t[]{ {hp[k],damage} };const auto work=basic_attack_work(t);
        if(!work.complete())return {work.status,0,0,0};
        if(work.attacks)targets[count++]={{work.attacks,timing.refresh_on_monster&&g.initial_strength[k]>0},
            g.initial_strength[k],hp[k],static_cast<int>(obs.p.chebyshev_distance(g.tiles[k]))};
    }
    std::sort(targets.begin(),targets.begin()+count,[](const Target& a,const Target& b) {
        if(a.strength!=b.strength)return a.strength>b.strength;
        if(a.distance!=b.distance)return a.distance<b.distance;
        return a.hp<b.hp;
    });
    std::array<TimedAttackJob,64> jobs;
    for(unsigned k=0;k<count;++k)jobs[k]=targets[k].job;
    if(timed_loss) {
        std::array<TimedDamageJob,64> risk;
        for(unsigned k=0;k<count;++k)risk[k]={targets[k].job,targets[k].strength*obs.camp_factor};
        const auto projection=timed_clear_damage(std::span<const TimedDamageJob>(risk.data(),count),timing.remaining,timing.period);
        *timed_loss=projection.damage;
        return projection.clock;
    }
    return attack_clock(std::span<const TimedAttackJob>(jobs.data(),count),timing.remaining,timing.period);
}
}
