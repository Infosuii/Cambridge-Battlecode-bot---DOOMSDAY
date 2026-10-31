#include "config.h"
#if DZ_SIEGE || DZ_ECONOMY_V2
#include "siege.h"

namespace dz {
namespace {
struct Exposure {
    std::array<CampThreat,64> camps{};
    unsigned count=0;bool complete=true;
    std::span<const CampThreat> view() const { return {camps.data(),count}; }
};
// Include the whole pull plus other awake/hidden damaging camps near it.
// Visible sleeping camps in another group are not woken by a basic attack.
Exposure exposure(const StaticWorld& w,const Memory& m,int group,vec2 p,float factor,const TurnContext& tc) {
    Exposure result;
    const auto started=fuel_left();
    LocalMask awake;awake.load(cambc::vision::awake_camp_tiles());
    for(unsigned g=0;g<w.groups.size();++g) {
        const auto& design=w.groups[g];
        if(design.strength<=0||w.distance_floor(g,p)>12)continue;
        if(!tc.allow(7000)){result.complete=false;return result;}
        const auto& hp=m.member_hp[g];
        for(unsigned k=0;k<hp.size();++k) {
            if(hp[k]<=0||design.initial_strength[k]<=0||p.chebyshev_distance(design.tiles[k])>12)continue;
            if(!tc.allow(6000)||started-fuel_left()>8000){result.complete=false;return result;}
            const bool visible=cambc::vision::in_vision(design.tiles[k]);
            if(g!=static_cast<unsigned>(group)&&visible&&!awake.test(design.tiles[k]))continue;
            if(result.count==result.camps.size()){result.complete=false;return result;}
            // Current visible strength is legal and avoids relying on an old
            // design snapshot. Unseen members retain their conservative design.
            float strength=design.initial_strength[k];
            if(g==static_cast<unsigned>(group)&&visible) {
                const auto& camp=design.sdk.camps()[k];
                if(camp.is_visible()&&!camp.is_dead())strength=std::max(strength,camp.strength());
            }
            result.camps[result.count++]={{design.tiles[k].x,design.tiles[k].y},strength*factor,design.attack_ranges[k]};
        }
    }
    return result;
}
bool free(const StaticWorld& w,const Memory& m,const Observation& o,vec2 p) {
    if(!w.walkable(p)||(p!=o.p&&o.is_occupied(p)))return false;
    const int g=w.group_at(p);
    if(g>=0) {
        const int member=w.tile_members[p.y*cambc::map::width()+p.x];
        if(member<0||m.member_hp[g][member]>0)return false;
    }
    return true;
}
EscapeRoute escape(const StaticWorld& w,const Memory& m,const Observation& o,vec2 from,const Exposure& threats,const TurnContext& tc,std::uint64_t started) {
    std::array<Tile,8> directions{{{-1,-1},{-1,0},{-1,1},{0,-1},{0,1},{1,-1},{1,0},{1,1}}};
    std::array<int,8> home{};
    for(unsigned i=0;i<directions.size();++i) {
        const vec2 next{from.x+directions[i].x,from.y+directions[i].y};
        home[i]=w.walkable(next)?w.home.get(next):65535;
    }
    // Put a homeward first step first without sorting or repeating SDK reads.
    const auto best=std::min_element(home.begin(),home.end())-home.begin();
    std::swap(directions[0],directions[best]);
    return siege::escape_route({from.x,from.y},threats.view(),directions,[&](Tile tile) {
        const vec2 p{tile.x,tile.y};
        return free(w,m,o,p)&&enemy_danger(p,o)<=enemy_danger(o.p,o);
    },[&]{return tc.allow(6000)&&started-fuel_left()<16000;});
}
void trace_task(const siege::Task& task,const TurnContext& tc,const char* event,float hp) {
#if DZ_TRACE
    TraceScope scope;
    trace("DZ_SIEGE round=%u body=%u event=%s group=%d member=%d phase=%d hp=%.0f target_hp=%.0f reserve=%.0f exit=%d,%d visits=%d\n",
        tc.round,static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),event,task.group,task.member,static_cast<int>(task.phase),hp,task.last_target_hp,task.escape_loss,task.exit.x,task.exit.y,task.visits);
#else
    (void)task;(void)tc;(void)event;(void)hp;
#endif
}
void defer(Memory& memory,int round,int delay) {
    auto& task=memory.siege_task;
    if(task.group>=0)memory.groups[task.group].avoid_until=std::max(memory.groups[task.group].avoid_until,round+delay);
    task.reset(round,5);memory.contract.objective=-1;
}
}
access::Route altar_route(const StaticWorld& w,const Memory& m,const Observation& o,unsigned index,const TurnContext& tc) {
    const auto& altar=w.altars[index];
    const int width=cambc::map::width(),height=cambc::map::height();
    if(altar.distances.size()!=static_cast<unsigned>(width*height))return {};
    const auto started=fuel_left();
    return access::inspect({o.p.x,o.p.y},[&](Tile p) {
        return p.x>=0&&p.y>=0&&p.x<width&&p.y<height?static_cast<int>(altar.distances[p.y*width+p.x]):65535;
    },[&](Tile tile) {
        const vec2 p{tile.x,tile.y};const int g=w.group_at(p);
        if(g<0)return access::Blocker{};
        const int k=w.tile_members[tile.y*width+tile.x];if(k<0)return access::Blocker{};
        const auto& belief=m.groups[g];
        if(belief.state==GroupState::Respawning&&belief.ready>static_cast<int>(tc.round))return access::Blocker{};
        const float hp=m.member_hp[g][k];
        // A remembered reward can have been captured and respawned out of view.
        // Do not certify a path from indefinitely stale dead-member evidence.
        const bool stale_dead=hp<=0&&static_cast<int>(tc.round)-belief.seen>=w.groups[g].sdk.max_respawn_timer();
        if(hp<=0&&!stale_dead)return access::Blocker{};
        return access::Blocker{g,k,(hp>0?hp:w.groups[g].initial_hp[k])/std::max(1.f,o.strength*o.camp_damage)};
    },[&]{return tc.allow(4000)&&started-fuel_left()<6000;},64);
}
std::optional<bool> altar_access(StaticWorld& w,Memory& m,const Observation& o,unsigned altar,const TurnContext& tc) {
    if(o.p.chebyshev_distance(w.altars[altar].tile)<=cambc::constants::submit_gems_range)return true;
    if(!local_masks_valid)return std::nullopt;
    if(m.access_fields.size()!=w.altars.size())m.access_fields.resize(w.altars.size());
    auto& cached=m.access_fields[altar];
    if(cached.revision==m.topology_revision&&cached.expires>static_cast<int>(tc.round))
        return !cached.closed&&cached.field&&cached.field->get(o.p)<65535;
    if(!tc.allow(8000))return std::nullopt;
    auto& build=m.access_build;const auto started=fuel_left();
    if(build.revision!=m.topology_revision||build.expires<=static_cast<int>(tc.round))build.altar=-1;
    if(build.altar>=0&&build.altar!=static_cast<int>(altar))return std::nullopt;
    if(build.altar<0) {
        build.mask.load(w.blocked);build.altar=altar;build.revision=m.topology_revision;
        build.group=0;build.member=0;build.expires=cambc::constants::max_rounds+1;
    }
    // Build from the legal camp ledger in bounded slices. Uncertain old dead
    // cells are blocked; known respawns supply exact cache expiry boundaries.
    while(build.group<w.groups.size()) {
        const auto& group=w.groups[build.group];const auto& belief=m.groups[build.group];
        const int respawn=group.sdk.max_respawn_timer();
        while(build.member<group.tiles.size()) {
            if((build.member&15)==0&&(!tc.allow(7000)||started-fuel_left()>12000))return std::nullopt;
            const unsigned k=build.member;
            bool live=m.member_hp[build.group][k]>0;
            if(belief.state==GroupState::Respawning&&belief.ready>static_cast<int>(tc.round)) {
                live=false;build.expires=std::min(build.expires,belief.ready);
            } else if(!live) {
                const int expiry=belief.seen+respawn;
                live=expiry<=static_cast<int>(tc.round);
                if(!live)build.expires=std::min(build.expires,expiry);
            }
            build.mask.set(group.tiles[k],live);++build.member;
        }
        ++build.group;build.member=0;
    }
    // A champion's occupied tile cannot simultaneously contain a living camp.
    // Recheck next round if a due spawn was conservatively blocked here.
    if(build.mask.test(o.p)){build.mask.set(o.p,false);build.expires=std::min(build.expires,static_cast<int>(tc.round)+1);}
    RootSet roots;
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
        const auto p=w.altars[altar].tile+vec2{dx,dy};
        if(w.walkable(p)&&!build.mask.test(p))roots.set(p);
    }
    if(roots.is_empty()) {
        tc.guard();cached.field.reset();cached.closed=true;cached.revision=build.revision;cached.expires=build.expires;
        build.altar=-1;return false;
    }
    if(!tc.allow(w.field_budget()+5000))return std::nullopt;
    cambc::bitboard blocked;build.mask.store(blocked);
    auto field=std::make_unique<cambc::distance_field>();field->compute(blocked,roots.board(),w.visited);
    tc.guard();cached.field=std::move(field);cached.closed=false;cached.revision=build.revision;cached.expires=build.expires;
    build.altar=-1;return cached.field->get(o.p)<65535;
}
bool siege_strike_allowed(const Memory& m,const Observation& o,int group,const TurnContext& tc) {
    const auto& task=m.siege_task;
    return task.active()&&task.group==group&&task.phase==siege::Phase::Strike&&task.last_round==static_cast<int>(tc.round)&&
        task.attack==Tile{o.p.x,o.p.y}&&o.hp+task.shield_credit>task.escape_loss;
}
std::optional<Goal> siege_goal(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc,bool altar_open) {
    auto& task=m.siege_task;const auto started=fuel_left();
    if(o.state.is_dead()){task.reset(tc.round,15);return std::nullopt;}
    if(task.active()&&(task.group>=static_cast<int>(w.groups.size())||task.member>=static_cast<int>(m.member_hp[task.group].size())))task.reset(tc.round,15);
    if(task.active()&&!task.finished&&(altar_open||m.member_hp[task.group][task.member]<=0||m.groups[task.group].state==GroupState::Respawning)) {
        trace_task(task,tc,"open",o.hp);task.finished=true;
        task.phase=siege::Phase::Escape;
    }
    if(task.phase==siege::Phase::Recover) {
        if(o.hp<.95f*o.max_hp)return Goal{GoalKind::Home};
        if(task.finished){trace_task(task,tc,"done",o.hp);task.reset(tc.round);m.contract.objective=-1;return std::nullopt;}
        task.phase=siege::Phase::Approach;task.checked=tc.round;task.distance=65535;task.struck=false;task.support_seen=false;
        trace_task(task,tc,"return",o.hp);
    }
    if(task.phase==siege::Phase::Escape) {
        const auto threats=exposure(w,m,task.group,o.p,o.camp_factor,tc);
        if(threats.complete&&camp_damage({o.p.x,o.p.y},threats.view())<=0) {
            task.phase=siege::Phase::Recover;trace_task(task,tc,"recover",o.hp);return Goal{GoalKind::Home};
        }
        if(!threats.complete||!tc.allow(9000))return Goal{GoalKind::Home};
        const auto route=escape(w,m,o,o.p,threats,tc,started);
        if(route.found){task.exit=route.exit;return Goal{GoalKind::Retreat,-1,vec2{route.exit.x,route.exit.y}};}
        return Goal{GoalKind::Retreat};
    }
    // Visible enemy contact is handled by EE/SafeMode, never by a camp-only
    // quote. Keep the task, so a safe interruption does not discard partial HP.
    for(const auto& enemy:o.enemies)if(enemy.p.chebyshev_distance(o.p)<=10)return std::nullopt;
    if(altar_open||static_cast<int>(tc.round)<task.retry_after)return std::nullopt;
    if(!tc.allow(18000))return task.active()?std::optional<Goal>{Goal{GoalKind::Home}}:std::nullopt;
    if(!task.active()) {
        for(unsigned i=0;i<m.route_gate_count;++i) {
            const auto [g,k]=m.route_gates[i];
            if(m.member_hp[g][k]>0||!m.groups[g].available(tc.round))continue;
            // The access model conservatively blocked an expired dead-cell
            // observation. Scout it instead of repeatedly rejecting a zero-HP
            // target; current legal vision will refresh its generation.
            if(tc.allow(4500))m.observe_group(w,g,tc);
            if(m.member_hp[g][k]<=0) {
                const auto& b=m.groups[g];
                m.contract.start(g,tc.round,w.distance(g,o.p),b.hp,b.capture);
                return Goal{GoalKind::Farm,g};
            }
        }
        struct Candidate { int group=-1,member=-1;float cost=1e30f; };
        std::array<Candidate,4> best{};
        auto consider=[&](int g,int k) {
            if(m.member_hp[g][k]<=0||!m.groups[g].available(tc.round))return;
            const float cost=w.distance_floor(g,o.p)+m.member_hp[g][k]/std::max(1.f,o.strength*o.camp_damage);
            bool duplicate=false;for(auto row:best)duplicate|=row.group==g&&row.member==k;
            if(duplicate||cost>=best.back().cost)return;
            best.back()={g,k,cost};std::sort(best.begin(),best.end(),[](auto a,auto b){return a.cost<b.cost;});
        };
        if(m.route_gate_count)for(unsigned i=0;i<m.route_gate_count;++i)consider(m.route_gates[i].first,m.route_gates[i].second);
        else for(const auto& altar:w.altars)for(auto [g,k]:altar.gate_members)consider(g,k);
        // Select a cut before movement; exact escape admission happens on the
        // actual attack tile. No long-range prediction is allowed to wake it.
        for(auto candidate:best)if(candidate.group>=0&&w.distance(candidate.group,o.p)<65535) {
            const int g=candidate.group,k=candidate.member;
            task.start(g,k,tc.round,w.distance(g,o.p),m.member_hp[g][k]);
            trace_task(task,tc,"select",o.hp);break;
        }
        if(!task.active())return std::nullopt;
    }
    const int g=task.group,k=task.member;const auto target=w.groups[g].tiles[k];
    if(!task.progress(tc.round,w.distance(g,o.p),m.member_hp[g][k])) {
        trace_task(task,tc,"abandon",o.hp);defer(m,tc.round,20);return std::nullopt;
    }
    // Approach from the least exposed reachable attack tile. At most 49 local
    // candidates for range<=3, no field allocation or map-wide rollout here.
    vec2 attack=o.p;float best=1e30f;
    for(int dx=-o.range;dx<=o.range;++dx)for(int dy=-o.range;dy<=o.range;++dy) {
        const auto p=target+vec2{dx,dy};if(p==target||!free(w,m,o,p))continue;
        const float score=p.chebyshev_distance(o.p)+.01f*w.home.get(p);
        if(score<best){best=score;attack=p;}
    }
    if(best>=1e30f){defer(m,tc.round,20);return std::nullopt;}
    task.attack={attack.x,attack.y};task.last_round=-1;
    m.contract.objective=g; // Memory observes this group through healing/return.
    if(attack!=o.p&&o.p.chebyshev_distance(target)>8){task.phase=siege::Phase::Approach;return Goal{GoalKind::Farm,g};}
    const auto threats=exposure(w,m,g,o.p,o.camp_factor,tc);
    if(!threats.complete)return Goal{GoalKind::Home};
    std::array<siege::Support,6> support{};unsigned supported=0;
    for(const auto& ally:o.allies) {
        if(supported==support.size()||ally.p.chebyshev_distance(o.p)>8||!tc.allow(8000))continue;
        const auto state=ally.sdk.state();
        if(!state.contains(cambc::champion_state::completed_turn)||state.is_dead()||
            state.contains(cambc::champion_state::recalling)||state.contains(cambc::champion_state::teleporting))continue;
        support[supported++]={{ally.p.x,ally.p.y},static_cast<unsigned>(static_cast<cambc::handle_champion_t>(ally.sdk)),ally.hp,ally.max_hp};
    }
    const auto incoming=siege::incoming({o.p.x,o.p.y},static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),
        threats.view(),std::span<const siege::Support>(support.data(),supported),1/std::max(.001f,o.camp_factor));
    if(!incoming.valid)return Goal{GoalKind::Home};
    const auto route=escape(w,m,o,o.p,threats,tc,started);
    if(!route.found)return Goal{GoalKind::Home};
    float shield_credit=0;
    const auto buffs=cambc::self().buffs();
    if(buffs.has_shield()) {
        const auto shield=buffs.get<cambc::buff_shield>();
        if(shield.duration>0)shield_credit=std::min(incoming.current,shield.value);
    }
    if(shield_credit==0&&!buffs.has_shield())for(const auto& ability:cambc::self().abilities()) {
        if(!tc.allow(6000))break;
        if(ability.is_shield()&&ability.is_ready()&&ability.can_target_self()&&
            std::get<cambc::ability_shield>(*ability.info()).duration>0)
            shield_credit=std::max(shield_credit,std::min(incoming.current,ability.shield_amount()));
    }
    const auto bare=siege::quote(o.hp,o.max_hp,m.member_hp[g][k],o.strength*o.camp_damage,incoming.current,route.damage,2000,incoming.raw);
    const auto wave=siege::quote(o.hp,o.max_hp,m.member_hp[g][k],o.strength*o.camp_damage,incoming.current,route.damage,2000,incoming.raw,shield_credit);
    task.exit=route.exit;task.incoming=incoming.current;task.escape_loss=wave.reserve;
    task.shield_credit=shield_credit;task.required_shield=bare.valid?0:shield_credit;
    if(!wave.valid) {
        if(o.hp>=.95f*o.max_hp&&!task.struck) {
            trace_task(task,tc,"infeasible",o.hp);defer(m,tc.round,60);return std::nullopt;
        }
        if(task.struck&&m.member_hp[g][k]+.01f>=task.visit_hp)++task.failures;
        if(task.failures>=2){defer(m,tc.round,60);return Goal{GoalKind::Home};}
        task.phase=siege::Phase::Escape;++task.visits;trace_task(task,tc,"escape",o.hp);
        return Goal{GoalKind::Retreat,-1,vec2{route.exit.x,route.exit.y}};
    }
    if(attack!=o.p){task.phase=siege::Phase::Approach;return Goal{GoalKind::Farm,g};}
    if(incoming.protected_camps&&!task.support_seen){trace_task(task,tc,"support",o.hp);task.support_seen=true;}
    if(!task.struck){task.visit_hp=m.member_hp[g][k];task.struck=true;}
    task.phase=siege::Phase::Strike;task.last_round=tc.round;
    return Goal{GoalKind::Farm,g};
}
}
#endif
