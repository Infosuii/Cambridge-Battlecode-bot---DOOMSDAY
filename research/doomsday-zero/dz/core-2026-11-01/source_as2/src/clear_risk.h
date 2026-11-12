#pragma once
#include "config.h"
#include "basic_clear.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <span>

namespace dz {
// Conservative solo-clear risk for objective selection. Extends the validated
// single-camp stationary duel to a group: every live member is assumed to hit
// the attacker every camp phase until it dies (members of a group are adjacent
// and their ranges are 3-5). No spells, resets, splash, healing or allies.
// This is a selection gate, not the calibrated ObjModel; V-M1 stays open.
struct ClearMember { float hp=0, incoming=0; };
struct ClearRisk {
    WorkStatus status=WorkStatus::Invalid;
    std::uint32_t attacks=0;
    double damage=0; // Future HP loss for a fresh engagement.
    bool complete() const { return status==WorkStatus::Complete; }
};
inline constexpr std::size_t clear_risk_members=64;
// Reference implementation: one job per member. Kept for host equivalence tests.
inline ClearRisk solo_clear_risk_reference(std::span<const ClearMember> members,float damage_per_attack,std::uint32_t horizon=2000) {
    if (members.size()>clear_risk_members||horizon>2000) return {};
    struct Job { std::uint32_t attacks; float incoming; };
    std::array<Job,clear_risk_members> jobs{};
    std::size_t count=0;
    std::uint32_t total=0;
    for (auto m:members) {
        if (!std::isfinite(m.incoming)||m.incoming<0) return {};
        const BasicTarget one[]{{m.hp,damage_per_attack}};
        auto work=basic_attack_work(one,horizon-total);
        if (!work.complete()) return {work.status,total+work.attacks,0};
        if (!work.attacks) continue;
        total+=work.attacks;
        jobs[count++]={work.attacks,m.incoming};
    }
    std::sort(jobs.begin(),jobs.begin()+count,[](const Job& a,const Job& b) {
        return static_cast<double>(a.incoming)*b.attacks>static_cast<double>(b.incoming)*a.attacks;
    });
    double damage=0;
    std::uint32_t elapsed=0;
    for (std::size_t i=0;i<count;++i) {
        elapsed+=jobs[i].attacks;
        damage+=static_cast<double>(jobs[i].incoming)*(elapsed-1);
    }
    return {WorkStatus::Complete,total,damage};
}
// Production version: identical members (a full wolf pack) are merged and
// priced in closed form, k identical jobs of a attacks after E elapsed attacks
// expose k(E-1) + a*k(k+1)/2 phases. Same result as the reference; repricing a
// 64-member pack one member at a time cost several thousand fuel.
inline ClearRisk solo_clear_risk(std::span<const ClearMember> members,float damage_per_attack,std::uint32_t horizon=2000) {
    if (members.size()>clear_risk_members||horizon>2000) return {};
    if (!std::isfinite(damage_per_attack)||damage_per_attack<0) return {};
    struct Job { std::uint32_t attacks; float incoming; std::uint32_t count; };
    std::array<Job,clear_risk_members> jobs;
    std::size_t distinct=0;
    std::uint32_t total=0;
    for (auto m:members) {
        if (!std::isfinite(m.incoming)||m.incoming<0||!std::isfinite(m.hp)||m.hp<0) return {};
        if (m.hp==0) continue;
        if (damage_per_attack==0) return {};
        // Widen before dividing, as basic_attack_work does; bound the quotient.
        const auto remaining=horizon-total;
        if (static_cast<double>(m.hp)>static_cast<double>(damage_per_attack)*remaining) return {WorkStatus::BeyondHorizon,total,0};
        const auto attacks=static_cast<std::uint32_t>(std::ceil(static_cast<double>(m.hp)/damage_per_attack));
        total+=attacks;
        std::size_t k=0;
        while (k<distinct&&!(jobs[k].attacks==attacks&&jobs[k].incoming==m.incoming)) ++k;
        if (k==distinct) jobs[distinct++]={attacks,m.incoming,1};
        else ++jobs[k].count;
    }
    std::sort(jobs.begin(),jobs.begin()+distinct,[](const Job& a,const Job& b) {
        return static_cast<double>(a.incoming)*b.attacks>static_cast<double>(b.incoming)*a.attacks;
    });
    double damage=0, elapsed=0;
    for (std::size_t i=0;i<distinct;++i) {
        const double k=jobs[i].count, a=jobs[i].attacks;
        damage+=static_cast<double>(jobs[i].incoming)*(k*(elapsed-1)+a*k*(k+1)/2);
        elapsed+=a*k;
    }
    return {WorkStatus::Complete,total,damage};
}
// Camps hit their nearest champion, so a crew spreads the group's damage. Price
// one member's share as if it absorbed two members' worth (capped at all of it).
inline double crew_share(unsigned crew) { return crew<=2 ? 1. : 2./crew; }
// Accept only with a margin over the predicted loss and a small HP floor.
inline bool clear_survivable(const ClearRisk& risk,float hp,float max_hp,double share=1) {
#if DZ_CLEAR_BOLD
    // Bolder clears (F1: camp clears and monster damage taken by R100 are the strongest early predictors; v76 takes
    // 2.2x DZ's monster damage by R100 and heals 4x): margin 1.1x expected damage + 5% max HP instead of 1.25x + 10%.
    return risk.complete()&&std::isfinite(hp)&&hp>0&&hp>1.1*risk.damage*share+.05*max_hp;
#else
    return risk.complete()&&std::isfinite(hp)&&hp>0&&hp>1.25*risk.damage*share+.1*max_hp;
#endif
}
}
