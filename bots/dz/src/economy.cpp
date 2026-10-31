#include "economy.h"
#if DZ_ECONOMY_V2
#include "allocation.h"
#include <bit>

namespace dz {
objective::Actor economic_actor(const SeenChampion& c) {
    objective::Actor actor{c.hp,c.max_hp,c.strength};
    auto owned=c.sdk.item_count();
    float jungle=0,durable=0,monster=0;
    for(auto stat:{cambc::item_stat::strength,cambc::item_stat::focus,cambc::item_stat::health}) {
        auto j=cambc::get_item_enum(cambc::item_family::jungle,stat,false);
        auto d=cambc::get_item_enum(cambc::item_family::durability,stat,false);
        auto m=cambc::get_item_enum(cambc::item_family::monster,stat,false);
        auto p=cambc::get_item_enum(cambc::item_family::prospector,stat,false);
        auto cap=cambc::get_item_enum(cambc::item_family::capture,stat,false);
        auto treasure=cambc::get_item_enum(cambc::item_family::treasure,stat,false);
        if(owned[j])jungle=std::max(jungle,j.passive_magnitude());
        if(owned[d])durable=std::max(durable,d.passive_magnitude());
        if(owned[m])monster=std::max(monster,m.passive_magnitude());
        actor.prospector|=owned[p]>0;
        if(owned[cap])actor.capture_rounds=3;
        if(owned[treasure])actor.gold_multiplier+=treasure.passive_magnitude();
    }
    if(c.sdk.champion_name()==cambc::champion_type::vesper_vale)actor.gold_multiplier+=.33f;
    actor.damage*=1+monster;actor.incoming_factor=(1-jungle)*(1-durable);
    // Existing shields are deliberately ignored by the economic admission gate:
    // travel/round order could expire them before the rendezvous.
    return actor;
}
namespace {
struct Participant { objective::Actor actor;vec2 p;unsigned slot; };
objective::Encounter encounter(const StaticWorld& w,const Memory& m,int g,std::span<ClearMember> members,int round,int horizon) {
    const auto& group=w.groups[g];const auto& belief=m.groups[g];
    for(unsigned k=0;k<members.size();++k)members[k]={m.member_hp[g][k],group.initial_strength[k]};
    objective::Encounter e{members,group.reward_gems,group.reward_gold};
    e.cluster=group.cluster;e.horizon=std::clamp(horizon,1,2000);
    e.ready_in=belief.state==GroupState::Respawning ? std::max(0,belief.ready-round) : 0;
    // Multi-member geometry is not stationary: include travel between members.
    // This explicit conservative bound can reject large groups; it never prices
    // them as one monster. Later exact geometry calibration may tighten it.
    e.reposition_rounds=group.radius*2;
    return e;
}
}
bool crew_ready(const StaticWorld& w,const Memory& m,const Observation& o,int g,const TurnContext& tc) {
    if(m.economic_crew==0||m.contract.objective!=g)
        return clear_survivable(group_clear_risk(w,m,o,g),o.hp,o.max_hp);
    const auto word=shared_word();unsigned present=1u<<w.slot;
    float damage=o.strength*o.camp_damage;
    for(auto& ally:o.allies) {
        auto it=std::find(w.allies.begin(),w.allies.end(),ally.sdk);
        if(it==w.allies.end())continue;
        const unsigned slot=static_cast<unsigned>(it-w.allies.begin());
        if(!(m.economic_crew&(1u<<slot)))continue;
        if(protocol::slot(word,slot).objective!=g||w.distance(g,ally.p)>std::max(1,ally.range)+1)continue;
        if(!tc.allow(5000))return false;
        auto actor=economic_actor(ally);
        damage+=actor.damage;present|=1u<<slot;
    }
    if((present&m.economic_crew)!=m.economic_crew)return false;
    // All expected crew members must actually be here. The old wake gate counted
    // any nearby ally and used an assumed damage share, even on another job.
    auto risk=group_clear_risk(w,m,o,g,damage-o.strength*o.camp_damage);
    return clear_survivable(risk,o.hp,o.max_hp);
}
std::optional<Goal> economic_goal(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc,int altar,int altar_distance) {
    const int remaining=std::max(1,2000-static_cast<int>(tc.round));
    const float gold_price=objective::gold_price(remaining);
    // Common GE/time currency: bag loss hazard against the opportunity cost of
    // delivery. Certain win/late delivery outranks collecting more resources.
    if(o.bag>0&&altar>=0&&altar_distance<65535) {
        const int channel=std::max(1,(o.bag+9)/10);
        const float hazard=.002f*(1+3*!o.enemies.empty())*(2-o.hp/o.max_hp);
        const float next_trip=altar_distance+channel+12.f;
        const float saved=o.bag*std::min(1.f,hazard*next_trip);
        const float cost=(altar_distance+channel)*std::max(.15f,m.economic_rate);
        if(o.submitted+o.bag>=static_cast<int>(cambc::constants::winning_gems)||
            remaining<=altar_distance+channel+8||saved>=cost||bank_now(o.bag,altar_distance,o.submitted,cambc::constants::winning_gems))
            return Goal{GoalKind::Bank,altar};
    }
    if(o.hp<.3f*o.max_hp||o.gold>=150)return Goal{GoalKind::Home};
    int current=m.contract.objective;
    if(current>=0) {
        const auto& b=m.groups[current];const int distance=w.distance(current,o.p);
        const bool helper_done=b.state==GroupState::Reward&&m.economic_capturer!=w.slot;
        const bool timed_out=std::popcount(m.economic_crew)>1&&static_cast<int>(tc.round)>m.rendezvous_until&&
            b.state!=GroupState::Partial&&b.state!=GroupState::Reward;
        if(!helper_done&&!timed_out&&b.available(tc.round)&&
            m.contract.progressing(tc.round,distance,b.hp,b.capture)) return Goal{GoalKind::Farm,current};
        if(helper_done||!b.available(tc.round))m.contract.objective=-1;
        else m.release(tc.round);
    }
    if(!tc.allow(16000))return std::nullopt;
    const auto start=fuel_left();
    std::array<Participant,objective::max_crew> team{};unsigned n=0,available=0;
    team[n++]={economic_actor({cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range}),o.p,w.slot};available|=1u<<w.slot;
    const auto word=shared_word();
    for(const auto& ally:o.allies) {
        if(!tc.allow(12000)||start-fuel_left()>9000)break;
        const auto it=std::find(w.allies.begin(),w.allies.end(),ally.sdk);
        if(it==w.allies.end()||n>=team.size()||ally.hp<.5f*ally.max_hp)continue;
        const unsigned slot=static_cast<unsigned>(it-w.allies.begin());
        const auto claim=protocol::slot(word,slot);
        // A currently visible body at a live job is physically reserved. No
        // claim without a visible body establishes freshness or reserves work.
        if(claim.objective==protocol::shop||claim.objective==protocol::retreat)continue;
        // Gold is self-only in the SDK; shopping intent comes from the visible
        // body's claim. Visible carried bags are legal to read.
        if(ally.sdk.gem_count()>=config::bank_bag)continue;
        team[n++]={economic_actor(ally),ally.p,slot};available|=1u<<slot;
    }
    struct Candidate { int g;float bound; };
    std::vector<Candidate> candidates;candidates.reserve(w.groups.size());
    for(unsigned g=0;g<w.groups.size();++g) {
        auto& b=m.groups[g];auto& group=w.groups[g];
        if((!b.available(tc.round)&&!b.waitable(tc.round,25))||group.tiles.size()>clear_risk_members)continue;
        const int d=w.distance_floor(g,o.p);
        if(d>30&&!group.field)continue;
        const float value=group.reward_gems+gold_price*group.reward_gold;
        if(value>0)candidates.push_back({static_cast<int>(g),value/(d+6.f)});
    }
    std::sort(candidates.begin(),candidates.end(),[](auto a,auto b){return a.bound>b.bound||(a.bound==b.bound&&a.g<b.g);});
    std::array<float,objective::max_crew> alternatives{};
    std::vector<economy::Bid> bids;bids.reserve(48);
    const unsigned limit=std::min<unsigned>(8,candidates.size());
    std::array<ClearMember,clear_risk_members> members{};
    for(unsigned index=0;index<limit;++index) {
        if(!tc.allow(10000)||start-fuel_left()>26000)break;
        const int g=candidates[index].g;const auto& group=w.groups[g];
        auto e=encounter(w,m,g,std::span<ClearMember>(members.data(),group.tiles.size()),tc.round,remaining);
        std::array<objective::Actor,objective::max_crew> actors{};std::array<int,objective::max_crew> arrival{};
        unsigned eligible=0;
        for(unsigned a=0;a<n;++a) {
            actors[a]=team[a].actor;arrival[a]=w.distance(g,team[a].p);
            if(arrival[a]>=65535)continue;
            if(!group.field&&arrival[a]>30)continue;
            actors[a].arrival=arrival[a]+(group.field?0:arrival[a]/3);
            eligible|=1u<<a;
        }
        float contested=1;
        for(const auto& enemy:o.enemies)if(enemy.p.chebyshev_distance(group.center)<=6+group.radius)contested=.33f;
        for(unsigned a=0;a<n;++a)if(eligible&(1u<<a)) {
            auto quote=objective::forecast(e,std::span<const objective::Actor>(&actors[a],1),0);
            if(!quote.complete()||!quote.survivable)continue;
            const float rate=contested*quote.reward(gold_price)/std::max(1,quote.finish);
            alternatives[team[a].slot]=std::max(alternatives[team[a].slot],rate);
            bids.push_back({g,1u<<team[a].slot,team[a].slot,contested*quote.reward(gold_price),static_cast<float>(quote.finish)});
        }
        if(group.strength<=0||m.groups[g].state==GroupState::Reward||n<2)continue;
        // Nearby crew subsets, up to six actors. Each gets real damage and its
        // own incoming mitigation, not the caller's stats multiplied by count.
        std::array<unsigned,objective::max_crew> order{};for(unsigned a=0;a<n;++a)order[a]=a;
        std::sort(order.begin(),order.begin()+n,[&](auto a,auto b){return arrival[a]<arrival[b];});
        std::array<objective::Actor,objective::max_crew> crew{};
        std::array<unsigned,objective::max_crew> crew_slots{};unsigned count=0,mask=0,capturer=0;
        for(unsigned k=0;k<n;++k) {
            const auto a=order[k];if(!(eligible&(1u<<a)))continue;
            crew_slots[count]=team[a].slot;crew[count++]=actors[a];mask|=1u<<team[a].slot;
            if(count<2)continue;
            for(unsigned cap=0;cap<count;++cap) {
                if(crew[cap].gold_multiplier>crew[capturer].gold_multiplier||
                    (crew[cap].gold_multiplier==crew[capturer].gold_multiplier&&crew[cap].capture_rounds<crew[capturer].capture_rounds))capturer=cap;
            }
            auto quote=objective::forecast(e,std::span<const objective::Actor>(crew.data(),count),capturer);
            if(!quote.complete()||!quote.survivable)continue;
            const unsigned cap_slot=crew_slots[capturer];
            bids.push_back({g,mask,cap_slot,contested*quote.reward(gold_price),static_cast<float>(quote.finish)});
            break; // Minimal survivable crew; never drag the whole team by default.
        }
    }
    for(auto& bid:bids)if(std::popcount(bid.crew)>1) {
        float best=0,total=0;
        for(unsigned slot=0;slot<alternatives.size();++slot)if(bid.crew&(1u<<slot)){total+=alternatives[slot];best=std::max(best,alternatives[slot]);}
        bid.opportunity=total-best;
    }
    const auto assignments=economy::allocate(bids,available);const auto chosen=assignments[w.slot];
    if(chosen.objective<0)return std::nullopt;
    const auto& belief=m.groups[chosen.objective];
    m.economic_crew=chosen.crew;m.economic_capturer=chosen.capturer;m.economic_rate=alternatives[w.slot];
    m.rendezvous_until=tc.round+std::min(40,w.distance(chosen.objective,o.p)+8);
    m.contract.start(chosen.objective,tc.round,w.distance(chosen.objective,o.p),belief.hp,belief.capture,
        std::popcount(chosen.crew)>1?config::crew_window:config::contract_window);
    tc.guard();return Goal{GoalKind::Farm,chosen.objective};
}
}
#endif
