#pragma once

#if GX_BANK_PROOF > 0
namespace {
volatile unsigned gx_bank_arm_data = 1000u + GX_PROOF_ARM;
}

[[gnu::noinline]] bool Bot::gx_proved_bank() {
    if (w.no_bank || walked || hp < max_hp * 0.62f || !bit(w.altar_ring,pos) ||
        bit(w.hot_zone,pos) || bc::fuel_remaining() < 24000) return false;
    const int goal = static_cast<int>(bc::constants::winning_gems);
    const int limit = static_cast<int>(bc::constants::max_rounds);
    const int time = std::max(bc::constants::submit_gem_minimum_duration,
        bc::constants::submit_gem_base_duration + static_cast<int>(std::ceil(gems*bc::constants::submit_gem_duration_multiplier)));
    if (round + time >= limit) return false;

    unsigned eligible = 0;
    if (ally_score + gems >= goal) eligible |= 1u;
    if (round >= limit - 35 && ally_score <= enemy_score && ally_score + gems > enemy_score) eligible |= 2u;
    if (!(eligible & 1u) && ally_score + gems >= goal - 140 && !w.allies.empty()) {
        int possible = ally_score + gems;
        for (const auto& a : w.allies) {
            if (a.hp < a.max_hp * 0.6f || cheb(a.pos,pos) > 7 || !bit(w.altar_ring,a.pos)) continue;
            d::champion_info info{};
            int left = 999;
            unsigned bag = 0;
            if (d::sdk_champion(a.id,&info) == 0 && (info.state & 4) &&
                d::sdk_champion_channel_time(a.id,&left) == 0 && left >= 0 && left <= time + 1 &&
                d::sdk_champion_gems(a.id,&bag) == 0) possible += static_cast<int>(bag);
        }
        if (possible >= goal) eligible |= 4u;
    }
    if (!eligible) return false;

    float incoming = 0.0f;
    for (const auto& e : w.enemies) {
        if (e.tributing()) continue;
        const int approach = std::max(0,cheb(e.pos,pos)-std::max(e.range,5));
        if (approach <= time) incoming += (e.strength + e.focus * 0.5f) * (time + 1 - approach);
    }
    if (incoming >= hp * 0.3f) return false;
    for (const auto a : w.altars) {
        if (cheb(a,pos) > bc::constants::submit_gems_range) continue;
        if (bc::vision::has_altar_lock(a) && bc::vision::altar_lock_at(a).is_enemy()) continue;
        // Every build reaches the same observation code before reading the
        // policy value. The neutral build measures the cost of that code.
        if (((gx_bank_arm_data - 1000u) & eligible) == 0) return false;
        if (d::sdk_submit_gems(a.x,a.y) == 0) {
            mode = "proved-bank";
            return true;
        }
    }
    return false;
}
#endif
