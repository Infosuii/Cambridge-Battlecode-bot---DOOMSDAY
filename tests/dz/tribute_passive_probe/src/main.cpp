#include <cambc.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include "config.h"
using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
bool walk(vec2 target,unsigned round) {
    if (!self().can_move()||self().position()==target) return false;
    if (self().position().chebyshev_distance(target)<=1&&(vision::has_champion(target)||vision::has_camp(target))) return false;
    return round_number()==round&&self().move_towards(target);
}
bool farm(const map::camp_group& g,std::vector<bool>& dead,unsigned round) {
    if (dead.size()!=g.camps().size()) dead.assign(g.camps().size(),false);
    bool visible=false;
    for (unsigned i=0;i<dead.size();++i) if (vision::in_vision(g.camps()[i].spawn_position())) { visible=true; dead[i]=g.camps()[i].is_dead(); }
    if (visible&&std::holds_alternative<map::camp_group_respawning>(g.state())) return true;
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
        auto next=g.camps()[0].spawn_position();nearest=65535;
        for (unsigned i=0;i<dead.size();++i) {
            if (!all_dead&&dead[i]) continue;
            auto q=g.camps()[i].spawn_position(); int d=static_cast<int>(self().position().chebyshev_distance(q));
            if (d<nearest&&!vision::has_champion(q)) { nearest=d; next=q; }
        }
        walk(next,round);
    }
    return false;
}
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vendetta,champion_draft::marcella,champion_draft::ryth,
            champion_draft::vesper_vale,champion_draft::heart_of_ruin};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    const bool actor=self().champion_name()==champion_type::vendetta;
    auto corner=map::spawn_region(team::ally).positions().front();int sign=corner.x<map::width()/2?1:-1;
    auto park=vec2{std::clamp(corner.x+sign*(10+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),corner.y};
    auto groups=map::camp_groups();std::array<int,4> selected;selected.fill(-1);std::array<int,4> distances;distances.fill(65535);
    if (actor) for (unsigned i=0;i<groups.size();++i) {
        auto& g=groups[i];bool gold=true,gem=true;
        for (auto& c:g.camps()) { gold&=c.is_gold_cluster();gem&=c.is_gem_cluster(); }
        int role=gold&&g.gold_value()>=150?0:gem&&g.camps().size()==1?1:gem&&g.camps().size()==2?2:gem&&g.camps().size()==(DZ_MID_BAG?5:14)?3:-1;
        int d=static_cast<int>(corner.chebyshev_distance(g.camps()[0].spawn_position()));
        if (role>=0&&d<distances[role]) { selected[role]=i;distances[role]=d; }
    }
    bool ready=selected[0]>=0&&selected[DZ_LARGE_BAG?3:2]>=0&&(!(DZ_SMALL_BAG||DZ_BIG_BAG)||selected[1]>=0)&&!map::altars().is_empty()&&
        !(DZ_BIG_BAG&&DZ_SMALL_BAG)&&!(DZ_LARGE_BAG&&(DZ_BIG_BAG||DZ_SMALL_BAG))&&!(DZ_MID_BAG&&!DZ_LARGE_BAG);
    if (actor) check("tribute_passive_setup",ready);
    auto altars=map::altars().positions();vec2 altar=altars.empty()?vec2{}:altars.front();std::vector<bool> dead;
    unsigned phase=0,bag=0,started=0,bank_before=0,gold_before=0;
    int base_timer=0,live_timer=0;float magnitude=0;
    for (;;) {
        auto round=round_number();
        try {
            if (!actor) { if (self().is_alive()&&!vision::has_champion(park)&&!vision::has_camp(park)) walk(park,round); }
            else if (ready&&phase<7) {
                if (!self().is_alive()) { std::printf("ERROR Tribute actor died\n");phase=7; }
                else if (phase==0) {
                    if (farm(groups[selected[0]],dead,round)) { check("tribute_financed",self().gold_count()==groups[selected[0]].gold_value());phase=1; }
                } else if (phase==1) {
                    if (!(DZ_SMALL_BAG||DZ_BIG_BAG)||farm(groups[selected[1]],dead,round)) phase=2;
                } else if (phase==2) {
                    if (DZ_SMALL_BAG||farm(groups[selected[DZ_LARGE_BAG?3:2]],dead,round)) phase=3;
                } else if (phase==3) {
                    if (self().position().chebyshev_distance(altar)>constants::submit_gems_range) walk(altar,round);
                    else if (round_number()==round) {
                        bag=self().gem_count();
                        auto wanted=DZ_LARGE_BAG?groups[selected[3]].gem_value():
                            (DZ_SMALL_BAG||DZ_BIG_BAG?groups[selected[1]].gem_value():0)+(DZ_SMALL_BAG?0:groups[selected[2]].gem_value());
                        check("tribute_bag_prepared",bag==wanted&&bag>0);
                        base_timer=std::max(constants::submit_gem_minimum_duration,constants::submit_gem_base_duration+
                            static_cast<int>(std::ceil(bag*constants::submit_gem_duration_multiplier)));
                        self().submit_gems(altar);int observed=self().remaining_channel_time();
                        check("tribute_baseline_timer",self().is_submitting_gems()&&observed==base_timer);
                        self().cancel_submit_gems();
                        check("tribute_cancel_retains_bag",self().gem_count()==bag&&global_submitted_gems(team::ally)==0&&!self().is_submitting_gems());
                        std::printf("CT12_BASE bag=%u timer=%d\n",bag,observed);phase=4;
                    }
                } else if (phase==4) {
                    if (!map::spawn_region(team::ally).is_set(self().position())) walk(corner,round);
                    else {
                        auto family=DZ_TRIBUTE?item_family::tribute:item_family::power;
                        auto shard=get_item_enum(family,item_stat::strength);unsigned cash=self().gold_count();
                        for (int i=0;i<5&&round_number()==round;++i) self().buy(shard);
                        auto emblem=get_item_enum(family,item_stat::strength,false);magnitude=DZ_TRIBUTE?emblem.passive_magnitude():0;
                        check("tribute_item_created",self().item_count()[emblem]==1&&cash-self().gold_count()==5*shard.cost());
                        std::printf("CT12_ITEM active=%d magnitude=%.9g\n",DZ_TRIBUTE,magnitude);phase=5;
                    }
                } else if (phase==5) {
                    if (self().position().chebyshev_distance(altar)>constants::submit_gems_range) walk(altar,round);
                    else if (round_number()==round) {
                        check("tribute_same_bag",self().gem_count()==bag);
                        bank_before=global_submitted_gems(team::ally);gold_before=self().gold_count();
                        self().submit_gems(altar);live_timer=self().remaining_channel_time();started=round;phase=6;
                    }
                } else if (phase==6&&!self().is_submitting_gems()) {
                    check("tribute_completed",self().gem_count()==0);
                    check("tribute_live_duration",round-started==static_cast<unsigned>(live_timer));
                    if constexpr (!DZ_OBSERVE_ONLY) {
                        int expected=std::max(constants::submit_gem_minimum_duration,static_cast<int>(std::ceil(base_timer*(1-static_cast<double>(magnitude)))));
                        check("tribute_passive_effect",live_timer==expected&&global_submitted_gems(team::ally)-bank_before==bag&&self().gold_count()==gold_before);
                    }
                    std::printf("CT12_RESULT bag=%u base_timer=%d initial_timer=%d elapsed=%u banked_delta=%u gold_delta=%d active=%d magnitude=%.9g\n",
                        bag,base_timer,live_timer,round-started,global_submitted_gems(team::ally)-bank_before,
                        static_cast<int>(self().gold_count())-static_cast<int>(gold_before),DZ_TRIBUTE,magnitude);
                    if constexpr (DZ_OBSERVE_ONLY) std::printf("CT12_OBSERVATION_ONLY effect_not_asserted=1\n");
                    phase=7;
                }
                if (round%100==0&&phase<7) std::printf("CT12_STATE round=%u phase=%u bag=%u gold=%u\n",round,phase,self().gem_count(),self().gold_count());
            }
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
