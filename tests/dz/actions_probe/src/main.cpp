#include <cambc.h>
#include <cstdio>
#include <algorithm>

using namespace cambc;
struct Outcome { bool accepted; int code; };
template<class F> Outcome attempt(F f) {
    try { return {f(),0}; } catch (const error& e) { return {false,static_cast<int>(e.code())}; }
}
void check(const char* name, bool passed, Outcome result) {
    std::printf("CT_CHECK name=%s pass=%d accepted=%d code=%d\n",name,passed,result.accepted,result.code);
}
std::optional<vec2> free_step(std::optional<vec2> target = {}, int max_distance = 10000) {
    auto origin = self().position();
    auto blocked = map::walls() | map::holes() | map::altars() | map::spawn_region(team::enemy) |
        vision::champion_tiles() | vision::camp_tiles() | vision::teleport_tiles();
    for (int dx=-1; dx<=1; ++dx) for (int dy=-1; dy<=1; ++dy) {
        auto p = origin + vec2{dx,dy};
        if (p == origin || !map::is_in_bounds(p) || blocked.is_set(p)) continue;
        if (!target || p.chebyshev_distance(*target) <= max_distance) return p;
    }
    return {};
}
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vesper_vale,champion_draft::marcella,
            champion_draft::vendetta,champion_draft::heart_of_ruin,champion_draft::ryth};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    auto type = self().champion_name();
    std::printf("CT7_ACTOR type=%d\n", static_cast<int>(type));
    auto groups = map::camp_groups();
    std::optional<camp> selected;
    int best = 65535, stage = 0;
    for (auto& g : groups) for (auto& c : g.camps()) {
        if (!c.is_elk() && !c.is_wolf()) continue;
        int d = static_cast<int>(self().position().chebyshev_distance(c.spawn_position()));
        if (d < best) { best=d; selected=c; }
    }
    for (;;) {
        auto round = round_number();
        try {
            if (self().is_alive() && type == champion_type::heart_of_ruin && stage == 0) {
                auto p = free_step();
                if (p && self().abilities()[0].is_ready()) {
                    auto shield = attempt([&] { return self().abilities()[0].use(); });
                    auto moved = attempt([&] { return self().move_absolute(*p); });
                    check("shield_then_move",shield.accepted && moved.accepted,moved); ++stage;
                }
            } else if (self().is_alive() && stage < 2 && selected &&
                (type == champion_type::vesper_vale || type == champion_type::marcella || type == champion_type::vendetta)) {
                auto pos = self().position();
                int setup_range = type == champion_type::vendetta ? 2 : 3;
                if (!selected->is_visible() || pos.chebyshev_distance(selected->position()) > setup_range) {
                    if (self().can_move() && round_number() == round) self().move_towards(selected->spawn_position());
                } else if (selected->is_alive() && selected->health() > 300) {
                    auto target = selected->position();
                    if (type == champion_type::vesper_vale) {
                        if (stage == 0) {
                            auto p = free_step(target,3);
                            if (p && round_number() == round) {
                                auto move = attempt([&] { return self().move_absolute(*p); });
                                auto hit = attempt([&] { self().attack(*selected); return true; });
                                check("ranged_move_blocks_attack",move.accepted && !hit.accepted && !self().can_attack(),hit); ++stage;
                            }
                        } else {
                            auto p = free_step();
                            if (p && self().abilities()[0].is_ready() && self().abilities()[1].is_ready() && round_number() == round) {
                                auto hit = attempt([&] { self().attack(*selected); return true; });
                                auto move = attempt([&] { return self().move_absolute(*p); });
                                check("ranged_attack_blocks_move",hit.accepted && !move.accepted && !self().can_move(),move);
                                auto reset = attempt([&] { return self().abilities()[0].use(); });
                                auto again = attempt([&] { self().attack(*selected); return true; });
                                check("reset_restores_attack",hit.accepted && reset.accepted && again.accepted,again);
                                auto cast = attempt([&] { return self().abilities()[1].use(*p); });
                                check("one_cast_per_turn",reset.accepted && !cast.accepted && cast.code==27,cast); ++stage;
                            }
                        }
                    } else if (type == champion_type::marcella) {
                        auto p = free_step(target,4);
                        if (p && self().abilities()[1].is_ready() && round_number() == round) {
                            if (stage == 0) {
                                auto moved = attempt([&] { return self().move_absolute(*p); });
                                auto cast = attempt([&] { return self().abilities()[1].use(*selected); });
                                check("move_blocks_exclusive_cast",moved.accepted && !cast.accepted && cast.code==126,cast);
                            } else {
                                auto cast = attempt([&] { return self().abilities()[1].use(*selected); });
                                auto moved = attempt([&] { return self().move_absolute(*p); });
                                check("exclusive_cast_blocks_move",cast.accepted && !moved.accepted && moved.code==127,moved);
                            }
                            ++stage;
                        }
                    } else {
                        if (stage == 0) {
                            auto p = free_step(target,1);
                            if (p && round_number() == round) {
                                auto moved = attempt([&] { return self().move_absolute(*p); });
                                auto hit = attempt([&] { self().attack(*selected); return true; });
                                check("melee_move_then_attack",moved.accepted && hit.accepted,hit); ++stage;
                            }
                        } else if (pos.chebyshev_distance(target) <= 1) {
                            auto p = free_step();
                            if (p && round_number() == round) {
                                auto hit = attempt([&] { self().attack(*selected); return true; });
                                auto moved = attempt([&] { return self().move_absolute(*p); });
                                check("melee_attack_then_move",hit.accepted && moved.accepted,moved); ++stage;
                            }
                        }
                    }
                }
            }
        } catch (const std::exception& e) { std::printf("ERROR %s\n",e.what()); }
        if (round_number() != round) continue;
        end_turn();
    }
}
