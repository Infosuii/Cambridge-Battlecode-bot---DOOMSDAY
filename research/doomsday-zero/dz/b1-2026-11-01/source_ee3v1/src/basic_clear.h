#pragma once
#include <cmath>
#include <cstdint>
#include <span>

namespace dz {
// A restricted work primitive, not the calibrated objective/crew model. Inputs
// are engine float values after modifiers. No spells, splash, resets or healing.
enum class WorkStatus { Complete, BeyondHorizon, Invalid };
struct BasicTarget { float hp=0, damage_per_attack=0; };
struct AttackWork {
    WorkStatus status=WorkStatus::Invalid;
    std::uint32_t attacks=0;
    bool complete() const { return status==WorkStatus::Complete; }
};
inline AttackWork basic_attack_work(std::span<const BasicTarget> targets,std::uint32_t horizon=2000) {
    if (horizon>2000 || targets.size()>2000) return {};
    // Validate the entire input before reporting a horizon-limited result.
    for (auto t:targets) if (!std::isfinite(t.hp)||!std::isfinite(t.damage_per_attack)||
        t.hp<0||t.damage_per_attack<0||(t.hp>0&&t.damage_per_attack==0)) return {};
    std::uint32_t attacks=0;
    for (auto t:targets) {
        if (t.hp==0) continue;
        const auto remaining=horizon-attacks;
        // Widen float inputs before arithmetic. The small bounded integer times
        // a float is exact in double; reject huge quotients before conversion.
        if (static_cast<double>(t.hp)>static_cast<double>(t.damage_per_attack)*remaining)
            return {WorkStatus::BeyondHorizon,attacks};
        attacks+=static_cast<std::uint32_t>(std::ceil(static_cast<double>(t.hp)/t.damage_per_attack));
    }
    return {WorkStatus::Complete,attacks};
}
struct StationaryDuel {
    AttackWork work;
    double future_damage_for_clear=0;
    bool survives=false;
};
// Sample immediately before the first attack, after this turn's camp phase.
// One camp, one stationary attacker, constant effective damage and incoming
// damage, no other actor. A kill now prevents the next camp phase. Zero HP dies.
inline StationaryDuel stationary_duel(float own_hp,BasicTarget target,float incoming,std::uint32_t horizon=2000) {
    if (!std::isfinite(own_hp)||own_hp<=0||!std::isfinite(incoming)||incoming<0) return {};
    const BasicTarget targets[]{target};
    auto work=basic_attack_work(targets,horizon);
    if (!work.complete()) return {work,0,false};
    double damage=static_cast<double>(incoming)*(work.attacks?work.attacks-1:0);
    return {work,damage,own_hp>damage};
}
}
