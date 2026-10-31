#pragma once
#include "allocation.h"
#include "formation.h"
#include <bit>

namespace dz::economy {
struct CrewEpoch {
    int group=-1;unsigned generation=0,version=0,topology=0;
    bool operator==(const CrewEpoch&) const=default;
};
struct CrewOffer {
    CrewEpoch epoch;
    int round=-1,expires=-1,horizon=0,work=0,arrival=0;
    unsigned mask=0,count=0;
    bool complete=false;
    std::array<crew::Unit,crew::max_units> actors{};
    std::array<float,crew::max_units> investment{};
    unsigned investment_until=0;
};
struct CrewMenu {
    std::array<Bid,32> bids{};
    unsigned count=0,request=0;
    bool complete=false,ready=false;
};
// Compact completed economic quotes, never copies of the large route search.
// Two geometry workspaces can therefore compare alternatives without erasing
// the executable crew or treating an unfinished route as an executable offer.
class CrewMarket {
    static constexpr unsigned capacity=32;
    std::array<CrewOffer,capacity> offers_{};
    struct Batch {
        CrewEpoch epoch;unsigned roster=0;std::uint64_t stats=0;
        std::array<unsigned,2> primary{};int used=-1;
    };
    std::array<Batch,8> batches_{};
    static bool valid_units(std::span<const crew::Unit> units) {
        if(units.empty()||units.size()>crew::max_units)return false;
        unsigned seen=0;
        for(auto u:units) {
            if(u.slot>=6||(seen&(1u<<u.slot))||u.arrival<0||u.arrival>2000||u.range<1||u.range>3||
                !std::isfinite(u.hp)||!std::isfinite(u.max_hp)||!std::isfinite(u.damage)||!std::isfinite(u.factor)||
                u.hp<=0||u.max_hp<u.hp||u.damage<=0||u.factor<=0)return false;
            seen|=1u<<u.slot;
        }
        return true;
    }
    static unsigned roster(std::span<const crew::Unit> units) {
        unsigned mask=0;for(auto u:units)if(u.slot<crew::max_units)mask|=1u<<u.slot;return mask;
    }
    static std::uint64_t signature(std::span<const crew::Unit> units) {
        std::uint64_t h=1469598103934665603ull;
        for(auto u:units)for(auto x:{u.slot,u.handle,std::bit_cast<unsigned>(u.max_hp),std::bit_cast<unsigned>(u.damage),
            std::bit_cast<unsigned>(u.factor),static_cast<unsigned>(u.range)})h=(h^x)*1099511628211ull;
        return h;
    }
    static float bound(unsigned mask,std::span<const crew::Unit> units,float hp) {
        float damage=0;int arrival=0;
        for(auto u:units)if(mask&(1u<<u.slot)){damage+=u.damage;arrival=std::max(arrival,u.arrival);}
        return std::isfinite(damage)&&damage>0&&hp>=0?1.f/(arrival+std::ceil(hp/damage)+6):0;
    }
    static bool usable(const CrewOffer& offer,std::span<const crew::Unit> units,int now,int horizon) {
        // A completed static quote is revalidated against current public inputs,
        // not discarded while a slower competing geometry job is still running.
        // Negative quotes and speculative gear benefits retain finite lifetimes.
        if(now<offer.round||(!offer.complete&&now>offer.expires)||
            (!offer.complete&&horizon>offer.horizon))return false;
        unsigned seen=0;int arrival=0;
        for(unsigned a=0;a<offer.count;++a) {
            const auto& old=offer.actors[a];const auto current=std::find_if(units.begin(),units.end(),[&](auto u){return u.slot==old.slot;});
            if(current==units.end()||!crew::same_roles(std::span<const crew::Unit>(&old,1),std::span<const crew::Unit>(&*current,1))||
                (offer.complete?current->hp<old.hp:current->hp!=old.hp))return false;
            seen|=1u<<current->slot;arrival=std::max(arrival,current->arrival);
        }
        return seen==offer.mask&&(offer.complete||arrival>=offer.arrival);
    }
public:
    void decline(int group,unsigned mask,int until) {
        for(auto& offer:offers_)if(offer.epoch.group==group&&offer.mask==mask) {
            offer.complete=false;offer.expires=until;offer.horizon=2000;
        }
    }
    bool active(int now) const {
        return std::any_of(offers_.begin(),offers_.end(),[&](const auto& o){return o.complete&&o.round<=now&&now<=o.expires;});
    }
    const CrewOffer* get(CrewEpoch epoch,unsigned mask,std::span<const crew::Unit> units,int now,int horizon) const {
        if(!valid_units(units))return nullptr;
        const auto it=std::find_if(offers_.begin(),offers_.end(),[&](const auto& o){return o.mask==mask&&o.epoch==epoch;});
        return it!=offers_.end()&&usable(*it,units,now,horizon)?&*it:nullptr;
    }
    static int duration(const CrewOffer& offer,std::span<const crew::Unit> units) {
        int arrival=0;for(auto u:units)if(offer.mask&(1u<<u.slot))arrival=std::max(arrival,u.arrival);
        return offer.work+arrival;
    }
    void put(CrewEpoch epoch,unsigned mask,std::span<const crew::Unit> units,int now,int horizon,int finish,int arrival,
             bool complete,std::span<const float> investment={},unsigned investment_until=0,int lifetime=40) {
        if(mask==0||mask>=64||units.size()<2||!valid_units(units)||roster(units)!=mask||finish<arrival)return;
        auto it=std::find_if(offers_.begin(),offers_.end(),[&](const auto& o){return o.mask==mask&&o.epoch.group==epoch.group;});
        if(it==offers_.end())it=std::min_element(offers_.begin(),offers_.end(),[](const auto& a,const auto& b){return a.expires<b.expires;});
        *it={};it->epoch=epoch;it->round=now;it->expires=now+std::max(0,lifetime);it->horizon=horizon;
        it->mask=mask;it->count=units.size();it->complete=complete;it->work=finish-arrival;it->arrival=arrival;
        std::copy(units.begin(),units.end(),it->actors.begin());
        if(investment.size()==units.size())std::copy(investment.begin(),investment.end(),it->investment.begin());
        it->investment_until=investment_until;
    }
    // Initial comparison is the best optimistic pair and triple, priced by the
    // full spatial/recovery model. Further masks are explored if both fail.
    // This is a bounded candidate frontier, not an exhaustive global optimum.
    std::array<unsigned,2> primary(CrewEpoch epoch,std::span<const crew::Unit> units,unsigned self,int now,float hp) {
        if(self>=6||!valid_units(units)||!std::isfinite(hp)||hp<0)return {};
        const unsigned all=roster(units);const auto stats=signature(units);
        auto it=std::find_if(batches_.begin(),batches_.end(),[&](auto b){return b.epoch.group==epoch.group;});
        if(it==batches_.end())it=std::min_element(batches_.begin(),batches_.end(),[](auto a,auto b){return a.used<b.used;});
        if(it->epoch!=epoch||it->roster!=all||it->stats!=stats) {
            *it={};it->epoch=epoch;it->roster=all;it->stats=stats;
            std::array<float,2> best{};
            for(unsigned mask=1;mask<64;++mask) {
                const unsigned count=std::popcount(mask);if(self>=6||!(mask&(1u<<self))||(mask&~all)||count<2||count>3)continue;
                const float score=bound(mask,units,hp);
                if(score>best[count-2]){best[count-2]=score;it->primary[count-2]=mask;}
            }
        }
        it->used=now;return it->primary;
    }
    // Validate each retained quote once. Separate ready/next/bids scans used to
    // exhaust the bounded metadata budget before a completed bid was emitted.
    template<class Budget=UnlimitedAuction>
    CrewMenu review(CrewEpoch epoch,std::array<unsigned,2> primary,std::span<const crew::Unit> units,unsigned proposer,
                    int now,int horizon,float hp,float gems,float gold,bool cluster,float gold_price,float contested,Budget budget={}) const {
        CrewMenu result;
        if(proposer>=6||!valid_units(units)||!std::isfinite(hp)||hp<0||!budget())return result;
        std::uint64_t known=0;unsigned checked=0;
        for(const auto& offer:offers_) {
            if((++checked&7u)==0&&!budget())return {};
            if(!(offer.epoch==epoch&&(offer.mask&(1u<<proposer))&&usable(offer,units,now,horizon)))continue;
            known|=std::uint64_t{1}<<offer.mask;
            if(!offer.complete)continue;
            const int finish=duration(offer,units);if(finish>horizon)continue;
            float best=-1;unsigned cap=0;
            for(unsigned a=0;a<offer.count;++a) {
                const auto& actor=offer.actors[a];const float boost=cluster&&actor.prospector?1.25f:1.f;
                if(actor.slot!=proposer)continue; // The proposal has an executable sender; later handoff may improve it.
                const float gain=now<=static_cast<int>(offer.investment_until)?offer.investment[a]:0;
                const float value=std::floor(gems*boost)+std::max(gold_price*std::floor(gold*boost*actor.gold_multiplier),gain);
                if(value>best){best=value;cap=actor.slot;}
            }
            if(best>0)result.bids[result.count++]={epoch.group,offer.mask,cap,contested*best,static_cast<float>(finish)};
        }
        result.complete=true;
        for(auto mask:primary)if(mask&&!(known&(std::uint64_t{1}<<mask))){result.request=mask;return result;}
        if(result.count){result.ready=true;return result;}
        const unsigned all=roster(units);float score=0;
        for(unsigned mask=1;mask<64;++mask) {
            if((mask&3u)==0&&!budget())return {};
            if((mask&(1u<<proposer))&&!(mask&~all)&&std::popcount(mask)>=2&&!(known&(std::uint64_t{1}<<mask))) {
                const float q=bound(mask,units,hp);if(q>score){result.request=mask;score=q;}
            }
        }
        return result;
    }
};
}
