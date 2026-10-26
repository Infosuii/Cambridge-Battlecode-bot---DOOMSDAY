// Agent A SDK metadata probe (scratch only; never part of the bot). Prints "SDKFACT <json>" records read from the
// engine through the SDK. printf costs ~65 fuel per character in this Wasm build (measured: the first draft turn's
// 937,830 fuel ran out after ~14 KB), so records are emitted a few per turn: a_sdk_dump_step() is called on every draft
// and gameplay turn of the probe and resumes where it stopped. Duplicates across guests are removed offline.
#include <cstdio>
#include <cstdint>

#include "cambc.h"

namespace bc = cambc;
namespace d = cambc::detail;

static void put_props(const d::ability_props& a) {
    std::printf("{\"kind\":%u,\"cooldown\":%d,\"max_charges\":%u,\"targets\":%u,\"attributes\":%u", a.kind, a.cooldown, a.max_charges,
        a.targets, a.attributes);
    switch (a.kind) {
    case 1: std::printf(",\"enhanced_attack\":%u", a.payload.enhanced_attack); break;
    case 2: std::printf(",\"range\":%g,\"modifier\":%g", a.payload.damage.range, a.payload.damage.modifier); break;
    case 3:
        std::printf(",\"range\":%g,\"radius\":%g,\"modifier\":%g,\"duration\":%d", a.payload.aoe_damage.range, a.payload.aoe_damage.radius,
            a.payload.aoe_damage.modifier, a.payload.aoe_damage.duration);
        break;
    case 4: std::printf(",\"range\":%g,\"modifier\":%g,\"duration\":%d", a.payload.cc.range, a.payload.cc.modifier, a.payload.cc.duration); break;
    case 5: std::printf(",\"range\":%g,\"modifier\":%g", a.payload.heal.range, a.payload.heal.modifier); break;
    case 6:
        std::printf(",\"range\":%g,\"radius\":%g,\"modifier\":%g,\"duration\":%d", a.payload.dash.range, a.payload.dash.radius,
            a.payload.dash.modifier, a.payload.dash.duration);
        break;
    case 7:
        std::printf(",\"range\":%g,\"modifier\":%g,\"duration\":%d", a.payload.shield.range, a.payload.shield.modifier, a.payload.shield.duration);
        break;
    default: break;
    }
    std::printf("}");
}

static void rec_settings() {
    const auto& s = d::cached_game_settings;
    std::printf("SDKFACT {\"rec\":\"settings\",\"capture_time\":%d,\"camp_sleep_time\":%d,\"respawn_time\":%d,\"recall_time\":%d,"
                "\"submit_gem_duration_multiplier\":%g,\"submit_gem_base_duration\":%d,\"submit_gem_minimum_duration\":%d,"
                "\"submit_gems_range\":%d,\"max_rounds\":%u,\"winning_gems\":%u,\"kill_gold\":%u,\"assist_gold\":%u,\"passive_gold\":%u,"
                "\"spawn_healing\":%g,\"active_wards\":%u,\"ward_charges\":%u,\"shared_memory_bytes\":%u,\"draft_memory_bytes\":%u,"
                "\"tile_reveal_rounds\":%u,\"ward_cooldown\":%d,\"ward_lifetime\":%d,\"ward_vision_radius\":%g,\"ward_placement_radius\":%g,"
                "\"control_ward_vision_radius\":%g,\"control_ward_placement_radius\":%g,\"altar_lock_hits\":%u,\"tp_scroll_time\":%d,"
                "\"tp_crystal_time\":%d}\n",
        s.capture_time, s.camp_sleep_time, s.respawn_time, s.recall_time, s.submit_gem_duration_multiplier, s.submit_gem_base_duration,
        s.submit_gem_minimum_duration, s.submit_gems_range, s.max_rounds, s.winning_gems, s.kill_gold, s.assist_gold, s.passive_gold,
        static_cast<double>(s.spawn_healing), s.active_wards, s.ward_charges, s.shared_memory_bytes, s.draft_memory_bytes, s.tile_reveal_rounds,
        s.ward_cooldown, s.ward_lifetime, static_cast<double>(s.ward_vision_radius), static_cast<double>(s.ward_placement_radius),
        static_cast<double>(s.control_ward_vision_radius), static_cast<double>(s.control_ward_placement_radius), s.altar_lock_hits,
        s.tp_scroll_time, s.tp_crystal_time);
}

