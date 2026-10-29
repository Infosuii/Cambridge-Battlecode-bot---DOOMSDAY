#include <cambc.h>
#include <algorithm>
#include <cstdio>
using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
bool walk(vec2 target,unsigned round) {
    auto p=self().position();
    if (!self().can_move()||p==target) return false;
    if (p.chebyshev_distance(target)<=1&&(vision::has_camp(target)||vision::has_champion(target))) return false;
    return round_number()==round&&self().move_towards(target);
}
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::ryth,champion_draft::marcella,champion_draft::vendetta,
            champion_draft::vesper_vale,champion_draft::heart_of_ruin};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    const bool actor=self().champion_name()==champion_type::ryth;
    auto corner=map::spawn_region(team::ally).positions().front();
    int sign=corner.x<map::width()/2?1:-1;
    auto away=corner+vec2{sign*6,sign};
    auto park=vec2{std::clamp(corner.x+sign*(10+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),corner.y};
    std::optional<map::camp_group> gold;
    std::optional<camp> wolf;
    if (actor) {
        int gold_distance=65535,wolf_distance=65535;
        for (auto& g:map::camp_groups()) {
            bool harmless=true;
            for (auto& c:g.camps()) {
                harmless&=c.is_gold_cluster()||c.is_gem_cluster();
                int d=static_cast<int>(corner.chebyshev_distance(c.spawn_position()));
                if (c.is_wolf()&&d<wolf_distance) { wolf_distance=d; wolf=c; }
            }
            int d=static_cast<int>(corner.chebyshev_distance(g.camps()[0].spawn_position()));
            if (harmless&&g.gold_value()>=60&&d<gold_distance) { gold_distance=d; gold=g; }
        }
        if (!gold||!wolf) std::printf("ERROR missing recovery fixture setup\n");
    }
    std::vector<bool> dead(gold?gold->camps().size():0,false);
    int phase=0,started=0; float before=0; bool injury_logged=false;
    for (;;) {
        auto round=round_number();
        try {
            if (!actor) {
                if (!vision::has_champion(park)&&!vision::has_camp(park)) walk(park,round);
            } else if (gold&&wolf&&self().is_alive()) {
                auto p=self().position();
                if (phase==0) {
                    if (self().gold_count()>=60) phase=1;
                    else {
                        const camp* target=nullptr; int distance=65535;
                        for (unsigned i=0;i<gold->camps().size();++i) {
                            auto& c=gold->camps()[i];
                            if (vision::in_vision(c.spawn_position())) dead[i]=c.is_dead();
                            if (!c.is_visible()||!c.is_alive()) continue;
                            int d=static_cast<int>(p.chebyshev_distance(c.position()));
                            if (d<distance) { target=&c; distance=d; }
                        }
                        if (target) {
                            if (distance<=self().attack_range()&&self().can_attack()&&round_number()==round) self().attack(*target);
                            else walk(target->spawn_position(),round);
                        } else {
                            vec2 closest=gold->camps()[0].spawn_position(); distance=65535;
                            bool all_dead=std::all_of(dead.begin(),dead.end(),[](bool x){return x;});
                            for (unsigned i=0;i<dead.size();++i) {
                                if (!all_dead&&dead[i]) continue;
                                auto q=gold->camps()[i].spawn_position(); int d=static_cast<int>(p.chebyshev_distance(q));
                                if (d<distance&&!vision::has_champion(q)) { distance=d; closest=q; }
                            }
                            walk(closest,round);
                        }
                    }
                } else if (phase==1) {
                    if (wolf->is_visible()&&p.chebyshev_distance(wolf->position())<=self().attack_range()&&self().can_attack()&&round_number()==round) {
                        self().attack(*wolf); phase=2;
                    } else walk(wolf->spawn_position(),round);
                } else if (phase==2) {
                    if (!injury_logged) { check("injury_established",self().health()<self().max_health()); injury_logged=true; }
                    auto center=wolf->spawn_position();
                    vec2 best=p; auto distance=p.chebyshev_distance(center);
                    for (int dx=-1;dx<=1;++dx) for (int dy=-1;dy<=1;++dy) {
                        auto q=p+vec2{dx,dy};
                        if (!map::is_in_bounds(q)||q.chebyshev_distance(center)<=distance||vision::has_champion(q)||vision::has_camp(q)) continue;
                        distance=q.chebyshev_distance(center); best=q;
                    }
                    if (p.chebyshev_distance(center)>wolf->attack_range()) phase=3;
                    else if (best!=p&&round_number()==round&&self().can_move()) self().move_absolute(best);
                } else if (phase==3&&round_number()==round) {
                    before=self().health(); started=round; self().recall(); phase=4;
                } else if (phase==4&&!self().is_recalling()) {
                    check("base_recall_five_ticks",round-started==static_cast<unsigned>(constants::recall_time)&&map::spawn_region(team::ally).is_set(p));
                    check("arrival_before_healing",self().health()==before&&self().health()<self().max_health());
                    auto hp=self().health(),max_hp=self().max_health();
                    if (round_number()==round) self().buy(get_item_enum(item_family::power,item_stat::health));
                    check("health_purchase_heals_gain",self().health()-hp==self().max_health()-max_hp&&self().max_health()>max_hp);
                    for (int i=0;i<5&&round_number()==round;++i) self().buy(get_item_enum(item_family::home,item_stat::strength));
                    auto emblem=get_item_enum(item_family::home,item_stat::strength,false);
                    check("home_emblem_created",self().item_count()[emblem]==1); phase=5;
                } else if (phase==5) {
                    check("next_spawn_turn_full_heal",self().health()==self().max_health()); phase=6;
                } else if (phase==6) {
                    if (p!=away) walk(away,round);
                    else if (round_number()==round) { started=round; self().recall(); phase=7; }
                } else if (phase==7&&!self().is_recalling()) {
                    std::printf("CT_HOME_DURATION ticks=%u\n",round-started);
                    check("home_recall_three_ticks",round-started==3&&map::spawn_region(team::ally).is_set(p)); phase=8;
                } else if (phase==8) {
                    bool accepted=false; int code=0;
                    try { if (round_number()==round) { self().recall(); accepted=true; } }
                    catch (const error& error) { code=static_cast<int>(error.code()); }
                    bool active=self().is_recalling(); int timer=active?self().remaining_channel_time():-1;
                    std::printf("CT_HOME_SPAWN accepted=%d active=%d timer=%d code=%d\n",accepted,active,timer,code);
                    if (active&&round_number()==round) self().cancel_recall();
                    phase=9;
                }
                if (round%40==0&&phase<9) std::printf("CT_RECOVERY_STATE round=%u phase=%d gold=%u hp=%.0f pos=%d,%d\n",round,phase,self().gold_count(),self().health(),p.x,p.y);
            }
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
