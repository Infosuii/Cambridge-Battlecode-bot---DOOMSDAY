#pragma once
#include "objective_model.h"
namespace dz::gear {
struct Output {
    float reset_rate=0,focus_rate=0;
    // One sustained cast stream. This is an economic estimate, never burst
    // damage, a guaranteed kill, or extra HP for neutral admission.
    float rate(float strength,float focus) const {
        if(!std::isfinite(strength)||!std::isfinite(focus)||!std::isfinite(reset_rate)||!std::isfinite(focus_rate)||
            strength<0||focus<0||reset_rate<0||focus_rate<0)return 0;
        const float result=strength+std::max(strength*reset_rate,focus*focus_rate);
        return std::isfinite(result)?result:0;
    }
};
enum class Passive { Power, Monster, Jungle, Durability, Treasure, Prospector, Capture, Home };
struct Context {
    float income=.45f,gold_income=2,death_rate=.002f,death_cost=35;
    float clear_fraction=.5f,camp_pressure=.5f,enemy_pressure=.25f,cluster_fraction=.2f;
    float capture_rate=.025f,recall_rate=.005f;
    int remaining=1000,gold=0;
};
struct Project {
    Passive passive=Passive::Power;
    float damage_growth=0,health_growth=0,magnitude=0,cost=30;
    unsigned shards_left=5,owned=0;
    // Growth points created by the combination beyond the ingredient points.
    float completion_damage=0,completion_health=0;
};
// Value only the inventory this affordable batch actually creates. An unfinished
// project earns shard stats, never a fraction of a future unfunded passive.
inline float batch_value(const Context& c,const Project& p,unsigned count,int delay=0) {
    if(c.remaining<=0||!std::isfinite(p.cost)||p.cost<=0||p.shards_left==0||p.shards_left>10||count==0||count>p.shards_left||delay<0)return 0;
    for(auto x:{c.income,c.gold_income,c.death_rate,c.death_cost,c.clear_fraction,c.camp_pressure,c.enemy_pressure,
                c.cluster_fraction,c.capture_rate,c.recall_rate,p.damage_growth,p.health_growth,p.magnitude,
                p.completion_damage,p.completion_health})if(!std::isfinite(x)||x<0)return 0;
    const float horizon=std::max(0,c.remaining-delay);
    const bool complete=count==p.shards_left;
    const float damage=count*p.damage_growth+(complete?p.completion_damage:0);
    const float health=count*p.health_growth+(complete?p.completion_health:0);
    const float stat=c.income*horizon*(damage*(c.clear_fraction+c.enemy_pressure*.25f)+
        .5f*health*(c.camp_pressure+c.enemy_pressure));
    const float death=c.death_rate*c.death_cost*horizon*health;
    float passive=0;
    switch(p.passive) {
    case Passive::Power:break; // Extra growth is in the actual result metadata.
    case Passive::Monster:passive=c.income*horizon*p.magnitude*c.clear_fraction;break;
    case Passive::Jungle:passive=horizon*p.magnitude*c.camp_pressure*(c.death_rate*c.death_cost+c.income*.25f);break;
    case Passive::Durability:passive=horizon*p.magnitude*(c.death_rate*c.death_cost+c.income*.15f)*(c.camp_pressure+c.enemy_pressure);break;
    case Passive::Treasure:passive=objective::gold_price(c.remaining)*horizon*p.magnitude*c.gold_income;break;
    case Passive::Prospector:passive=c.income*horizon*p.magnitude*c.cluster_fraction;break;
    case Passive::Capture:passive=2*c.capture_rate*horizon*c.income;break;
    case Passive::Home:passive=2*c.recall_rate*horizon*c.income;break;
    }
    const float value=stat+death+(complete?passive:0);
    return std::isfinite(value)?value:0;
}
inline float advance_value(const Context& c,const Project& p,unsigned count,int defer) {
    // Same inventory bought on the next concrete visit is the counterfactual.
    // Do not award the entire remaining-game payoff for bringing it forward.
    if(defer<0)return 0;
    return std::max(0.f,batch_value(c,p,count)-batch_value(c,p,count,defer));
}
inline float utility(const Context& c,const Project& p) {
    if(!std::isfinite(p.cost)||p.cost<=0||c.gold<0||p.shards_left>10)return 0;
    const unsigned count=std::min<unsigned>(p.shards_left,c.gold/p.cost);
    return count?batch_value(c,p,count)/(count*p.cost):0;
}
}
