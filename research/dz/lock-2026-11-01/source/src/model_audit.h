#pragma once
#include "actions.h"
#include "clear_clock.h"
#include "shield_clear.h"
#include "splash_reduction.h"

#if DZ_TRACE && DZ_TRACE_MODEL
namespace dz {
struct AuditShield {
    ShieldClearProjection result;
    ShieldClearInput input;
    int member=-1,live=0,mode=0,skip=0;
    std::uint32_t hp_hash=0;
    std::uint64_t fuel=0,available=0;
};
inline AuditShield audit_single_shield(const StaticWorld& world,const Memory& mem,
                                      const Observation& obs,int group,ResetTiming reset,const TurnContext& tc) {
    AuditShield quote;
    const bool heart=DZ_TRACE_HEART&&cambc::self().champion_name()==cambc::champion_type::heart_of_ruin;
    if(group<0||(!heart&&cambc::self().champion_name()!=cambc::champion_type::varg))return quote;
    const auto& hp=mem.member_hp[group];const auto& g=world.groups[group];
    if(hp.size()>64||hp.size()!=g.initial_strength.size()){quote.skip=3;return quote;}
    const auto fuel=cambc::fuel_remaining();quote.available=fuel;
    for(unsigned k=0;k<hp.size();++k)if(hp[k]>0){++quote.live;quote.member=static_cast<int>(k);}
    if(quote.live!=1) {
        if(heart)return quote; // Heart's initial extension never reduces mixed groups.
#if DZ_TRACE_SPLASH
        if(quote.live<2){quote.skip=2;return quote;}
        if(!tc.allow(55000)){quote.skip=4;return quote;}
        if(!obs.enemies.empty()){quote.skip=5;return quote;}
        if(world.is_spawn(obs.p)||cambc::map::spawn_region(cambc::team::ally).is_set(obs.p)){quote.skip=6;return quote;}
        if(hp.size()!=g.tiles.size()||hp.size()!=g.attack_ranges.size()){quote.skip=7;return quote;}
        std::array<SplashMember,64> members;
        for(unsigned k=0;k<hp.size();++k)members[k]={{g.tiles[k].x,g.tiles[k].y},std::max(0.f,hp[k]),g.initial_strength[k],g.attack_ranges[k]};
        const auto reduction=splash_reduction(std::span<const SplashMember>(members.data(),hp.size()),{obs.p.x,obs.p.y},obs.range);
        if(!reduction.supported){quote.skip=8;return quote;}
        LocalMask visible;visible.load(cambc::vision::camp_tiles());
        for(unsigned k=0;k<hp.size();++k)if(hp[k]>0&&!visible.test(g.tiles[k])){quote.skip=9;return quote;}
        quote.member=reduction.target;quote.mode=1;
#else
        return quote;
#endif
    }
    if(quote.member<0||g.initial_strength[quote.member]<=0){quote.skip=10;return quote;}
    if(!tc.allow(45000)){quote.skip=11;return quote;}
    quote.hp_hash=member_hp_hash(hp);
    auto& in=quote.input;
    if(heart){quote.mode=2;in.missing_health_bonus=cambc::constants::passive_abilities::heart_of_ruin_missing_health_damage_max_bonus;}
    in.hp=obs.hp;in.max_hp=obs.max_hp;in.target_hp=hp[quote.member];
    in.damage=obs.strength*obs.camp_damage; // raw constant-kit damage; risk quantization is unchanged
    in.incoming=g.initial_strength[quote.member]*obs.camp_factor;
    in.reset_cd=reset.remaining;in.reset_period=reset.period;
    auto& me=cambc::self();in.can_cast=me.can_cast();
    const auto buffs=me.buffs();
    if(buffs.has<cambc::buff_shield>()) {
        const auto buff=buffs.get<cambc::buff_shield>();
        in.existing=true;in.existing_value=buff.value;in.existing_duration=static_cast<unsigned>(std::max(0,buff.duration));
    }
    for(auto ability:me.abilities())if(ability.is_shield()&&ability.info()) {
        const auto info=std::get<cambc::ability_shield>(*ability.info());
        in.shield_cd=static_cast<unsigned>(std::max(0,ability.cooldown()));
        in.shield_period=static_cast<unsigned>(std::max(0,info.max_cooldown));
        in.shield_duration=static_cast<unsigned>(std::max(0,info.duration));in.shield_amount=ability.shield_amount();
    }
    quote.result=shield_clear(in,96);quote.fuel=fuel-cambc::fuel_remaining();return quote;
}
// Diagnostic only. Quotes use personal observation and remembered HP; the
// separate offline reader supplies outcomes, never inputs to the live bot.
inline void audit_model(const Goal& goal,const StaticWorld& world,const Memory& mem,
                        const Observation& obs,const TurnContext& tc) {
    if (world.slot!=DZ_TRACE_SLOT || tc.round>DZ_TRACE_MODEL_TO || !tc.allow(45000)) return;
    static int last_kind=-1,last_group=-1;
    static bool contact_logged=false;
#if DZ_TRACE_SHIELD
    static bool shield_logged=false;
#if DZ_TRACE_SPLASH
    static bool splash_refusal_logged=false;
#endif
#endif
    const int kind=static_cast<int>(goal.kind);
    const int index=goal.kind==GoalKind::Farm?goal.index:-1;
    const bool changed=kind!=last_kind || index!=last_group;
    if(!changed&&index<0)return;
    const bool late_shield=!changed&&contact_logged;
    if(late_shield) {
#if DZ_TRACE_SHIELD
        const auto type=cambc::self().champion_name();
        if(shield_logged||(type!=cambc::champion_type::varg&&!(DZ_TRACE_HEART&&type==cambc::champion_type::heart_of_ruin)))return;
        if(mem.member_hp[index].size()>64)return;
        unsigned live=0;for(float hp:mem.member_hp[index])live+=hp>0;
        if(live!=1&&!DZ_TRACE_SPLASH)return;
#else
        return;
#endif
    }
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
#if DZ_TRACE_SHIELD
    AuditShield shield;
    if(contact)shield=audit_single_shield(world,mem,obs,index,timing,tc);
    if(late_shield&&shield.result.status==ShieldClearStatus::NotQuoted) {
#if DZ_TRACE_SPLASH
        if(!contact||splash_refusal_logged)return;
#else
        return;
#endif
    }
#endif
    const auto body=static_cast<std::uint32_t>(static_cast<cambc::handle_champion_t>(cambc::self()));
    // Retry a dropped record next turn. Never pretend a missing prediction
    // was issued at an earlier position or before an earlier attack.
#define DZ_MODEL_LINE "DZ_MODEL v=2 r=%u b=%u s=%u k=%d g=%d n=%d c=%d x=%d y=%d st=%d sn=%d d=%d f=%d a=%u l=%.2f h=%.2f ch=%.2f rw=%.2f q=%.2f rg=%d cl=%d m=%zu na=%u ne=%zu ok=%d rc=%u rm=%u t=%u ts=%d tl=%.2f"
    // One compact record stays within trace.h's512-byte reservation and avoids
    // a second trace call being suppressed by the per-turn formatting cap.
    const auto emit=[&](const char* format,auto... extra) {
        return trace(format,tc.round,body,world.slot,kind,index,changed,contact,obs.p.x,obs.p.y,state,seen,distance,field,
                     risk.attacks,risk.damage,obs.hp,remembered,obs.strength*obs.camp_damage,
                     index>=0?mem.quantize_out:0.f,obs.range,cluster,members,nearby,obs.enemies.size(),
                     index>=0?static_cast<int>(risk.status):-1,timing.remaining,timing.period,clock.rounds,
                     static_cast<int>(clock.status),timed_loss,extra...);
    };
#if DZ_TRACE_SHIELD
    bool logged=false;
    if(shield.result.status!=ShieldClearStatus::NotQuoted)
        logged=emit(DZ_MODEL_LINE " ss=%d pm=%d ph=%u hb=%.2f ps=%d pt=%u pl=%.2f pc=%u pn=%d pi=%d cd=%u cp=%u ca=%.2f ct=%u ex=%d ev=%.2f et=%u inc=%.2f cast=%d fuel=%llu\n",
                    late_shield,shield.mode,shield.hp_hash,shield.input.missing_health_bonus,static_cast<int>(shield.result.status),shield.result.rounds,shield.result.loss,
                    shield.result.shields,shield.live,shield.member,shield.input.shield_cd,shield.input.shield_period,
                    shield.input.shield_amount,shield.input.shield_duration,shield.input.existing,
                    shield.input.existing_value,shield.input.existing_duration,shield.input.incoming,
                    shield.input.can_cast,static_cast<unsigned long long>(shield.fuel));
    else {
#if DZ_TRACE_SPLASH
        logged=emit(DZ_MODEL_LINE " ss=%d sk=%d af=%llu\n",late_shield,shield.skip,static_cast<unsigned long long>(shield.available));
#else
        logged=emit(DZ_MODEL_LINE " ss=%d\n",late_shield);
#endif
    }
#else
    const bool logged=emit(DZ_MODEL_LINE "\n");
#endif
#undef DZ_MODEL_LINE
    if(logged) {
#if DZ_TRACE_SHIELD
        if(changed)shield_logged=false;
#if DZ_TRACE_SPLASH
        if(changed)splash_refusal_logged=false;
        if(late_shield&&shield.result.status==ShieldClearStatus::NotQuoted)splash_refusal_logged=true;
#endif
        shield_logged|=shield.result.status!=ShieldClearStatus::NotQuoted;
#endif
        if (changed) contact_logged=false;
        contact_logged|=contact;last_kind=kind;last_group=index;
    }
}
}
#endif
