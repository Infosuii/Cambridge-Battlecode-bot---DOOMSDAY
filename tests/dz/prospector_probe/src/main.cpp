#include <cambc.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include "config.h"
#include "objective_math.h"
using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
bool walk(vec2 target,unsigned round) {
    if (!self().can_move()||self().position()==target) return false;
    if (self().position().chebyshev_distance(target)<=1&&(vision::has_champion(target)||vision::has_camp(target))) return false;
    return round_number()==round&&self().move_towards(target);
}
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vendetta,champion_draft::marcella,champion_draft::vesper_vale,
            champion_draft::ryth,champion_draft::heart_of_ruin};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    const bool actor=self().champion_name()==(DZ_VESPER?champion_type::vesper_vale:champion_type::vendetta);
    const unsigned gold_bonus=DZ_VESPER?constants::passive_abilities::vesper_vale_bonus_gold_percent:0;
    auto corner=map::spawn_region(team::ally).positions().front();
    int sign=corner.x<map::width()/2?1:-1;
    auto park=vec2{std::clamp(corner.x+sign*(10+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),corner.y};
    auto groups=map::camp_groups();
    std::array<int,5> selected;selected.fill(-1);
    std::array<int,5> distance;distance.fill(65535);
    if (actor) for (unsigned i=0;i<groups.size();++i) {
        auto& g=groups[i]; bool gold=true,gem=true;
        for (auto& c:g.camps()) { gold&=c.is_gold_cluster(); gem&=c.is_gem_cluster(); }
        int role=-1;
        if (gold&&g.gold_value()>=150) role=0;
        else if (gem&&g.camps().size()==1) role=1;
        else if (gem&&g.camps().size()==2) role=2;
        else if (gold&&g.camps().size()==1) role=3;
        else if (g.camps().size()==1&&g.camps()[0].is_wolf()) role=4;
        int d=static_cast<int>(corner.chebyshev_distance(g.camps()[0].spawn_position()));
        if (role>=0&&d<distance[role]) { selected[role]=i; distance[role]=d; }
    }
    if (actor) {
        check("prospector_setup",std::all_of(selected.begin(),selected.end(),[](int i){return i>=0;}));
        std::printf("CT13_ACTOR vesper=%d bonus_gold_percent=%u\n",DZ_VESPER,gold_bonus);
        if constexpr (DZ_OBJECTIVE_MATH) std::printf("CT_MATH enabled=1\n");
    }
    const std::array labels{"baseline_gold","gem_7_floor","gem_14_floor","gold_cluster_bonus","wolf_reward_unchanged"};
    unsigned phase=0,gold_before=0,gems_before=0,entered=0;
    std::uint64_t cumulative_gold_units=0; // Exact rational award history, denominator 400.
    int model_remainder=0; unsigned predicted_receipt=0;
    bool sampled=false,shop_done=false,dead_logged=false;
    std::vector<bool> dead;
    for (;;) {
        auto round=round_number();
        try {
            if (!actor) {
                if (self().is_alive()&&!vision::has_champion(park)&&!vision::has_camp(park)) walk(park,round);
            } else if (!self().is_alive()) {
                if (!dead_logged) { std::printf("ERROR Prospector actor died\n"); dead_logged=true; }
            } else if (phase<selected.size()&&selected[phase]>=0) {
                if (phase>0&&!shop_done) {
                    if (!map::spawn_region(team::ally).is_set(self().position())) walk(corner,round);
                    else {
                        auto family=DZ_CAPTURE_ITEM?item_family::capture:(DZ_PROSPECTOR?item_family::prospector:item_family::power);
                        auto shard=get_item_enum(family,item_stat::strength);
                        for (int i=0;i<5&&round_number()==round;++i) self().buy(shard);
                        auto emblem=get_item_enum(family,item_stat::strength,false);
                        check("item_created",self().item_count()[emblem]==1&&(!DZ_PROSPECTOR||emblem.passive_magnitude()==.25f));
                        std::printf("CT13_ITEM prospector=%d\n",DZ_PROSPECTOR);
                        if constexpr (DZ_CAPTURE_TEST) std::printf("CT_CAP_ITEM active=%d timer=%d\n",DZ_CAPTURE_ITEM,
                            DZ_CAPTURE_ITEM?static_cast<int>(emblem.passive_magnitude()):constants::capture_time);
                        shop_done=true;
                    }
                } else {
                    const unsigned role=DZ_WOLF_FIRST&&phase>=3?7-phase:phase;
                    auto& g=groups[selected[role]];
                    if (!sampled) { gold_before=self().gold_count(); gems_before=self().gem_count(); dead.assign(g.camps().size(),false); sampled=true; entered=0; }
                    bool visible=false;
                    for (unsigned i=0;i<dead.size();++i) if (vision::in_vision(g.camps()[i].spawn_position())) { visible=true; dead[i]=g.camps()[i].is_dead(); }
                    if (visible&&std::holds_alternative<map::camp_group_respawning>(g.state())) {
                        auto actual_gems=self().gem_count()-gems_before,actual_gold=self().gold_count()-gold_before;
                        bool boosted=DZ_PROSPECTOR&&role>=1&&role<=3;
                        double multiplier=boosted?1.25:1.0;
                        unsigned expected_gems=static_cast<unsigned>(std::floor(g.gem_value()*multiplier));
                        auto award_units=static_cast<std::uint64_t>(g.gold_value())*(boosted?5:4)*(100+gold_bonus);
                        unsigned expected_gold=static_cast<unsigned>((cumulative_gold_units+award_units)/400-cumulative_gold_units/400);
                        cumulative_gold_units+=award_units;
                        if constexpr (DZ_OBJECTIVE_MATH) {
                            const auto kind=role==4?dz::RewardKind::Wolf:role==1||role==2?dz::RewardKind::GemCluster:dz::RewardKind::GoldCluster;
                            const bool owns_prospector=DZ_PROSPECTOR&&shop_done;
                            auto quote=dz::solo_reward(kind,g.gem_value(),g.gold_value(),owns_prospector,DZ_VESPER,model_remainder);
                            auto uncertain=dz::solo_reward(kind,g.gem_value(),g.gold_value(),owns_prospector,DZ_VESPER);
                            check((std::string("math_reward_")+labels[role]).c_str(),quote.supported()&&quote.gems==actual_gems&&quote.gold_min==actual_gold&&quote.gold_max==actual_gold);
                            check((std::string("math_unknown_")+labels[role]).c_str(),uncertain.supported()&&uncertain.gems==actual_gems&&uncertain.gold_min<=actual_gold&&actual_gold<=uncertain.gold_max&&uncertain.next_remainder==-1);
                            model_remainder=quote.next_remainder;
                        }
                        check(labels[role],actual_gems==expected_gems&&actual_gold==expected_gold);
                        std::printf("CT13_REWARD label=%s base_gems=%u actual_gems=%u expected_gems=%u base_gold=%u actual_gold=%u expected_gold=%u\n",
                            labels[role],g.gem_value(),actual_gems,expected_gems,g.gold_value(),actual_gold,expected_gold);
                        if constexpr (DZ_CAPTURE_TEST) {
                            int timer=phase>0&&DZ_CAPTURE_ITEM?static_cast<int>(get_item_enum(item_family::capture,item_stat::strength,false).passive_magnitude()):constants::capture_time;
                            check((std::string("capture_elapsed_")+labels[role]).c_str(),entered>0&&round-entered==static_cast<unsigned>(timer+1));
                            std::printf("CT_CAP_RESULT label=%s entered=%u captured=%u elapsed=%u configured=%d\n",labels[role],entered,round,round-entered,timer);
                            if constexpr (DZ_OBJECTIVE_MATH) check((std::string("math_capture_receipt_")+labels[role]).c_str(),predicted_receipt==round);
                        }
                        ++phase; sampled=false;
                    } else {
                        const camp* target=nullptr; int nearest=65535;
                        for (auto& c:g.camps()) if (c.is_visible()&&c.is_alive()) {
                            int d=static_cast<int>(self().position().chebyshev_distance(c.spawn_position()));
                            if (d<nearest) { nearest=d; target=&c; }
                        }
                        if (target) {
                            if (nearest<=self().attack_range()&&self().can_attack()&&round_number()==round) self().attack(*target);
                            else walk(target->spawn_position(),round);
                        } else {
                            bool all_dead=std::all_of(dead.begin(),dead.end(),[](bool x){return x;});
                            vec2 next=g.camps()[0].spawn_position();nearest=65535;
                            for (unsigned i=0;i<dead.size();++i) {
                                if (!all_dead&&dead[i]) continue;
                                auto q=g.camps()[i].spawn_position(); int d=static_cast<int>(self().position().chebyshev_distance(q));
                                if (d<nearest&&!vision::has_champion(q)) { nearest=d; next=q; }
                            }
                            walk(next,round);
                        }
                    }
                    if constexpr (DZ_CAPTURE_TEST) if (sampled) {
                        for (unsigned i=0;i<dead.size();++i) if (vision::in_vision(g.camps()[i].spawn_position())) dead[i]=g.camps()[i].is_dead();
                        bool all_dead=std::all_of(dead.begin(),dead.end(),[](bool x){return x;});
                        bool onsite=std::any_of(g.camps().begin(),g.camps().end(),[](auto& c){return c.spawn_position()==self().position();});
                        if (!entered&&all_dead&&onsite) {
                            entered=round;
                            std::printf("CT_CAP_ENTER label=%s round=%u all_dead=1 onsite=1\n",labels[role],round);
                        }
                        if (entered) {
                            check((std::string("capture_stayed_onsite_")+labels[role]).c_str(),all_dead&&onsite);
                            auto cap=g.capture_state();
                            std::printf("CT_CAP_STEP label=%s round=%u timer=%d state=%d\n",labels[role],round,cap.timer,static_cast<int>(cap.state));
                            if constexpr (DZ_OBJECTIVE_MATH) {
                                int configured=phase>0&&DZ_CAPTURE_ITEM?static_cast<int>(get_item_enum(item_family::capture,item_stat::strength,false).passive_magnitude()):constants::capture_time;
                                auto quote=dz::solo_capture_delay(static_cast<dz::CapturePhase>(cap.state),cap.timer,configured,true,onsite);
                                if (round==entered) predicted_receipt=round+quote.rounds;
                                check((std::string("math_capture_step_")+labels[role]).c_str(),quote.supported()&&round+quote.rounds==predicted_receipt);
                            }
                        }
                    }
                }
                if (round%100==0) std::printf("CT13_STATE round=%u phase=%u gold=%u bag=%u hp=%.0f\n",round,phase,self().gold_count(),self().gem_count(),self().health());
            }
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
