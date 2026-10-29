#include <cambc.h>
#include <algorithm>
#include <cstdio>
#include "config.h"
using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
template<class F> void query(const char* name,F read) {
    try { std::printf("CT10_QUERY name=%s accepted=1 value=%.9g code=0\n",name,static_cast<double>(read())); }
    catch (const error& error) { std::printf("CT10_QUERY name=%s accepted=0 value=0 code=%d\n",name,static_cast<int>(error.code())); }
}
bool walk(vec2 target,unsigned round,bool adjacent=false) {
    auto p=self().position();if (!self().can_move()||p==target) return false;
    // Use an actual local field: a greedy step can stall at the unrelated
    // mirrored group's camp barrier on the scripted enemy's long approach.
    auto blocked=map::walls()|map::holes()|map::altars()|map::spawn_region(team::enemy)|vision::camp_tiles()|vision::champion_tiles()|vision::teleport_tiles();
    blocked.set(p,false);bitboard roots,visited;
    if (adjacent||blocked.is_set(target)) {
        for (int dx=-1;dx<=1;++dx) for (int dy=-1;dy<=1;++dy) {
            auto q=target+vec2{dx,dy};if ((!dx&&!dy)||!map::is_in_bounds(q)||blocked.is_set(q)) continue;
            roots.set(q);
        }
    } else roots.set(target);
    if (roots.is_empty()) return false;
    distance_field path;path.compute(blocked,roots,visited);
    for (auto delta:path.next_moves_from(p)) if (round_number()==round) return self().move_absolute(p+delta);
    return false;
}
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vendetta,champion_draft::ryth,champion_draft::marcella,
            champion_draft::vesper_vale,champion_draft::heart_of_ruin};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    const auto type=self().champion_name();
    const bool observer=!CT_OPPONENT&&type==champion_type::vendetta;
    const bool actor=CT_OPPONENT&&type==champion_type::ryth;
    auto own=map::spawn_region(team::ally).positions().front();
    auto reference=map::spawn_region(CT_OPPONENT?team::enemy:team::ally).positions().front();
    bool low=own.x<map::width()/2;unsigned id=static_cast<unsigned>(static_cast<handle_champion_t>(self()));
    int px=id%3==2?1:0,py=id%3==1?1:0;
    vec2 park{low?px:map::width()-1-px,low?py:map::height()-1-py};
    std::optional<map::camp_group> group;int nearest=65535;
    if (observer||actor) for (auto& g:map::camp_groups()) {
        if (g.camps().size()!=12||!std::all_of(g.camps().begin(),g.camps().end(),[](auto& c){return c.is_gold_cluster();})) continue;
        int d=65535;for (auto& c:g.camps()) d=std::min(d,static_cast<int>(reference.chebyshev_distance(c.spawn_position())));
        if (d<nearest) { nearest=d;group=g; }
    }
    std::optional<champion> enemy_actor;
    if (observer) for (auto& c:champions(team::enemy)) if (c.champion_name()==champion_type::ryth) enemy_actor=c;
    if (observer||actor) check("single_spawn_setup",group.has_value()&&(!observer||enemy_actor.has_value()));
    vec2 edge{};bool ray=false,ready=false,done=false,receipt=false;unsigned cooldown_seen=0;
    std::vector<bool> dead(group?group->camps().size():0,false);
    unsigned seen_member=0;
    if (group) for (unsigned i=0;i<group->camps().size();++i) {
        auto x=group->camps()[i].spawn_position().x;
        auto best=group->camps()[seen_member].spawn_position().x;
        if (reference.x<map::width()/2?x>best:x<best) seen_member=i;
    }
    if (actor) std::printf("CT10_ORDER seen_member_first=%d\n",DZ_SEEN_MEMBER_FIRST);
    if (observer&&group) edge={low?map::width()-1:0,group->camps()[0].spawn_position().y};
    for (;;) {
        auto round=round_number();
        try {
            if (observer&&group&&enemy_actor&&!done) {
                unsigned count=0,live=0;
                for (auto& c:group->camps()) { count+=vision::in_vision(c.spawn_position());live+=c.is_visible(); }
                if (!ready) {
                    if (!ray) { if (self().position()==edge) ray=true;else walk(edge,round); }
                    else if (count==1) {
                        ready=true;check("single_spawn_position",true);
                        for (auto& c:group->camps()) if (vision::in_vision(c.spawn_position())) {
                            query("visible_camp_health",[&]{return c.health();});
                            check("visible_camp_full_health",c.health()==c.base_stats().base_health);
                        }
                        for (auto& c:group->camps()) if (!vision::in_vision(c.spawn_position())) { query("hidden_camp_health",[&]{return c.health();});break; }
                    } else if (count==0) walk(self().position()+vec2{low?-1:1,0},round);
                    else { std::printf("ERROR ray skipped single-spawn boundary count=%u\n",count);done=true; }
                } else {
                    auto state=group->state();auto cap=group->capture_state();
                    int code=std::holds_alternative<map::camp_group_alive>(state)?1:std::holds_alternative<map::camp_group_reward_available>(state)?2:3;
                    std::printf("CT10_SAMPLE round=%u spawns=%u live=%u group=%d capture=%d timer=%d actor_visible=%d\n",round,count,live,code,static_cast<int>(cap.state),cap.timer,enemy_actor->is_visible());
                    if (code==3&&!cooldown_seen) cooldown_seen=round;
                    if (cooldown_seen&&round>=cooldown_seen+16) done=true;
                }
            } else if (actor&&group&&round>=60&&!receipt) {
                if (self().gold_count()>=group->gold_value()) {
                    check("single_spawn_actor_receipt",self().gold_count()==group->gold_value());
                    std::printf("CT10_RECEIPT gold=%u expected=%u\n",self().gold_count(),group->gold_value());receipt=true;
                } else {
                    for (unsigned i=0;i<dead.size();++i) if (vision::in_vision(group->camps()[i].spawn_position())) dead[i]=group->camps()[i].is_dead();
                    const camp* target=nullptr;int distance=65535;
                    const camp* forced=DZ_SEEN_MEMBER_FIRST&&!dead[seen_member]?&group->camps()[seen_member]:nullptr;
                    if (forced) { target=forced;distance=static_cast<int>(self().position().chebyshev_distance(forced->spawn_position())); }
                    else for (auto& c:group->camps()) if (c.is_visible()&&c.is_alive()) {
                        int d=static_cast<int>(self().position().chebyshev_distance(c.spawn_position()));
                        if (d<distance) { distance=d;target=&c; }
                    }
                    if (target) {
                        if (target->is_visible()&&distance<=self().attack_range()&&self().can_attack()&&round_number()==round) self().attack(*target);
                        else walk(target->spawn_position(),round,true);
                    } else {
                        bool all_dead=std::all_of(dead.begin(),dead.end(),[](bool x){return x;});
                        auto next=group->camps()[0].spawn_position();distance=65535;
                        for (unsigned i=0;i<dead.size();++i) {
                            if (!all_dead&&dead[i]) continue;
                            auto q=group->camps()[i].spawn_position();int d=static_cast<int>(self().position().chebyshev_distance(q));
                            if (d<distance&&!vision::has_champion(q)) { distance=d;next=q; }
                        }
                        walk(next,round,!all_dead);
                    }
                }
            } else if (!observer&&!actor&&self().is_alive()) walk(park,round);
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
