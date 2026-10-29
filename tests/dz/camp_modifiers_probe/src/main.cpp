#include <cambc.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include "basic_clear.h"
#include "config.h"
using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
bool walk(vec2 target,unsigned round) {
    if (!self().can_move()||self().position()==target) return false;
    if (self().position().chebyshev_distance(target)<=1&&(vision::has_champion(target)||vision::has_camp(target))) return false;
    return round_number()==round&&self().move_towards(target);
}
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vendetta,champion_draft::marcella,champion_draft::ryth,
            champion_draft::vesper_vale,champion_draft::heart_of_ruin};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    const bool actor=self().champion_name()==champion_type::vendetta;
    auto corner=map::spawn_region(team::ally).positions().front(); int sign=corner.x<map::width()/2?1:-1;
    auto park=vec2{std::clamp(corner.x+sign*(10+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),corner.y};
    std::optional<map::camp_group> gold; std::optional<camp> wolf;
    int gd=65535,wd=65535;
    if (actor) for (auto& g:map::camp_groups()) {
        bool all_gold=std::all_of(g.camps().begin(),g.camps().end(),[](auto& c){return c.is_gold_cluster();});
        int d=static_cast<int>(corner.chebyshev_distance(g.camps()[0].spawn_position()));
        if (all_gold&&g.gold_value()>=450&&d<gd) { gd=d; gold=g; }
        if (g.camps().size()==1&&g.camps()[0].is_wolf()&&d<wd) { wd=d; wolf=g.camps()[0]; }
    }
    if (actor) check("modifier_setup",gold&&wolf);
    std::vector<bool> dead(gold?gold->camps().size():0,false);
    unsigned phase=0,first=0,attacks=0;
    float start_hp=0,previous_hp=0,strength=0,hit=0,incoming=0;
    bool hit_ok=true,phase_ok=true,isolated=true,fixed_stats=true;
    dz::StationaryDuel prediction;
    for (;;) {
        auto round=round_number();
        try {
            if (!actor) {
                if (self().is_alive()&&!vision::has_champion(park)&&!vision::has_camp(park)) walk(park,round);
            } else if (gold&&wolf&&phase<5) {
                if (!self().is_alive()) { std::printf("ERROR modifier actor died\n"); phase=5; }
                else if (phase==0) {
                    bool visible=false;
                    for (unsigned i=0;i<dead.size();++i) if (vision::in_vision(gold->camps()[i].spawn_position())) { visible=true; dead[i]=gold->camps()[i].is_dead(); }
                    if (visible&&std::holds_alternative<map::camp_group_respawning>(gold->state())) {
                        check("modifier_gold_captured",self().gold_count()==gold->gold_value()); phase=1;
                    } else {
                        const camp* target=nullptr; int nearest=65535;
                        for (auto& c:gold->camps()) if (c.is_visible()&&c.is_alive()) {
                            int d=static_cast<int>(self().position().chebyshev_distance(c.spawn_position()));
                            if (d<nearest) { nearest=d; target=&c; }
                        }
                        if (target) {
                            if (nearest<=self().attack_range()&&self().can_attack()&&round_number()==round) self().attack(*target);
                            else walk(target->spawn_position(),round);
                        } else {
                            bool all_dead=std::all_of(dead.begin(),dead.end(),[](bool x){return x;});
                            auto next=gold->camps()[0].spawn_position();nearest=65535;
                            for (unsigned i=0;i<dead.size();++i) {
                                if (!all_dead&&dead[i]) continue;
                                auto q=gold->camps()[i].spawn_position(); int d=static_cast<int>(self().position().chebyshev_distance(q));
                                if (d<nearest&&!vision::has_champion(q)) { nearest=d; next=q; }
                            }
                            walk(next,round);
                        }
                    }
                } else if (phase==1) {
                    if (!map::spawn_region(team::ally).is_set(self().position())) walk(corner,round);
                    else {
                        struct Purchase { bool active; item_family family; item_stat stat; };
                        const std::array purchases{Purchase{DZ_MONSTER,item_family::monster,DZ_MONSTER_FOCUS?item_stat::focus:item_stat::strength},
                            Purchase{DZ_JUNGLE,item_family::jungle,item_stat::health},Purchase{DZ_DURABILITY,item_family::durability,item_stat::health}};
                        bool items_ok=true;
                        for (auto purchase:purchases) {
                            auto shard=get_item_enum(purchase.family,purchase.stat);
                            if (purchase.active) for (int i=0;i<5&&round_number()==round;++i) self().buy(shard);
                            auto emblem=get_item_enum(purchase.family,purchase.stat,false);
                            items_ok&=self().item_count()[emblem]==static_cast<unsigned>(purchase.active)&&self().item_count()[shard]==0;
                        }
                        check("modifier_items_created",items_ok); phase=2;
                    }
                } else if (phase==2) {
                    auto stand=wolf->spawn_position()+vec2{-sign,0};
                    if (self().position()!=stand) walk(stand,round);
                    else phase=3;
                } else {
                    if (phase==3) {
                        start_hp=self().health(); strength=self().strength();
                        auto monster=get_item_enum(item_family::monster,DZ_MONSTER_FOCUS?item_stat::focus:item_stat::strength,false);
                        auto jungle=get_item_enum(item_family::jungle,item_stat::health,false);
                        auto durability=get_item_enum(item_family::durability,item_stat::health,false);
                        hit=strength*self().base_stats().camp_damage_multiplier*(1+(DZ_MONSTER?monster.passive_magnitude():0));
                        incoming=wolf->strength()*(1-(DZ_JUNGLE?jungle.passive_magnitude():0))*(1-(DZ_DURABILITY?durability.passive_magnitude():0));
                        prediction=dz::stationary_duel(start_hp,{wolf->health(),hit},incoming);
                        check("modifier_feasible",prediction.work.complete()&&prediction.survives&&start_hp==self().max_health()&&!wolf->is_awake());
                        first=round; phase=4;
                        std::printf("CT_MOD_SETUP monster=%d jungle=%d durability=%d strength=%.9g camp_hp=%.9g camp_strength=%.9g hit=%.9g incoming=%.9g predicted=%u\n",
                            DZ_MONSTER,DZ_JUNGLE,DZ_DURABILITY,strength,wolf->health(),wolf->strength(),hit,incoming,prediction.work.attacks);
                    } else {
                        auto delta=previous_hp-self().health(); phase_ok&=std::abs(delta-incoming)<.01f;
                        std::printf("CT_MOD_PHASE round=%u delta=%.9g\n",round,delta);
                    }
                    unsigned threats=0;
                    for (auto& c:vision::camps()) if (c.is_awake()&&c.strength()>0&&self().position().chebyshev_distance(c.spawn_position())<=c.attack_range()) ++threats;
                    isolated&=threats==static_cast<unsigned>(attacks>0);
                    fixed_stats&=self().strength()==strength;
                    if (self().can_attack()&&round_number()==round) {
                        float before=wolf->health(); self().attack(*wolf); ++attacks;
                        auto after=wolf->is_dead()?0:wolf->health();
                        hit_ok&=std::abs((before-after)-std::min(before,hit))<.01f;
                        if (wolf->is_dead()) {
                            auto loss=start_hp-self().health();
                            check("modifier_hit_damage",hit_ok);
                            check("modifier_phase_damage",phase_ok);
                            check("modifier_attack_count",attacks==prediction.work.attacks);
                            check("modifier_elapsed",round-first==attacks-1);
                            check("modifier_total_damage",std::abs(loss-prediction.future_damage_for_clear)<.1);
                            check("modifier_isolated_fixed_stats",isolated&&fixed_stats);
                            std::printf("CT_MOD_RESULT attacks=%u elapsed=%u hp_lost=%.9g expected_damage=%.9g\n",attacks,round-first,loss,prediction.future_damage_for_clear);
                            phase=5;
                        }
                    }
                    previous_hp=self().health();
                }
                if (round%100==0&&phase<3) std::printf("CT_MOD_STATE round=%u phase=%u gold=%u\n",round,phase,self().gold_count());
            }
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