static void rec_memory() {
    unsigned team_size = 0;
    try {
        team_size = bc::draft::team_size();
    } catch (...) {
    }
    std::printf("SDKFACT {\"rec\":\"memory\",\"shared_memory_capacity\":%u,\"draft_memory_snapshot_size\":%zu,\"draft_team_size\":%u,"
                "\"is_draft\":%d,\"round\":%u,\"map_w\":%d,\"map_h\":%d,\"symmetry\":%d,\"fuel_remaining\":%llu}\n",
        d::shared_memory_capacity, bc::draft_memory.size(), team_size, bc::is_draft() ? 1 : 0, bc::round_number(), bc::map::width(),
        bc::map::height(), static_cast<int>(bc::map::symmetry()), static_cast<unsigned long long>(bc::fuel_remaining()));
}

static void rec_champion(int t) {
    d::champion_design cd{};
    if (d::sdk_champion_design(t, &cd) != 0) return;
    const auto& b = cd.base_stats;
    std::printf("SDKFACT {\"rec\":\"champion\",\"type\":%d,\"name\":\"%s\",\"passive\":%u,\"vision_type\":%u,\"attack_type\":%u,"
                "\"vision_radius\":%d,\"base_move_speed\":%d,\"base_attack_range\":%d,\"base_health\":%g,\"health_growth\":%g,"
                "\"base_strength\":%g,\"strength_growth\":%g,\"base_focus\":%g,\"focus_growth\":%g,\"camp_damage_multiplier\":%g,\"abilities\":[",
        t, bc::to_string(static_cast<bc::champion_type>(t)).c_str(), cd.definition.passive_type, cd.definition.vision_type,
        cd.definition.attack_type, b.vision_radius, b.base_move_speed, b.base_attack_range, static_cast<double>(b.base_health),
        static_cast<double>(b.health_growth), static_cast<double>(b.base_strength), static_cast<double>(b.strength_growth),
        static_cast<double>(b.base_focus), static_cast<double>(b.focus_growth), static_cast<double>(b.camp_damage_multiplier));
    put_props(cd.definition.abilities[0]);
    std::printf(",");
    put_props(cd.definition.abilities[1]);
    std::printf("]}\n");
}

static void rec_camp(int t) {
    d::camp_design cd{};
    if (d::sdk_camp_design(t, &cd) != 0) return;
    const auto& b = cd.base_stats;
    std::printf("SDKFACT {\"rec\":\"camp\",\"type\":%d,\"name\":\"%s\",\"vision_radius\":%g,\"base_move_speed\":%d,\"base_attack_range\":%d,"
                "\"base_health\":%g,\"health_growth\":%g,\"base_strength\":%g,\"strength_growth\":%g,\"base_focus\":%g,\"focus_growth\":%g,"
                "\"attack_type\":%u,\"abilities\":[",
        t, bc::to_string(static_cast<bc::camp_type>(t)).c_str(), static_cast<double>(b.vision_radius), b.base_move_speed, b.base_attack_range,
        static_cast<double>(b.base_health), static_cast<double>(b.health_growth), static_cast<double>(b.base_strength),
        static_cast<double>(b.strength_growth), static_cast<double>(b.base_focus), static_cast<double>(b.focus_growth),
        cd.definition.attack_type);
    put_props(cd.definition.abilities[0]);
    std::printf(",");
    put_props(cd.definition.abilities[1]);
    std::printf("]}\n");
}

