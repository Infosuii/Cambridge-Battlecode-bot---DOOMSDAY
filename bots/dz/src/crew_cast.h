#pragma once
#include "crew_sequence.h"

namespace dz::crew {
struct CastWork {bool complete=false;int finish=0,phases=0;unsigned casts=0;};
inline void advance_kit(objective::Kit& kit,int rounds) {
    for(auto& c:kit.casts)c.cooldown-=std::min<unsigned>(c.cooldown,std::max(0,rounds));
    kit.shield_duration-=std::min<unsigned>(kit.shield_duration,std::max(0,rounds));
    if(!kit.shield_duration)kit.shield=0;
    if(rounds>0)kit.can_cast=true;
}
// A conditional work estimate for the exact formation sequence. It credits
// only observed reset/direct/self-shield metadata and one cast per owner turn.
// Shield HP is NEVER credited to admission: the caller retains the full basic
// work bound and each actor's raw-exposure escape reserve.
template<class Budget=Unlimited>
CastWork cast_work(std::span<const Unit> units,std::span<const Monster> remaining,const SequenceSearch& search,
                   unsigned first,int capture,int recall,int upper,int sleep=-1,Budget budget={}) {
    CastWork result;
    if(units.empty()||units.size()>max_units||search.stage!=SequenceSearch::Stage::Done||
        units.size()!=search.actors||search.count>max_camps||search.phases.size()<search.count||first>search.count||remaining.size()!=search.count-first||upper<1||upper>2000||
        capture<0||capture>2000||recall<0||recall>2000||sleep< -1||sleep>2000||(sleep>=0&&remaining.size()!=1))return result;
    std::array<objective::Kit,max_units> kits{};std::array<double,max_units> hp{};int arrival=0;bool useful=false;
    for(unsigned u=0;u<units.size();++u) {
        kits[u]=units[u].kit;hp[u]=units[u].hp;arrival=std::max(arrival,units[u].arrival);useful|=kits[u].useful();
        if(!std::isfinite(units[u].hp)||!std::isfinite(units[u].max_hp)||!std::isfinite(units[u].damage)||
            units[u].hp<=0||units[u].max_hp<units[u].hp||units[u].damage<=0||units[u].arrival<0||units[u].arrival>2000)return result;
        if(!std::isfinite(kits[u].shield)||kits[u].shield<0||kits[u].shield_duration>2000)return result;
        for(auto c:kits[u].casts)if(c.cooldown>2000||c.period>2000||c.duration>2000||!std::isfinite(c.amount)||c.amount<0||
            (c.kind!=objective::CastKind::None&&!c.period)||(c.kind==objective::CastKind::Shield&&(!c.duration||!c.amount)))return result;
    }
    if(!useful)return result;
    // All members wait for the last arrival. Do not grant a different clock
    // merely because the visible roster was supplied in another order.
    for(unsigned u=0;u<units.size();++u){kits[u]=units[u].kit;advance_kit(kits[u],arrival);}
    int elapsed=0;
    auto advance=[&](int rounds){for(unsigned u=0;u<units.size();++u)advance_kit(kits[u],rounds);};
    for(unsigned c=0;c<remaining.size();++c) {
        if(!budget())return {};
        const auto& p=search.phases[first+c];float target=remaining[c].hp;
        if(!std::isfinite(target)||target<=0||remaining[c].member!=p.target.member)return {};
        for(auto rounds:{p.transfer,p.approach_rounds,p.return_rounds})if(rounds<0||rounds>2000)return {};
        for(unsigned u=0;u<units.size();++u)for(double v:{p.raw[u],p.escape[u],p.approach_loss[u],p.transfer_loss[u]})
            if(!std::isfinite(v)||v<0)return {};
        std::array<double,max_units> entry{};int cap=2000;
        for(unsigned u=0;u<units.size();++u){entry[u]=c?p.transfer_loss[u]:(sleep>=0?0:p.approach_loss[u]);cap=std::min(cap,capacity(units[u],hp[u]-entry[u],p,u));}
        const int recovery=std::max(p.return_rounds+recall,std::max(0,sleep))+p.approach_rounds+(sleep>=0);
        int initial=c?p.transfer:p.approach_rounds+std::max(0,sleep)+(sleep>=0);
        if(cap<=0) {
            initial=recovery;
            for(unsigned u=0;u<units.size();++u){entry[u]=sleep>=0?0:p.approach_loss[u];hp[u]=units[u].max_hp;}
        }
        elapsed+=initial;advance(initial);for(unsigned u=0;u<units.size();++u)hp[u]-=entry[u];
        while(target>0) {
            cap=2000;for(unsigned u=0;u<units.size();++u)cap=std::min(cap,capacity(units[u],hp[u],p,u));
            if(cap<=0)return {};
            for(int phase=0;phase<cap&&target>0;++phase) {
                if(!budget())return {};
                for(unsigned u=0;u<units.size();++u) {
                    auto& kit=kits[u];if(!kit.shield_duration)kit.shield=0;
                    bool cast=false;
                    if(target>0&&kit.can_cast&&kit.shield<=0&&p.raw[u]>0)for(auto& s:kit.casts)
                        if(s.kind==objective::CastKind::Shield&&!s.cooldown&&p.raw[u]>=.5f*s.amount) {
                            kit.shield=s.amount;kit.shield_duration=s.duration;s.cooldown=s.period;cast=true;++result.casts;break;
                        }
                    if(target>0)target-=units[u].damage;
                    if(target>0&&!cast&&kit.can_cast)for(auto& s:kit.casts) {
                        if(s.cooldown||(s.kind!=objective::CastKind::Reset&&s.kind!=objective::CastKind::Damage))continue;
                        target-=s.kind==objective::CastKind::Reset?units[u].damage:s.amount;
                        s.cooldown=s.period;++result.casts;break;
                    }
                    advance_kit(kit,1);kit.shield=std::max(0.f,kit.shield-static_cast<float>(p.raw[u]));
                    hp[u]-=p.raw[u]; // No projected shield/tank safety credit.
                }
                ++elapsed;++result.phases;
                if(elapsed+capture>upper)return {};
            }
            if(target>0) {
                elapsed+=recovery;advance(recovery);
                for(unsigned u=0;u<units.size();++u)hp[u]=units[u].max_hp-(sleep>=0?0:p.approach_loss[u]);
                if(elapsed+capture>upper)return {};
            }
        }
        ++elapsed;advance(1); // The same round-order ambiguity paid by basic work.
    }
    result.finish=elapsed+capture;result.complete=result.finish<=upper;return result;
}
}
