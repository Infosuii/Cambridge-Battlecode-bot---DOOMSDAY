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
int layout(const StaticWorld& w,const Memory& m,int group,std::span<const crew::Unit> units,std::span<const crew::Monster> camps,const TurnContext& tc) {
    auto& cache=m.crew_layout;
    const unsigned outside=m.topology_revision-m.group_topology[group];
    const unsigned offset=cache.camps>=camps.size()?cache.camps-camps.size():cache.camps;
    const bool matches=cache.group==group&&(cache.expires>static_cast<int>(tc.round)||cache.search.stage==crew::SequenceSearch::Stage::Done)&&cache.topology==outside&&
        cache.generation==m.conversions[group]&&offset+camps.size()==cache.camps&&
        crew::same_roles(units,std::span<const crew::Unit>(cache.roster.data(),cache.units))&&
        crew::same_scene(camps,std::span<const crew::Monster>(cache.scene.data()+offset,camps.size()));
    if(matches&&cache.search.stage==crew::SequenceSearch::Stage::Done)return offset;
    // A different speculative quote cannot erase the unfinished job. A changed
    // roster/scene for the SAME job invalidates it; an expired job is replaceable.
    if(!matches&&cache.group!=group&&cache.expires>static_cast<int>(tc.round)&&cache.search.pending())return -1;
    if(!matches) {
        // Mutate the logical job, never copy the BFS's unvisited storage.
        tc.guard();cache.group=group;cache.topology=outside;cache.generation=m.conversions[group];cache.expires=tc.round+config::crew_window;
        cache.units=units.size();cache.camps=camps.size();
        std::copy(units.begin(),units.end(),cache.roster.begin());std::copy(camps.begin(),camps.end(),cache.scene.begin());
        cache.search.begin(units,camps,cambc::map::width(),cambc::map::height());
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
}
void progress_crew_layout(const StaticWorld& w,const Memory& m,const TurnContext& tc) {
    auto& c=m.crew_layout;
    if(!c.search.pending()||c.group<0||c.group>=static_cast<int>(m.groups.size())||!tc.allow(25000))return;
    if(c.expires<=static_cast<int>(tc.round)||c.topology!=m.topology_revision-m.group_topology[c.group]||c.generation!=m.conversions[c.group])return;
    layout(w,m,c.group,std::span<const crew::Unit>(c.roster.data(),c.units),std::span<const crew::Monster>(c.scene.data(),c.camps),tc);
}
CrewQuote crew_quote(const StaticWorld& w,const Memory& m,int group,std::span<const crew::Unit> given,int capture,const TurnContext& tc) {
    if(!tc.allow(19000)||given.size()<2||given.size()>crew::max_units)return {};
    std::array<crew::Unit,crew::max_units> ordered{};std::copy(given.begin(),given.end(),ordered.begin());
    std::sort(ordered.begin(),ordered.begin()+given.size(),[](auto a,auto b){return a.slot<b.slot;});
    const auto units=std::span<const crew::Unit>(ordered.data(),given.size());
    const auto set=camp_set(w,m,group);if(!set.complete||!set.count)return {false,0,0,CrewQuoteStatus::Unsupported};
    const auto camps=std::span<const crew::Monster>(set.camps.data(),set.count);
    const int first=layout(w,m,group,units,camps,tc);
    if(first<0)return {false,0,0,
        m.crew_layout.search.pending()?CrewQuoteStatus::Budget:CrewQuoteStatus::Formation};
    int arrival=0;
    for(unsigned u=0;u<units.size();++u)arrival=std::max(arrival,units[u].arrival);
    const auto model_start=fuel_left();
    const auto q=crew::quote(units,camps,m.crew_layout.search,first,capture,cambc::constants::recall_time,cambc::constants::max_rounds-tc.round,
        [&]{return tc.allow(10000)&&model_start-fuel_left()<6000;});
#if DZ_TRACE
    static unsigned next_price_trace=0;
    if(w.slot==0&&tc.round>=next_price_trace) {
        next_price_trace=tc.round+50;const auto& p=m.crew_layout.search.phases[first];TraceScope scope;
        trace("DZ_CREW_PRICE round=%u group=%d reason=%d finish=%d count=%u first=%d n=%zu hp=%.0f,%.0f damage=%.0f,%.0f raw=%.0f,%.0f escape=%.0f,%.0f approach=%.0f,%.0f\n",
            tc.round,group,static_cast<int>(q.reason),q.finish,m.crew_layout.search.count,first,units.size(),units[0].hp,units[1].hp,units[0].damage,units[1].damage,
            p.raw[0],p.raw[1],p.escape[0],p.escape[1],p.approach_loss[0],p.approach_loss[1]);
    }
#endif
    if(!q.complete)return {false,0,0,CrewQuoteStatus::Model};
    if(arrival+q.finish>static_cast<int>(cambc::constants::max_rounds-tc.round))return {false,0,0,CrewQuoteStatus::Horizon};
    unsigned mask=0;for(unsigned u=0;u<units.size();++u)mask|=1u<<units[u].slot;
    return {true,mask,arrival+q.finish,CrewQuoteStatus::Ready};
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
    if(goal.kind!=GoalKind::Farm&&state.joined&&state.group>=0&&m.neutral_recovery.active&&!state.recovering) {
        state.recovering=true;state.recovery_deadline=tc.round+2*std::min<int>(w.home.get(o.p),2000)+cambc::constants::recall_time+config::crew_window;
    }
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
    if(static_cast<int>(tc.round)-state.last_progress>config::crew_window&&m.groups[g].state!=GroupState::Partial) {
        m.release(tc.round);m.economic_crew=0;state.managed=false;return {GoalKind::Idle};
    }
    std::array<crew::Unit,crew::max_units> units{};unsigned n=0,self=0,consented=1u<<w.slot;
    units[n++]=crew_unit({cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range},w.slot);
    for(const auto& ally:o.allies) {
        const auto it=std::find(w.allies.begin(),w.allies.end(),ally.sdk);
        if(it==w.allies.end()||n==units.size())continue;
        const unsigned slot=it-w.allies.begin();
        const auto claim=protocol::slot(word,slot).objective;
        const bool recovered=(state.joined||(lease.valid&&lease.objective==g&&lease.members==expected))&&state.recovering&&ally.hp>=ally.max_hp-.01f&&w.home.get(ally.p)==0&&
            (claim==protocol::shop||claim==protocol::idle);
        if(!(expected&(1u<<slot))||(claim!=g&&!recovered)||!tc.allow(14000))continue;
        units[n++]=crew_unit(ally,slot);consented|=1u<<slot;
    }
    const auto set=camp_set(w,m,g);if(!set.complete||!set.count)return goal;
    const auto camps=std::span<const crew::Monster>(set.camps.data(),set.count);
    state.focus=camps[0].member;
    if((consented&expected)!=expected||!tc.allow(17000)) {
        // An unseen ally contributes no damage/HP. A previously accepted crew
        // may still navigate to its cached safe staging tile and reunite there.
        const auto& cache=m.crew_layout;
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
    const int first=layout(w,m,g,std::span<const crew::Unit>(units.data(),n),camps,tc);
    DZ_PROF('L');
    if(first<0)return goal;
    m.crew_layout.expires=tc.round+config::crew_window;
    const auto& sequence=m.crew_layout.search;const auto& phase=sequence.phases[first];const auto& plan=phase.formation;
#if DZ_TRACE
    if(previous_focus!=state.focus){TraceScope scope;trace("DZ_CREW_ADVANCE round=%u body=%u group=%d member=%d phase=%d\n",tc.round,
        static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,state.focus,first);}
#endif
    std::array<Tile,crew::max_units> actual{};for(unsigned u=0;u<n;++u)actual[u]=units[u].p;
    const auto positions=std::span<const Tile>(actual.data(),n);
    auto march=first?crew::march(sequence.phases[first-1],phase,positions):crew::March{};
    bool transfer=march.valid;
    if(!march.valid)march=crew::approach(phase,positions);
    bool formed=true,ready=true;int attacks=2000;
    for(unsigned u=0;u<n;++u){formed&=units[u].p==plan.positions[u];const int cap=crew::capacity(units[u],units[u].hp,phase,u);ready&=cap>0;attacks=std::min(attacks,cap);}
    state.destination=phase.staging[self];state.tank=units[plan.tank].slot;state.formed=formed;state.joined|=formed;
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
    if(tc.round%25==0){TraceScope scope;trace("DZ_CREW_PHASE round=%u body=%u group=%d phase=%d march=%d direct=%d attacks=%d\n",tc.round,
        static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,first,march.valid,state.direct_step,attacks);}
#endif
    return goal;
}
}
#endif
