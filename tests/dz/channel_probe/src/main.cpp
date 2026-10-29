#include <cambc.h>
#include <cstdio>
#include <algorithm>

using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vendetta,champion_draft::ryth,champion_draft::marcella,
            champion_draft::vesper_vale,champion_draft::varg};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    auto spawn=map::spawn_region(team::ally).positions();
    const auto corner=spawn.front();
    const auto park=vec2{std::clamp(corner.x+(corner.x<map::width()/2?1:-1)*
        (8+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),
        corner.y<map::height()/2?0:map::height()-1};
    auto blocked=map::walls()|map::holes()|map::altars()|map::spawn_region(team::enemy);
    bitboard visited;
    distance_field home; home.compute(blocked,map::spawn_region(team::ally),visited);
    std::optional<camp> target;
    if (self().champion_name()==champion_type::vendetta) {
        int best=65535;
        for (auto& g:map::camp_groups()) for (auto& c:g.camps()) {
            if (!c.is_elk()) continue;
            int distance=static_cast<int>(self().position().chebyshev_distance(c.spawn_position()));
            if (distance<best) { best=distance; target=c; }
        }
    }
    int stage=0,started=0; float before=0;
    for (;;) {
        const auto round=round_number();
        try {
            if (!target) {
                if (self().is_alive()&&self().can_move()&&!vision::has_champion(park)&&round_number()==round) self().move_towards(park);
            } else if (self().is_alive()&&round>=15) {
                auto p=self().position();
                if (stage==0) {
                    if (target->is_visible()&&target->is_alive()&&p.chebyshev_distance(target->position())<=1) {
                        if (round_number()==round) self().attack(*target);
                        stage=1;
                    } else if (self().can_move()&&round_number()==round) self().move_towards(target->spawn_position());
                } else if (stage==1) {
                    before=self().health();
                    if (round_number()==round) self().recall();
                    check("recall_starts_in_camp_range",self().is_recalling()); stage=2;
                } else if (stage==2) {
                    check("camp_damage_interrupts_recall",self().health()<before&&!self().is_recalling()); stage=3;
                } else if (stage==3) {
                    bool camp_in_range=false;
                    for (auto& c:vision::camps()) if (c.is_awake()&&c.strength()>0&&p.chebyshev_distance(c.position())<=c.attack_range()) camp_in_range=true;
                    if (!camp_in_range&&!map::spawn_region(team::ally).is_set(p)) {
                        before=self().health(); started=round;
                        if (round_number()==round) self().recall();
                        stage=4;
                    } else if (self().can_move()) {
                        auto dynamic=blocked|vision::champion_tiles()|vision::camp_tiles();
                        dynamic.set(p,false);
                        bitboard safe;
                        std::vector<std::pair<vec2,int>> threats;
                        for (auto& c:vision::camps()) if (c.is_awake()&&c.strength()>0) threats.push_back({c.position(),c.attack_range()});
                        for (auto q:self().visible_tiles().positions()) {
                            if (dynamic.is_set(q)||map::spawn_region(team::ally).is_set(q)) continue;
                            bool threatened=false;
                            for (auto [position,range]:threats) if (q.chebyshev_distance(position)<=range) threatened=true;
                            if (!threatened) safe.set(q);
                        }
                        distance_field route; route.compute(dynamic,safe,visited);
                        for (auto delta:route.next_moves_from(p)) {
                            auto q=p+delta;
                            if (!vision::has_champion(q)&&!vision::has_camp(q)&&round_number()==round) { self().move_absolute(q); break; }
                        }
                    }
                } else if (stage==4 && !self().is_recalling()) {
                    check("base_recall_duration_five",round-started==static_cast<unsigned>(constants::recall_time)&&map::spawn_region(team::ally).is_set(p));
                    check("spawn_arrival_precedes_heal",self().health()==before&&self().health()<self().max_health());
                    stage=5;
                } else if (stage==5) {
                    check("one_spawn_turn_full_heal",self().health()==self().max_health()); stage=6;
                }
                if (round%20==0&&stage<6) std::printf("CT16_STATE round=%u stage=%d pos=%d,%d hp=%.0f\n",round,stage,p.x,p.y,self().health());
            } else if (target && stage<6 && !self().is_alive()) {
                std::printf("CT_SETUP_FAILURE subject_died stage=%d\n",stage); stage=99;
            }
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