static void rec_item(std::uint32_t i) {
    d::item_info it{};
    if (d::sdk_item_info(i, &it) != 0) return;
    std::printf("SDKFACT {\"rec\":\"item\",\"id\":%u,\"name\":\"%s\",\"cost\":%u,\"purchasable\":%u,\"health\":%d,\"strength\":%d,\"focus\":%d,"
                "\"passive\":%u,\"passive_magnitude\":%g,\"combine_count\":%u,\"result\":%u,\"combine_cost\":%u}\n",
        i, bc::to_string(bc::item_type{i}).c_str(), it.cost, it.purchasable, it.health_points, it.strength_points, it.focus_points, it.passive,
        static_cast<double>(it.passive_magnitude), it.combine_count, it.result, it.combine_cost);
}

static void rec_consumable(std::uint32_t raw) {
    d::consumable_info ci{};
    const int code = d::sdk_consumable_info(raw, &ci);
    std::printf("SDKFACT {\"rec\":\"consumable_raw\",\"raw_id\":%u,\"status\":%d,\"cost\":%u,\"carry_limit\":%u}\n", raw, code, ci.cost,
        ci.carry_limit);
}

static void rec_group(std::size_t k) {
    static std::vector<bc::map::camp_group> groups;
    static bool loaded = false;
    if (!loaded) loaded = true, groups = bc::map::camp_groups();
    if (k >= groups.size()) return;
    const auto& g = groups[k];
    std::printf("SDKFACT {\"rec\":\"camp_group\",\"handle\":%u,\"gold\":%u,\"gems\":%u,\"max_respawn\":%d,\"camps\":[",
        static_cast<unsigned>(static_cast<bc::handle_camp_group_t>(g)), g.gold_value(), g.gem_value(), g.max_respawn_timer());
    bool first = true;
    for (const auto& c : g) {
        std::printf("%s[%d,%d,%d]", first ? "" : ",", static_cast<int>(c.kind()), c.spawn_position().x, c.spawn_position().y);
        first = false;
    }
    std::printf("]}\n");
}

static void rec_turn() {
    auto& me = bc::self();
    d::champion_info info{};
    d::sdk_champion(static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(me)), &info);
    d::ward_resources wr{};
    d::sdk_champion_wards(static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(me)), &wr);
    std::printf("SDKFACT {\"rec\":\"turn\",\"round\":%u,\"type\":%d,\"move_speed\":%d,\"attack_range\":%d,\"state\":%d,\"gold\":%u,"
                "\"ward_charges\":%u,\"ward_cooldown\":%d,\"shared_memory_size\":%zu,\"allies\":%zu,\"enemies\":%zu,\"fuel_remaining\":%llu,"
                "\"draft_memory_size\":%zu}\n",
        bc::round_number(), info.type, info.move_speed, info.attack_range, info.state, me.gold_count(), wr.charges, wr.cooldown,
        bc::shared_memory_buffer::size(), bc::champions(bc::team::ally).size(), bc::champions(bc::team::enemy).size(),
        static_cast<unsigned long long>(bc::fuel_remaining()), bc::draft_memory.size());
}

// Record index space: 0 settings, 1 memory, 2..14 champions, 15..20 camps, 21..62 items, 63..66 consumables, 67.. groups.
static int g_next = 0;
void a_sdk_dump_step(int per_call) {
    for (int n = 0; n < per_call; ++n, ++g_next) {
        const int k = g_next;
        if (k == 0) rec_settings();
        else if (k == 1) rec_memory();
        else if (k < 15) rec_champion(k - 2);
        else if (k < 21) rec_camp(k - 15);
        else if (k < 63) rec_item(static_cast<std::uint32_t>(k - 21));
        else if (k < 67) rec_consumable(static_cast<std::uint32_t>(k - 63));
        else if (k < 67 + 256) rec_group(static_cast<std::size_t>(k - 67));
        else return;
    }
    std::fflush(stdout);
}

// Gameplay-perspective facts on the first turns of each champion guest.
void a_sdk_dump_turn() {
    static int turns = 0;
    if (turns++ < 3) rec_turn();
    a_sdk_dump_step(2);
}
