#include <cambc.h>
#include <bit>
#include <cstdio>
#include <string>
#include <type_traits>

// Canonical, named scalar fields. Never hash struct padding or inactive payloads.
template<class T> void emit(const std::string& key,T value) {
    if constexpr (std::is_same_v<T,float>)
        std::printf("CT27_FIELD %s f32 %08x\n",key.c_str(),std::bit_cast<unsigned>(value));
    else if constexpr (std::is_same_v<T,double>)
        std::printf("CT27_FIELD %s f64 %016llx\n",key.c_str(),static_cast<unsigned long long>(std::bit_cast<std::uint64_t>(value)));
    else std::printf("CT27_FIELD %s u32 %08x\n",key.c_str(),static_cast<unsigned>(value));
}
#define FIELD(object,name) emit(prefix+"." #name,object.name)
template<class T> void stats(const std::string& prefix,const T& s) {
    FIELD(s,vision_radius); FIELD(s,base_move_speed); FIELD(s,base_attack_range);
    FIELD(s,base_health); FIELD(s,health_growth); FIELD(s,base_strength); FIELD(s,strength_growth);
    FIELD(s,base_focus); FIELD(s,focus_growth);
    if constexpr (requires{s.camp_damage_multiplier;}) FIELD(s,camp_damage_multiplier);
}
void ability(const std::string& prefix,const cambc::detail::ability_props& a) {
    FIELD(a,kind); FIELD(a,cooldown); FIELD(a,max_charges); FIELD(a,targets); FIELD(a,attributes);
    using K=cambc::ability_kind;
    switch (static_cast<K>(a.kind)) {
    case K::attack_reset: FIELD(a,payload.enhanced_attack); break;
    case K::damage: FIELD(a,payload.damage.range); FIELD(a,payload.damage.modifier); break;
    case K::aoe_damage:
        FIELD(a,payload.aoe_damage.range); FIELD(a,payload.aoe_damage.modifier);
        FIELD(a,payload.aoe_damage.radius); FIELD(a,payload.aoe_damage.duration); break;
    case K::cc:
        FIELD(a,payload.cc.range); FIELD(a,payload.cc.modifier); FIELD(a,payload.cc.duration); break;
    case K::heal: FIELD(a,payload.heal.range); FIELD(a,payload.heal.modifier); break;
    case K::dash:
        FIELD(a,payload.dash.range); FIELD(a,payload.dash.radius); FIELD(a,payload.dash.modifier); FIELD(a,payload.dash.duration); break;
    case K::shield:
        FIELD(a,payload.shield.range); FIELD(a,payload.shield.modifier); FIELD(a,payload.shield.duration); break;
    default: if (a.kind!=0) throw std::runtime_error("unrecognized ability kind");
    }
}
void definition(const std::string& prefix,const cambc::detail::unit_definition& d) {
    FIELD(d,type); FIELD(d,vision_type); FIELD(d,passive_type); FIELD(d,attack_type);
    for (unsigned i=0;i<2;++i) ability(prefix+".ability"+std::to_string(i),d.abilities[i]);
}
void fingerprint() {
    using namespace cambc;
    std::string prefix="settings";
    const auto& s=detail::cached_game_settings;
    FIELD(s,capture_time); FIELD(s,camp_sleep_time); FIELD(s,respawn_time); FIELD(s,recall_time);
    FIELD(s,submit_gem_duration_multiplier); FIELD(s,submit_gem_base_duration); FIELD(s,submit_gem_minimum_duration);
    FIELD(s,submit_gems_range); FIELD(s,max_rounds); FIELD(s,winning_gems); FIELD(s,kill_gold); FIELD(s,assist_gold);
    FIELD(s,passive_gold); FIELD(s,spawn_healing); FIELD(s,active_wards); FIELD(s,ward_charges);
    FIELD(s,shared_memory_bytes); FIELD(s,draft_memory_bytes); FIELD(s,tile_reveal_rounds); FIELD(s,ward_cooldown);
    FIELD(s,ward_lifetime); FIELD(s,ward_vision_radius); FIELD(s,ward_placement_radius);
    FIELD(s,control_ward_vision_radius); FIELD(s,control_ward_placement_radius); FIELD(s,altar_lock_hits);
    FIELD(s,tp_scroll_time); FIELD(s,tp_crystal_time);
    for (unsigned i=0;i<champion_designs.size();++i) {
        detail::champion_design design{}; detail::check(detail::sdk_champion_design(i,&design));
        prefix="champion"+std::to_string(i);
        definition(prefix,design.definition); stats(prefix,design.base_stats);
    }
    for (unsigned i=0;i<6;++i) {
        detail::camp_design design{}; detail::check(detail::sdk_camp_design(i,&design));
        prefix="camp"+std::to_string(i);
        definition(prefix,design.definition); stats(prefix,design.base_stats);
    }
    for (unsigned i=0;i<static_cast<unsigned>(item_type::count);++i) {
        prefix="item"+std::to_string(i); auto item=static_cast<item_type>(i).info();
        FIELD(item,cost); FIELD(item,combine_count); FIELD(item,health_points); FIELD(item,strength_points); FIELD(item,focus_points);
        emit(prefix+".result",item.result ? static_cast<unsigned>(*item.result) : 0xffffffffu);
        emit(prefix+".passive",item.passive ? static_cast<unsigned>(*item.passive) : 0xffffffffu);
        FIELD(item,passive_magnitude); FIELD(item,purchasable);
    }
    for (auto id:detail::raw_consumable_ids) {
        detail::consumable_info info{}; detail::check(detail::sdk_consumable_info(id,&info));
        prefix="consumable"+std::to_string(id); FIELD(info,cost); FIELD(info,carry_limit);
    }
    prefix="sdk_passive";
    using namespace constants::passive_abilities;
    emit(prefix+".prism_focus_per_gem",prism_focus_per_gem);
    emit(prefix+".varg_splash_radius",varg_splash_radius);
    emit(prefix+".vesper_vale_bonus_gold_percent",vesper_vale_bonus_gold_percent);
    emit(prefix+".marcella_tribute_gold_per_gem",marcella_tribute_gold_per_gem);
    emit(prefix+".ryth_health_strength_ratio",ryth_health_strength_ratio);
    emit(prefix+".ren_retaliation_focus_ratio",ren_retaliation_focus_ratio);
    emit(prefix+".heart_of_ruin_missing_health_damage_max_bonus",heart_of_ruin_missing_health_damage_max_bonus);
    std::printf("CT27_COMPLETE schema=1\n");
}
int main() {
    using namespace cambc;
    if (is_draft()) {
        const std::array picks{champion_draft::vesper_vale,champion_draft::heart_of_ruin,champion_draft::vendetta,
            champion_draft::marcella,champion_draft::ryth};
        bool dumped=false;
        for (;;) {
            try {
                draft::pick(picks.at(draft::current_draft(team::ally).size()));
                // The metadata dump belongs in the 10M first draft budget;
                // printing all named fields cannot fit an ordinary play turn.
                if (!dumped) { fingerprint(); dumped=true; }
            } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
            end_turn();
        }
    }
    for (;;) end_turn();
}
