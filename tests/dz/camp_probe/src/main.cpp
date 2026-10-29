#include <cambc.h>
#include <cstdio>
#include <algorithm>

// Controlled CT-11 fixture: only Vendetta leaves spawn, only basic attacks, no
// items/spells. Other bodies remain idle. Logs include every visible awake camp
// in range so multi-camp damage cannot be mistaken for a single camp's cadence.
int main() {
    using namespace cambc;
    if (is_draft()) {
        const std::array picks{champion_draft::vendetta, champion_draft::ryth,
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
    if (self().champion_name() == champion_type::vendetta) {
        int best = 65535;
        for (const auto& g : groups) for (const auto& c : g.camps()) {
            if (!c.is_elk()) continue;
            int d = static_cast<int>(self().position().chebyshev_distance(c.spawn_position()));
            if (d < best) { best = d; selected = c; }
        }
    }
    float previous_hp = -1;
    for (;;) {
        const auto round = round_number();
        try {
            if (!selected && self().is_alive() && self().can_move()) {
                // Vacate the spawn exits; an idle teammate can otherwise trap the
                // subject in a corner and turn this into a no-op diagnostic.
                if (!vision::has_champion(park) && round_number() == round) self().move_towards(park);
            } else if (selected && self().is_alive()) {
                auto p = self().position();
                float hp = self().health(), incoming = 0;
                unsigned active = 0;
                for (const auto& c : vision::camps()) {
                    if (!c.is_awake()) continue;
                    if (p.chebyshev_distance(c.position()) <= c.attack_range()) { incoming += c.strength(); ++active; }
                }
                std::printf("CT11 round=%u hp=%.0f delta=%.0f active=%u incoming=%.0f pos=%d,%d target=%d,%d\n",
                    round, hp, previous_hp < 0 ? 0 : previous_hp-hp, active, incoming, p.x, p.y,
                    selected->spawn_position().x, selected->spawn_position().y);
                previous_hp = hp;
                // Check after every potentially expensive observation. No action
                // can be issued with a position sampled in another round.
                if (round_number() != round) continue;
                if (round < 15) { end_turn(); continue; }
                if (selected->is_visible() && selected->is_alive() && p.chebyshev_distance(selected->position()) <= self().attack_range()) {
                    if (self().can_attack() && round_number() == round) self().attack(*selected);
                } else if ((!selected->is_visible() || selected->is_alive()) && self().can_move() && round_number() == round) {
                    self().move_towards(selected->spawn_position());
                }
            } else if (selected) {
                std::printf("CT11 round=%u dead=1\n", round); previous_hp = -1;
            }
        } catch (const std::exception& e) { std::printf("ERROR %s\n", e.what()); }
        if (round_number() != round) continue;
        end_turn();
    }
}
