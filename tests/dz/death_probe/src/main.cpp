#include <cambc.h>
#include <algorithm>
#include <cstdio>
#include "config.h"
using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
template<class F> void query(const char* name,F read) {
    try { std::printf("CT_QUERY name=%s accepted=1 value=%d code=0\n",name,static_cast<int>(read())); }
    catch (const error& error) { std::printf("CT_QUERY name=%s accepted=0 value=0 code=%d\n",name,static_cast<int>(error.code())); }
}
int main() {
    if (is_draft()) {
        std::array picks{champion_draft::ryth,champion_draft::vendetta,champion_draft::marcella,
            champion_draft::vesper_vale,champion_draft::heart_of_ruin};
        if constexpr (DZ_REVERSE_DRAFT) std::swap(picks[0],picks[1]);
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    auto type=self().champion_name();
    bool observer=!CT_OPPONENT&&type==champion_type::ryth;
    bool sacrifice=type==(CT_OPPONENT?champion_type::ryth:champion_type::vendetta);
    auto corner=map::spawn_region(team::ally).positions().front();
    auto park=vec2{std::clamp(corner.x+(corner.x<map::width()/2?1:-1)*(8+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),corner.y};
    std::optional<camp> target;
    if (sacrifice) {
        int nearest=65535;
        for (auto& g:map::camp_groups()) for (auto& c:g.camps()) if (c.is_monolith()) {
            int distance=static_cast<int>(corner.chebyshev_distance(c.spawn_position()));
            if (distance<nearest) { nearest=distance; target=c; }
        }
    }
    std::optional<champion> enemy,ally;
    if (observer) {
        for (auto& c:champions(team::enemy)) if (c.champion_name()==champion_type::ryth) enemy=c;
        for (auto& c:champions(team::ally)) if (c.champion_name()==champion_type::vendetta) ally=c;
    }
    bool stopped=false,before_seen=false,enemy_dead=false,enemy_returned=false,ally_dead=false,ally_returned=false;
    unsigned enemy_died=0,ally_died=0;
    for (;;) {
        auto round=round_number();
        try {
            if (observer&&enemy&&ally) {
                if (!before_seen) {
                    check("enemy_hidden_before_death",!enemy->is_visible());
                    query("hidden_alive_before",[&]{return enemy->is_alive();});
                    query("hidden_health_before",[&]{return enemy->health();});
                    before_seen=true;
                }
                bool alive=enemy->is_alive();
                if (!enemy_returned||!ally_returned) std::printf("CT_LIFEVIEW round=%u observer=%u enemy=%u enemy_alive=%d ally=%u ally_alive=%d\n",
                    round,static_cast<unsigned>(static_cast<handle_champion_t>(self())),static_cast<unsigned>(static_cast<handle_champion_t>(*enemy)),alive,
                    static_cast<unsigned>(static_cast<handle_champion_t>(*ally)),ally->is_alive());
                if (!alive&&!enemy_dead) {
                    check("enemy_hidden_during_death",!enemy->is_visible());
                    query("hidden_enemy_dead_alive",[&]{return enemy->is_alive();});
                    query("hidden_health_dead",[&]{return enemy->health();});
                    enemy_died=round; enemy_dead=true;
                } else if (alive&&enemy_dead&&!enemy_returned) {
                    query("hidden_enemy_respawn_alive",[&]{return enemy->is_alive();});
                    std::printf("CT_RESPAWN enemy_ticks=%u base_setting=%d observation_min=%d observation_max=%d\n",round-enemy_died,constants::respawn_time,constants::respawn_time,constants::respawn_time+1);
                    check("enemy_respawn_observation_bound",round-enemy_died>=static_cast<unsigned>(constants::respawn_time)&&round-enemy_died<=static_cast<unsigned>(constants::respawn_time+1));
                    enemy_returned=true;
                }
                if (!ally->is_alive()&&!ally_dead) {
                    query("ally_dead_alive",[&]{return ally->is_alive();});
                    ally_died=round; ally_dead=true;
                } else if (ally->is_alive()&&ally_dead&&!ally_returned) {
                    query("ally_respawn_alive",[&]{return ally->is_alive();});
                    std::printf("CT_RESPAWN ally_ticks=%u base_setting=%d observation_min=%d observation_max=%d\n",round-ally_died,constants::respawn_time,constants::respawn_time,constants::respawn_time+1);
                    check("ally_respawn_observation_bound",round-ally_died>=static_cast<unsigned>(constants::respawn_time)&&round-ally_died<=static_cast<unsigned>(constants::respawn_time+1));
                    ally_returned=true;
                }
            } else if (sacrifice&&target) {
                if (!self().is_alive()) stopped=true;
                if (!stopped&&self().is_alive()) {
                    if (target->is_visible()&&self().position().chebyshev_distance(target->position())<=self().attack_range()&&self().can_attack()&&round_number()==round) self().attack(*target);
                    else if (self().can_move()&&round_number()==round) self().move_towards(target->spawn_position());
                }
            } else if (self().is_alive()&&self().can_move()&&!vision::has_champion(park)&&!vision::has_camp(park)&&round_number()==round) self().move_towards(park);
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
