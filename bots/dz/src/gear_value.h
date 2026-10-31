#pragma once
#include "objective_model.h"
namespace dz::gear {
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
};
inline float utility(const Context& c,const Project& p) {
    if(c.remaining<=0||p.cost<=0||p.shards_left==0||p.shards_left>10||
        !std::isfinite(p.damage_growth)||!std::isfinite(p.health_growth)||!std::isfinite(p.magnitude))return 0;
    const float fill=std::max(0.f,(p.cost*p.shards_left-c.gold)/std::max(.1f,c.gold_income));
    const float horizon=std::max(0.f,c.remaining-fill);
    const float stat=c.income*c.remaining*(p.damage_growth*(c.clear_fraction+c.enemy_pressure*.25f)+
        .5f*p.health_growth*(c.camp_pressure+c.enemy_pressure));
    const float death=c.death_rate*c.death_cost*c.remaining*p.health_growth;
    float passive=0;
    switch(p.passive) {
    case Passive::Power:passive=c.income*horizon*p.damage_growth;break;
    case Passive::Monster:passive=c.income*horizon*p.magnitude*c.clear_fraction;break;
    case Passive::Jungle:passive=horizon*p.magnitude*c.camp_pressure*(c.death_rate*c.death_cost+c.income*.25f);break;
    case Passive::Durability:passive=horizon*p.magnitude*(c.death_rate*c.death_cost+c.income*.15f)*(c.camp_pressure+c.enemy_pressure);break;
    case Passive::Treasure:passive=objective::gold_price(c.remaining)*horizon*p.magnitude*c.gold_income;break;
    case Passive::Prospector:passive=c.income*horizon*p.magnitude*c.cluster_fraction;break;
    case Passive::Capture:passive=2*c.capture_rate*horizon*c.income;break;
    case Passive::Home:passive=2*c.recall_rate*horizon*c.income;break;
    }
    // The passive's future payoff is amortised over remaining purchases. Near
    // game end a project that cannot finish earns only the next shard's stats.
    return (stat+death+passive/p.shards_left)/p.cost;
}
}
