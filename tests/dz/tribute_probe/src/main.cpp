#include <cambc.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include "config.h"
using namespace cambc;
void check(const char* name,bool passed) { std::printf("CT_CHECK name=%s pass=%d\n",name,passed); }
bool walk(vec2 target,unsigned round) {
    auto p=self().position();
    if (!self().can_move()||p==target) return false;
    if (p.chebyshev_distance(target)<=1&&(vision::has_champion(target)||vision::has_camp(target))) return false;
    return round_number()==round&&self().move_towards(target);
}
bool approach(vec2 target,int range,unsigned round) {
    auto p=self().position();
    auto blocked=map::walls()|map::holes()|map::altars()|map::spawn_region(team::enemy)|vision::champion_tiles()|vision::camp_tiles();
    blocked.set(p,false); bitboard roots,visited;
    for (int dx=-range;dx<=range;++dx) for (int dy=-range;dy<=range;++dy) {
        auto q=target+vec2{dx,dy};
        if (range==3&&std::max(std::abs(dx),std::abs(dy))!=3) continue;
        if (map::is_in_bounds(q)&&!blocked.is_set(q)) roots.set(q);
    }
    distance_field field; field.compute(blocked,roots,visited);
    for (auto delta:field.next_moves_from(p)) if (round_number()==round) return self().move_absolute(p+delta);
    return false;
}
void farm(const map::camp_group& g,unsigned round) {
    const camp* target=nullptr; int distance=65535;
    for (auto& c:g.camps()) if (c.is_visible()&&c.is_alive()) {
        int d=static_cast<int>(self().position().chebyshev_distance(c.position()));
        if (d<distance) { distance=d; target=&c; }
    }
    if (target) {
        if (distance<=self().attack_range()&&self().can_attack()&&round_number()==round) self().attack(*target);
        else walk(target->spawn_position(),round);
    } else {
        vec2 closest=g.camps()[0].spawn_position(); distance=65535;
        for (auto& c:g.camps()) {
            auto q=c.spawn_position(); int d=static_cast<int>(self().position().chebyshev_distance(q));
            if (d<distance&&!vision::has_champion(q)) { closest=q; distance=d; }
        }
        walk(closest,round);
    }
}
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vesper_vale,champion_draft::marcella,champion_draft::ryth,
            champion_draft::vendetta,champion_draft::heart_of_ruin};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    bool actor=self().champion_name()==champion_type::vesper_vale;
    auto altar=map::altars().positions().front();
    auto groups=map::camp_groups(); int group=-1,gold_group=-1,stage=0,started=0,bag=0,expected_ticks=0;
    auto corner=map::spawn_region(team::ally).positions().front();
    auto park=vec2{std::clamp(corner.x+(corner.x<map::width()/2?1:-1)*(10+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),corner.y};
    bool bought=false,range_checked=false; int hits=0;
    if (actor) {
        int best=65535,best_gold=65535;
        for (unsigned i=0;i<groups.size();++i) {
            bool harmless=true; for (auto& c:groups[i].camps()) harmless&=c.is_gem_cluster()||c.is_gold_cluster();
            if (!harmless) continue;
            int distance=static_cast<int>(self().position().chebyshev_distance(groups[i].camps()[0].spawn_position()));
            if (groups[i].gem_value()>0&&distance<best) { best=distance; group=i; }
            if (groups[i].gold_value()>=consumable_type::altar_lock.cost()&&distance<best_gold) { best_gold=distance; gold_group=i; }
        }
        std::printf("CT17_SETUP gems=%d gold=%d opponent=%d\n",group,gold_group,CT_OPPONENT);
        if (group<0||gold_group<0) std::printf("ERROR no harmless reward fixture\n");
    }
    for (;;) {
        auto round=round_number();
        try {
            if (!actor) { if (!vision::has_champion(park)) walk(park,round); }
            else if (!bought) {
                if (self().can_buy(consumable_type::altar_lock)&&round_number()==round) { self().buy(consumable_type::altar_lock); bought=true; }
                else if (self().gold_count()>=consumable_type::altar_lock.cost()) {
                    if (!self().is_recalling()&&round_number()==round) self().recall();
                } else if (gold_group>=0) farm(groups[gold_group],round);
            } else if constexpr (CT_OPPONENT) {
                if (stage==0) {
                    if (self().position().chebyshev_distance(altar)>2) approach(altar,2,round);
                    else for (auto& e:vision::champions(team::enemy)) if (e.is_submitting_gems()&&round_number()==round) {
                        self().consumables()[consumable_type::altar_lock].use(altar); stage=1; break;
                    }
                }
            } else if (group>=0) {
                if (stage==0) {
                    if (self().gem_count()>0) stage=1;
                    else farm(groups[group],round);
                } else if (stage==1) {
                    if (!range_checked&&self().position().chebyshev_distance(altar)!=3) {
                        approach(altar,3,round);
                        if (round_number()==round) end_turn();
                        continue;
                    }
                    if (!range_checked&&self().position().chebyshev_distance(altar)==3) {
                        bool rejected=false;
                        try { if (round_number()==round) self().consumables()[consumable_type::altar_lock].use(altar); }
                        catch (const error& e) { rejected=true; std::printf("CT17 range_three_code=%d\n",static_cast<int>(e.code())); }
                        check("lock_range_three_rejected",rejected&&self().consumables()[consumable_type::altar_lock].count()==1);
                        range_checked=true;
                    }
                    if (self().position().chebyshev_distance(altar)>1) approach(altar,1,round);
                    else if (round_number()==round) { bag=self().gem_count(); self().submit_gems(altar); stage=2; }
                } else if (stage==2) {
                    auto locks=vision::altar_locks(team::enemy);
                    if (!locks.empty()) {
                        check("lock_interrupts_channel",!self().is_submitting_gems());
                        check("lock_keeps_carried_gems",self().gem_count()==static_cast<unsigned>(bag));
                        if (round_number()==round) self().consumables()[consumable_type::altar_lock].use(altar);
                        check("both_team_locks_visible",vision::altar_lock_tiles(team::ally).is_set(altar)&&vision::altar_lock_tiles(team::enemy).is_set(altar));
                        if (round_number()==round) self().submit_gems(altar);
                        auto after=vision::altar_locks(team::enemy);
                        check("submit_into_lock_hits_once",after.size()==1&&after[0].hits_remaining()==constants::altar_lock_hits-1&&!self().is_submitting_gems());
                        hits=1; stage=3;
                    }
                } else if (stage==3) {
                    auto locks=vision::altar_locks(team::enemy);
                    if (!locks.empty()&&self().can_attack()&&round_number()==round) { self().attack(locks.front()); ++hits; }
                    if (vision::altar_locks(team::enemy).empty()) {
                        check("enemy_lock_removed_five_hits",hits==static_cast<int>(constants::altar_lock_hits)); stage=4;
                    }
                } else if (stage==4&&round_number()==round) {
                    expected_ticks=std::max(constants::submit_gem_minimum_duration,constants::submit_gem_base_duration+
                        static_cast<int>(std::ceil(bag*constants::submit_gem_duration_multiplier)));
                    self().submit_gems(altar); started=round; stage=5;
                } else if (stage==5&&!self().is_submitting_gems()) {
                    check("tribute_completes",self().gem_count()==0&&global_submitted_gems(team::ally)==static_cast<unsigned>(bag));
                    check("tribute_duration",round-started==static_cast<unsigned>(expected_ticks)); stage=6;
                }
                if (round%40==0&&stage<6) std::printf("CT17_STATE round=%u stage=%d pos=%d,%d bag=%u\n",round,stage,self().position().x,self().position().y,self().gem_count());
            }
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
