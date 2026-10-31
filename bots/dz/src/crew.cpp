#include "crew.h"
#if DZ_ECONOMY_V2
#include "economy.h"
#include "access_route.h"
#include "objective_math.h"
#include "crew_traffic.h"
#include <bit>

namespace dz {
crew::Unit crew_unit(const SeenChampion& seen,unsigned slot) {
    const auto actor=economic_actor(seen);
    return {slot,static_cast<unsigned>(static_cast<cambc::handle_champion_t>(seen.sdk)),{seen.p.x,seen.p.y},
        actor.hp,actor.max_hp,actor.damage,actor.incoming_factor,seen.range,actor.arrival,actor.gold_multiplier,actor.capture_rounds,
        actor.health_growth,actor.damage_growth,actor.health_damage_growth,actor.power_health,actor.power_strength,actor.inventory_known,actor.prospector};
}
namespace {
struct CampSet { std::array<crew::Monster,crew::max_camps> camps{};unsigned count=0;bool complete=true; };
CampSet camp_set(const StaticWorld& w,const Memory& m,int g) {
    CampSet result;const auto& group=w.groups[g];
    if(group.tiles.size()>crew::max_camps){result.complete=false;return result;}
    for(unsigned k=0;k<group.tiles.size();++k)if(m.member_hp[g][k]>0) {
        const auto p=group.tiles[k];
        result.camps[result.count++]={k,{p.x,p.y},m.member_hp[g][k],m.member_strength[g][k],group.attack_ranges[k]};
    }
    return result;
}
int layout(const StaticWorld& w,const Memory& m,Memory::FormationCache& cache,int group,std::span<const crew::Unit> units,std::span<const crew::Monster> camps,const TurnContext& tc) {
    const unsigned outside=m.topology_revision-m.group_topology[group];
    const unsigned offset=cache.camps>=camps.size()?cache.camps-camps.size():cache.camps;
    const bool matches=cache.group==group&&(cache.expires>static_cast<int>(tc.round)||cache.search.stage==crew::SequenceSearch::Stage::Done)&&cache.topology==outside&&
        cache.generation==m.conversions[group]&&offset+camps.size()==cache.camps&&
        crew::same_roles(units,std::span<const crew::Unit>(cache.roster.data(),cache.units))&&
        crew::same_scene(camps,std::span<const crew::Monster>(cache.scene.data()+offset,camps.size()));
    if(matches&&cache.search.stage==crew::SequenceSearch::Stage::Done)return offset;
    // A different speculative quote cannot erase the unfinished job. A changed
    // roster/scene for the SAME job invalidates it; an expired job is replaceable.
    if(!matches&&cache.group!=group&&cache.group>=0&&cache.expires>static_cast<int>(tc.round)&&
        cache.generation==m.conversions[cache.group]&&cache.topology==m.topology_revision-m.group_topology[cache.group]&&
        cache.pending())return -1;
    if(!matches) {
        // Mutate the logical job, never copy the BFS's unvisited storage.
        tc.guard();cache.group=group;cache.topology=outside;cache.generation=m.conversions[group];cache.expires=tc.round+config::crew_window;
        cache.units=units.size();cache.camps=camps.size();
        std::copy(units.begin(),units.end(),cache.roster.begin());std::copy(camps.begin(),camps.end(),cache.scene.begin());
        cache.search.begin(units,camps,cambc::map::width(),cambc::map::height());
        cache.progression={};cache.progression_work=-1;
    }
    const auto started=fuel_left();unsigned operations=0;
    const bool complete=cache.search.resume(units,std::span<const crew::Monster>(cache.scene.data(),cache.camps),[&](Tile tile,unsigned cleared) {
        const vec2 p{tile.x,tile.y};if(!w.walkable(p))return false;
        const int g=w.group_at(p);if(g<0)return true;
        const int member=w.tile_members[tile.y*cambc::map::width()+tile.x];
        if(g==group)for(unsigned k=0;k<cleared;++k)if(cache.scene[k].member==static_cast<unsigned>(member))return true;
        const auto& b=m.groups[g];
        return member>=0&&!access::member_blocks(m.member_hp[g][member]>0,b.state==GroupState::Respawning,b.ready,tc.round+1);
    },[&](Tile p){return w.home_distance(p);},[&]{
        if(!tc.allow(10000)||started-fuel_left()>=14000)return false;
        ++operations;return true;
    });
    tc.guard();if(operations)cache.expires=tc.round+config::crew_window;
    return complete?static_cast<int>(cache.camps-camps.size()):-1;
}
void price_progression(const StaticWorld& w,const Memory& m,Memory::FormationCache& cache,int g,int work,const TurnContext& tc) {
    auto& p=cache.progression;
    if(p.stage==crew::Progression::Stage::Empty) {
        if(!tc.allow(16000))return;
        const auto& group=w.groups[g];p.stage=crew::Progression::Stage::Done;
        // Only a complete catalog can price the next full renewable objective.
        // Partial suffixes, large jobs or unavailable delivery retain raw value.
        if(cache.camps!=group.tiles.size()||cache.camps>8||group.tiles.empty())return;
        int delivery=65535;
        for(unsigned a=0;a<w.altars.size();++a) {
            int d=0;for(auto tile:group.tiles)d=std::max(d,w.altar_distance(a,tile));
            delivery=std::min(delivery,d);
        }
        const auto bank=tribute_delay(group.reward_gems,cambc::constants::submit_gem_base_duration,
            cambc::constants::submit_gem_minimum_duration,cambc::constants::submit_gem_duration_multiplier,0);
        if(delivery>=65535||!bank.supported())return;
        std::array<team::Cash,crew::max_units> reports{};
        unsigned until=tc.round+team::lifetime(w.allies.size());
        for(unsigned u=0;u<cache.units;++u) {
            reports[u]=m.team.budget(cache.roster[u].slot,tc.round,w.allies.size());
            if(cache.roster[u].slot==w.slot) {
                const unsigned gold=cambc::self().gold_count();reports[u]={tc.round,gold,gold,true};
            }
        }
        std::array<crew::Shard,2> shards{};
        for(unsigned s=0;s<2;++s) {
            const auto info=cambc::get_item_enum(cambc::item_family::power,s?cambc::item_stat::health:cambc::item_stat::strength).info();
            if(!info.result)continue;const auto result=info.result->info();
            const int points=s?info.health_points:info.strength_points,result_points=s?result.health_points:result.strength_points;
            if(points<=0||result_points<0)continue;
            shards[s]={info.cost,info.combine_count,static_cast<unsigned>(points),static_cast<unsigned>(result_points)};
        }
        p.begin(std::span<const crew::Unit>(cache.roster.data(),cache.units),std::span<const team::Cash>(reports.data(),cache.units),shards,
            tc.round,until,std::max(0,static_cast<int>(cambc::constants::max_rounds-tc.round)-work),
            2*cache.search.phases[0].return_rounds+cambc::constants::recall_time+1,delivery+bank.rounds,
            group.sdk.max_respawn_timer(),cambc::constants::recall_time,group.reward_gems,group.reward_gold,group.cluster);
    }
    if(tc.round>p.expires){p.stage=crew::Progression::Stage::Done;return;}
    std::array<crew::Monster,crew::max_camps> full{};
    for(unsigned c=0;c<cache.camps;++c){full[c]=cache.scene[c];full[c].hp=w.groups[g].initial_hp[full[c].member];}
    const auto started=fuel_left();
    if(p.pending())cache.expires=tc.round+config::crew_window;
    p.resume(std::span<const crew::Unit>(cache.roster.data(),cache.units),std::span<const crew::Monster>(full.data(),cache.camps),cache.search,
        [&]{return tc.allow(10000)&&started-fuel_left()<6000;});
}
}
void progress_crew_layout(const StaticWorld& w,const Memory& m,const TurnContext& tc) {
    auto advance=[&](Memory::FormationCache& c) {
        if(!c.pending()||c.group<0||c.group>=static_cast<int>(m.groups.size())||!tc.allow(25000))return;
        if(c.expires<=static_cast<int>(tc.round)||c.topology!=m.topology_revision-m.group_topology[c.group]||c.generation!=m.conversions[c.group])return;
        if(c.search.pending())layout(w,m,c,c.group,std::span<const crew::Unit>(c.roster.data(),c.units),std::span<const crew::Monster>(c.scene.data(),c.camps),tc);
        else {
            if(c.progression_work<0) {
                const auto started=fuel_left();
                const auto q=crew::quote(std::span<const crew::Unit>(c.roster.data(),c.units),std::span<const crew::Monster>(c.scene.data(),c.camps),c.search,
                    0,cambc::constants::capture_time+1,cambc::constants::recall_time,cambc::constants::max_rounds-tc.round,
                    [&]{return tc.allow(10000)&&started-fuel_left()<6000;});
                if(q.reason==crew::SequenceReason::Budget)return;
                if(!q.complete){c.progression.stage=crew::Progression::Stage::Done;return;}
                int arrival=0;for(unsigned u=0;u<c.units;++u)arrival=std::max(arrival,c.roster[u].arrival);
                c.progression_work=arrival+q.finish;
            }
            price_progression(w,m,c,c.group,c.progression_work,tc);
        }
    };
    if(m.crew_live)advance(*m.crew_live);
    if(m.crew_draft)advance(*m.crew_draft);
}

void prepare_crew_reward(const StaticWorld& w,Memory& m,const Observation& o,int g,const TurnContext& tc) {
    auto& reward=m.crew_reward;auto& cache=m.crew_layout();
    if(cache.group!=g||cache.generation!=m.conversions[g]||cache.camps!=w.groups[g].tiles.size()||
        cache.topology!=m.topology_revision-m.group_topology[g]||cache.search.stage!=crew::SequenceSearch::Stage::Done)return;
    if(reward.group!=g||reward.generation!=m.conversions[g]) {
        reward={g,static_cast<int>(tc.round),o.gold,o.bag,m.conversions[g]};
        cache.progression={}; // Reprice at the actual payout, with today's own cash.
    }
    if(reward.priced||!tc.allow(18000))return;
    price_progression(w,m,cache,g,0,tc);
    if(cache.progression.pending())return;
    const auto plan=cache.progression.best(w.slot,tc.round);
    reward.priced=true;
    if(plan.valid&&plan.purchases) {
        const auto me=economic_actor({cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range});
        const auto& group=w.groups[g];const float boost=group.cluster&&me.prospector?1.25f:1.f;
        reward.required_gold=std::floor(group.reward_gold*boost*me.gold_multiplier);
        reward.required_gems=std::floor(group.reward_gems*boost);
        reward.stat=plan.stat;reward.value=plan.gain;reward.promised=true;
#if DZ_TRACE
        {TraceScope scope;trace("DZ_CREW_REWARD_PLAN round=%u group=%d slot=%u stat=%u gain=%.2f cash=%d\n",tc.round,g,w.slot,plan.stat,plan.gain,o.gold);}
#endif
    }
}
CrewQuote crew_quote(const StaticWorld& w,const Memory& m,int group,std::span<const crew::Unit> given,int capture,const TurnContext& tc,bool investments) {
    if(!tc.allow(19000)||given.empty()||given.size()>crew::max_units)return {};
    // A free planner uses the otherwise idle live workspace for the incumbent
    // counterfactual. Keep its geometry while the augmented roster is priced.
    auto& cache=investments?m.crew_proposal():m.crew_layout();
    std::array<crew::Unit,crew::max_units> ordered{};std::copy(given.begin(),given.end(),ordered.begin());
    std::sort(ordered.begin(),ordered.begin()+given.size(),[](auto a,auto b){return a.slot<b.slot;});
    const auto units=std::span<const crew::Unit>(ordered.data(),given.size());
    unsigned proposed=0;for(auto unit:units)proposed|=1u<<unit.slot;
    if(m.crew_decline.group==group&&m.crew_decline.members==proposed&&static_cast<int>(tc.round)<m.crew_decline.until)
        return {false,0,0,CrewQuoteStatus::Unsupported};
    const auto set=camp_set(w,m,group);if(!set.complete||!set.count)return {false,0,0,CrewQuoteStatus::Unsupported};
    const auto camps=std::span<const crew::Monster>(set.camps.data(),set.count);
    const int first=layout(w,m,cache,group,units,camps,tc);
    if(first<0)return {false,0,0,
        cache.pending()?CrewQuoteStatus::Budget:CrewQuoteStatus::Formation};
    int arrival=0;
    for(unsigned u=0;u<units.size();++u)arrival=std::max(arrival,units[u].arrival);
    const auto model_start=fuel_left();
    const auto q=crew::quote(units,camps,cache.search,first,capture,cambc::constants::recall_time,cambc::constants::max_rounds-tc.round,
        [&]{return tc.allow(10000)&&model_start-fuel_left()<6000;});
#if DZ_TRACE
    static unsigned next_price_trace=0;
    if(w.slot==0&&tc.round>=next_price_trace) {
        next_price_trace=tc.round+50;const auto& p=cache.search.phases[first];TraceScope scope;
        trace("DZ_CREW_PRICE round=%u group=%d reason=%d finish=%d count=%u first=%d n=%zu hp=%.0f,%.0f damage=%.0f,%.0f raw=%.0f,%.0f escape=%.0f,%.0f approach=%.0f,%.0f\n",
            tc.round,group,static_cast<int>(q.reason),q.finish,cache.search.count,first,units.size(),units[0].hp,units[1].hp,units[0].damage,units[1].damage,
            p.raw[0],p.raw[1],p.escape[0],p.escape[1],p.approach_loss[0],p.approach_loss[1]);
    }
#endif
    if(!q.complete)return {false,0,0,q.reason==crew::SequenceReason::Budget?CrewQuoteStatus::Budget:CrewQuoteStatus::Model};
    if(arrival+q.finish>static_cast<int>(cambc::constants::max_rounds-tc.round))return {false,0,0,CrewQuoteStatus::Horizon};
    cache.progression_work=arrival+q.finish;
    if(investments)price_progression(w,m,cache,group,arrival+q.finish,tc);
    else cache.progression.stage=crew::Progression::Stage::Done;
    if(cache.progression.pending()||cache.progression.stage==crew::Progression::Stage::Empty)
        return {false,0,0,CrewQuoteStatus::Budget};
    unsigned mask=0;for(unsigned u=0;u<units.size();++u)mask|=1u<<units[u].slot;
    return {true,mask,arrival+q.finish,CrewQuoteStatus::Ready,arrival};
}
bool build_crew_field(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc) {
    auto& cache=m.crew_field;
    if(!cache.pending||!m.crew_execution.managed||!o.enemies.empty()||o.channel()||
        !requested_navigation_fits(fuel_left(),w.field_budget()+2000,true))return false;
    const vec2 root{cache.root.x,cache.root.y};if(!w.walkable(root)){cache.pending=false;return false;}
    // Static terrain/spawn occupancy gives a reusable conservative route.
    // Actors are handled by step/retry at execution, not baked into this cache.
    auto spawns=w.camp_spawns;
    const int group=m.crew_execution.group;
    if(group>=0&&group<static_cast<int>(m.groups.size())&&m.groups[group].state!=GroupState::Respawning) {
        LocalMask live;live.load(spawns);
        for(unsigned k=0;k<w.groups[group].tiles.size();++k)if(m.member_hp[group][k]<=0)live.set(w.groups[group].tiles[k],false);
        live.store(spawns);
    }
    auto blocked=w.blocked|spawns;blocked.set(root,false);
    const bool own_spawn=w.is_spawn(o.p)&&o.p!=root;if(own_spawn)blocked.set(o.p,false);
    RootSet roots;roots.set(root);auto field=std::make_unique<cambc::distance_field>();
    field->compute(blocked,roots.board(),w.visited);tc.guard();cache.field=std::move(field);
    cache.expires=own_spawn?static_cast<int>(tc.round)+1:cambc::constants::max_rounds+1;cache.pending=false;
    return true;
}
Goal crew_action(Goal goal,StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc) {
    auto& state=m.crew_execution;
    [[maybe_unused]] const int previous_focus=state.focus;
    state.direct_step=false;
    const auto traffic_word=shared_word();
    // Fair, dated cohort records outlive the single transient invitation word.
    // An idle/redundant body must not park on another crew's roles or capture.
    if(!m.siege_task.active()&&!o.channel()&&o.enemies.empty()&&o.camps_complete&&tc.allow(12000)&&
        (goal.kind==GoalKind::Idle||goal.kind==GoalKind::YieldSpawn||goal.kind==GoalKind::Farm||
         (goal.kind==GoalKind::Home&&o.hp>=o.max_hp-.01f&&m.shopping_since<0))) {
        for(const auto& record:m.team.cohorts) {
            if(!record.valid||record.objective<0||record.objective>=static_cast<int>(w.groups.size()))continue;
            const int job=record.objective;const auto owner=m.team.cohort(job,traffic_word,tc.round,w.allies.size());
            if(!owner.valid||(owner.members&(1u<<w.slot))||m.groups[job].state==GroupState::Respawning||
                (goal.kind==GoalKind::Farm&&goal.index!=job))continue;
            // Require an actual visible claimant nearby. A dated plan without
            // observed presence cannot force an outsider's movement.
            bool present=false,adjacent=false;int member_range=1;
            for(const auto& ally:o.allies) {
                const auto it=std::find(w.allies.begin(),w.allies.end(),ally.sdk);
                if(it!=w.allies.end()&&(owner.members&(1u<<(it-w.allies.begin())))&&w.distance(job,ally.p)<=6) {
                    present=true;adjacent|=ally.p.chebyshev_distance(o.p)<=1;member_range=std::max(member_range,ally.range);
                }
            }
            if(!present)continue;
            const auto& group=w.groups[job];if(group.tiles.size()>64)continue;
            std::array<Tile,64> workspace{};int radius=member_range;
            for(unsigned k=0;k<group.tiles.size();++k){workspace[k]={group.tiles[k].x,group.tiles[k].y};radius=std::max(radius,group.attack_ranges[k]);}
            const auto area=std::span<const Tile>(workspace.data(),group.tiles.size());
            if(adjacent)radius=std::max(radius,crew::clearance({o.p.x,o.p.y},area));
            const auto next=crew::yield_step({o.p.x,o.p.y},area,radius,
                [&](Tile p){const vec2 q{p.x,p.y};const int dx=p.x-o.p.x,dy=p.y-o.p.y;
                    const bool guarded=m.neutral_moves.round==static_cast<int>(tc.round)&&m.neutral_moves.origin==Tile{o.p.x,o.p.y};
                    return (!guarded||(m.neutral_moves.allowed&(1u<<((dx+1)*3+dy+1))))&&w.walkable(q)&&!o.is_occupied(q)&&!w.is_spawn(q);},
                [&](Tile p){return w.home_distance(p);},[&](Tile p){return danger({p.x,p.y},o);});
            if(goal.kind==GoalKind::Farm&&goal.index==job){m.contract.objective=-1;m.leave_crew();goal={GoalKind::Idle};}
            if(next) {
#if DZ_TRACE
                {TraceScope scope;trace("DZ_CREW_YIELD round=%u slot=%u group=%d owner=%u from=%d,%d to=%d,%d\n",tc.round,w.slot,job,owner.members,o.p.x,o.p.y,next->x,next->y);}
#endif
                return {GoalKind::YieldSpawn,-1,vec2{next->x,next->y}};
            }
        }
    }
    if(goal.kind!=GoalKind::Farm&&state.joined&&state.group>=0&&m.neutral_recovery.active&&!state.recovering) {
        state.recovering=true;state.recovery_deadline=tc.round+2*std::min<int>(w.home.get(o.p),2000)+cambc::constants::recall_time+config::crew_window;
    }
    if(goal.kind==GoalKind::Farm&&!m.siege_task.active()&&goal.index>=0) {
        auto owner=m.team.cohort(goal.index,traffic_word,tc.round,w.allies.size());
        const auto invitation=protocol::compact::lease(traffic_word,tc.round);
        if(invitation.valid&&invitation.objective==goal.index)owner=invitation;
        const bool extending=team::extends(owner,w.slot,m.economic_crew,m.economic_capturer)&&
            m.contract.objective==goal.index&&tc.round<=static_cast<unsigned>(m.rendezvous_until)&&m.groups[goal.index].state!=GroupState::Reward;
        if(owner.valid&&owner.objective==goal.index&&!(owner.members&(1u<<w.slot))&&!extending) {
            // A recovered former leader or legacy solo task cannot take back a
            // camp/payout already handed to a fresh crew that excludes it.
            m.contract.objective=-1;m.leave_crew();
            return {w.distance(goal.index,o.p)<=o.range+2?GoalKind::Retreat:GoalKind::Idle};
        }
    }
    if(goal.kind!=GoalKind::Farm||m.siege_task.active()||goal.index<0||w.groups[goal.index].strength<=0||
        std::popcount(m.economic_crew)<2||!(m.economic_crew&(1u<<w.slot))||m.contract.objective!=goal.index) {state.managed=false;return goal;}
    const int g=goal.index;unsigned expected=m.economic_crew;
    if(state.group!=g||state.members!=expected){state={};state.group=g;state.members=expected;state.since=state.last_progress=tc.round;}
    const Tile here{o.p.x,o.p.y};if(state.has_self&&state.last_self!=here)state.last_progress=tc.round;
    state.last_self=here;state.has_self=true;
    state.round=tc.round;state.managed=true;state.formed=false;state.fire=false;state.focus=-1;
    goal.destination=o.p; // Pending geometry/consent holds; it cannot attack or drift into the camp.
    if(m.groups[g].state==GroupState::Reward) {
        if(m.economic_capturer!=w.slot) {
            m.contract.objective=-1;m.leave_crew();
            return {w.group_at(o.p)==g?GoalKind::YieldSpawn:GoalKind::Idle};
        }
        m.leave_crew();m.economic_crew=1u<<w.slot;m.economic_capturer=w.slot;return goal;
    }
    const auto word=shared_word();
    const auto lease=protocol::compact::lease(word,tc.round);
    const auto cohort=m.team.cohort(g,word,tc.round,w.allies.size());
    bool promised=(lease.valid&&lease.objective==g&&lease.members==expected)||state.joined||
        (cohort.valid&&cohort.members==expected);
    const unsigned leader=m.economic_capturer;
    const auto& sent=m.crew_publication;
    if(leader==w.slot&&(sent.group!=g||sent.members!=expected||sent.capturer!=leader))
        return goal; // Publish the invitation before changing any incumbent's live formation.
    if(!promised&&leader!=w.slot) {
        // Local recovery handoff uses CURRENT visible job claimants. A remote
        // expired lease never establishes their presence or combat power.
        unsigned replacement=1u<<w.slot;
        for(const auto& ally:o.allies) {
            const auto slot=std::find(w.allies.begin(),w.allies.end(),ally.sdk);
            if(slot==w.allies.end()||ally.hp<.5f*ally.max_hp||w.distance(g,ally.p)>ally.range+2)continue;
            const unsigned index=slot-w.allies.begin();
            if(protocol::slot(word,index).objective==g)replacement|=1u<<index;
        }
        unsigned owner=0;while(owner<protocol::slots&&!(replacement&(1u<<owner)))++owner;
        if(std::popcount(replacement)>=2&&owner==w.slot) {
            expected=replacement;m.economic_crew=replacement;m.economic_capturer=w.slot;state.members=replacement;state.since=tc.round;promised=true;
#if DZ_TRACE
            {TraceScope scope;trace("DZ_CREW_HANDOFF round=%u body=%u group=%d members=%u\n",tc.round,
                static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,replacement);}
#endif
        } else {
#if DZ_TRACE
            {TraceScope scope;trace("DZ_CREW_NO_PROMISE round=%u slot=%u group=%d expected=%u claims=%u,%u,%u cohort=%u\n",tc.round,w.slot,g,expected,
                protocol::slot(word,0).objective,protocol::slot(word,1).objective,protocol::slot(word,2).objective,cohort.members);}
#endif
            m.contract.objective=-1;m.leave_crew();return {GoalKind::Idle};
        }
    }
    if(static_cast<int>(tc.round)-state.last_progress>config::crew_window) {
        m.release(tc.round);m.economic_crew=0;state.managed=false;return {GoalKind::Idle};
    }
    std::array<crew::Unit,crew::max_units> units{};unsigned n=0,self=0,consented=1u<<w.slot;
    units[n++]=crew_unit({cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range},w.slot);
    for(const auto& ally:o.allies) {
        const auto it=std::find(w.allies.begin(),w.allies.end(),ally.sdk);
        if(it==w.allies.end()||n==units.size())continue;
        const unsigned slot=it-w.allies.begin();
        const auto claim=protocol::slot(word,slot).objective;
        // Home/shopping capacity is not consent to this project. A returning
        // member publishes the objective through its recovery commitment.
        if(!(expected&(1u<<slot))||claim!=g||!tc.allow(14000))continue;
        units[n++]=crew_unit(ally,slot);consented|=1u<<slot;
    }
    if(state.joined)for(unsigned slot=0;slot<w.allies.size();++slot)if(slot!=w.slot&&(expected&(1u<<slot))&&
        protocol::slot(word,slot).objective!=g) {
        // An acknowledged worker has explicitly left. Preserve partial camp
        // memory and re-auction a fresh cohort instead of pricing it as support.
#if DZ_TRACE
        {TraceScope scope;trace("DZ_CREW_WITHDRAW round=%u slot=%u group=%d missing=%u claim=%u\n",tc.round,w.slot,g,slot,protocol::slot(word,slot).objective);}
#endif
        m.contract.objective=-1;m.leave_crew();return {GoalKind::Home};
    }
    const auto set=camp_set(w,m,g);if(!set.complete||!set.count)return goal;
    const auto camps=std::span<const crew::Monster>(set.camps.data(),set.count);
    state.focus=camps[0].member;
    if((consented&expected)!=expected||!tc.allow(17000)) {
        unsigned acknowledged=0;
        for(unsigned slot=0;slot<w.allies.size();++slot)if(protocol::slot(word,slot).objective==g)acknowledged|=1u<<slot;
        if((acknowledged&expected)!=expected&&static_cast<int>(tc.round)-state.since>=config::contract_window) {
            // An offer is not an accepted assignment. A body can legitimately
            // decline for a private recovery/shop/failure reason. Re-auction
            // another roster instead of renewing a phantom helper indefinitely.
            m.crew_decline={g,static_cast<int>(tc.round)+config::crew_window,expected};
#if DZ_TRACE
            {TraceScope scope;trace("DZ_CREW_DECLINED round=%u slot=%u group=%d proposed=%u accepted=%u\n",tc.round,w.slot,g,expected,acknowledged);}
#endif
            m.contract.objective=-1;m.leave_crew();return {GoalKind::Home};
        }
        // An unseen ally contributes no damage/HP. A previously accepted crew
        // may still navigate to its cached safe staging tile and reunite there.
        const auto& cache=m.crew_layout();
        if(cache.group==g&&cache.topology==m.topology_revision-m.group_topology[g]&&cache.generation==m.conversions[g]&&
            cache.search.stage==crew::SequenceSearch::Stage::Done&&cache.camps>=set.count) {
            const unsigned first=cache.camps-set.count;
            if(crew::same_scene(camps,std::span<const crew::Monster>(cache.scene.data()+first,set.count)))
                for(unsigned u=0;u<cache.units;++u)if(cache.roster[u].slot==w.slot) {
                    const auto p=cache.search.phases[first].staging[u];state.destination=p;goal.destination=vec2{p.x,p.y};break;
                }
        }
        return goal;
    }
    std::sort(units.begin(),units.begin()+n,[](auto a,auto b){return a.slot<b.slot;});
    for(unsigned u=0;u<n;++u)if(units[u].slot==w.slot)self=u;
    bool progress=state.position_count!=n;
    for(unsigned u=0;u<n;++u){progress|=state.last_positions[u]!=units[u].p;state.last_positions[u]=units[u].p;}
    state.position_count=n;if(progress)state.last_progress=tc.round;
    state.last_progress=std::max(state.last_progress,m.last_work);m.rendezvous_until=state.last_progress+config::crew_window;
    // Re-elect a recipient if recovery removed the previous capturer. The
    // leader publishes it through the existing exact-round lease unchanged.
    if(!(expected&(1u<<m.economic_capturer))) {
        unsigned cap=0;
        for(unsigned u=1;u<n;++u)if(units[u].gold_multiplier>units[cap].gold_multiplier||
            (units[u].gold_multiplier==units[cap].gold_multiplier&&units[u].capture_rounds<units[cap].capture_rounds))cap=u;
        m.economic_capturer=units[cap].slot;
    }
    const int first=layout(w,m,m.crew_layout(),g,std::span<const crew::Unit>(units.data(),n),camps,tc);
    DZ_PROF('L');
    if(first<0)return goal;
    m.crew_layout().expires=tc.round+config::crew_window;
    const auto& sequence=m.crew_layout().search;const auto& phase=sequence.phases[first];const auto& plan=phase.formation;
#if DZ_TRACE
    if(previous_focus!=state.focus){TraceScope scope;trace("DZ_CREW_ADVANCE round=%u body=%u group=%d member=%d phase=%d\n",tc.round,
        static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,state.focus,first);}
#endif
    std::array<Tile,crew::max_units> actual{};for(unsigned u=0;u<n;++u)actual[u]=units[u].p;
    const auto positions=std::span<const Tile>(actual.data(),n);
    auto march=first?crew::march(sequence.phases[first-1],phase,positions):crew::March{};
    bool transfer=march.valid;
    if(!march.valid)march=crew::approach(phase,positions);
    if(march.valid&&!march.complete&&o.is_occupied({march.next.x,march.next.y})&&
        std::none_of(units.begin(),units.begin()+n,[&](auto u){return u.p==march.next;})) {
        if(state.blocked_since<0||state.blocked_tile!=march.next){state.blocked_since=tc.round;state.blocked_tile=march.next;}
        if(static_cast<int>(tc.round)-state.blocked_since>=config::contract_window) {
            m.release(tc.round);return {GoalKind::Home};
        }
    } else state.blocked_since=-1;
    bool formed=true,ready=true;int attacks=2000;
    for(unsigned u=0;u<n;++u){formed&=units[u].p==plan.positions[u];const int cap=crew::capacity(units[u],units[u].hp,phase,u);ready&=cap>0;attacks=std::min(attacks,cap);}
    state.destination=phase.staging[self];state.tank=units[plan.tank].slot;state.formed=formed;state.joined|=formed;
    if(formed&&m.economic_capturer==w.slot&&(!team::protected_lease(word,tc.round,w.allies.size())||lease.leader==w.slot)) {
        unsigned cap=self;const auto& group=w.groups[g];
        auto value=[&](unsigned u) {
            const float boost=group.cluster&&units[u].prospector?1.25f:1.f;
            return std::floor(group.reward_gems*boost)+objective::gold_price(cambc::constants::max_rounds-tc.round)*
                std::floor(group.reward_gold*boost*units[u].gold_multiplier);
        };
        for(unsigned u=0;u<n;++u)if(value(u)>value(cap)||(value(u)==value(cap)&&units[u].capture_rounds<units[cap].capture_rounds))cap=u;
        m.economic_capturer=units[cap].slot;
    }
    auto recover=[&]() {
#if DZ_TRACE
        if(!state.recovering){TraceScope scope;trace("DZ_CREW_RECOVER round=%u body=%u group=%d member=%d hp=%.0f\n",tc.round,
            static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,state.focus,o.hp);}
#endif
        if(!state.recovering)state.recovery_deadline=tc.round+2*phase.return_rounds+cambc::constants::recall_time+config::crew_window;
        state.recovering=true;m.neutral_recovery.update(true,false,o.hp,o.max_hp);state.managed=false;
        if(formed)return Goal{GoalKind::Retreat,-1,vec2{phase.staging[self].x,phase.staging[self].y}};
        if(transfer&&first)return Goal{GoalKind::Retreat,-1,vec2{sequence.phases[first-1].staging[self].x,sequence.phases[first-1].staging[self].y}};
        return Goal{GoalKind::Home};
    };
    if(!ready)return recover();
    if(march.valid&&!march.complete) {
        const auto& start=transfer?sequence.phases[first-1].formation.positions:phase.staging;
        bool beginning=true;for(unsigned u=0;u<n;++u)beginning&=actual[u]==start[u];
        if(beginning)for(unsigned u=0;u<n;++u) {
            const auto loss=transfer?phase.transfer_loss[u]:phase.approach_loss[u];
            if(crew::capacity(units[u],units[u].hp-loss,phase,u)<=0)return recover();
        }
        state.destination=actual[self];
        if(march.actor==self){state.destination=march.next;state.direct_step=true;}
    } else if(formed) {
        state.destination=plan.positions[self];state.fire=true;state.recovering=false;
    }
    if(!m.crew_field.field||m.crew_field.root!=state.destination||m.crew_field.expires<=static_cast<int>(tc.round)) {
        m.crew_field.field.reset();m.crew_field.root=state.destination;m.crew_field.pending=true;
    }
    if(state.direct_step||state.destination==actual[self])m.crew_field.pending=false;
    goal.destination=vec2{state.destination.x,state.destination.y};
#if DZ_TRACE
    if(tc.round%10==0){TraceScope scope;trace("DZ_CREW round=%u body=%u group=%d focus=%d tank=%u members=%u formed=%d fire=%d pose=%d,%d\n",tc.round,
        static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,state.focus,state.tank,expected,formed,state.fire,state.destination.x,state.destination.y);}
    if(tc.round%25==0){TraceScope scope;trace("DZ_CREW_PHASE round=%u body=%u group=%d phase=%d march=%d direct=%d attacks=%d n=%u p0=%d,%d p1=%d,%d s0=%d,%d s1=%d,%d\n",tc.round,
        static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,first,march.valid,state.direct_step,attacks,n,
        units[0].p.x,units[0].p.y,units[1].p.x,units[1].p.y,phase.staging[0].x,phase.staging[0].y,phase.staging[1].x,phase.staging[1].y);}
#endif
    return goal;
}
}
#endif
