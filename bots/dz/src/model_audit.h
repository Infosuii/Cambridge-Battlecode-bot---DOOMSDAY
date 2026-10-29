#pragma once
#include "actions.h"
#include "clear_clock.h"

#if DZ_TRACE && DZ_TRACE_MODEL
namespace dz {
// Diagnostic only. Quotes use personal observation and remembered HP; the
// separate offline reader supplies outcomes, never inputs to the live bot.
inline void audit_model(const Goal& goal,const StaticWorld& world,const Memory& mem,
                        const Observation& obs,const TurnContext& tc) {
    if (world.slot!=DZ_TRACE_SLOT || tc.round>DZ_TRACE_MODEL_TO || !tc.allow(22000)) return;
    static int last_kind=-1,last_group=-1;
    static bool contact_logged=false;
    const int kind=static_cast<int>(goal.kind);
    const int index=goal.kind==GoalKind::Farm?goal.index:-1;
    const bool changed=kind!=last_kind || index!=last_group;
    if (!changed && (index<0 || contact_logged)) return;
    bool contact=false;
    if (index>=0 && cambc::self().can_attack()) {
        const auto& g=world.groups[index];
        for (unsigned k=0;k<g.tiles.size();++k) {
            auto tile=g.tiles[k];
            if (mem.member_hp[index][k]>0 && obs.p.chebyshev_distance(tile)<=obs.range &&
                cambc::vision::in_vision(tile) && cambc::vision::has_camp(tile)) { contact=true; break; }
        }
    }
    if (!changed && !contact) return;
    ClearRisk risk;
    int distance=-1,field=0,state=-1,seen=-1,cluster=0;
    float remembered=0;std::size_t members=0;
    if (index>=0) {
        const auto& g=world.groups[index];const auto& b=mem.groups[index];
        risk=group_clear_risk(world,mem,obs,index);
        distance=world.distance(index,obs.p);field=bool(g.field);state=static_cast<int>(b.state);
        seen=b.seen;remembered=b.hp;members=g.tiles.size();cluster=g.cluster;
    }
    unsigned nearby=0;
    for (const auto& a:obs.allies) nearby+=a.hp>0 && a.p.chebyshev_distance(obs.p)<=4;
    const auto timing=reset_timing();
    AttackClock clock;double timed_loss=0;
    if(index>=0 && risk.complete())clock=group_attack_clock(world,mem,obs,index,mem.quantize_out,timing,&timed_loss);
    const auto body=static_cast<std::uint32_t>(static_cast<cambc::handle_champion_t>(cambc::self()));
    // Retry a dropped record next turn. Never pretend a missing prediction
    // was issued at an earlier position or before an earlier attack.
    if (trace("DZ_MODEL round=%u body=%u slot=%u kind=%d group=%d new=%d contact=%d x=%d y=%d state=%d seen=%d dist=%d field=%d attacks=%u loss=%.2f hp=%.2f camp_hp=%.2f raw=%.2f quant=%.2f range=%d cluster=%d members=%zu nearby=%u enemies=%zu status=%d reset_cd=%u reset_max=%u clock=%u clock_status=%d timed_loss=%.2f\n",
              tc.round,body,world.slot,kind,index,changed,contact,obs.p.x,obs.p.y,state,seen,distance,field,
              risk.attacks,risk.damage,obs.hp,remembered,obs.strength*obs.camp_damage,
              index>=0?mem.quantize_out:0.f,obs.range,cluster,members,nearby,obs.enemies.size(),
              index>=0?static_cast<int>(risk.status):-1,timing.remaining,timing.period,clock.rounds,static_cast<int>(clock.status),timed_loss)) {
        if (changed) contact_logged=false;
        contact_logged|=contact;last_kind=kind;last_group=index;
    }
}
}
#endif
