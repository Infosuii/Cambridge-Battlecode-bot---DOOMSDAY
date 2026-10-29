#include <cambc.h>
#include <algorithm>
#include <cstdio>
#include "config.h"
using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
bool walk(vec2 q,unsigned round) {
    auto p=self().position();
    if (p==q||!self().can_move()) return false;
    if (p.chebyshev_distance(q)<=1&&(vision::has_champion(q)||vision::has_camp(q))) return false;
    return round_number()==round&&self().move_towards(q);
}
bool member(vec2 p,const map::camp_group& g) {
    for (auto& c:g.camps()) if (p==c.spawn_position()) return true;
    return false;
}
bool stage_outside(const map::camp_group& g,unsigned round) {
    auto p=self().position();
    auto blocked=map::walls()|map::holes()|map::altars()|map::spawn_region(team::enemy)|vision::champion_tiles()|vision::camp_tiles();
    blocked.set(p,false); bitboard roots,visited;
    for (auto& c:g.camps()) for (int dx=-1;dx<=1;++dx) for (int dy=-1;dy<=1;++dy) {
        auto q=c.spawn_position()+vec2{dx,dy};
        if (map::is_in_bounds(q)&&!blocked.is_set(q)&&!member(q,g)) roots.set(q);
    }
    distance_field route; route.compute(blocked,roots,visited);
    for (auto delta:route.next_moves_from(p)) if (round_number()==round) return self().move_absolute(p+delta);
    return false;
}
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vesper_vale,champion_draft::marcella,champion_draft::vendetta,
            champion_draft::ryth,champion_draft::heart_of_ruin};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    auto corner=map::spawn_region(team::ally).positions().front();
    auto park=vec2{std::clamp(corner.x+(corner.x<map::width()/2?1:-1)*(8+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),corner.y};
    bool actor=self().champion_name()==champion_type::vesper_vale;
    std::optional<map::camp_group> group;
    for (auto& g:map::camp_groups()) if (g.gem_value()>0&&g.camps().size()>=2) { group=g; break; }
    vec2 capture=corner; int distance=65535;
    if (group) for (auto& c:group->camps()) {
        int d=static_cast<int>(corner.chebyshev_distance(c.spawn_position()));
        if (d<distance) { distance=d; capture=c.spawn_position(); }
    }
    int phase=0,entered=0,contested=0; bool resumed=false;
    for (;;) {
        auto round=round_number();
        try {
            if (!actor) { if (!vision::has_champion(park)) walk(park,round); }
            else if (group&&self().is_alive()) {
                auto& g=*group; auto p=self().position();
                bool visible=false;
                for (auto& c:g.camps()) if (vision::in_vision(c.spawn_position())) visible=true;
                if constexpr (CT_OPPONENT) {
                    if (phase==0) {
                        if (visible&&std::holds_alternative<map::camp_group_reward_available>(g.state())&&
                            g.capture_state().state==map::camp_group_capture_type::enemy_capturing&&
                            g.capture_state().timer>0&&g.capture_state().timer<constants::capture_time) {
                            std::printf("CT_CONTEST_PROGRESS round=%u timer=%d max=%d enemy_capturing=1\n",round,g.capture_state().timer,constants::capture_time);
                            if (p!=capture) walk(capture,round);
                            if (self().position()==capture) { phase=1; entered=round; }
                        } else stage_outside(g,round);
                    } else if (phase==1&&round>=static_cast<unsigned>(entered+4)) {
                        if (member(p,g)) stage_outside(g,round);
                        if (!member(self().position(),g)) phase=2;
                    }
                } else {
                    if (phase==0) {
                        const camp* target=nullptr;
                        for (auto& c:g.camps()) if (c.is_visible()&&c.is_alive()) { target=&c; break; }
                        if (target) {
                            if (p.chebyshev_distance(target->position())<=self().attack_range()&&self().can_attack()&&round_number()==round) self().attack(*target);
                            else walk(target->spawn_position(),round);
                        } else if (visible&&std::holds_alternative<map::camp_group_reward_available>(g.state())) phase=1;
                        else walk(capture,round);
                    } else if (phase<4) {
                        if (!member(p,g)) walk(capture,round);
                        bool enemy_onsite=false; unsigned enemy_gems=0;
                        for (auto& e:vision::champions(team::enemy)) if (member(e.position(),g)) { enemy_onsite=true; enemy_gems+=e.gem_count(); }
                        if (self().gem_count()>0) {
                            check("full_reward_after_enemy_leaves",!enemy_onsite&&self().gem_count()==g.gem_value());
                            check("capture_progress_resumed",resumed); phase=4;
                        } else if (std::holds_alternative<map::camp_group_reward_available>(g.state())) {
                            int timer=g.capture_state().timer;
                            if (enemy_onsite&&timer==constants::capture_time) {
                                ++contested;
                                if (contested==3) {
                                    check("contest_resets_capture_timer",g.capture_state().state==map::camp_group_capture_type::contested);
                                    check("contest_preserves_unclaimed_gems",self().gem_count()==0&&enemy_gems==0); phase=2;
                                }
                            }
                            if (phase==2&&!enemy_onsite&&timer<constants::capture_time&&g.capture_state().state==map::camp_group_capture_type::ally_capturing) resumed=true;
                        }
                    }
                    if (round%20==0&&phase<4) std::printf("CT_CONTEST_STATE round=%u phase=%d pos=%d,%d contested=%d\n",round,phase,p.x,p.y,contested);
                }
            }
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
