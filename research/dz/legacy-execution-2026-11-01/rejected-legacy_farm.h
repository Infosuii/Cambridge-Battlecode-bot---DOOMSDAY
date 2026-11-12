#pragma once
#include "clear_clock.h"

namespace dz {
struct LegacyClearQuote { bool safe=false;unsigned rounds=0;double loss=0; };
// Adapt v76 fight_camps' basic/reset sequence to the already validated DZ
// reset clock. Keep the whole group's incoming damage, paid member travel and
// an escape/health margin. This is neither a crew promise nor a second planner.
inline LegacyClearQuote legacy_clear_quote(const StaticWorld& w,const Memory& m,const Observation& o,int g,ResetTiming timing) {
    const auto& group=w.groups[g];
    if(group.tiles.size()>8||m.member_hp[g].size()!=group.tiles.size())return {};
    // Ryth loses basic strength with HP. A fixed-damage clock cannot admit its
    // damaging clears; leave those with DZ's health-aware objective model.
    if(group.strength>0&&cambc::self().champion_name()==cambc::champion_type::ryth)return {};
    double loss=0;
    const auto clock=group_attack_clock(w,m,o,g,o.strength*o.camp_damage,timing,&loss);
    if(!clock.complete())return {};
    float scale=1,incoming=0;
    for(unsigned k=0;k<group.tiles.size();++k) {
        const float initial=group.initial_strength[k];
        const float current=std::max(initial,m.member_strength[g][k]);
        if(initial<=0&&current>0)return {};
        if(initial>0)scale=std::max(scale,current/initial);
        incoming+=current;
    }
    loss=loss*scale+incoming*o.camp_factor*(2*group.radius+1);
    return {o.hp>1.25*loss+.15*o.max_hp,clock.rounds,loss};
}
}
