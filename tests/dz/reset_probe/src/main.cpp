#include <cambc.h>
#include <cstdio>
#include <algorithm>

using namespace cambc;
std::optional<vec2> step(std::optional<vec2> target={}) {
    auto p=self().position();
    auto blocked=map::walls()|map::holes()|map::altars()|map::spawn_region(team::enemy)|
        vision::champion_tiles()|vision::camp_tiles()|vision::teleport_tiles();
    for (int dx=-1;dx<=1;++dx) for (int dy=-1;dy<=1;++dy) {
        auto q=p+vec2{dx,dy};
        if (q==p||!map::is_in_bounds(q)||blocked.is_set(q)) continue;
        if (!target||q.chebyshev_distance(*target)<p.chebyshev_distance(*target)) return q;
    }
    return {};
}
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vendetta,champion_draft::ryth,champion_draft::marcella,
            champion_draft::vesper_vale,champion_draft::heart_of_ruin};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    const bool subject=self().champion_name()==champion_type::vendetta;
    auto corner=map::spawn_region(team::ally).positions().front();
    auto park=vec2{std::clamp(corner.x+(corner.x<map::width()/2?1:-1)*
        (8+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),
        corner.y<map::height()/2?0:map::height()-1};
    std::optional<camp> selected; int best=65535,stage=0;
    if (subject) for (auto& g:map::camp_groups()) for (auto& c:g.camps()) if (c.is_gem_cluster()) {
        int d=static_cast<int>(self().position().chebyshev_distance(c.spawn_position()));
        if (d<best) { best=d; selected=c; }
    }
    for (;;) {
        auto round=round_number();
        try {
            if (!subject) {
                if (self().can_move()&&!vision::has_champion(park)&&round_number()==round) self().move_towards(park);
            } else if (selected&&self().is_alive()&&stage<2) {
                auto p=self().position(),target=selected->spawn_position();
                if (!selected->is_visible()||p.chebyshev_distance(target)>3) {
                    if (self().can_move()&&round_number()==round) self().move_towards(target);
                } else if (stage==0) {
                    auto dest=step(target);
                    if (dest&&self().abilities()[1].is_ready()&&round_number()==round) {
                        self().abilities()[1].use(*dest); stage=1;
                    }
                } else if (p.chebyshev_distance(target)>1) {
                    if (self().can_move()&&round_number()==round) self().move_towards(target);
                } else if (selected->is_alive()&&selected->health()>self().strength()&&self().abilities()[0].is_ready()) {
                    if (round_number()!=round) continue;
                    self().attack(*selected); self().abilities()[0].use();
                    int reset_before=self().abilities()[0].cooldown(),dash_before=self().abilities()[1].cooldown();
                    self().attack(*selected);
                    const bool dead=selected->is_dead();
                    int reset_after=self().abilities()[0].cooldown(),dash_after=self().abilities()[1].cooldown();
                    std::printf("CT_CHECK name=camp_kill_resets_both_cooldowns pass=%d\n",
                        dead&&reset_before>0&&dash_before>0&&reset_after==0&&dash_after==0);
                    std::printf("CT26 reset_before=%d dash_before=%d reset_after=%d dash_after=%d can_cast_after=%d\n",
                        reset_before,dash_before,reset_after,dash_after,self().can_cast());
                    if (auto dest=step()) {
                        try { bool ok=self().abilities()[1].use(*dest); std::printf("CT26 second_cast_after_kill=%d code=0\n",ok); }
                        catch (const error& e) { std::printf("CT26 second_cast_after_kill=0 code=%d\n",static_cast<int>(e.code())); }
                    }
                    stage=2;
                }
            }
        } catch (const std::exception& e) { std::printf("ERROR %s\n",e.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
