#include <cambc.h>
#include <cstdio>
#include <algorithm>
#include "config.h"

// Controlled CT-11 fixture: only the subject approaches camps. Ordinary cases
// use basic attacks; monolith isolation uses Ryth's ground spell and a ward.
// No items. Other bodies park. Logs include every visible awake camp
// in range so multi-camp damage cannot be mistaken for a single camp's cadence.
int main() {
    using namespace cambc;
    if (is_draft()) {
        std::array picks{champion_draft::vendetta, champion_draft::ryth,
            champion_draft::marcella, champion_draft::vesper_vale, champion_draft::varg};
        for (;;) {
            try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {}
            end_turn();
        }
    }
    auto groups = map::camp_groups();
    const auto spawn = map::spawn_region(team::ally).positions();
    const auto corner = spawn.front();
    const auto park = vec2{std::clamp(corner.x + (corner.x < map::width()/2 ? 1 : -1) *
        (8 + static_cast<int>(static_cast<handle_champion_t>(self())) % 5), 0, map::width()-1),
        corner.y < map::height()/2 ? 0 : map::height()-1};
    std::optional<camp> selected;
    std::vector<camp> members;
    std::vector<std::pair<vec2,int>> damaging;
    if constexpr (DZ_MONOLITH) for (auto& g:groups) for (auto& c:g.camps()) {
        if (c.base_stats().base_strength>0) damaging.push_back({c.spawn_position(),c.attack_range()});
    }
    const bool subject=self().champion_name()==(DZ_MONOLITH ? champion_type::ryth : champion_type::vendetta);
    if (subject) {
        int best = 65535;
        for (const auto& g : groups) for (const auto& c : g.camps()) {
            const bool match=DZ_WOLF ? c.is_wolf() : DZ_GOLEM ? c.is_golem() : DZ_MONOLITH ? c.is_monolith() : c.is_elk();
            if (!match) continue;
            int d = static_cast<int>(self().position().chebyshev_distance(c.spawn_position()));
            if (d < best) { best = d; selected = c; auto view=g.camps(); members.assign(view.begin(),view.end()); }
        }
        if (!selected) std::printf("ERROR no matching camp fixture\n");
    }
    float previous_hp = -1;
    for (;;) {
        const auto round = round_number();
        try {
            if (!selected && self().is_alive() && self().can_move()) {
                // Vacate the spawn exits; an idle teammate can otherwise trap the
                // subject in a corner and turn this into a no-op diagnostic.
                if (!vision::has_champion(park)&&!vision::has_camp(park)&&!map::walls().is_set(park)&&!map::holes().is_set(park)&&
                    !map::altars().is_set(park)&&!map::spawn_region(team::enemy).is_set(park)&&round_number()==round) self().move_towards(park);
            } else if (selected && self().is_alive()) {
                auto p = self().position();
                float hp = self().health(), incoming = 0;
                unsigned active = 0;
                for (const auto& c : vision::camps()) {
                    if (!c.is_awake()) continue;
                    if (p.chebyshev_distance(c.position()) <= c.attack_range()) { incoming += c.strength(); ++active; }
                }
                const bool target_awake=selected->is_visible()&&selected->is_awake();
                std::printf("CT11 round=%u hp=%.0f delta=%.0f active=%u incoming=%.0f pos=%d,%d target=%d,%d target_awake=%d target_strength=%.0f target_in_range=%d\n",
                    round, hp, previous_hp < 0 ? 0 : previous_hp-hp, active, incoming, p.x, p.y,
                    selected->spawn_position().x, selected->spawn_position().y,target_awake,target_awake?selected->strength():0,
                    p.chebyshev_distance(selected->spawn_position())<=selected->attack_range());
                previous_hp = hp;
                // Check after every potentially expensive observation. No action
                // can be issued with a position sampled in another round.
                if (round_number() != round) continue;
                if (round < 15) { end_turn(); continue; }
                if constexpr (DZ_MONOLITH) {
                    // Ryth's range-four, radius-one ground spell can wake the
                    // target from range five. Exclude every other damaging camp
                    // so five hits can be observed without doubling incoming DPS.
                    auto blocked=map::walls()|map::holes()|map::altars()|map::spawn_region(team::enemy)|vision::camp_tiles()|vision::champion_tiles();
                    blocked.set(p,false); bitboard roots,visited;
                    auto center=selected->spawn_position();
                    for (int dx=-5;dx<=5;++dx) for (int dy=-5;dy<=5;++dy) {
                        if (std::max(std::abs(dx),std::abs(dy))!=5) continue;
                        if (dx&&dy) continue; // Avoid diagonal bush/wall occlusion in this fixture.
                        auto q=center+vec2{dx,dy};
                        if (!map::is_in_bounds(q)||blocked.is_set(q)) continue;
                        bool safe=true;
                        for (auto [other,range]:damaging) if (other!=center&&q.chebyshev_distance(other)<=range) safe=false;
                        if (safe) roots.set(q);
                    }
                    if (roots.is_set(p)) {
                        if (!selected->is_visible()&&self().ward_cooldown()==0) {
                            auto sign=[](int x){return (x>0)-(x<0);};
                            int range=static_cast<int>(constants::ward_placement_radius);
                            for (int step=range;step>=1;--step) {
                                auto ward=p+vec2{sign(center.x-p.x)*step,sign(center.y-p.y)*step};
                                if (!map::is_in_bounds(ward)||map::walls().is_set(ward)||map::holes().is_set(ward)||map::altars().is_set(ward)||
                                    vision::has_champion(ward)||vision::has_camp(ward)||vision::ward_tiles(team::ally).is_set(ward)) continue;
                                if (round_number()==round) self().place_ward(ward);
                                break;
                            }
                        }
                        if (!target_awake) {
                            auto sign=[](int x){return (x>0)-(x<0);};
                            auto ground=center+vec2{sign(p.x-center.x),sign(p.y-center.y)};
                            auto ability=self().abilities()[0];
                            if (ability.is_ready()&&ability.valid_tiles().is_set(ground)&&round_number()==round) ability.use(ground);
                        }
                    } else if (self().can_move()&&!roots.is_empty()) {
                        distance_field route; route.compute(blocked,roots,visited);
                        for (auto delta:route.next_moves_from(p)) if (round_number()==round) { self().move_absolute(p+delta); break; }
                    }
                    if (round_number()==round) end_turn();
                    continue;
                }
                if (!(target_awake&&p.chebyshev_distance(selected->spawn_position())<=selected->attack_range())) {
                    const camp* wake=nullptr;
                    for (auto& c:members) if (c.is_visible()&&c.is_alive()&&p.chebyshev_distance(c.position())<=self().attack_range()) { wake=&c; break; }
                    if (wake&&self().can_attack()&&round_number()==round) self().attack(*wake);
                    else if (!wake&&self().can_move()&&round_number()==round) self().move_towards(selected->spawn_position());
                }
            } else if (selected) {
                std::printf("CT11 round=%u dead=1\n", round); previous_hp = -1;
            }
        } catch (const std::exception& e) { std::printf("ERROR %s\n", e.what()); }
        if (round_number() != round) continue;
        end_turn();
    }
}
