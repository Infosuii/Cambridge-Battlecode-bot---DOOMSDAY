#pragma once
#include "crew_sequence.h"
#include "team_protocol.h"

namespace dz::crew {
// Restricted to Power: all benefit is in purchased growth points. There is no
// unbought passive, assumed ally cash, or future enemy knowledge in this model.
struct Shard {
    unsigned cost=0,combine=0,points=0,result_points=0;
    bool valid() const {return cost&&combine&&combine<=10&&points&&result_points>=combine*points;}
};
struct Upgrade { Unit unit;unsigned purchases=0;bool valid=false; };
inline Upgrade upgrade(Unit unit,unsigned stat,unsigned cash,Shard shard) {
    Upgrade r{unit};if(stat>1||!shard.valid())return r;
    for(auto x:{unit.health_growth,unit.damage_growth,unit.health_damage_growth})if(!std::isfinite(x)||x<0)return r;
    const unsigned owned=stat?unit.power_health:unit.power_strength;
    if(unit.inventory_known&&owned>=shard.combine)return r;
    r.purchases=std::min(16u,cash/shard.cost);
    const unsigned extra=unit.inventory_known?(owned+r.purchases)/shard.combine:0;
    // Unknown ingredients receive only the guaranteed purchased shard points.
    const unsigned points=r.purchases*shard.points+extra*(shard.result_points-shard.combine*shard.points);
    if(stat){r.unit.max_hp+=points*unit.health_growth;r.unit.damage+=points*unit.health_damage_growth;}
    else r.unit.damage+=points*unit.damage_growth;
    r.unit.hp=r.unit.max_hp;r.valid=std::isfinite(r.unit.hp)&&std::isfinite(r.unit.damage);return r;
}
struct Investment { bool valid=false;unsigned slot=0,stat=0,purchases=0;float gain=0; };
struct Progression {
    enum class Stage { Empty, Pricing, Done } stage=Stage::Empty;
    std::array<team::Cash,max_units> cash{};
    std::array<unsigned,max_units> slots{};
    std::array<Investment,2*max_units> choices{};
    std::array<Shard,2> shards{};
    unsigned actors=0,actor=0,stat=0,sample=0,began=0,expires=0;
    int horizon=0,trip=0,delivery=0,respawn=0,recall=0;
    float gems=0,gold=0;bool cluster=false;
    float least=std::numeric_limits<float>::infinity();
    unsigned previous_before=~0u,previous_after=~0u;float previous_gain=0;
    bool pending() const {return stage==Stage::Pricing;}
    void begin(std::span<const Unit> units,std::span<const team::Cash> reports,std::array<Shard,2> spec,
               unsigned now,unsigned until,int remaining,int home_trip,int bank_trip,int reset,int heal,float reward,float payout,bool resource=false) {
        *this={};stage=Stage::Done;
        if(units.size()<2||units.size()>max_units||reports.size()!=units.size()||remaining<1||remaining>2000||now>2047||until<now||until>2047||
            home_trip<0||bank_trip<0||reset<0||heal<0||!std::isfinite(reward)||!std::isfinite(payout)||reward<0||payout<0)return;
        actors=units.size();std::copy(reports.begin(),reports.end(),cash.begin());shards=spec;
        for(unsigned u=0;u<actors;++u)slots[u]=units[u].slot;
        began=now;expires=until;horizon=remaining;trip=home_trip;delivery=bank_trip;respawn=reset;recall=heal;gems=reward;gold=payout;cluster=resource;
        stage=Stage::Pricing;
    }
    float banked(const SequenceQuote& q,float reward) const {
        if(!q.complete)return 0;
        const long long first=static_cast<long long>(trip)+q.finish+delivery;
        const long long cycle=std::max(static_cast<long long>(respawn)+q.finish,
            static_cast<long long>(trip)+q.finish+2*delivery);
        return first<=horizon&&cycle>0?reward*(1+(horizon-first)/cycle):0;
    }
    template<class Budget=Unlimited>
    void resume(std::span<const Unit> units,std::span<const Monster> full,const SequenceSearch& geometry,Budget budget={}) {
        if(!pending())return;
        if(units.size()!=actors||full.size()!=geometry.count||geometry.stage!=SequenceSearch::Stage::Done){stage=Stage::Done;return;}
        while(pending()) {
            if(!budget())return;
            const auto& report=cash[actor];const auto spec=shards[stat];
            if(!report.valid||!spec.valid()||report.high==std::numeric_limits<unsigned>::max()||
                !std::isfinite(units[actor].gold_multiplier)||units[actor].gold_multiplier<0) {advance();continue;}
            const float boost=cluster&&units[actor].prospector?1.25f:1.f;
            const unsigned grant=std::min<double>(std::numeric_limits<unsigned>::max()-report.high,
                std::floor(gold*boost*units[actor].gold_multiplier));
            const unsigned money=sample==0?0:sample==1?report.low:report.high;
            const auto before=upgrade(units[actor],stat,money,spec),after=upgrade(units[actor],stat,money+grant,spec);
            float gain=0;
            if(before.purchases==previous_before&&after.purchases==previous_after)gain=previous_gain;
            else if(before.valid&&after.valid&&after.purchases>before.purchases) {
                std::array<Unit,max_units> old{},improved{};
                for(unsigned u=0;u<actors;++u){old[u]=improved[u]=units[u];old[u].hp=improved[u].hp=units[u].max_hp;}
                old[actor]=before.unit;improved[actor]=after.unit;
                const int cap=units[actor].capture_rounds+1;
                const auto a=quote(std::span<const Unit>(old.data(),actors),full,geometry,0,cap,recall,horizon,budget,true);
                if(a.reason==SequenceReason::Budget)return;
                const auto b=quote(std::span<const Unit>(improved.data(),actors),full,geometry,0,cap,recall,horizon,budget,true);
                if(b.reason==SequenceReason::Budget)return;
                const float reward=std::floor(gems*boost);
                gain=std::max(0.f,banked(b,reward)-banked(a,reward));
            }
            previous_before=before.purchases;previous_after=after.purchases;previous_gain=gain;
            least=std::min(least,gain);
            if(++sample==3) {
                choices[2*actor+stat]={least>0,units[actor].slot,stat,std::min(16u,grant/spec.cost),least};
                advance();
            }
        }
    }
    void advance() {
        sample=0;least=std::numeric_limits<float>::infinity();previous_before=previous_after=~0u;previous_gain=0;
        if(++stat==2){stat=0;if(++actor==actors)stage=Stage::Done;}
    }
    Investment best(unsigned slot,unsigned now) const {
        Investment result;if(stage!=Stage::Done||now>expires)return result;
        bool fresh=false;
        for(unsigned u=0;u<actors;++u)if(slots[u]==slot)
            fresh|=cash[u].valid&&cash[u].round<=now&&now-cash[u].round<=expires-began;
        if(!fresh)return result;
        for(auto p:choices)if(p.valid&&p.slot==slot&&p.gain>result.gain)result=p;
        return result;
    }
};
}
