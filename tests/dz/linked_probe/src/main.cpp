#include <cambc.h>
#include <algorithm>
#include <cstdio>
#include "config.h"
using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::cassi_and_issac,champion_draft::vendetta,champion_draft::ryth,
            champion_draft::marcella};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    std::optional<champion> cassi,issac;
    for (auto& c:champions(team::ally)) {
        if (c.champion_name()==champion_type::cassi) cassi=c;
        if (c.champion_name()==champion_type::issac) issac=c;
    }
    auto kind=self().champion_name();
    const bool observer=kind==champion_type::vendetta;
    const bool sacrifice=kind==(DZ_ISSAC_DIES?champion_type::issac:champion_type::cassi);
    const bool partner=kind==(DZ_ISSAC_DIES?champion_type::cassi:champion_type::issac);
    auto corner=map::spawn_region(team::ally).positions().front();
    int sign=corner.x<map::width()/2?1:-1;
    auto park=vec2{std::clamp(corner.x+sign*(10+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),corner.y};
    std::optional<camp> monolith;
    int nearest=65535;
    for (auto& g:map::camp_groups()) for (auto& c:g.camps()) if (c.is_monolith()) {
        int d=static_cast<int>(corner.chebyshev_distance(c.spawn_position()));
        if (d<nearest) { monolith=c; nearest=d; }
    }
    if (observer) {
        check("linked_roster",cassi&&issac&&*cassi!=*issac&&champions(team::ally).size()==draft::team_size()+1);
        std::printf("CT19_SETTING respawn=%d\n",constants::respawn_time);
    }
    bool stopped=false,parked=false,dead_seen=false,done=false;
    for (;;) {
        auto round=round_number();
        try {
            if (observer&&cassi&&issac&&!done) {
                bool first=cassi->is_alive(),second=issac->is_alive();
                std::printf("CT19_VIEW round=%u observer=%u first=%u first_alive=%d second=%u second_alive=%d\n",round,
                    static_cast<unsigned>(static_cast<handle_champion_t>(self())),static_cast<unsigned>(static_cast<handle_champion_t>(*cassi)),first,
                    static_cast<unsigned>(static_cast<handle_champion_t>(*issac)),second);
                if ((!first||!second)&&!dead_seen) { check("linked_both_dead",!first&&!second); dead_seen=true; }
                if (dead_seen&&first&&second) { check("linked_both_return",true); done=true; }
            } else if (sacrifice&&monolith) {
                if (!self().is_alive()) stopped=true;
                if (!stopped) {
                    auto p=self().position(),stand=monolith->spawn_position()+vec2{-sign,0};
                    if (p!=stand&&self().can_move()&&round_number()==round) self().move_towards(stand);
                    else if (p==stand&&round>=30&&monolith->is_visible()&&self().can_attack()&&round_number()==round) self().attack(*monolith);
                }
            } else if (!observer&&self().is_alive()) {
                if (self().position()!=park&&self().can_move()&&!vision::has_champion(park)&&!vision::has_camp(park)&&round_number()==round) self().move_towards(park);
                if (partner&&!parked&&self().position()==park) {
                    bool safe=true;
                    for (auto& g:map::camp_groups()) for (auto& c:g.camps())
                        if (c.base_stats().base_strength>0&&park.chebyshev_distance(c.spawn_position())<=c.attack_range()) safe=false;
                    check("linked_partner_parked",safe&&self().health()==self().max_health());
                    std::printf("CT19_PARK round=%u body=%u hp=%.0f\n",round,static_cast<unsigned>(static_cast<handle_champion_t>(self())),self().health());
                    parked=true;
                }
            }
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
