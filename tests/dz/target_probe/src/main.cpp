#include <cambc.h>
#include <algorithm>
#include <cstdio>
#include "config.h"
using namespace cambc;
bool ring(vec2 target,int radius,unsigned round) {
    auto p=self().position(); if (!self().can_move()||p.chebyshev_distance(target)==radius) return false;
    auto blocked=map::walls()|map::holes()|map::altars()|map::spawn_region(team::enemy)|vision::camp_tiles()|vision::champion_tiles();
    blocked.set(p,false); bitboard roots,visited;
    for (int dx=-radius;dx<=radius;++dx) for (int dy=-radius;dy<=radius;++dy) {
        auto q=target+vec2{dx,dy};
        if (std::max(std::abs(dx),std::abs(dy))==radius&&map::is_in_bounds(q)&&!blocked.is_set(q)) roots.set(q);
    }
    distance_field route; route.compute(blocked,roots,visited);
    for (auto delta:route.next_moves_from(p)) if (round_number()==round) return self().move_absolute(p+delta);
    return false;
}
int main() {
    if (is_draft()) {
        std::array picks{champion_draft::vendetta,champion_draft::marcella,champion_draft::ryth,
            champion_draft::vesper_vale,champion_draft::varg};
        if constexpr (DZ_REVERSE_DRAFT) std::swap(picks[0],picks[1]);
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    const bool leader=self().champion_name()==champion_type::vendetta,partner=self().champion_name()==champion_type::marcella;
    std::vector<camp> camps;
    for (auto& g:map::camp_groups()) for (auto& c:g.camps()) camps.push_back(c);
    auto home=map::spawn_region(team::ally).positions().front();
    auto park=vec2{std::clamp(home.x+(home.x<map::width()/2?1:-1)*(8+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),home.y};
    auto allies=champions(team::ally);
    std::optional<champion> other;
    for (auto& c:allies) if (c.champion_name()==champion_type::marcella) other=c;
    int selected=-1,phase=1,started=0; float hp_a=-1,hp_b=-1; bool partner_attacked=false;
    if (leader) {
        int nearest=65535;
        for (unsigned i=0;i<camps.size();++i) if (camps[i].is_elk()) {
            int distance=static_cast<int>(self().position().chebyshev_distance(camps[i].spawn_position()));
            if (distance<nearest) { nearest=distance; selected=i; }
        }
        if (selected<0) std::printf("ERROR no elk target fixture\n");
        std::printf("CT11_HANDLES a=%u b=%u\n",static_cast<unsigned>(static_cast<handle_champion_t>(self())),
            static_cast<unsigned>(static_cast<handle_champion_t>(*other)));
    }
    for (;;) {
        const auto round=round_number();
        try {
            std::uint64_t word{}; shared_memory.read(0,std::span<std::uint64_t>(&word,1));
            if (leader&&selected>=0) word=static_cast<unsigned>(selected+1)|(static_cast<std::uint64_t>(phase)<<32);
            if (leader&&round_number()==round) shared_memory.write(0,std::span<const std::uint64_t>(&word,1));
            int index=static_cast<int>(word&0xffffffffu)-1;
            if (index>=0&&(leader||partner)&&self().is_alive()&&round>=15) {
                auto& target=camps.at(index); auto center=target.spawn_position(); auto p=self().position();
                int active_phase=static_cast<int>(word>>32);
                if (leader) {
                    if (!other->is_visible()) {
                        if (phase==1) ring(center,1,round);
                        if (round_number()==round) end_turn();
                        continue;
                    }
                    auto b=other->position(); float a_hp=self().health(),b_hp=other->health();
                    if (phase==2||phase==4||phase==6) {
                        float a_incoming=0,b_incoming=0;
                        for (auto& c:vision::camps()) if (c.is_awake()&&c.strength()>0) {
                            if (p.chebyshev_distance(c.position())<=c.attack_range()) a_incoming+=c.strength();
                            if (b.chebyshev_distance(c.position())<=c.attack_range()) b_incoming+=c.strength();
                        }
                        std::printf("CT11_TARGET phase=%d round=%u da=%.0f db=%.0f ia=%.0f ib=%.0f dista=%u distb=%u\n",
                            phase,round,hp_a<0?0:hp_a-a_hp,hp_b<0?0:hp_b-b_hp,a_incoming,b_incoming,
                            static_cast<unsigned>(p.chebyshev_distance(center)),static_cast<unsigned>(b.chebyshev_distance(center)));
                    }
                    hp_a=a_hp; hp_b=b_hp;
                    if (phase==1) {
                        if (p.chebyshev_distance(center)!=1) ring(center,1,round);
                        else if (b.chebyshev_distance(center)==2 && target.is_visible()&&self().can_attack()&&round_number()==round) {
                            self().attack(target); phase=2; started=round;
                        }
                    } else if ((phase==2||phase==4||phase==6)&&round>=static_cast<unsigned>(started+6)) {
                        ++phase;
                    } else if (phase==3) {
                        if (p.chebyshev_distance(center)!=2) ring(center,2,round);
                        else if (b.chebyshev_distance(center)==1) { phase=4; started=round; }
                    } else if (phase==5) {
                        if (p.chebyshev_distance(center)!=1) ring(center,1,round);
                        else if (b.chebyshev_distance(center)==1) { phase=6; started=round; }
                    } else if (phase>=7&&self().can_move()&&p!=home&&!vision::has_champion(home)&&round_number()==round) self().move_towards(home);
                } else if (active_phase==1) ring(center,2,round);
                else if (active_phase==3||active_phase==4||active_phase==5||active_phase==6) {
                    ring(center,1,round);
                    if (active_phase==5&&!partner_attacked&&p.chebyshev_distance(center)==1&&self().can_attack()&&round_number()==round) {
                        self().attack(target); partner_attacked=true;
                        std::printf("CT11_SECOND_ATTACKER body=%u round=%u\n",static_cast<unsigned>(static_cast<handle_champion_t>(self())),round);
                    }
                }
                else if (active_phase>=7&&p!=home&&self().can_move()&&!vision::has_champion(home)&&round_number()==round) self().move_towards(home);
            } else if (!leader&&!partner&&self().is_alive()&&!vision::has_champion(park)&&!vision::has_camp(park)&&
                !map::walls().is_set(park)&&!map::holes().is_set(park)&&!map::altars().is_set(park)&&
                !map::spawn_region(team::enemy).is_set(park)&&self().can_move()&&round_number()==round) self().move_towards(park);
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
