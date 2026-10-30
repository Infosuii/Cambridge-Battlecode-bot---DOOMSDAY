#include <cambc.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <optional>
#include <vector>
#include "config.h"
#include "shield_clear.h"
using namespace cambc;
void check(const char* name,bool pass){std::printf("CT_CHECK name=%s pass=%d\n",name,pass);}
struct Sample {
    dz::ShieldClearInput input;dz::ShieldClearProjection forecast;
    unsigned round=0,basics=0,casts=0,resets=0;
};
int main(){
    if(is_draft()) {
        const std::array picks{DZ_SHIELD_HEART?champion_draft::heart_of_ruin:champion_draft::varg,
            champion_draft::vesper_vale,champion_draft::marcella,champion_draft::vendetta,champion_draft::ryth};
        for(;;){try{draft::pick(picks.at(draft::current_draft(team::ally).size()));}catch(...){}end_turn();}
    }
    const bool actor=self().champion_name()==(DZ_SHIELD_HEART?champion_type::heart_of_ruin:champion_type::varg);
    const auto corner=map::spawn_region(team::ally).positions().front();const int sign=corner.x<map::width()/2?1:-1;
    std::optional<camp> target;
    if(actor){
        int nearest=65535;
        for(const auto& g:map::camp_groups())if(g.camps().size()==1){
            const auto c=g.camps()[0];const int d=corner.chebyshev_distance(c.spawn_position());
            if(c.base_stats().base_strength>0&&d<nearest){nearest=d;target=c;}
        }
    }
    std::vector<Sample> samples;unsigned basics=0,casts=0,resets=0;bool finished=false,isolated=true,stationary=true,existing_sample=false;
    vec2 stand;int npc_range=0;
    const auto quote=[&](unsigned round){
        Sample s;s.round=round;s.basics=basics;s.casts=casts;s.resets=resets;auto& in=s.input;
        in.hp=self().health();in.max_hp=self().max_health();in.target_hp=target->health();
        in.damage=self().strength()*self().base_stats().camp_damage_multiplier;in.incoming=target->strength();in.can_cast=self().can_cast();
        if(DZ_SHIELD_HEART)in.missing_health_bonus=constants::passive_abilities::heart_of_ruin_missing_health_damage_max_bonus;
        auto buffs=self().buffs();if(buffs.has<buff_shield>()){
            auto b=buffs.get<buff_shield>();in.existing=true;in.existing_value=b.value;in.existing_duration=static_cast<unsigned>(std::max(0,b.duration));
        }
        for(const auto& a:self().abilities()){
            if(a.is_attack_reset()&&a.info()){
                in.reset_cd=static_cast<unsigned>(std::max(0,a.cooldown()));in.reset_period=static_cast<unsigned>(std::max(0,std::get<ability_attack_reset>(*a.info()).max_cooldown));
            }
            if(a.is_shield()&&a.info()){
                const auto info=std::get<ability_shield>(*a.info());in.shield_cd=static_cast<unsigned>(std::max(0,a.cooldown()));
                in.shield_period=static_cast<unsigned>(std::max(0,info.max_cooldown));in.shield_duration=static_cast<unsigned>(std::max(0,info.duration));in.shield_amount=a.shield_amount();
            }
        }
        s.forecast=dz::shield_clear(in);samples.push_back(s);
        std::printf("CT_SHIELD_QUOTE sample=%zu heart=%d existing=%d round=%u status=%d rounds=%u loss=%.4f basics=%u shields=%u resets=%u\n",
            samples.size()-1,DZ_SHIELD_HEART,in.existing,round,static_cast<int>(s.forecast.status),s.forecast.rounds,s.forecast.loss,s.forecast.attacks,s.forecast.shields,s.forecast.resets);
    };
    const auto finish=[&](unsigned round,bool cleared){
        const float hp=self().is_alive()?self().health():0;
        for(unsigned k=0;k<samples.size();++k){const auto& s=samples[k];const auto& p=s.forecast;
            check("shield_outcome",p.status==(cleared?dz::ShieldClearStatus::Cleared:dz::ShieldClearStatus::Dead));
            check("shield_elapsed",round-s.round+1==p.rounds);check("shield_hp",std::abs(s.input.hp-hp-p.loss)<.03f);
            check("shield_basics",basics-s.basics==p.attacks);check("shield_casts",casts-s.casts==p.shields&&resets-s.resets==p.resets);
            check("shield_isolated",isolated&&stationary);
            std::printf("CT_SHIELD_RESULT sample=%u cleared=%d rounds=%u loss=%.4f basics=%u shields=%u resets=%u\n",
                k,cleared,round-s.round+1,s.input.hp-hp,basics-s.basics,casts-s.casts,resets-s.resets);
        }finished=true;
    };
    for(;;){const auto round=round_number();try{
        // Non-subjects stay on their actual spawn tiles, safely outside the
        // fixture camp's range. The spawn-region corner is not a spawn tile.
        if(actor&&!finished&&target){
            if(!self().is_alive()){if(samples.empty())std::printf("ERROR died before quote\n");else finish(round,false);finished=true;}
            else if(!samples.empty()&&target->is_dead())finish(round,true);
            else {
                stand=target->spawn_position()+vec2{-sign,0};
                if(samples.empty()&&self().position()!=stand){if(self().can_move())self().move_towards(stand);}
                else if(target->is_visible()&&self().can_attack()){
                    npc_range=target->attack_range();stationary&=self().position()==stand;
                    for(auto side:{team::ally,team::enemy})for(const auto& c:vision::champions(side))
                        if(static_cast<handle_champion_t>(c)!=static_cast<handle_champion_t>(self())&&c.is_alive()&&c.position().chebyshev_distance(target->position())<=npc_range)isolated=false;
                    unsigned awake=0;for(const auto& c:vision::camps())if(c.is_awake()&&c.strength()>0&&self().position().chebyshev_distance(c.position())<=c.attack_range())++awake;
                    isolated&=awake<=1;
                    if(samples.empty())quote(round);
                    else if(!existing_sample&&self().buffs().has<buff_shield>()){existing_sample=true;quote(round);}
                    if(round_number()==round){self().attack(*target);++basics;}
                    bool cast=false;
                    for(const auto& a:self().abilities()){
                        if(!target->is_dead()&&a.is_attack_reset()&&a.is_ready()&&self().can_cast()&&a.use()){
                            ++resets;cast=true;if(self().can_attack()){self().attack(*target);++basics;}
                        }
                        if(!target->is_dead()&&!cast&&a.is_shield()&&a.is_ready()&&self().can_cast()&&self().health()<.85f*self().max_health()&&!self().buffs().has<buff_shield>()&&a.use()){++casts;cast=true;}
                    }
                    if(target->is_dead())finish(round,true);
                }
            }
        }
    }catch(const std::exception& e){std::printf("ERROR %s\n",e.what());}
    if(round_number()!=round)continue;end_turn();}
}
