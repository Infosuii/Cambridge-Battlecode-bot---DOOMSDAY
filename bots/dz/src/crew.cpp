#include "crew.h"
#if DZ_ECONOMY_V2
#include "economy.h"
#include "access_route.h"
#include <bit>

namespace dz {
crew::Unit crew_unit(const SeenChampion& seen,unsigned slot) {
    const auto actor=economic_actor(seen);
    return {slot,static_cast<unsigned>(static_cast<cambc::handle_champion_t>(seen.sdk)),{seen.p.x,seen.p.y},
        actor.hp,actor.max_hp,actor.damage,actor.incoming_factor,seen.range,actor.arrival,actor.gold_multiplier,actor.capture_rounds};
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
crew::Formation layout(const StaticWorld& w,const Memory& m,int group,std::span<const crew::Unit> units,std::span<const crew::Monster> camps,const TurnContext& tc) {
    auto& cache=m.crew_layout;
    const bool matches=cache.group==group&&cache.expires>static_cast<int>(tc.round)&&cache.topology==m.topology_revision&&
        crew::same_roles(units,std::span<const crew::Unit>(cache.roster.data(),cache.units))&&
        crew::same_scene(camps,std::span<const crew::Monster>(cache.scene.data(),cache.camps));
    if(matches&&cache.formation.valid)return cache.formation;
    // A different speculative quote cannot erase the unfinished job. A changed
    // roster/scene for the SAME job invalidates it; an expired job is replaceable.
    if(!matches&&cache.group!=group&&cache.expires>static_cast<int>(tc.round)&&cache.search.pending())return {};
    if(!matches) {
        Memory::FormationCache next;next.group=group;next.topology=m.topology_revision;next.expires=tc.round+config::crew_window;
        next.units=units.size();next.camps=camps.size();next.search.begin(units,camps);
        std::copy(units.begin(),units.end(),next.roster.begin());std::copy(camps.begin(),camps.end(),next.scene.begin());
        for(unsigned g=0;g<w.groups.size();++g)if(m.groups[g].state==GroupState::Respawning&&
            m.groups[g].ready>static_cast<int>(tc.round)&&w.groups[g].center.chebyshev_distance(w.groups[group].center)<=16)
            next.expires=std::min(next.expires,m.groups[g].ready);
        tc.guard();cache=next;
    }
    const auto started=fuel_left();
    const auto formation=cache.search.resume(units,camps,[&](Tile tile) {
        const vec2 p{tile.x,tile.y};if(!w.walkable(p))return false;
        const int g=w.group_at(p);if(g<0)return true;
        const int member=w.tile_members[tile.y*cambc::map::width()+tile.x];
        const auto& b=m.groups[g];
        return member>=0&&!access::member_blocks(m.member_hp[g][member]>0,b.state==GroupState::Respawning,b.ready,tc.round+1);
    },[&](Tile p){return w.home_distance(p);},[&]{return tc.allow(8000)&&started-fuel_left()<14000;});
    tc.guard();if(formation.valid)cache.formation=formation;
    return formation;
}
crew::Visit wave(const StaticWorld& w,std::span<const crew::Unit> units,std::span<const crew::Monster> camps,const crew::Formation& f,const TurnContext& tc) {
    if(!tc.allow(11000))return {};
    const auto started=fuel_left();unsigned checks=0;
    return crew::visit(units,camps,f,cambc::constants::recall_time,[&](Tile p) {
        const vec2 tile{p.x,p.y};return w.walkable(tile)&&!w.is_spawn(tile);
    },[&](Tile p){return w.home_distance(p);},[&]{return (++checks&7u)||(tc.allow(8000)&&started-fuel_left()<12000);});
}
}
CrewQuote crew_quote(const StaticWorld& w,const Memory& m,int group,std::span<const crew::Unit> units,int capture,const TurnContext& tc) {
    if(!tc.allow(19000)||units.size()<2)return {};
    const auto set=camp_set(w,m,group);if(!set.complete||!set.count)return {false,0,0,CrewQuoteStatus::Unsupported};
    const auto camps=std::span<const crew::Monster>(set.camps.data(),set.count);
    const auto plan=layout(w,m,group,units,camps,tc);
    if(!plan.valid||std::popcount(plan.active)<2)return {false,0,0,
        m.crew_layout.search.pending()?CrewQuoteStatus::Budget:CrewQuoteStatus::Formation};
    int arrival=0;
    for(unsigned u=0;u<units.size();++u)if(plan.active&(1u<<u))arrival=std::max(arrival,units[u].arrival);
    const auto model_start=fuel_left();unsigned checks=0;
    const auto q=crew::forecast(units,camps,plan,0,capture,cambc::constants::max_rounds-tc.round,
        [&]{return (++checks&3u)||(tc.allow(8000)&&model_start-fuel_left()<6000);});
    if(!q.complete)return {false,0,0,CrewQuoteStatus::Model};
    int finish=q.finish;
    if(!q.survivable) {
        const auto partial=wave(w,units,camps,plan,tc);
        if(!partial.complete||partial.attacks<1)return {false,0,0,partial.complete?CrewQuoteStatus::Exhausted:CrewQuoteStatus::Escape};
        finish=partial.finish;
    }
    if(arrival+finish>static_cast<int>(cambc::constants::max_rounds-tc.round))return {false,0,0,CrewQuoteStatus::Horizon};
    unsigned mask=0;for(unsigned u=0;u<units.size();++u)if(plan.active&(1u<<u))mask|=1u<<units[u].slot;
    return {true,mask,arrival+finish,CrewQuoteStatus::Ready};
}
bool build_crew_field(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc) {
    auto& cache=m.crew_field;
    if(!cache.pending||!m.crew_execution.managed||!o.enemies.empty()||o.channel()||
        !requested_navigation_fits(fuel_left(),w.field_budget()+2000,true))return false;
    const vec2 root{cache.root.x,cache.root.y};if(!w.walkable(root)){cache.pending=false;return false;}
    // Static terrain/spawn occupancy gives a reusable conservative route.
    // Actors are handled by step/retry at execution, not baked into this cache.
    auto blocked=w.blocked|w.camp_spawns;blocked.set(root,false);
    const bool own_spawn=w.is_spawn(o.p)&&o.p!=root;if(own_spawn)blocked.set(o.p,false);
    RootSet roots;roots.set(root);auto field=std::make_unique<cambc::distance_field>();
    field->compute(blocked,roots.board(),w.visited);tc.guard();cache.field=std::move(field);
    cache.expires=own_spawn?static_cast<int>(tc.round)+1:cambc::constants::max_rounds+1;cache.pending=false;
    return true;
}
Goal crew_action(Goal goal,StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc) {
    auto& state=m.crew_execution;
    if(goal.kind==GoalKind::Farm&&!m.siege_task.active()&&goal.index>=0) {
        const auto owner=protocol::compact::lease(shared_word(),tc.round);
        if(owner.valid&&owner.objective==goal.index&&!(owner.members&(1u<<w.slot))) {
            // A recovered former leader or legacy solo task cannot take back a
            // camp/payout already handed to a fresh crew that excludes it.
            m.contract.objective=-1;m.leave_crew();
            return {w.distance(goal.index,o.p)<=o.range+2?GoalKind::Retreat:GoalKind::Idle};
        }
    }
    if(goal.kind!=GoalKind::Farm||m.siege_task.active()||goal.index<0||w.groups[goal.index].strength<=0||
        std::popcount(m.economic_crew)<2||!(m.economic_crew&(1u<<w.slot))||m.contract.objective!=goal.index) {state.managed=false;return goal;}
    const int g=goal.index;unsigned expected=m.economic_crew;
    if(state.group!=g||state.members!=expected){state={};state.group=g;state.members=expected;state.since=tc.round;}
    state.round=tc.round;state.managed=true;state.formed=false;state.fire=false;state.focus=-1;
    if(m.groups[g].state==GroupState::Reward) {
        if(m.economic_capturer!=w.slot) {
            m.contract.objective=-1;m.leave_crew();
            return {w.group_at(o.p)==g?GoalKind::YieldSpawn:GoalKind::Idle};
        }
        m.leave_crew();m.economic_crew=1u<<w.slot;m.economic_capturer=w.slot;return goal;
    }
    const auto word=shared_word();
    const auto lease=protocol::compact::lease(word,tc.round);
    bool promised=(lease.valid&&lease.objective==g&&lease.members==expected)||state.joined;
    unsigned leader=0;while(leader<protocol::slots&&!(expected&(1u<<leader)))++leader;
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
            expected=replacement;m.economic_crew=replacement;state.members=replacement;state.since=tc.round;promised=true;
#if DZ_TRACE
            {TraceScope scope;trace("DZ_CREW_HANDOFF round=%u body=%u group=%d members=%u\n",tc.round,
                static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,replacement);}
#endif
        } else {m.contract.objective=-1;m.leave_crew();return {GoalKind::Idle};}
    }
    if(static_cast<int>(tc.round)-state.since>config::crew_window&&m.groups[g].state!=GroupState::Partial) {
        m.release(tc.round);m.economic_crew=0;state.managed=false;return {GoalKind::Idle};
    }
    std::array<crew::Unit,crew::max_units> units{};unsigned n=0,self=0,consented=1u<<w.slot;
    units[n++]=crew_unit({cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range},w.slot);
    for(const auto& ally:o.allies) {
        const auto it=std::find(w.allies.begin(),w.allies.end(),ally.sdk);
        if(it==w.allies.end()||n==units.size())continue;
        const unsigned slot=it-w.allies.begin();
        if(!(expected&(1u<<slot))||protocol::slot(word,slot).objective!=g||!tc.allow(14000))continue;
        units[n++]=crew_unit(ally,slot);consented|=1u<<slot;
    }
    if((consented&expected)!=expected||!tc.allow(17000))return goal;
    // Re-elect a recipient if recovery removed the previous capturer. The
    // leader publishes it through the existing exact-round lease unchanged.
    if(!(expected&(1u<<m.economic_capturer))) {
        unsigned cap=0;
        for(unsigned u=1;u<n;++u)if(units[u].gold_multiplier>units[cap].gold_multiplier||
            (units[u].gold_multiplier==units[cap].gold_multiplier&&units[u].capture_rounds<units[cap].capture_rounds))cap=u;
        m.economic_capturer=units[cap].slot;
    }
    const auto set=camp_set(w,m,g);if(!set.complete||!set.count)return goal;
    const auto camps=std::span<const crew::Monster>(set.camps.data(),set.count);
    // The fixed member order is common; an unseen earlier member is scouted,
    // never silently skipped to a different focus by a follower.
    state.focus=camps[0].member;
    const auto plan=layout(w,m,g,std::span<const crew::Unit>(units.data(),n),camps,tc);
    DZ_PROF('L');
    if(!plan.valid)return goal;
    if(!(plan.active&(1u<<self))) {
        m.contract.objective=-1;m.leave_crew();return {GoalKind::Idle};
    }
    unsigned active=0;bool formed=true;
    for(unsigned u=0;u<n;++u)if(plan.active&(1u<<u)){active|=1u<<units[u].slot;formed&=units[u].p==plan.positions[u];}
    m.economic_crew=active;state.members=active;state.destination=plan.positions[self];state.tank=units[plan.tank].slot;state.formed=formed;
    state.joined|=formed;
    if(!m.crew_field.field||m.crew_field.root!=state.destination||m.crew_field.expires<=static_cast<int>(tc.round)) {
        m.crew_field.field.reset();m.crew_field.root=state.destination;m.crew_field.pending=true;
    }
    const auto model_start=fuel_left();unsigned model_checks=0;
    const auto quote=crew::forecast(std::span<const crew::Unit>(units.data(),n),camps,plan,0,6,cambc::constants::max_rounds-tc.round,
        [&]{return (++model_checks&3u)||(tc.allow(8000)&&model_start-fuel_left()<6000);});
    state.fire=formed&&quote.complete&&quote.survivable;
    if(formed&&quote.complete&&!quote.survivable) {
        const auto partial=wave(w,std::span<const crew::Unit>(units.data(),n),camps,plan,tc);
        DZ_PROF('W');
        state.fire=partial.complete&&partial.attacks>0;
        if(partial.complete&&!(partial.ready&1u)) {
            m.neutral_recovery.update(true,false,o.hp,o.max_hp);state.managed=false;return {GoalKind::Home};
        }
#if DZ_TRACE
        if(tc.round%10==0){TraceScope scope;trace("DZ_CREW_WAVE round=%u body=%u group=%d complete=%d attacks=%d visits=%d\n",tc.round,
            static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,partial.complete,partial.attacks,partial.waves);}
#endif
    }
    goal.destination=vec2{state.destination.x,state.destination.y};
#if DZ_TRACE
    if(tc.round%10==0){TraceScope scope;trace("DZ_CREW round=%u body=%u group=%d focus=%d tank=%u members=%u formed=%d fire=%d pose=%d,%d\n",tc.round,
        static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,state.focus,state.tank,active,formed,state.fire,state.destination.x,state.destination.y);}
#endif
    return goal;
}
}
#endif
