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
objective::Encounter encounter(const StaticWorld& w,const Memory& m,int g,std::span<ClearMember> members,std::span<unsigned> counts,int round,int horizon) {
    const auto& group=w.groups[g];const auto& belief=m.groups[g];
    unsigned distinct=0;
    for(unsigned k=0;k<m.member_hp[g].size();++k) {
        if(m.member_hp[g][k]<=0)continue;
        const ClearMember member{m.member_hp[g][k],group.initial_strength[k]};
        unsigned i=0;
        while(i<distinct&&(members[i].hp!=member.hp||members[i].incoming!=member.incoming))++i;
        if(i==distinct) {
            if(distinct==members.size())return {{},0,0,0,-1,0,false,true}; // Unsupported heterogeneity, no admission.
            members[distinct]=member;counts[distinct++]=0;
        }
        ++counts[i];
    }
    objective::Encounter e{members.first(distinct),group.reward_gems,group.reward_gold};
    e.multiplicities=counts.first(distinct);
    e.exact_arrival=static_cast<bool>(group.field);
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
    if(m.access_group==g&&m.access_member>=0) {
        const float attacks=std::ceil(m.member_hp[g][m.access_member]/std::max(1.f,o.strength*o.camp_damage));
        float incoming=0;int escape=1;
        for(unsigned k=0;k<m.member_hp[g].size();++k) {
            if(m.member_hp[g][k]>0)incoming+=w.groups[g].initial_strength[k]*o.camp_factor;
            escape=std::max(escape,w.groups[g].attack_ranges[k]+1);
        }
        return o.hp>1.25f*incoming*(attacks+escape)+.15f*o.max_hp;
    }
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
    if(m.member_hp[g].size()<=clear_risk_members) {
        auto risk=group_clear_risk(w,m,o,g,damage-o.strength*o.camp_damage);
        return clear_survivable(risk,o.hp,o.max_hp);
    }
    if(!tc.allow(12000))return false;
    std::array<ClearMember,clear_risk_members> members{};std::array<unsigned,clear_risk_members> counts{};
    auto e=encounter(w,m,g,members,counts,tc.round,cambc::constants::max_rounds-tc.round);
    const objective::Actor tank{o.hp,o.max_hp,damage,o.camp_factor};
    const auto quote=objective::forecast(e,std::span<const objective::Actor>(&tank,1),0);
    return quote.complete()&&quote.survivable;
}
std::optional<Goal> economic_goal(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc,int altar,int altar_distance) {
    if(m.legacy(tc.round))return std::nullopt; // Preserve the productive starvation escape.
    m.race.observe(tc.round,o.submitted,cambc::global_submitted_gems(cambc::team::enemy));
    float bags=o.bag;for(const auto& a:o.allies)bags+=a.sdk.gem_count();
    const int remaining=m.race.remaining(tc.round,cambc::constants::max_rounds,cambc::constants::winning_gems,bags);
    const float gold_price=objective::gold_price(remaining);
    if(altar>=0) {m.access_group=-1;m.access_member=-1;}
    else if(o.enemies.empty()&&tc.allow(14000)) {
        // Price the actual cut member, not a full boss group. Killing one gate
        // can open delivery for the whole team; unrelated monsters still count
        // in incoming exposure until we leave. No map-name special cases.
        int chosen_group=-1,chosen_member=-1;float best=0;
        for(const auto& blocked:w.altars)for(auto [g,k]:blocked.gate_members) {
            if(!tc.allow(10000))break;
            if(!m.groups[g].available(tc.round)||m.member_hp[g][k]<=0)continue;
            const int travel=w.distance(g,o.p);if(travel>=65535)continue;
            const float attacks=std::ceil(m.member_hp[g][k]/std::max(1.f,o.strength*o.camp_damage));
            float incoming=0;
            for(unsigned member=0;member<m.member_hp[g].size();++member)
                if(m.member_hp[g][member]>0)incoming+=w.groups[g].initial_strength[member]*o.camp_factor;
            // Reserve enough HP to walk out of maximum camp range. If this
            // cannot fit, ordinary dynamic crew allocation may take the group.
            int escape=1;for(auto r:w.groups[g].attack_ranges)escape=std::max(escape,r+1);
            if(o.hp<=1.25f*incoming*(attacks+escape)+.15f*o.max_hp)continue;
            const float value=(60+bags+w.groups[g].reward_gems)/((travel+attacks+escape+1.f)*(1+m.pressure(w.groups[g].center,6+w.groups[g].radius,tc.round)));
            if(value>best){best=value;chosen_group=g;chosen_member=k;}
        }
        if(chosen_group>=0) {
            const bool continuing=m.access_group==chosen_group&&m.access_member==chosen_member&&m.contract.objective==chosen_group;
            if(continuing&&!m.contract.progressing(tc.round,w.distance(chosen_group,o.p),m.groups[chosen_group].hp,m.groups[chosen_group].capture)) {
                m.release(tc.round);m.access_group=-1;m.access_member=-1;return std::nullopt;
            }
            m.access_group=chosen_group;m.access_member=chosen_member;m.economic_crew=1u<<w.slot;m.economic_capturer=w.slot;
            const auto& b=m.groups[chosen_group];
            if(!continuing)m.contract.start(chosen_group,tc.round,w.distance(chosen_group,o.p),b.hp,b.capture);
            return Goal{GoalKind::Farm,chosen_group};
        }
    }
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
    const int occupied=w.group_at(o.p);
    if(occupied>=0&&m.groups[occupied].state==GroupState::Respawning) {
        m.contract.objective=-1;return Goal{GoalKind::YieldSpawn};
    }
    int current=m.contract.objective;
    const auto lease=protocol::compact::lease(shared_word(),tc.round);
    if(lease.valid&&lease.leader!=w.slot&&(lease.members&(1u<<w.slot))&&
        lease.leader<w.allies.size()&&lease.capturer<w.allies.size()&&
        !(lease.members&~((1u<<w.allies.size())-1u))&&
        lease.objective<static_cast<int>(w.groups.size())&&m.groups[lease.objective].available(tc.round)&&
        !(m.groups[lease.objective].state==GroupState::Reward&&lease.capturer!=w.slot)&&
        w.allies[lease.leader].is_alive()) {
        const int distance=w.distance(lease.objective,o.p);
        if(distance<65535&&o.hp>=.5f*o.max_hp) {
            if(current!=lease.objective) {
                const auto& b=m.groups[lease.objective];
                m.contract.start(lease.objective,tc.round,distance,b.hp,b.capture,config::crew_window);
            }
            m.economic_crew=lease.members;m.economic_capturer=lease.capturer;
            m.rendezvous_until=tc.round+config::crew_window;current=lease.objective;
        }
    }
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
    if(static_cast<int>(tc.round)<m.economic_retry_after||!tc.allow(28000))return std::nullopt;
    const auto start=fuel_left();
    std::array<Participant,objective::max_crew> team{};unsigned n=0,available=0;
    std::array<int,objective::max_crew> reserved;reserved.fill(-1);
    team[n++]={economic_actor({cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range}),o.p,w.slot};available|=1u<<w.slot;
    const auto word=shared_word();
    for(const auto& ally:o.allies) {
        if(!tc.allow(12000)||start-fuel_left()>9000)break;
        const auto it=std::find(w.allies.begin(),w.allies.end(),ally.sdk);
        if(it==w.allies.end()||n>=team.size()||ally.hp<.5f*ally.max_hp)continue;
        const unsigned slot=static_cast<unsigned>(it-w.allies.begin());
        const auto claim=protocol::slot(word,slot);
        if(lease.valid&&(lease.members&(1u<<slot))&&lease.leader!=w.slot)continue;
        // A currently visible body at a live job is physically reserved. No
        // claim without a visible body establishes freshness or reserves work.
        if(claim.objective==protocol::shop||claim.objective==protocol::retreat)continue;
        // Gold is self-only in the SDK; shopping intent comes from the visible
        // body's claim. Visible carried bags are legal to read.
        if(ally.sdk.gem_count()>=config::bank_bag)continue;
        if(protocol::is_group_code(claim.objective)&&claim.objective<w.groups.size()&&
            w.distance(claim.objective,ally.p)<=std::max(1,ally.range)+1&&
            (m.groups[claim.objective].state==GroupState::Partial||m.groups[claim.objective].state==GroupState::Reward))
            reserved[slot]=claim.objective;
        team[n++]={economic_actor(ally),ally.p,slot};available|=1u<<slot;
    }
    struct Candidate { int g;float bound; };
    std::vector<Candidate> candidates;candidates.reserve(w.groups.size());
    for(unsigned g=0;g<w.groups.size();++g) {
        auto& b=m.groups[g];auto& group=w.groups[g];
        if(lease.valid&&lease.objective==static_cast<int>(g)&&!(lease.members&(1u<<w.slot)))continue;
        if(!b.available(tc.round)&&!b.waitable(tc.round,25))continue;
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
    std::array<unsigned,clear_risk_members> counts{};
    for(unsigned index=0;index<limit;++index) {
        if(!tc.allow(22000)||start-fuel_left()>18000)break;
        const int g=candidates[index].g;const auto& group=w.groups[g];
        auto e=encounter(w,m,g,members,counts,tc.round,remaining);
        std::array<objective::Actor,objective::max_crew> actors{};std::array<int,objective::max_crew> arrival{};
        unsigned eligible=0;
        for(unsigned a=0;a<n;++a) {
            actors[a]=team[a].actor;arrival[a]=w.distance(g,team[a].p);
            if(reserved[team[a].slot]>=0&&reserved[team[a].slot]!=g)continue;
            if(arrival[a]>=65535)continue;
            if(!group.field&&arrival[a]>30)continue;
            actors[a].arrival=arrival[a]+(group.field?0:arrival[a]/3);
            eligible|=1u<<a;
        }
        float contested=1;
        for(const auto& enemy:o.enemies)if(enemy.p.chebyshev_distance(group.center)<=6+group.radius)contested=.33f;
        contested=std::min(contested,1/(1+m.pressure(group.center,6+group.radius,tc.round)));
        int active_capturer=-1;
        if(m.groups[g].state==GroupState::Reward)for(unsigned a=0;a<n;++a) {
            if(w.group_at(team[a].p)!=g)continue;
            const auto claim=protocol::slot(word,team[a].slot);
            if(team[a].slot!=w.slot&&claim.objective!=g)continue;
            if(active_capturer<0||team[a].slot<team[active_capturer].slot)active_capturer=a;
        }
        for(unsigned a=0;a<n;++a)if(eligible&(1u<<a)) {
            if(!tc.allow(18000+200*e.members.size())||start-fuel_left()>18000)break;
            if(active_capturer>=0&&a!=static_cast<unsigned>(active_capturer))continue;
            auto solo_encounter=e;
            if(active_capturer==static_cast<int>(a)&&m.groups[g].capture_phase==static_cast<int>(cambc::map::camp_group_capture_type::ally_capturing))
                solo_encounter.capture_remaining=m.groups[g].capture;
            if(m.groups[g].capture_phase==static_cast<int>(cambc::map::camp_group_capture_type::contested)||
                m.groups[g].capture_phase==static_cast<int>(cambc::map::camp_group_capture_type::enemy_capturing))solo_encounter.contested=true;
            auto quote=objective::forecast(solo_encounter,std::span<const objective::Actor>(&actors[a],1),0);
            if(!quote.complete()||!quote.survivable)continue;
            const float rate=contested*quote.reward(gold_price)/std::max(1,quote.finish);
            alternatives[team[a].slot]=std::max(alternatives[team[a].slot],rate);
            float followup=0;unsigned circuit=0;
            if(group.cluster)for(unsigned next=0;next<limit;++next) {
                const int other=candidates[next].g;if(other==g||!w.groups[other].cluster)continue;
                const auto& future=w.groups[other];
                const int travel=group.center.chebyshev_distance(future.center);
                if(travel>25)continue;++circuit;
                const int wait=std::max(0,m.groups[other].ready-static_cast<int>(tc.round)-quote.finish);
                const float reward=future.reward_gems+gold_price*future.reward_gold;
                followup=std::max(followup,reward/(std::max(travel,wait)+actors[a].capture_rounds+1.f));
            }
            bids.push_back({g,1u<<team[a].slot,team[a].slot,contested*quote.reward(gold_price),static_cast<float>(quote.finish),0,circuit>=3?.5f*followup:0});
        }
        if(group.strength<=0||m.groups[g].state==GroupState::Reward||n<2)continue;
        // Nearby crew subsets, up to six actors. Each gets real damage and its
        // own incoming mitigation, not the caller's stats multiplied by count.
        std::array<unsigned,objective::max_crew> order{};for(unsigned a=0;a<n;++a)order[a]=a;
        std::sort(order.begin(),order.begin()+n,[&](auto a,auto b){return arrival[a]<arrival[b];});
        std::array<objective::Actor,objective::max_crew> crew{};
        std::array<unsigned,objective::max_crew> crew_slots{};unsigned count=0,mask=0,capturer=0;
        for(unsigned k=0;k<n;++k) {
            if(!tc.allow(18000+200*e.members.size())||start-fuel_left()>18000)break;
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
    if(chosen.objective<0){m.economic_retry_after=tc.round+8;return std::nullopt;}
    const auto& belief=m.groups[chosen.objective];
    m.economic_crew=chosen.crew;m.economic_capturer=chosen.capturer;m.economic_rate=alternatives[w.slot];
    m.rendezvous_until=tc.round+std::min(40,w.distance(chosen.objective,o.p)+8);
    m.contract.start(chosen.objective,tc.round,w.distance(chosen.objective,o.p),belief.hp,belief.capture,
        std::popcount(chosen.crew)>1?config::crew_window:config::contract_window);
    tc.guard();return Goal{GoalKind::Farm,chosen.objective};
}
}
#endif
