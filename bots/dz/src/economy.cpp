#include "economy.h"
#if DZ_ECONOMY_V2
#include "allocation.h"
#include "macro_value.h"
#include "objective_math.h"
#include "siege.h"
#include "crew.h"
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
struct Participant { objective::Actor actor;vec2 p;unsigned slot;int range=1;unsigned handle=0; };
objective::Encounter encounter(const StaticWorld& w,const Memory& m,int g,std::span<ClearMember> members,std::span<unsigned> counts,int round,int horizon) {
    const auto& group=w.groups[g];const auto& belief=m.groups[g];
    unsigned distinct=0;
    for(unsigned k=0;k<m.member_hp[g].size();++k) {
        if(m.member_hp[g][k]<=0)continue;
        const ClearMember member{m.member_hp[g][k],m.member_strength[g][k]};
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
// The macro planner orders complete farm/delivery/equipment itineraries in the
// same finite-horizon currency. It does not replace the executor's admission
// checks, or turn an estimated delivery/risk cost into a safety certificate.
Goal macro_goal(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc,
                Goal work,int altar,int altar_distance,int remaining) {
    const int home=w.home.get(o.p);
    const auto owned=cambc::self().item_count();
    auto reduction=[&](cambc::item_family family) {
        float value=0;
        for(auto stat:{cambc::item_stat::strength,cambc::item_stat::focus,cambc::item_stat::health}) {
            const auto emblem=cambc::get_item_enum(family,stat,false);
            if(owned[emblem])value=std::max(value,emblem.passive_magnitude());
        }
        return value;
    };
    const float tribute=reduction(cambc::item_family::tribute);
    auto bank_time=[&](int bag) {
        const auto delay=tribute_delay(bag,cambc::constants::submit_gem_base_duration,cambc::constants::submit_gem_minimum_duration,
            cambc::constants::submit_gem_duration_multiplier,tribute);
        return delay.supported()?delay.rounds:65535;
    };
    auto relinquish=[&](Goal goal) {
        m.contract.objective=-1;m.economic_crew=0;
        return goal;
    };
    const int direct_bank=o.bag>0&&altar>=0&&altar_distance<65535?altar_distance+bank_time(o.bag):65535;
    if(o.bag>0&&o.submitted+o.bag>=static_cast<int>(cambc::constants::winning_gems)&&direct_bank<=remaining)
        return relinquish({GoalKind::Bank,altar});
    if(direct_bank<=remaining&&remaining-direct_bank<=config::contract_window)
        return relinquish({GoalKind::Bank,altar}); // No room for another finite contract before delivery.
    if(m.shopping_since>=0) {
        if(home>0&&static_cast<int>(tc.round)<=m.shopping_deadline)return {GoalKind::Home};
        m.shopping_since=-1;m.shopping_deadline=-1;
    }
    if(o.hp<.3f*o.max_hp)return {GoalKind::Home};
    auto& commitment=m.opening_commitment;
    if(altar>=0) {
        const bool convert=commitment.executing;commitment={};
        if(convert&&o.bag>0)return relinquish({GoalKind::Bank,altar});
    }
    if(commitment.active()) {
        const int resource=commitment.resource;
        const bool done=resource>=0&&resource<static_cast<int>(m.groups.size())&&m.groups[resource].state==GroupState::Respawning;
        if(commitment.advance(tc.round,o.bag,o.gold,done)) {
            if(auto goal=begin_opening(w,m,o,tc,commitment.altar))return *goal;
            // A changed route/equipment quote may still be rebuilding. Keep the
            // bounded commitment while doing useful work; never re-promise it
            // indefinitely after one more farm job.
        }
    }
    const auto* opening=altar<0?best_opening(m,o,tc):nullptr;
    const int opening_work=opening?opening->rounds:65535;
    const int homeward=home<65535?std::min(home,cambc::constants::recall_time)+1:65535;
    const macro::Context context{remaining,static_cast<float>(o.bag),m.economic_gem_rate,objective::gold_price(remaining),m.economic_gold_rate};
    std::array<macro::Option,4> choices{};
    choices[0].kind=macro::Kind::Farm;
    // Refresh the actual retained job instead of subtracting elapsed wall time
    // from a stale quote while the body was blocked, healing or interrupted.
    if(work.kind==GoalKind::Farm&&work.index>=0&&tc.allow(13000)) {
        const int g=work.index;const auto& group=w.groups[g];
        std::array<ClearMember,clear_risk_members> members{};std::array<unsigned,clear_risk_members> counts{};
        auto e=encounter(w,m,g,members,counts,tc.round,remaining);
        std::array<objective::Actor,objective::max_crew> actors{};unsigned n=1,cap=0;
        actors[0]=economic_actor({cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range});
        actors[0].arrival=w.distance(g,o.p);
        bool roster=true;
        for(unsigned slot=0;slot<w.allies.size();++slot)if(slot!=w.slot&&(m.economic_crew&(1u<<slot))) {
            const auto ally=std::find_if(o.allies.begin(),o.allies.end(),[&](const auto& a){return a.sdk==w.allies[slot];});
            if(ally==o.allies.end()||n==actors.size()||!tc.allow(11000)){roster=false;break;}
            if(slot==m.economic_capturer)cap=n;
            actors[n]=economic_actor(*ally);actors[n++].arrival=w.distance(g,ally->p);
        }
        if(m.groups[g].state==GroupState::Reward&&w.group_at(o.p)==g&&m.economic_capturer==w.slot&&
            m.groups[g].capture_phase==static_cast<int>(cambc::map::camp_group_capture_type::ally_capturing))
            e.capture_remaining=m.groups[g].capture;
        const auto q=objective::forecast(e,std::span<const objective::Actor>(actors.data(),n),cap);
        if(roster&&q.complete()&&q.survivable) {
            float discount=1/(1+m.pressure(group.center,6+group.radius,tc.round));
            int delivery=-1;
            if(altar>=0&&!group.tiles.empty()) {
                // Static endpoint estimate, not dynamic reachability evidence.
                // The current access planner and executor still check camps.
                const int distance=w.altar_distance(altar,group.tiles.front());
                if(distance<65535)delivery=distance+bank_time(o.bag+static_cast<int>(q.gems));
            } else if(opening&&opening->quality==gate::Quality::Ready) {
                // Farm -> Home -> opening -> delivery. The opening quote keeps
                // current equipment, so a funded upgrade is not invented here.
                const int home_after=std::min<int>(w.home.get(group.tiles.front()),cambc::constants::recall_time)+1;
                delivery=home_after+opening_work+opening->delivery+bank_time(o.bag+static_cast<int>(q.gems));
            }
            choices[0]={macro::Kind::Farm,g,q.finish,delivery,discount*q.gems,discount*q.gold_low,0,
                (1-discount)*o.bag,true};
        } else if(roster&&q.quality==objective::Quality::BeyondHorizon&&direct_bank<=remaining)
            return relinquish({GoalKind::Bank,altar});
        // A missing crew view / incomplete quote retains the contract. It does
        // not invent zero work and induce a spurious bank/shop interruption.
    }
    const float local_loss=enemy_danger(o.p,o);
    if(direct_bank<=remaining)choices[1]={macro::Kind::Bank,altar,direct_bank,0,0,0,0,
        std::min(1.f,local_loss*direct_bank/std::max(1.f,o.hp))*o.bag,true};
    if(home<65535&&o.enemies.empty()&&o.gold>=static_cast<int>(cambc::item_type::monster_shard_of_strength.cost())&&tc.allow(7000)) {
        const int recall=std::max(1,static_cast<int>(std::ceil(cambc::constants::recall_time*(1-reduction(cambc::item_family::home)))));
        const int outward=home>recall&&channel_safe(w,o,tc)?recall:home;
        const int visit=opening?outward+1:outward+home+1;
        if((m.shop_quote_gold!=o.gold||static_cast<int>(tc.round)-m.shop_quote_round>=16)&&tc.allow(17000)) {
            const auto quote=shop_visit(tc,o,std::max(0,remaining-visit));
            m.shop_quote=quote;m.shop_quote_gold=o.gold;m.shop_quote_round=tc.round;
        }
        if(m.shop_quote.valid&&m.shop_quote_gold==o.gold&&visit<=remaining) {
            // A cached value cannot retain more horizon than its original quote.
            const float age_scale=std::clamp((remaining-visit)/static_cast<float>(std::max(1,remaining-visit+static_cast<int>(tc.round)-m.shop_quote_round)),0.f,1.f);
            const int after=altar>=0?altar_distance+bank_time(std::max(1,o.bag)):
                opening&&opening->quality==gate::Quality::Ready?opening_work+opening->delivery+bank_time(std::max(1,o.bag)):-1;
            choices[2]={macro::Kind::Shop,-1,visit,o.bag>0?after:(altar>=0?0:after),0,0,m.shop_quote.value*age_scale,0,true};
        }
    }
    if(opening) {
        bool reserved=false;
        const auto word=shared_word();
        if(opening->count)for(const auto& ally:o.allies) {
            const auto it=std::find(w.allies.begin(),w.allies.end(),ally.sdk);
            if(it==w.allies.end())continue;const unsigned slot=it-w.allies.begin();
            // Only a visible, physically committed worker reserves the cut.
            // An unchanged old claim cannot prove remote liveness or freshness.
            if(protocol::slot(word,slot).objective==opening->cuts[0].group&&
                w.distance(opening->cuts[0].group,ally.p)<=ally.range+1&&ally.hp>.5f*ally.max_hp)reserved=true;
        }
        if(!reserved&&opening->quality==gate::Quality::Ready)
            choices[3]={macro::Kind::Gate,opening->altar,homeward+opening_work,opening->delivery+bank_time(std::max(1,o.bag)),0,0,0,0,true};
        else if(!reserved&&opening->quality==gate::Quality::Scout)
            choices[3]={macro::Kind::Gate,opening->altar,homeward+opening_work,-1,0,0,0,0,true};
    }
    // Only compare a full contract quote with interruptions. If the forecast
    // was cut short, preserve the productive fallback; a certain-win bank above
    // remains available independently of the expensive search.
    if(work.kind==GoalKind::Farm&&!choices[0].feasible)return work;
    const int selected=macro::choose(context,choices,choices[0].feasible?0:-1);
#if DZ_TRACE
    if(selected>=0&&tc.round%20==0){TraceScope scope;trace("DZ_MACRO round=%u body=%u action=%d farm=%.1f bank=%.1f shop=%.1f gate=%.1f bag=%d gold=%d horizon=%d\n",
        tc.round,static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),selected,
        macro::value(context,choices[0]),macro::value(context,choices[1]),macro::value(context,choices[2]),macro::value(context,choices[3]),o.bag,o.gold,remaining);}
#endif
    if(selected==1)return relinquish({GoalKind::Bank,altar});
    if(selected==2) {
        if(opening&&opening->quality==gate::Quality::Ready&&!commitment.active())
            commitment.start(opening->altar,-1,o.bag,o.gold,tc.round+choices[2].work);
        commit_shop_visit(m.shop_quote);m.shopping_since=tc.round;m.shopping_deadline=tc.round+home+15;
#if DZ_TRACE
        {TraceScope scope;trace("DZ_SHOP_PLAN round=%u body=%u item=%u purchases=%u cost=%d value=%.2f gold=%d\n",
            tc.round,static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),static_cast<unsigned>(m.shop_quote.item),
            m.shop_quote.purchases,m.shop_quote.cost,m.shop_quote.value,o.gold);}
#endif
        return relinquish({GoalKind::Home});
    }
    if(selected==3)if(auto goal=begin_opening(w,m,o,tc,choices[3].id))return *goal;
    if(selected==0&&opening&&opening->quality==gate::Quality::Ready&&!commitment.active()&&
        choices[0].delivery>=0&&choices[0].work+choices[0].delivery<=remaining&&std::isfinite(macro::value(context,choices[3]))) {
        commitment.start(opening->altar,work.index,o.bag,o.gold,tc.round+choices[0].work);
#if DZ_TRACE
        {TraceScope scope;trace("DZ_OPENING_COMMIT round=%u body=%u altar=%d after=%d deadline=%d\n",tc.round,
            static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),commitment.altar,work.index,commitment.deadline);}
#endif
    }
    return work;
}
}
bool crew_ready(const StaticWorld& w,const Memory& m,const Observation& o,int g,const TurnContext& tc) {
    if(m.crew_execution.managed&&m.crew_execution.round==static_cast<int>(tc.round)&&m.crew_execution.group==g)
        return m.crew_execution.fire;
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
    const auto incoming_lease=protocol::compact::lease(shared_word(),tc.round);
    if(m.legacy(tc.round)&&altar>=0&&std::popcount(m.economic_crew)<2&&
        !(incoming_lease.valid&&(incoming_lease.members&(1u<<w.slot))))return std::nullopt;
    m.race.observe(tc.round,o.submitted,cambc::global_submitted_gems(cambc::team::enemy));
    float bags=o.bag;for(const auto& a:o.allies)bags+=a.sdk.gem_count();
    const int remaining=m.race.remaining(tc.round,cambc::constants::max_rounds,cambc::constants::winning_gems,bags);
    const float gold_price=objective::gold_price(remaining);
    m.access_group=-1;m.access_member=-1;
    if(altar<0&&o.enemies.empty())quote_opening(w,m,o,tc);
    if(m.shopping_since>=0||o.hp<.3f*o.max_hp)
        return macro_goal(w,m,o,tc,{GoalKind::Home},altar,altar_distance,remaining);
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
            m.contract.progressing(tc.round,distance,b.hp,b.capture)) return macro_goal(w,m,o,tc,{GoalKind::Farm,current},altar,altar_distance,remaining);
        if(helper_done||!b.available(tc.round))m.contract.objective=-1;
        else m.release(tc.round);
    }
    if(static_cast<int>(tc.round)<m.economic_retry_after||!tc.allow(28000))
        return macro_goal(w,m,o,tc,{GoalKind::Home},altar,altar_distance,remaining);
    const auto start=fuel_left();
    std::array<Participant,objective::max_crew> team{};unsigned n=0,available=0;
    std::array<int,objective::max_crew> reserved;reserved.fill(-1);
    team[n++]={economic_actor({cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range}),o.p,w.slot,o.range,
        static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self()))};available|=1u<<w.slot;
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
        team[n++]={economic_actor(ally),ally.p,slot,ally.range,static_cast<unsigned>(static_cast<cambc::handle_champion_t>(ally.sdk))};available|=1u<<slot;
    }
    struct Candidate { int g;float bound; };
    std::vector<Candidate> candidates;candidates.reserve(w.groups.size());
    int cold_resource=-1;float cold_rate=0;
    for(unsigned g=0;g<w.groups.size();++g) {
        auto& b=m.groups[g];auto& group=w.groups[g];
        if(lease.valid&&lease.objective==static_cast<int>(g)&&!(lease.members&(1u<<w.slot)))continue;
        if(!b.available(tc.round)&&!b.waitable(tc.round,25))continue;
        const int d=w.distance_floor(g,o.p);
        const float value=group.reward_gems+gold_price*group.reward_gold;
        if(!group.field&&group.strength<=0&&value>0) {
            const float bound=value/(d+std::ceil(std::max(0.f,b.hp)/std::max(1.f,o.strength*o.camp_damage))+cambc::constants::capture_time+1);
            if(bound>cold_rate){cold_rate=bound;cold_resource=g;}
        }
        if(d>30&&!group.field)continue;
        if(value>0)candidates.push_back({static_cast<int>(g),value/(d+6.f)});
    }
    std::sort(candidates.begin(),candidates.end(),[](auto a,auto b){return a.bound>b.bound||(a.bound==b.bound&&a.g<b.g);});
    // Expensive infeasible monster bounds must not occupy the entire shortlist
    // while a reachable non-damaging production job is never even priced.
    const auto production=std::find_if(candidates.begin(),candidates.end(),[&](auto c){return w.groups[c.g].strength<=0&&w.groups[c.g].field&&w.distance(c.g,o.p)<65535;});
    if(production!=candidates.end())std::rotate(candidates.begin(),production,production+1);
    std::array<float,objective::max_crew> alternatives{};
    float gem_rate=0,gold_rate=0,continuation_rate=-1;
    std::vector<economy::Bid> bids;bids.reserve(48);
    const unsigned limit=std::min<unsigned>(8,candidates.size());
    std::array<ClearMember,clear_risk_members> members{};
    std::array<unsigned,clear_risk_members> counts{};
    unsigned spatial_quotes=0;
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
            if(team[a].slot==w.slot&&rate>continuation_rate) {
                continuation_rate=rate;
                gem_rate=contested*quote.gems/std::max(1,quote.finish);
                gold_rate=contested*quote.gold_low/std::max(1,quote.finish);
            }
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
        std::array<objective::Actor,objective::max_crew> crew_actors{};
        std::array<crew::Unit,objective::max_crew> spatial{};
        std::array<unsigned,objective::max_crew> crew_slots{};unsigned count=0;
        const unsigned eligible_count=std::popcount(eligible);
        const unsigned first_trial=std::clamp(m.coalition_cursor[g],2u,std::max(2u,eligible_count));
        for(unsigned k=0;k<n;++k) {
            if(!tc.allow(18000+200*e.members.size())||start-fuel_left()>18000)break;
            const auto a=order[k];if(!(eligible&(1u<<a)))continue;
            crew_slots[count]=team[a].slot;crew_actors[count]=actors[a];
            spatial[count]={team[a].slot,team[a].handle,{team[a].p.x,team[a].p.y},actors[a].hp,actors[a].max_hp,actors[a].damage,
                actors[a].incoming_factor,team[a].range,actors[a].arrival};
            ++count;
            if(count<first_trial)continue;
            if(spatial_quotes>=2)break;
            ++spatial_quotes;
            m.coalition_cursor[g]=economy::next_coalition_size(count,eligible_count);
            const auto quote=crew_quote(w,m,g,std::span<const crew::Unit>(spatial.data(),count),cambc::constants::capture_time+1,tc);
            if(!quote.complete)continue;
            unsigned cap=0;bool have_cap=false;
            for(unsigned c=0;c<count;++c)if(quote.members&(1u<<crew_slots[c])) {
                if(!have_cap||crew_actors[c].gold_multiplier>crew_actors[cap].gold_multiplier||
                    (crew_actors[c].gold_multiplier==crew_actors[cap].gold_multiplier&&crew_actors[c].capture_rounds<crew_actors[cap].capture_rounds)){cap=c;have_cap=true;}
            }
            if(!have_cap)continue;
            const float boost=group.cluster&&crew_actors[cap].prospector?1.25f:1.f;
            const float value=std::floor(group.reward_gems*boost)+gold_price*std::floor(group.reward_gold*boost*crew_actors[cap].gold_multiplier);
            bids.push_back({g,quote.members,crew_slots[cap],contested*value,static_cast<float>(quote.finish)});
            break; // First viable priced coalition; omitted helpers are never committed.
        }
    }
    for(auto& bid:bids)if(std::popcount(bid.crew)>1) {
        float best=0,total=0;
        for(unsigned slot=0;slot<alternatives.size();++slot)if(bid.crew&(1u<<slot)){total+=alternatives[slot];best=std::max(best,alternatives[slot]);}
        bid.opportunity=total-best;
    }
    m.economic_gem_rate=gem_rate;m.economic_gold_rate=gold_rate;
    const auto assignments=economy::allocate(bids,available);const auto chosen=assignments[w.slot];
    if(chosen.objective<0){
        if(cold_resource>=0)m.field_needed=cold_resource;
        m.economic_retry_after=tc.round+(cold_resource>=0?1:8);
        return macro_goal(w,m,o,tc,{GoalKind::Home},altar,altar_distance,remaining);
    }
    const auto& belief=m.groups[chosen.objective];
    m.economic_crew=chosen.crew;m.economic_capturer=chosen.capturer;m.economic_rate=alternatives[w.slot];
    m.rendezvous_until=tc.round+std::min(40,w.distance(chosen.objective,o.p)+8);
    m.contract.start(chosen.objective,tc.round,w.distance(chosen.objective,o.p),belief.hp,belief.capture,
        std::popcount(chosen.crew)>1?config::crew_window:config::contract_window);
    tc.guard();return macro_goal(w,m,o,tc,{GoalKind::Farm,chosen.objective},altar,altar_distance,remaining);
}
}
#endif
