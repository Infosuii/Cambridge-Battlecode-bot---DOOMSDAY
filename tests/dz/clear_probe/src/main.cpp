#include <cambc.h>
#include <algorithm>
#include <cstdio>
#include "basic_clear.h"
#include "config.h"
using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vendetta,champion_draft::vesper_vale,champion_draft::marcella,
            champion_draft::ryth,champion_draft::heart_of_ruin};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    const bool actor=self().champion_name()==(DZ_RANGED?champion_type::vesper_vale:champion_type::vendetta);
    auto corner=map::spawn_region(team::ally).positions().front();
    const int sign=corner.x<map::width()/2?1:-1;
    auto park=vec2{std::clamp(corner.x+sign*(10+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),corner.y};
    std::optional<map::camp_group> group;
    std::vector<camp> members;
    std::vector<bool> dead;
    bool harmless=true;
    if (actor) {
        int nearest=65535;
        for (auto& g:map::camp_groups()) {
            int distance=65535;
            for (auto& c:g.camps()) distance=std::min(distance,static_cast<int>(corner.chebyshev_distance(c.spawn_position())));
            if (distance<nearest) { nearest=distance; group=g; }
        }
        if (group) {
            for (auto& c:group->camps()) { members.push_back(c); harmless&=c.base_stats().base_strength==0; }
            dead.assign(members.size(),false);
        } else std::printf("ERROR missing clear group\n");
    }
    bool started=false,finished=false,hit_damage_ok=true,health_steps_ok=true,isolated=true,shape_ok=true;
    unsigned first=0,attacks=0,moves=0; float start_hp=0,previous_hp=0,incoming=0;
    dz::AttackWork work;
    dz::StationaryDuel duel;
    for (;;) {
        auto round=round_number();
        try {
            if (!actor) {
                if (self().is_alive()&&self().can_move()&&!vision::has_champion(park)&&!vision::has_camp(park)&&round_number()==round) self().move_towards(park);
            } else if (group&&!finished) {
                if (!self().is_alive()) {
                    if (started) {
                        if (incoming<=0) { std::printf("ERROR unexpected death without incoming camp damage\n"); finished=true; end_turn(); continue; }
                        const auto lethal_tick=static_cast<unsigned>(std::ceil(static_cast<double>(start_hp)/incoming));
                        check("clear_outcome",!duel.survives);
                        check("clear_attack_count",attacks==lethal_tick&&attacks<work.attacks);
                        check("clear_elapsed",round-first==lethal_tick&&moves==0);
                        check("clear_damage",health_steps_ok);
                        check("clear_hit_damage",hit_damage_ok);
                        check("clear_isolated",isolated&&shape_ok);
                        std::printf("CT_CLEAR_RESULT outcome=dead attacks=%u predicted=%u elapsed=%u moves=%u\n",attacks,work.attacks,round-first,moves);
                    } else std::printf("ERROR died before clear began\n");
                    finished=true;
                } else {
                    auto p=self().position();
                    if (started) health_steps_ok&=previous_hp-self().health()==incoming;
                    unsigned awake=0;
                    for (auto& c:vision::camps()) if (c.is_awake()&&c.strength()>0&&p.chebyshev_distance(c.position())<=c.attack_range()) ++awake;
                    isolated&=awake<=static_cast<unsigned>(!harmless);
                    const camp* target=nullptr; int distance=65535;
                    for (unsigned i=0;i<members.size();++i) {
                        auto& c=members[i];
                        if (vision::in_vision(c.spawn_position())) dead[i]=c.is_dead();
                        if (dead[i]) continue;
                        int d=static_cast<int>(p.chebyshev_distance(c.spawn_position()));
                        if (d<distance) { target=&c; distance=d; }
                    }
                    // Single damaging camps are tested at a fixed adjacent tile,
                    // avoiding ranged immunity from standing outside camp range.
                    auto stand=members[0].spawn_position()+vec2{-sign,0};
                    if (!harmless&&!started&&p!=stand) {
                        if (self().can_move()&&round_number()==round) self().move_towards(stand);
                    } else if (target&&target->is_visible()&&distance<=self().attack_range()&&self().can_attack()) {
                        float hit=self().strength()*self().base_stats().camp_damage_multiplier;
                        if (!started) {
                            first=round; start_hp=self().health();
                            incoming=harmless?0:members[0].strength();
                            std::vector<dz::BasicTarget> targets;
                            for (auto& c:members) targets.push_back({c.base_stats().base_health,hit});
                            work=dz::basic_attack_work(targets);
                            if (!harmless) duel=dz::stationary_duel(start_hp,{members[0].health(),hit},incoming);
                            shape_ok&=work.complete()&&(harmless||members.size()==1);
                            std::printf("CT_CLEAR_START ranged=%d round=%u members=%zu hp=%.0f camp_hp=%.0f hit=%.0f incoming=%.0f predicted=%u survives=%d\n",
                                DZ_RANGED,round,members.size(),start_hp,members[0].base_stats().base_health,hit,incoming,work.attacks,harmless||duel.survives);
                            started=true;
                        }
                        auto before=target->health();
                        if (round_number()==round) { self().attack(*target); ++attacks; }
                        // Defeated camps are not visible; query through their spawn
                        // visibility, and never treat a disappeared live camp as dead.
                        float after=target->is_dead()?0:target->health();
                        hit_damage_ok&=before-after==std::min(before,hit);
                        for (unsigned i=0;i<members.size();++i) if (vision::in_vision(members[i].spawn_position())) dead[i]=members[i].is_dead();
                        if (std::all_of(dead.begin(),dead.end(),[](bool x){return x;})) {
                            check("clear_outcome",harmless||duel.survives);
                            check("clear_attack_count",attacks==work.attacks);
                            check("clear_elapsed",round-first==attacks+moves-1);
                            check("clear_damage",health_steps_ok&&start_hp-self().health()==(harmless?0:duel.future_damage_for_clear));
                            check("clear_hit_damage",hit_damage_ok);
                            check("clear_isolated",isolated&&shape_ok);
                            std::printf("CT_CLEAR_RESULT outcome=kill attacks=%u predicted=%u elapsed=%u moves=%u\n",attacks,work.attacks,round-first,moves);
                            finished=true;
                        }
                    } else if (target&&self().can_move()&&round_number()==round) {
                        if (self().move_towards(target->spawn_position())&&started) ++moves;
                    }
                    if (started) previous_hp=self().health();
                }
            }
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
