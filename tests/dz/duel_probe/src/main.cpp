#include <cambc.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <optional>
#include <vector>
#include "config.h"
#include "duel.h"
#include "fight.h"
using namespace cambc;
void check(const char* name,bool pass){std::printf("CT_CHECK name=%s pass=%d\n",name,pass);}
dz::DuelActor kit(const champion& c,bool next_owner_start){
    dz::DuelActor p;p.hp=c.health();p.max_hp=c.max_health();p.damage=c.strength();
    p.first_can_cast=next_owner_start||c.can_cast(); // controlled actors have no CC/restrictions
    if(c.champion_name()==champion_type::heart_of_ruin)p.missing_health_bonus=constants::passive_abilities::heart_of_ruin_missing_health_damage_max_bonus;
    auto buffs=c.buffs();if(buffs.has<buff_shield>()){
        auto b=buffs.get<buff_shield>();p.existing=true;p.existing_value=b.value;p.existing_duration=static_cast<unsigned>(std::max(0,b.duration));
    }
    for(const auto& a:c.abilities()){
        if(a.is_attack_reset()&&a.info()){
            p.reset_cd=static_cast<unsigned>(std::max(0,a.cooldown()));p.reset_period=static_cast<unsigned>(std::max(0,std::get<ability_attack_reset>(*a.info()).max_cooldown));
        }
        if(a.is_shield()&&a.info()){
            const auto info=std::get<ability_shield>(*a.info());p.shield_cd=static_cast<unsigned>(std::max(0,a.cooldown()));
            p.shield_period=static_cast<unsigned>(std::max(0,info.max_cooldown));p.shield_duration=static_cast<unsigned>(std::max(0,info.duration));p.shield_amount=a.shield_amount();
        }
    }return p;
}
struct Sample{dz::DuelProjection p;unsigned round=0,basics=0,resets=0,shields=0;};
int main(){
    constexpr bool heart=CT_OPPONENT?DZ_DUEL_OTHER_HEART:DZ_DUEL_HEART;
    constexpr bool other_heart=CT_OPPONENT?DZ_DUEL_HEART:DZ_DUEL_OTHER_HEART;
    constexpr int slot=CT_OPPONENT?DZ_DUEL_OTHER_SLOT:DZ_DUEL_SLOT;
    constexpr int other_slot=CT_OPPONENT?DZ_DUEL_SLOT:DZ_DUEL_OTHER_SLOT;
    if(is_draft()){
        auto picks=std::array{heart?champion_draft::heart_of_ruin:champion_draft::varg,
            champion_draft::vesper_vale,champion_draft::marcella,champion_draft::vendetta,champion_draft::ryth};
        if(slot)std::swap(picks[0],picks[1]);
        for(;;){try{draft::pick(picks.at(draft::current_draft(team::ally).size()));}catch(...){}end_turn();}
    }
    const bool actor=self().champion_name()==(heart?champion_type::heart_of_ruin:champion_type::varg);
    const bool left=map::spawn_region(team::ally).positions().front().x<map::width()/2;
    const vec2 stand{map::width()/2+(left?-1:0),map::height()/2-1},other_stand{map::width()/2+(left?0:-1),map::height()/2-1};
    std::optional<champion> enemy;std::vector<Sample> samples;
    unsigned basics=0,resets=0,shields=0;bool finished=false,isolated=true,stationary=true,shield_sample=false,zero_sample=false;
    float last_enemy_hp=0;
    const auto capture=[&](unsigned round,const dz::DuelActor& a,const dz::DuelActor& b){
        const bool ours_first=left?(round%2==1):(round%2==0);
        const auto p=dz::stationary_duel(a,b,{slot==other_slot,ours_first},96);samples.push_back({p,round,basics,resets,shields});
        const dz::Fighter old_a[]{{a.hp,a.damage}},old_b[]{{1.25f*b.hp,b.damage}};
        const auto old=dz::simulate_fight(old_a,old_b);
        std::printf("CT_DUEL_QUOTE sample=%zu heart=%d other=%d round=%u status=%d rounds=%u hp=%.4f enemy_hp=%.4f basics=%u shields=%u resets=%u defender_zero=%d old_won=%d\n",
            samples.size()-1,heart,other_heart,round,static_cast<int>(p.status),p.owner_rounds,p.our_hp,p.enemy_hp,p.ours.basics,p.ours.shields,p.ours.resets,
            b.existing&&b.existing_duration==0,old.won());
    };
    const auto finish=[&](unsigned round,bool won){
        const float hp=self().is_alive()?self().health():0;
        for(unsigned k=0;k<samples.size();++k){const auto& s=samples[k];const auto& p=s.p;
            check("duel_outcome",p.status==(won?dz::DuelStatus::Won:dz::DuelStatus::Dead));
            check("duel_elapsed",round-s.round+1==p.owner_rounds);check("duel_hp",std::abs(hp-p.our_hp)<.03f&&std::abs(last_enemy_hp-p.enemy_hp)<.03f);
            check("duel_basics",basics-s.basics==p.ours.basics);check("duel_casts",resets-s.resets==p.ours.resets&&shields-s.shields==p.ours.shields);
            check("duel_isolated",isolated&&stationary);
            std::printf("CT_DUEL_RESULT sample=%u won=%d rounds=%u hp=%.4f enemy_hp=%.4f basics=%u shields=%u resets=%u\n",k,won,round-s.round+1,hp,last_enemy_hp,basics-s.basics,shields-s.shields,resets-s.resets);
        }finished=true;
    };
    for(;;){const auto round=round_number();try{
        if(actor&&!finished){
            if(!self().is_alive()){if(samples.empty())std::printf("ERROR died before quote\n");else finish(round,false);finished=true;}
            else if(!samples.empty()&&enemy&&!enemy->is_alive()){last_enemy_hp=0;finish(round,true);}
            else if(samples.empty()&&self().position()!=stand){if(self().can_move())self().move_towards(stand);}
            else {
                if(!enemy)for(const auto& c:vision::champions(team::enemy))if(c.champion_name()==(other_heart?champion_type::heart_of_ruin:champion_type::varg)&&c.position()==other_stand)enemy=c;
                if(enemy&&enemy->is_alive()&&enemy->is_visible()&&self().can_attack()){
                    stationary&=self().position()==stand&&enemy->position()==other_stand;
                    for(auto side:{team::ally,team::enemy})for(const auto& c:vision::champions(side))
                        if(static_cast<handle_champion_t>(c)!=static_cast<handle_champion_t>(self())&&static_cast<handle_champion_t>(c)!=static_cast<handle_champion_t>(*enemy)&&c.is_alive()&&
                           std::min(c.position().chebyshev_distance(stand),c.position().chebyshev_distance(other_stand))<=6)isolated=false;
                    for(const auto& c:vision::camps())if(c.is_awake()&&c.strength()>0&&self().position().chebyshev_distance(c.position())<=c.attack_range())isolated=false;
                    if(DZ_DUEL_PRECAST&&samples.empty()&&round<30){
                        if(round==29){
                            bool success=false;for(const auto& a:self().abilities())if(a.is_shield()&&a.is_ready()&&self().can_cast()&&a.use()){++shields;success=true;}
                            check("duel_precast",success);std::printf("CT_DUEL_PRECAST round=%u success=%d\n",round,success);
                        }
                        if(round_number()==round)end_turn();continue;
                    }
                    const auto a=kit(self(),false),b=kit(*enemy,true);const bool active=a.existing||b.existing,zero=b.existing&&b.existing_duration==0;
                    if(samples.empty()||(!shield_sample&&active)||(!zero_sample&&zero)){capture(round,a,b);shield_sample|=active;zero_sample|=zero;}
                    if(round_number()==round){self().attack(*enemy);++basics;}
                    bool cast=false;
                    for(const auto& ability:self().abilities()){
                        if(enemy->is_alive()&&ability.is_attack_reset()&&ability.is_ready()&&self().can_cast()&&ability.use()){
                            ++resets;cast=true;if(self().can_attack()){self().attack(*enemy);++basics;}
                        }
                        if(enemy->is_alive()&&!cast&&ability.is_shield()&&ability.is_ready()&&self().can_cast()&&self().health()<.85f*self().max_health()&&!self().buffs().has<buff_shield>()&&ability.use()){++shields;cast=true;}
                    }
                    last_enemy_hp=enemy->is_alive()?enemy->health():0;if(!enemy->is_alive())finish(round,true);
                }
            }
        }
    }catch(const std::exception& e){std::printf("ERROR %s\n",e.what());}
    if(round_number()!=round)continue;end_turn();}
}
