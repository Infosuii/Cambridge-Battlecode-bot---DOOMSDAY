#include <cambc.h>
#include <cstdio>
#include <algorithm>
#include <vector>

using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
bool walk_to(vec2 target,unsigned round) {
    auto p=self().position();
    if (p==target || !self().can_move()) return false;
    bool occupied=vision::has_camp(target)||vision::has_champion(target);
    if (occupied&&p.chebyshev_distance(target)<=1) return false;
    if (round_number()!=round) return false;
    return self().move_towards(target);
}
bool leave_group(const map::camp_group& g,unsigned round) {
    auto p=self().position();
    for (int dx=-1;dx<=1;++dx) for (int dy=-1;dy<=1;++dy) {
        auto q=p+vec2{dx,dy};
        if (q==p||!map::is_in_bounds(q)||map::walls().is_set(q)||map::holes().is_set(q)||map::altars().is_set(q)||
            map::spawn_region(team::enemy).is_set(q)||vision::has_champion(q)||vision::has_camp(q)) continue;
        bool member=false;
        for (auto& c:g.camps()) if (q==c.spawn_position()) member=true;
        if (!member&&round_number()==round) return self().move_absolute(q);
    }
    return false;
}
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vesper_vale,champion_draft::marcella,champion_draft::ryth,
            champion_draft::vendetta,champion_draft::heart_of_ruin};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    auto groups=map::camp_groups(); auto type=self().champion_name();
    bool primary=type==champion_type::vesper_vale,partner=type==champion_type::marcella;
    auto corner=map::spawn_region(team::ally).positions().front();
    auto park=vec2{std::clamp(corner.x+(corner.x<map::width()/2?1:-1)*
        (8+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),
        corner.y<map::height()/2?0:map::height()-1};
    int selected=-1,stage=0,captured=0,released=0;
    std::vector<bool> defeated;
    bool partner_checked=false;
    if (primary) {
        int best=65535;
        for (unsigned i=0;i<groups.size();++i) {
            auto& g=groups[i]; bool clusters=true;
            for (auto& c:g.camps()) clusters&=c.is_gem_cluster()||c.is_gold_cluster();
            if (!clusters||g.camps().size()<2||g.gem_value()==0) continue;
            int d=static_cast<int>(self().position().chebyshev_distance(g.camps()[0].spawn_position()));
            if (d<best) { best=d; selected=i; }
        }
        if (selected<0) std::printf("CT_SETUP_FAILURE no_multi_tile_cluster\n");
    }
    for (;;) {
        auto round=round_number();
        try {
            std::uint64_t word{}; shared_memory.read(0,std::span<std::uint64_t>(&word,1));
            if (primary&&selected>=0&&stage==0) {
                word=(std::uint64_t{1}<<32)|static_cast<unsigned>(selected+1);
                if (round_number()==round) shared_memory.write(0,std::span<const std::uint64_t>(&word,1));
                stage=1;
            }
            int index=static_cast<int>(word&0xffffffffu)-1,phase=static_cast<int>(word>>32);
            if (index>=0&&(primary||partner)) {
                auto& g=groups.at(index);
                if (defeated.size()!=g.camps().size()) defeated.assign(g.camps().size(),false);
                for (unsigned i=0;i<g.camps().size();++i) {
                    auto& c=g.camps()[i];
                    if (vision::in_vision(c.spawn_position())) defeated[i]=c.is_dead();
                }
                if (primary&&stage==1) {
                    if (self().gem_count()>0) {
                        check("split_primary_low_handle_remainder",self().gem_count()==(g.gem_value()+1)/2);
                        captured=round; stage=2;
                        word=(std::uint64_t{2}<<32)|static_cast<unsigned>(index+1);
                        if (round_number()==round) shared_memory.write(0,std::span<const std::uint64_t>(&word,1));
                    } else {
                        const camp* target=nullptr; int nearest=65535;
                        for (auto& c:g.camps()) if (c.is_visible()&&c.is_alive()) {
                            int distance=static_cast<int>(self().position().chebyshev_distance(c.position()));
                            if (distance<nearest) { nearest=distance; target=&c; }
                        }
                        if (target) {
                            if (self().position().chebyshev_distance(target->position())<=self().attack_range()&&self().can_attack()) {
                                if (round_number()==round) self().attack(*target);
                                if (target->is_alive()&&self().abilities()[0].is_ready()&&round_number()==round) {
                                    self().abilities()[0].use();
                                    if (target->is_alive()&&self().can_attack()&&round_number()==round) self().attack(*target);
                                }
                            } else walk_to(target->spawn_position(),round);
                        } else {
                            vec2 closest=g.camps()[0].spawn_position(); int distance=65535;
                            bool group_visible=false;
                            for (auto& c:g.camps()) if (vision::in_vision(c.spawn_position())) group_visible=true;
                            bool reward=group_visible&&std::holds_alternative<map::camp_group_reward_available>(g.state());
                            for (unsigned i=0;i<g.camps().size();++i) {
                                if (!reward&&defeated[i]) continue;
                                auto& c=g.camps()[i];
                                auto q=c.spawn_position();
                                int d=static_cast<int>(self().position().chebyshev_distance(q));
                                if (d<distance&&!vision::has_champion(q)) { distance=d; closest=q; }
                            }
                            walk_to(closest,round);
                        }
                    }
                } else if (primary&&stage==2&&round>=static_cast<unsigned>(captured+g.max_respawn_timer()+3)) {
                    auto state=g.state(); auto* waiting=std::get_if<map::camp_group_respawning>(&state);
                    check("occupied_spawn_delays_respawn",waiting&&waiting->timer<=0);
                    word=(std::uint64_t{3}<<32)|static_cast<unsigned>(index+1);
                    if (round_number()==round) shared_memory.write(0,std::span<const std::uint64_t>(&word,1));
                    if (leave_group(g,round)) { stage=3; released=round; }
                } else if (primary&&stage==3) {
                    if (std::holds_alternative<map::camp_group_alive>(g.state())) {
                        check("vacated_spawn_respawns",round-released<=2); stage=4;
                    } else if (round>static_cast<unsigned>(released+4)) { check("vacated_spawn_respawns",false); stage=4; }
                } else if (partner) {
                    if (phase==1) walk_to(g.camps()[1].spawn_position(),round);
                    if (phase>=2&&!partner_checked) {
                        check("split_partner_share",self().gem_count()==g.gem_value()/2); partner_checked=true;
                    }
                    if (phase==3) {
                        bool onsite=false;
                        for (auto& c:g.camps()) if (self().position()==c.spawn_position()) onsite=true;
                        if (onsite) leave_group(g,round);
                    }
                }
                if (primary&&round%40==0) std::printf("CT24_STATE round=%u stage=%d pos=%d,%d gems=%u members=%zu\n",
                    round,stage,self().position().x,self().position().y,self().gem_count(),g.camps().size());
            } else if (!primary&&!partner&&self().can_move()&&!vision::has_champion(park)) walk_to(park,round);
        } catch (const std::exception& e) { std::printf("ERROR %s\n",e.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
