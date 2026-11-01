#include "config.h"
#if DZ_SIEGE || DZ_ECONOMY_V2
#include "siege.h"
#include "gate_plan.h"
#include "objective_math.h"

namespace dz {
namespace {
struct Exposure {
    std::array<CampThreat,64> camps{};
    unsigned count=0;bool complete=true,uncertain=false;
    std::span<const CampThreat> view() const { return {camps.data(),count}; }
};
// Include the whole pull plus other awake/hidden damaging camps near it.
// Visible sleeping camps in another group are not woken by a basic attack.
Exposure exposure(const StaticWorld& w,const Memory& m,int group,vec2 p,float factor,const TurnContext& tc,
                  std::span<const gate::Cut> cleared={}) {
    Exposure result;
    const auto started=fuel_left();
#if DZ_ECONOMY_V2
    const bool cached=cleared.empty()&&m.neutral.round==static_cast<int>(tc.round)&&m.neutral.origin==Tile{p.x,p.y}&&m.neutral.factor==factor;
    if(cached) {
        result.camps=m.neutral.camps;result.count=m.neutral.count;result.complete=m.neutral.complete;result.uncertain=m.neutral.uncertain;
        if(group<0||!result.complete)return result;
    }
#endif
    LocalMask awake;awake.load(cambc::vision::awake_camp_tiles());
    for(unsigned g=0;g<w.groups.size();++g) {
        const auto& design=w.groups[g];
#if DZ_ECONOMY_V2
        if(cached&&g!=static_cast<unsigned>(group))continue;
#endif
        if(m.groups[g].state==GroupState::Respawning&&m.groups[g].ready>static_cast<int>(tc.round))continue;
        if(design.strength<=0||w.distance_floor(g,p)>12)continue;
        if(!tc.allow(7000)){result.complete=false;return result;}
        const auto& hp=m.member_hp[g];
        for(unsigned k=0;k<hp.size();++k) {
            bool removed=false;for(const auto& cut:cleared)removed|=cut.group==static_cast<int>(g)&&cut.member==static_cast<int>(k);
            if(removed)continue;
            if(hp[k]<=0||design.initial_strength[k]<=0||p.chebyshev_distance(design.tiles[k])>12)continue;
            if(!tc.allow(6000)||started-fuel_left()>8000){result.complete=false;return result;}
            const bool visible=cambc::vision::in_vision(design.tiles[k]);
            if(g!=static_cast<unsigned>(group)&&visible&&!awake.test(design.tiles[k]))continue;
#if DZ_ECONOMY_V2
            if(cached&&std::any_of(result.view().begin(),result.view().end(),[&](const auto& camp){return camp.p==Tile{design.tiles[k].x,design.tiles[k].y};}))continue;
#endif
            if(result.count==result.camps.size()){result.complete=false;return result;}
            // Current visible strength is legal and avoids relying on an old
            // design snapshot. Unseen members retain their conservative design.
            float strength=
#if DZ_ECONOMY_V2
                m.member_strength[g][k];
#else
                design.initial_strength[k];
#endif
            if(!visible&&p.chebyshev_distance(design.tiles[k])<=design.attack_ranges[k])result.uncertain=true;
            if(visible) {
                const auto& camp=design.members()[k];
                if(camp.is_dead())continue;
                if(camp.is_visible())strength=std::max(strength,camp.strength());
            }
            result.camps[result.count++]={{design.tiles[k].x,design.tiles[k].y},strength*factor,design.attack_ranges[k]};
        }
    }
    return result;
}
bool free(const StaticWorld& w,const Memory& m,const Observation& o,vec2 p,int arrival) {
    if(!w.walkable(p)||(p!=o.p&&o.is_occupied(p)))return false;
    if(p==o.p)return true; // Actual occupancy proves the cell is currently free of camps.
    const int g=w.group_at(p);
    if(g>=0) {
        const int member=w.tile_members[p.y*cambc::map::width()+p.x];
        const auto& b=m.groups[g];
        if(member<0||access::member_blocks(m.member_hp[g][member]>0,b.state==GroupState::Respawning,b.ready,arrival))return false;
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
        return free(w,m,o,p,tc.round+cheb(tile,{from.x,from.y}))&&enemy_danger(p,o)<=enemy_danger(o.p,o);
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
void trace_guard(const siege::Task& task,const Observation& o,const TurnContext& tc,const char* reason,std::uint64_t started) {
#if DZ_TRACE
    if(tc.round%10==0){TraceScope scope;trace("DZ_SIEGE_GUARD round=%u body=%u reason=%s pos=%d,%d attack=%d,%d work=%llu\n",tc.round,
        static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),reason,o.p.x,o.p.y,task.attack.x,task.attack.y,
        static_cast<unsigned long long>(started-fuel_left()));}
#else
    (void)task;(void)o;(void)tc;(void)reason;(void)started;
#endif
}
void defer(Memory& memory,int round,int delay) {
    auto& task=memory.siege_task;
    if(task.group>=0)memory.groups[task.group].avoid_until=std::max(memory.groups[task.group].avoid_until,round+delay);
    task.reset(round,5);memory.contract.objective=-1;
#if DZ_ECONOMY_V2
    memory.siege_depth=0;memory.opening_commitment={};
#endif
}
std::optional<Goal> finish_siege(Memory& m,const Observation& o,const TurnContext& tc) {
    auto& task=m.siege_task;
    trace_task(task,tc,"done",o.hp);task.reset(tc.round);m.contract.objective=-1;
#if DZ_ECONOMY_V2
    if(m.siege_depth) {
        task=m.siege_parents[--m.siege_depth];task.phase=siege::Phase::Approach;
        task.checked=tc.round;task.distance=65535;task.last_round=-1;task.struck=false;task.support_seen=false;
        m.contract.objective=task.group;trace_task(task,tc,"resume",o.hp);
        return Goal{GoalKind::Farm,task.group};
    }
#endif
    return std::nullopt;
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
#if DZ_ECONOMY_V2
namespace {
bool delivery_threats(const StaticWorld& w,const Memory& m,const Observation& o,unsigned a,Memory::BankAccess& view,const TurnContext& tc,bool forecast=false) {
    const auto started=fuel_left();const auto center=w.altars[a].tile;
    LocalMask visible,awake;visible.load(cambc::vision::visible_tiles());awake.load(cambc::vision::awake_camp_tiles());
    view.count=0;view.until=cambc::constants::max_rounds-tc.round;
    int escape_range=0;
    for(const auto& group:w.groups) {
        if(!tc.allow(11000)||started-fuel_left()>7000)return false;
        for(auto r:group.attack_ranges)escape_range=std::max(escape_range,r);
    }
    for(unsigned g=0;g<w.groups.size();++g) {
        if(!tc.allow(11000)||started-fuel_left()>7000)return false;
        const auto& design=w.groups[g];const auto& belief=m.groups[g];
        int range=0;for(auto r:design.attack_ranges)range=std::max(range,r);
        // Include hazards on the entire bounded escape ray, not only camps
        // which can hit the submission tile. Unrelated camps cannot be cut by
        // the channel model, but their exit damage must still be paid.
        if(w.distance_floor(g,center)>range+2*escape_range+2+cambc::constants::submit_gems_range)continue;
        for(unsigned k=0;k<design.tiles.size();++k) {
            if(!tc.allow(11000)||started-fuel_left()>7000)return false;
            const auto tile=design.tiles[k];const int reach=design.attack_ranges[k];
            if(tile.chebyshev_distance(center)>reach+2*escape_range+2+cambc::constants::submit_gems_range)continue;
            // Non-damaging spawns away from submission roots are occupancy
            // constraints in escape(), not deadlines for the entire bank.
            const bool deadline=design.initial_strength[k]>0||tile.chebyshev_distance(center)<=cambc::constants::submit_gems_range;
            if(belief.state==GroupState::Respawning&&belief.ready>static_cast<int>(tc.round)) {
                if(deadline)view.until=std::min(view.until,belief.ready-static_cast<int>(tc.round)-1);continue;
            }
            const bool seen=visible.test(tile);float hp=m.member_hp[g][k];
            if(seen) {
                const auto& camp=design.members()[k];if(camp.is_dead())hp=0;else if(camp.is_visible())hp=camp.health();
            }
            if(hp<=0) {
                // Per-member evidence, not another member's recent observation.
                const int last=seen?static_cast<int>(tc.round):m.member_seen[g][k];
                const int until=last+design.sdk.max_respawn_timer()-static_cast<int>(tc.round)-1;
                if(until>0){if(deadline)view.until=std::min(view.until,until);continue;}
                if(seen)continue;hp=design.initial_hp[k];
            }
            if(view.count==view.threats.size())return false;
            const float raw=(forecast||!seen||awake.test(tile))?std::max(m.member_strength[g][k],design.initial_strength[k])*o.camp_factor:0;
            view.threats[view.count++]={static_cast<int>(g),static_cast<int>(k),{{tile.x,tile.y},raw,reach},
                std::max(1.f,hp)/std::max(1.f,o.strength*o.camp_damage)};
        }
    }
    return true;
}
bool opening_geometry_current(const gate::Plan& p,const Memory& m,const TurnContext& tc) {
    if(p.started<0||static_cast<int>(tc.round)>=p.expires)return false;
    for(unsigned i=0;i<p.dependency_count;++i) {
        const auto& d=p.dependencies[i];const auto& b=m.groups[d.group];
        if(!gate::Plan::dependency_matches(d,m.member_hp[d.group][d.member]>0,b.state==GroupState::Respawning,b.ready))return false;
    }
    return true;
}
bool opening_current(const gate::Plan& p,const Memory& m,const Observation& o,const TurnContext& tc) {
    // Scouting resolves stale member evidence; it promises no bank delivery.
    // Preserve that bounded fallback while a full channel quote is unfinished.
    if(p.quality==gate::Quality::Scout)
        return opening_geometry_current(p,m,tc)&&p.matches(tc.round,m.topology_revision,o.max_hp,o.strength*o.camp_damage,o.camp_factor,o.range);
    if(p.altar<0||p.altar>=static_cast<int>(m.bank_access.size()))return false;
    const auto& bank=m.bank_access[p.altar];
    const int age=static_cast<int>(tc.round)-bank.round;
    if(age<0||age>4||bank.revision!=m.topology_revision||!bank.plan.complete()||
        p.rounds+p.delivery+bank.channel+1>bank.until-age)return false;
    for(unsigned i=0;i<bank.plan.count;++i) {
        const auto& threat=bank.threats[bank.plan.cuts[i]];
        if(std::none_of(p.cuts.begin(),p.cuts.begin()+p.count,[&](const auto& cut){return cut.group==threat.group&&cut.member==threat.member;}))return false;
    }
    return p.channel_ready&&opening_geometry_current(p,m,tc)&&p.matches(tc.round,m.topology_revision,o.max_hp,o.strength*o.camp_damage,o.camp_factor,o.range);
}
}
int bank_duration(int bag) {
    const auto owned=cambc::self().item_count();float reduction=0;
    for(auto stat:{cambc::item_stat::strength,cambc::item_stat::focus,cambc::item_stat::health}) {
        const auto emblem=cambc::get_item_enum(cambc::item_family::tribute,stat,false);
        if(owned[emblem])reduction=std::max(reduction,emblem.passive_magnitude());
    }
    const auto q=tribute_delay(bag,cambc::constants::submit_gem_base_duration,cambc::constants::submit_gem_minimum_duration,
        cambc::constants::submit_gem_duration_multiplier,reduction);
    return q.supported()?q.rounds:-1;
}
const Memory::BankAccess* bank_access(StaticWorld& w,Memory& m,const Observation& o,unsigned a,const TurnContext& tc) {
    if(a>=w.altars.size())return nullptr;
    if(m.bank_access.size()!=w.altars.size())m.bank_access.resize(w.altars.size());
    auto& saved=m.bank_access[a];
    saved.status=1;
    // Price the actual carrier. A hypothetical minimum-size bag can require
    // an unaffordable second gate even when the current payout is deliverable.
    const int channel=bank_duration(std::max(o.bag,1));
    if(channel<0)return nullptr;
    const bool same=saved.revision==m.topology_revision&&saved.max_hp==o.max_hp&&saved.factor==o.camp_factor&&saved.channel==channel;
    const int age=static_cast<int>(tc.round)-saved.round;
    if(same&&age>=0&&age<=4&&saved.plan.complete()&&saved.plan.work+saved.plan.travel+channel+1<=saved.until-age){saved.status=5;return &saved;}
    saved.status=2;
    if(!tc.allow(24000))return nullptr;
    const auto started=fuel_left();Memory::BankAccess view;
    view.round=tc.round;view.revision=m.topology_revision;view.max_hp=o.max_hp;view.factor=o.camp_factor;view.channel=channel;
    saved.status=3;
    if(!delivery_threats(w,m,o,a,view,tc,true)) {
#if DZ_TRACE
        if(tc.round%100==0){TraceScope scope;trace("DZ_BANK_UNKNOWN round=%u body=%u altar=%u stage=scene fuel=%llu count=%u\n",tc.round,
            static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),a,static_cast<unsigned long long>(fuel_left()),view.count);}
#endif
        return nullptr;
    }
    // A complete feasible prefix is sufficient; cap both stack initialization
    // and root enumeration independently of the number of altar neighbours.
    std::array<bank::Root,32> roots{};unsigned n=0;const auto altar=w.altars[a].tile;
    const auto threats=std::span<const bank::Threat>(view.threats.data(),view.count);
    const int radius=cambc::constants::submit_gems_range;if(radius>3)return nullptr;
    for(int dx=-radius;dx<=radius;++dx)for(int dy=-radius;dy<=radius;++dy) {
        const auto p=altar+vec2{dx,dy};if(!w.walkable(p))continue;
        n+=bank::escape_roots({p.x,p.y},w.altar_distance(a,o.p),view.until,threats,std::span<bank::Root>(roots).subspan(n),[&](Tile tile,int step) {
            const vec2 q{tile.x,tile.y};if(!w.walkable(q)||enemy_danger(q,o)>enemy_danger(o.p,o))return false;
            const auto camp=std::find_if(threats.begin(),threats.end(),[&](const auto& t){return t.camp.p==tile;});
            return camp!=threats.end()||free(w,m,o,q,tc.round+step+channel);
        },[&]{return tc.allow(15000)&&started-fuel_left()<12000;});
        if(n==roots.size())break;
    }
    saved.status=4;
    const auto model_start=fuel_left();
    view.plan=bank::choose({o.max_hp,o.max_hp,0,0,channel,static_cast<int>(cambc::constants::max_rounds-tc.round)},
        threats,std::span<const bank::Root>(roots.data(),n),
        [&]{return tc.allow(10000)&&model_start-fuel_left()<5000;});
    if(!view.plan.complete()) {
#if DZ_TRACE
        if(tc.round%100==0){TraceScope scope;trace("DZ_BANK_UNKNOWN round=%u body=%u altar=%u stage=roots fuel=%llu count=%u roots=%u until=%d channel=%d\n",tc.round,
            static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),a,static_cast<unsigned long long>(fuel_left()),view.count,n,view.until,channel);}
#endif
        return nullptr;
    }
#if DZ_TRACE
    if(saved.plan.quality!=view.plan.quality||saved.plan.count!=view.plan.count||saved.plan.root!=view.plan.root) {
        TraceScope scope;trace("DZ_BANK_ACCESS round=%u body=%u altar=%u root=%d,%d cuts=%u channel=%d until=%d loss=%.1f\n",tc.round,
            static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),a,view.plan.root.x,view.plan.root.y,view.plan.count,channel,view.until,view.plan.loss);
    }
#endif
    view.status=5;tc.guard();saved=std::move(view);return &saved;
}
bool bank_admission(const StaticWorld& w,Memory& m,const Observation& o,unsigned a,const TurnContext& tc) {
    if(a>=w.altars.size()||!tc.allow(11000))return false;
    Memory::BankAccess view;if(!delivery_threats(w,m,o,a,view,tc))return false;
    const auto p=cambc::self().position();const int channel=bank_duration(cambc::self().gem_count());
    if(channel<0||channel+1>view.until)return false;
    Exposure scene;for(unsigned k=0;k<view.count;++k)scene.camps[scene.count++]=view.threats[k].camp;
    const float raw=camp_damage({p.x,p.y},scene.view());if(raw<=0)return true;
    const auto started=fuel_left();const auto route=escape(w,m,o,p,scene,tc,started);
    if(!route.found){m.neutral_recovery.update(true,false,cambc::self().health(),cambc::self().max_health());return false;}
    bank::Context context{cambc::self().health(),cambc::self().max_health(),0,0,channel,view.until};
    const auto buffs=cambc::self().buffs();
    if(buffs.has_shield()){const auto shield=buffs.get<cambc::buff_shield>();context.shield=shield.value;context.shield_rounds=shield.duration;}
    const float loss=bank::channel_loss(context,raw,route.damage);
#if DZ_TRACE
    {TraceScope scope;trace("DZ_BANK_ADMIT round=%u body=%u altar=%u hp=%.1f raw=%.1f channel=%d shield=%.1f shield_rounds=%d escape=%.1f loss=%.1f allowed=%d\n",tc.round,
        static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),a,context.hp,raw,channel,context.shield,context.shield_rounds,route.damage,loss,context.hp>loss);}
#endif
    if(context.hp>loss)return true;
    m.neutral_recovery.update(true,false,context.hp,context.max_hp);m.neutral_escape.arm(tc.round,{p.x,p.y},route);
    return false;
}
std::optional<Goal> neutral_recovery(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc) {
    const auto started=fuel_left();
    const auto scene=exposure(w,m,-1,o.p,o.camp_factor,tc);
    const bool injured=m.neutral.round==static_cast<int>(tc.round)-1&&m.neutral.hp+o.max_hp-m.neutral.max_hp>o.hp+.01f;
    tc.guard();m.neutral.round=tc.round;m.neutral.origin={o.p.x,o.p.y};m.neutral.factor=o.camp_factor;
    m.neutral.camps=scene.camps;m.neutral.count=scene.count;m.neutral.complete=scene.complete;m.neutral.uncertain=scene.uncertain;
    m.neutral.hp=o.hp;m.neutral.max_hp=o.max_hp;m.neutral.risk_count=0;
    // Visible awake camps are actual hazards. Hidden spawns are uncertain and
    // stay in the full admission scene, but are not declared awake merely from
    // design HP. A new unexplained HP loss activates that conservative scene.
    const bool recovering=m.neutral_recovery.update(false,w.home.get(o.p)==0,o.hp,o.max_hp);
    LocalMask visible;visible.load(cambc::vision::visible_tiles());
    Exposure hazards;
    for(const auto& camp:scene.view())if(visible.test({camp.p.x,camp.p.y})||injured||recovering)hazards.camps[hazards.count++]=camp;
    m.neutral.risks=hazards.camps;m.neutral.risk_count=hazards.count;
    m.neutral_moves={static_cast<int>(tc.round),{o.p.x,o.p.y},511,0};
    const float raw=camp_damage({o.p.x,o.p.y},hazards.view());
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy)
        if(siege::withdrawal_safe(o.hp,raw,camp_damage({o.p.x+dx,o.p.y+dy},hazards.view())))
            m.neutral_moves.withdrawal|=1u<<((dx+1)*3+dy+1);
    if(!scene.complete) {
        if(raw>0)return Goal{GoalKind::Retreat};
        return Goal{GoalKind::Home};
    }
    if(!hazards.count)return recovering?std::optional<Goal>{Goal{GoalKind::Home}}:std::nullopt;
    auto route=escape(w,m,o,o.p,hazards,tc,started);
    if(recovering&&m.neutral_escape.round==static_cast<int>(tc.round)-1) {
        const auto retained=siege::retained_escape({o.p.x,o.p.y},m.neutral_escape.exit,hazards.view(),[&](Tile p) {
            return free(w,m,o,{p.x,p.y},tc.round+cheb({o.p.x,o.p.y},p))&&enemy_danger({p.x,p.y},o)<=enemy_danger(o.p,o);
        },[&]{return tc.allow(6000)&&started-fuel_left()<16000;});
        if(retained.found&&o.hp>retained.damage)route=retained;
    }
    if(route.found) {
        m.neutral_moves.allowed=0;
        for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
            const Tile next{o.p.x+dx,o.p.y+dy};
            if(siege::backtrack_safe(o.hp,o.max_hp,raw,camp_damage(next,hazards.view()),route.damage))
                m.neutral_moves.allowed|=1u<<((dx+1)*3+dy+1);
        }
    }
    // The siege controller retains its precise first-phase shield and committed
    // ally admission. Every OTHER macro/legacy path gets the same camp reserve.
    if(m.siege_task.active())return std::nullopt;
    if(raw>0&&(recovering||!route.found||o.hp<=.15f*o.max_hp+1.25f*route.damage+2*raw)) {
        m.neutral_recovery.update(true,false,o.hp,o.max_hp);
        if(route.found)m.neutral_escape.arm(tc.round,{o.p.x,o.p.y},route);
#if DZ_TRACE
        {TraceScope scope;trace("DZ_NEUTRAL_ESCAPE round=%u body=%u hp=%.0f incoming=%.0f escape=%.0f route=%d from=%d,%d exit=%d,%d\n",tc.round,
            static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),o.hp,raw,route.damage,route.found,o.p.x,o.p.y,route.exit.x,route.exit.y);}
#endif
        return Goal{GoalKind::Retreat,-1,route.found?std::optional<vec2>{vec2{route.exit.x,route.exit.y}}:std::nullopt};
    }
    if(recovering)return Goal{GoalKind::Home};
    return std::nullopt;
}
void quote_opening(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc) {
    if(w.altars.empty()||!local_masks_valid||!tc.allow(13000))return;
    if(m.openings.size()!=w.altars.size())m.openings.resize(w.altars.size());
    const unsigned a=m.opening_commitment.active()?static_cast<unsigned>(m.opening_commitment.altar):m.opening_cursor++%w.altars.size();
    if(a>=w.altars.size()){m.opening_commitment={};return;}
    const auto* delivery=bank_access(w,m,o,a,tc);
    if(!delivery)return; // Unknown delivery cannot publish a complete opening.
    auto& plan=m.openings[a];
    const auto started=fuel_left();
    if(!opening_geometry_current(plan,m,tc))plan.reset(tc.round,m.topology_revision,o.max_hp,o.strength*o.camp_damage,o.camp_factor,o.range);
    else if(!plan.matches(tc.round,m.topology_revision,o.max_hp,o.strength*o.camp_damage,o.camp_factor,o.range)) {
        // Equipment changes prices, not the already inspected route geometry.
        plan.max_hp=o.max_hp;plan.damage=o.strength*o.camp_damage;plan.factor=o.camp_factor;plan.range=o.range;
        plan.priced=0;plan.rounds=0;plan.visits=0;
        if(plan.path_ready)plan.quality=gate::Quality::Building;
    }
    for(unsigned i=0;i<plan.count;++i)if(m.hp_version[plan.cuts[i].group]!=plan.cuts[i].version) {
        plan.priced=0;plan.rounds=0;plan.visits=0;plan.quality=gate::Quality::Building;
        for(unsigned k=0;k<plan.count;++k)plan.cuts[k].version=m.hp_version[plan.cuts[k].group];
        break;
    }
    if(plan.channel_ready)for(unsigned i=0;i<delivery->plan.count;++i) {
        const auto& t=delivery->threats[delivery->plan.cuts[i]];
        if(std::none_of(plan.cuts.begin(),plan.cuts.begin()+plan.count,[&](const auto& c){return c.group==t.group&&c.member==t.member;})) {
            plan.channel_ready=false;plan.quality=gate::Quality::Building;
            plan.priced=0;plan.rounds=0;plan.visits=0;break;
        }
    }
    if(plan.quality!=gate::Quality::Building)return;
    const auto& altar=w.altars[a];const int width=cambc::map::width(),height=cambc::map::height();
    auto unsupported=[&](gate::Failure why){plan.quality=gate::Quality::Unsupported;plan.failure=why;};
    if(altar.distances.size()!=static_cast<unsigned>(width*height)){unsupported(gate::Failure::Geometry);return;}
    auto distance=[&](Tile p) {
        return p.x>=0&&p.y>=0&&p.x<width&&p.y<height?static_cast<int>(altar.distances[p.y*width+p.x]):65535;
    };
    if(!plan.origin_ready) {
        // Start the repeated-wave itinerary from Home. The real executor first
        // restocks there; a different spawn cell adds at most the spawn diameter
        // to this static arrival estimate. No camp-death teleport is assumed.
        const auto spawns=cambc::map::spawn_region(cambc::team::ally).positions();
        if(spawns.empty()||spawns.size()>512){plan.quality=gate::Quality::Unsupported;return;}
        int nearest=65535,x0=width,y0=height,x1=0,y1=0;
        for(auto p:spawns) {
            const int d=distance({p.x,p.y});
            if(d<nearest){nearest=d;plan.origin={p.x,p.y};}
            x0=std::min(x0,p.x);y0=std::min(y0,p.y);x1=std::max(x1,p.x);y1=std::max(y1,p.y);
        }
        if(nearest>=65535){plan.quality=gate::Quality::Unsupported;return;}
        plan.cursor=plan.origin;plan.origin_ready=true;plan.altar=a;plan.delivery=nearest+std::max(x1-x0,y1-y0);
    }
    if(!plan.path_ready) {
        bool unsupported=false,scout=false;
        const auto route=access::itinerary(plan.cursor,distance,[&](Tile tile) {
            const vec2 p{tile.x,tile.y};const int g=w.group_at(p);
            if(g<0)return access::Blocker{};
            const int k=w.tile_members[tile.y*width+tile.x];if(k<0)return access::Blocker{};
            const auto& b=m.groups[g];
            if(b.state==GroupState::Respawning&&b.ready>static_cast<int>(tc.round))return access::Blocker{};
            const bool stale=m.member_hp[g][k]<=0&&static_cast<int>(tc.round)-b.seen>=w.groups[g].sdk.max_respawn_timer();
            if(m.member_hp[g][k]<=0&&!stale)return access::Blocker{};
            return access::Blocker{g,k,std::max(m.member_hp[g][k],1.f)/std::max(1.f,plan.damage)};
        },[&](access::Blocker member,Tile previous,Tile tile,int steps) {
            const int g=w.group_at({tile.x,tile.y});
            if(g>=0) {
                if(plan.dependency_count==plan.dependencies.size()){unsupported=true;return false;}
                const int k=w.tile_members[tile.y*width+tile.x];const auto& b=m.groups[g];
                if(k<0){unsupported=true;return false;}
                plan.dependencies[plan.dependency_count++]={g,k,b.ready,m.member_hp[g][k]>0,b.state==GroupState::Respawning};
                if(b.state==GroupState::Respawning&&b.ready>static_cast<int>(tc.round))plan.expires=std::min(plan.expires,b.ready);
                else if(m.member_hp[g][k]<=0)plan.expires=std::min(plan.expires,std::max(static_cast<int>(tc.round)+8,b.seen+w.groups[g].sdk.max_respawn_timer()));
            }
            if(member.group<0)return true;
            if(plan.count==plan.cuts.size()){unsupported=true;return false;}
            auto& cut=plan.cuts[plan.count++];
            cut.group=member.group;cut.member=member.member;cut.tile=tile;cut.approach=previous;
            cut.arrival=plan.travel+steps;cut.hp=m.member_hp[cut.group][cut.member];cut.version=m.hp_version[cut.group];
            if(cut.hp<=0){scout=true;return false;}
            return true;
        },[&]{return tc.allow(8000)&&started-fuel_left()<6000;},8);
        plan.travel+=route.steps;plan.cursor=route.tile;
        if(scout){plan.quality=gate::Quality::Scout;plan.rounds=plan.travel;return;}
        if(unsupported||route.status==access::Status::Unreachable){plan.quality=gate::Quality::Unsupported;return;}
        if(route.status!=access::Status::Clear)return; // Resume the same path, not its beginning.
        plan.path_ready=true;
        return; // Geometry quotes start on a later turn.
    }
    if(!plan.channel_ready) {
        // A physically clear path is only one part of delivery. Append every
        // required channel cut, including off-path monsters, before assigning
        // any banking value to the project. Existing cuts are never duplicated.
        for(unsigned i=0;i<delivery->plan.count;++i) {
            const auto& t=delivery->threats[delivery->plan.cuts[i]];
            if(std::any_of(plan.cuts.begin(),plan.cuts.begin()+plan.count,[&](const auto& c){return c.group==t.group&&c.member==t.member;}))continue;
            if(plan.count==plan.cuts.size()||plan.dependency_count==plan.dependencies.size()) {unsupported(gate::Failure::Capacity);return;}
            if(!tc.allow(11000)||started-fuel_left()>8000)return;
            const auto target=w.groups[t.group].tiles[t.member];Tile approach{};int nearest=65535;
            if(plan.approach_search.active&&plan.approach_group==t.group&&plan.approach_member==t.member) {
                approach=plan.channel_approach;nearest=w.home.get({approach.x,approach.y});
            } else {
              for(int dx=-o.range;dx<=o.range;++dx)for(int dy=-o.range;dy<=o.range;++dy) {
                if(!dx&&!dy)continue;
                const auto p=target+vec2{dx,dy};if(!w.walkable(p))continue;
                const int g=w.group_at(p);
                if(g>=0) {
                    const int k=w.tile_members[p.y*width+p.x];
                    if(k<0||m.member_hp[g][k]>0)continue;
                }
                const int d=w.home.get(p);
                if(d<nearest){nearest=d;approach={p.x,p.y};}
              }
              if(nearest<65535) {
                plan.approach_group=t.group;plan.approach_member=t.member;plan.channel_approach=approach;plan.approach_search.begin(approach);
              }
            }
            if(nearest>=65535){unsupported(gate::Failure::Approach);return;}
            const auto home=[&](Tile p) {
                return p.x>=0&&p.y>=0&&p.x<width&&p.y<height&&w.home_distances.size()==static_cast<unsigned>(width*height)?
                    static_cast<int>(w.home_distances[p.y*width+p.x]):65535;
            };
            const auto prerequisites=plan.approach_search.advance(home,[&](Tile tile) {
                const int g=w.tile_groups[tile.y*width+tile.x];if(g<0)return access::Blocker{};
                const int k=w.tile_members[tile.y*width+tile.x];if(k<0)return access::Blocker{};
                const auto& b=m.groups[g];
                if((b.state==GroupState::Respawning&&b.ready>static_cast<int>(tc.round))||m.member_hp[g][k]<=0||
                    std::any_of(plan.cuts.begin(),plan.cuts.begin()+plan.count,[&](const auto& c){return c.group==g&&c.member==k;}))return access::Blocker{};
                return access::Blocker{g,k,m.member_hp[g][k]/std::max(1.f,plan.damage)};
            },[&]{return tc.allow(10000)&&started-fuel_left()<12000;});
            if(prerequisites.status!=access::Status::Clear) {
                if(!plan.approach_search.active)unsupported(gate::Failure::Approach);
                return;
            }
            for(unsigned k=0;k<prerequisites.count;++k) {
                if(plan.count+1>=plan.cuts.size()||plan.dependency_count+1>=plan.dependencies.size()) {plan.quality=gate::Quality::Unsupported;return;}
                const auto& q=prerequisites.cuts[k];const auto g=q.blocker.group,member=q.blocker.member;
                auto& cut=plan.cuts[plan.count++];cut.group=g;cut.member=member;cut.tile=q.tile;cut.approach=q.approach;
                cut.arrival=q.arrival;cut.hp=m.member_hp[g][member];cut.version=m.hp_version[g];
                const auto& b=m.groups[g];plan.dependencies[plan.dependency_count++]={g,member,b.ready,true,b.state==GroupState::Respawning};
            }
            if(std::any_of(plan.cuts.begin(),plan.cuts.begin()+plan.count,[&](const auto& c){return c.group==t.group&&c.member==t.member;}))continue;
            auto& cut=plan.cuts[plan.count++];cut.group=t.group;cut.member=t.member;
            cut.tile={target.x,target.y};cut.approach=approach;cut.arrival=nearest;
            cut.hp=m.member_hp[t.group][t.member];cut.version=m.hp_version[t.group];
            const auto& belief=m.groups[t.group];
            plan.dependencies[plan.dependency_count++]={t.group,t.member,belief.ready,cut.hp>0,belief.state==GroupState::Respawning};
            if(cut.hp<=0){plan.quality=gate::Quality::Scout;plan.rounds=nearest;return;}
        }
        plan.channel_ready=true;
        if(!plan.count){plan.quality=gate::Quality::Unsupported;return;}
    }
    // At most one cut geometry / escape search per call. Path and prices are
    // published only when every layer is complete, with member-HP versions.
    if(plan.priced<plan.count) {
        auto& cut=plan.cuts[plan.priced];const vec2 p{cut.approach.x,cut.approach.y};
        const auto cleared=std::span<const gate::Cut>(plan.cuts.data(),plan.priced);
        const auto threats=exposure(w,m,cut.group,p,o.camp_factor,tc,cleared);
        if(!threats.complete)return;
        const auto route=siege::escape_route(cut.approach,threats.view(),std::array<Tile,8>{{{-1,-1},{-1,0},{-1,1},{0,-1},{0,1},{1,-1},{1,0},{1,1}}},[&](Tile tile) {
            const vec2 q{tile.x,tile.y};if(!w.walkable(q))return false;
            const int g=w.group_at(q);if(g<0)return true;
            const int k=w.tile_members[tile.y*width+tile.x];
            const auto& b=m.groups[g];
            if(b.state==GroupState::Respawning&&b.ready>static_cast<int>(tc.round)+cheb(tile,cut.approach))return true;
            if(k<0||m.member_hp[g][k]<=0)return true;
            return std::any_of(cleared.begin(),cleared.end(),[&](const auto& c){return c.group==g&&c.member==k;});
        },[&]{return tc.allow(6000)&&started-fuel_left()<16000;});
        if(!route.found){unsupported(gate::Failure::Exit);return;}
        cut.hp=m.member_hp[cut.group][cut.member];cut.version=m.hp_version[cut.group];
        cut.incoming=camp_damage(cut.approach,threats.view());cut.escape_loss=route.damage;cut.escape_rounds=route.steps;
        // Re-use the already traced prefix for repeat visits; an unchecked
        // static Home shortcut might itself cross a future live barrier.
        cut.home=cut.arrival+route.steps;
        const auto work=gate::price(cut,o.max_hp,o.max_hp,plan.damage);
        if(!work.valid||plan.rounds+work.rounds>2000){unsupported(gate::Failure::Work);return;}
        plan.rounds+=work.rounds;plan.visits+=work.visits;++plan.priced;
    }
    if(plan.priced==plan.count) {
        if(plan.rounds+plan.delivery+delivery->channel+1>delivery->until){unsupported(gate::Failure::Window);return;}
        plan.quality=gate::Quality::Ready;
        plan.failure=gate::Failure::None;
        plan.expires=std::min(plan.expires,static_cast<int>(tc.round)+32);
#if DZ_TRACE
        {TraceScope scope;trace("DZ_OPENING_QUOTE round=%u body=%u altar=%u cuts=%u visits=%d work=%d delivery=%d\n",tc.round,
            static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),a,plan.count,plan.visits,plan.rounds,plan.delivery);}
#endif
    }
}
const gate::Plan* best_opening(const Memory& m,const Observation& o,const TurnContext& tc) {
    const gate::Plan* result=nullptr;
    for(const auto& plan:m.openings)if((plan.quality==gate::Quality::Ready||plan.quality==gate::Quality::Scout)&&opening_current(plan,m,o,tc)) {
        bool fresh=true;for(unsigned i=0;i<plan.priced;++i)fresh&=m.hp_version[plan.cuts[i].group]==plan.cuts[i].version;
        if(fresh&&(!result||plan.rounds+plan.delivery<result->rounds+result->delivery))result=&plan;
    }
    return result;
}
std::optional<Goal> yield_siege_lane(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc) {
    if(!o.enemies.empty()||!tc.allow(12000))return std::nullopt;
    const auto word=shared_word();const int home=w.home.get(o.p);bool needed=false;
    for(const auto& ally:o.allies) {
        const auto slot=std::find(w.allies.begin(),w.allies.end(),ally.sdk);
        if(slot==w.allies.end()||protocol::slot(word,slot-w.allies.begin()).objective!=protocol::retreat)continue;
        if(siege::yield_lane({o.p.x,o.p.y},{ally.p.x,ally.p.y},o.hp,o.max_hp,ally.hp,ally.max_hp,home,w.home.get(ally.p)))needed=true;
    }
    if(!needed)return std::nullopt;
    const auto threats=exposure(w,m,-1,o.p,o.camp_factor,tc);
    if(!threats.complete)return std::nullopt;
    vec2 best=o.p;int distance=home;float damage=1e30f;
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
        const auto p=o.p+vec2{dx,dy};if(p==o.p||!free(w,m,o,p,tc.round+1))continue;
        const bool guarded=m.neutral_moves.round==static_cast<int>(tc.round)&&m.neutral_moves.origin==Tile{o.p.x,o.p.y};
        if(guarded&&!(m.neutral_moves.allowed&(1u<<((dx+1)*3+dy+1))))continue;
        const int d=w.home.get(p);if(d>=home)continue;
        const float incoming=camp_damage({p.x,p.y},threats.view());
        if(o.hp<=incoming+.15f*o.max_hp)continue;
        if(incoming<damage||(incoming==damage&&d<distance)){best=p;damage=incoming;distance=d;}
    }
    if(best==o.p)return std::nullopt;
#if DZ_TRACE
    {TraceScope scope;trace("DZ_LANE_YIELD round=%u body=%u from=%d,%d to=%d,%d\n",tc.round,
        static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),o.p.x,o.p.y,best.x,best.y);}
#endif
    // Yield exactly this step. Generic Retreat can recall/cast first and leave
    // the planned lane occupied while the injured worker keeps taking hits.
    return Goal{GoalKind::YieldSpawn,-1,best};
}
std::optional<Goal> begin_opening(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc,int altar) {
    if(altar<0||altar>=static_cast<int>(m.openings.size()))return std::nullopt;
    const auto& plan=m.openings[altar];
    if(!opening_current(plan,m,o,tc)||!plan.count)return std::nullopt;
    const auto& cut=plan.cuts[0];
    m.economic_crew=0;m.contract.objective=cut.group;
    if(plan.quality==gate::Quality::Scout)return Goal{GoalKind::Farm,cut.group};
    if(plan.quality!=gate::Quality::Ready)return std::nullopt;
    m.opening_commitment.begin(altar,tc.round,plan.rounds+plan.delivery);
    auto& task=m.siege_task;task.start(cut.group,cut.member,tc.round,w.distance(cut.group,o.p),m.member_hp[cut.group][cut.member]);
    task.attack=cut.approach;task.planned_approach=true;task.restock=true;task.phase=siege::Phase::Recover;
    trace_task(task,tc,"select",o.hp);
    return siege_goal(w,m,o,tc,false);
}
#endif
bool siege_strike_allowed(const Memory& m,const Observation& o,int group,const TurnContext& tc) {
    const auto& task=m.siege_task;
    return task.active()&&task.group==group&&task.phase==siege::Phase::Strike&&task.last_round==static_cast<int>(tc.round)&&
        task.attack==Tile{o.p.x,o.p.y}&&o.hp+task.shield_credit>task.escape_loss;
}
std::optional<Goal> siege_goal(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc,bool altar_open) {
    auto& task=m.siege_task;const auto started=fuel_left();
    if(o.state.is_dead()){task.reset(tc.round,15);return std::nullopt;}
    if(task.active()&&(task.group>=static_cast<int>(w.groups.size())||task.member>=static_cast<int>(m.member_hp[task.group].size())))task.reset(tc.round,15);
#if DZ_ECONOMY_V2
    if(task.active()&&m.opening_commitment.executing&&static_cast<int>(tc.round)>m.opening_commitment.deadline) {
        trace_task(task,tc,"project_timeout",o.hp);task.finished=true;task.phase=siege::Phase::Escape;
        m.opening_commitment={};m.siege_depth=0;
    }
#endif
    if(task.active()&&!task.finished&&(altar_open||m.member_hp[task.group][task.member]<=0||m.groups[task.group].state==GroupState::Respawning)) {
        trace_task(task,tc,"open",o.hp);task.finished=true;
        task.phase=siege::Phase::Escape;
    }
    if(task.phase==siege::Phase::Recover) {
        if(task.restock&&w.home.get(o.p)>0)return Goal{GoalKind::Home};
        if(o.hp<.95f*o.max_hp)return Goal{GoalKind::Home};
        if(task.finished)return finish_siege(m,o,tc);
        task.phase=siege::Phase::Approach;task.checked=tc.round;task.distance=65535;task.struck=false;task.support_seen=false;task.restock=false;
        trace_task(task,tc,"return",o.hp);
    }
    if(task.phase==siege::Phase::Escape) {
        const auto threats=exposure(w,m,task.group,o.p,o.camp_factor,tc);
        if(threats.complete&&camp_damage({o.p.x,o.p.y},threats.view())<=0) {
            // A free, completed cut need not start a recall before converting
            // nearby bags or resuming a blocked parent. Avoid throwing away a
            // short access window by healing an already healthy champion.
            if(task.finished&&(altar_open||o.hp>=.95f*o.max_hp))return finish_siege(m,o,tc);
            task.phase=siege::Phase::Recover;trace_task(task,tc,"recover",o.hp);return Goal{GoalKind::Home};
        }
        if(!threats.complete||!tc.allow(9000))return Goal{GoalKind::Retreat};
        const auto route=escape(w,m,o,o.p,threats,tc,started);
        if(route.found){task.exit=route.exit;
#if DZ_ECONOMY_V2
            m.neutral_escape.arm(tc.round,{o.p.x,o.p.y},route);
#endif
            return Goal{GoalKind::Retreat,-1,vec2{route.exit.x,route.exit.y}};}
        return Goal{GoalKind::Retreat};
    }
    // Visible enemy contact is handled by EE/SafeMode, never by a camp-only
    // quote. Keep the task, so a safe interruption does not discard partial HP.
    for(const auto& enemy:o.enemies)if(enemy.p.chebyshev_distance(o.p)<=10)return std::nullopt;
    if(altar_open||static_cast<int>(tc.round)<task.retry_after)return std::nullopt;
    if(!tc.allow(18000))return task.active()?std::optional<Goal>{Goal{task.struck?GoalKind::Retreat:GoalKind::Home}}:std::nullopt;
#if DZ_ECONOMY_V2
    if(task.active()&&task.planned_approach&&task.phase==siege::Phase::Approach&&m.opening_commitment.executing&&
        m.opening_commitment.altar>=0&&m.opening_commitment.altar<static_cast<int>(w.altars.size())) {
        const auto route=altar_route(w,m,o,m.opening_commitment.altar,tc);
        if(route.status==access::Status::Blocked&&(route.blocker.group!=task.group||route.blocker.member!=task.member)&&
            m.member_hp[route.blocker.group][route.blocker.member]>0) {
            bool cycle=false;
            for(unsigned i=0;i<m.siege_depth;++i)cycle|=m.siege_parents[i].group==route.blocker.group&&m.siege_parents[i].member==route.blocker.member;
            if(!cycle&&m.siege_depth<m.siege_parents.size()) {
                trace_task(task,tc,"suspend",o.hp);m.siege_parents[m.siege_depth++]=task;
                const auto b=route.blocker;
                task.start(b.group,b.member,tc.round,w.distance(b.group,o.p),m.member_hp[b.group][b.member]);
                task.attack=route.previous;task.planned_approach=true;
                m.contract.objective=b.group;trace_task(task,tc,"select",o.hp);
                return Goal{GoalKind::Farm,b.group}; // Fresh live admission on the next turn.
            }
        }
    }
#endif
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
    if(task.planned_approach) {
        attack={task.attack.x,task.attack.y};
        // An occupied rally tile is not a reason to skip exposure/withdrawal
        // admission while waiting under already awake camps.
        best=0;
    } else
    for(int dx=-o.range;dx<=o.range;++dx)for(int dy=-o.range;dy<=o.range;++dy) {
        const auto p=target+vec2{dx,dy};if(p==target||!free(w,m,o,p,tc.round))continue;
        const float score=p.chebyshev_distance(o.p)+.01f*w.home.get(p);
        if(score<best){best=score;attack=p;}
    }
    if(best>=1e30f){defer(m,tc.round,20);return std::nullopt;}
    task.attack={attack.x,attack.y};task.last_round=-1;
    m.contract.objective=g; // Memory observes this group through healing/return.
    if(attack!=o.p&&o.p.chebyshev_distance(target)>8){task.phase=siege::Phase::Approach;return Goal{GoalKind::Farm,g};}
    const auto threats=exposure(w,m,g,o.p,o.camp_factor,tc);
    if(!threats.complete){trace_guard(task,o,tc,"exposure",started);task.phase=siege::Phase::Escape;return Goal{GoalKind::Retreat};}
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
    if(!incoming.valid){trace_guard(task,o,tc,"incoming",started);return Goal{GoalKind::Home};}
    const auto route=escape(w,m,o,o.p,threats,tc,started);
    if(!route.found){
        trace_guard(task,o,tc,"escape",started);
        task.phase=siege::Phase::Escape;trace_task(task,tc,"escape",o.hp);
        return Goal{GoalKind::Retreat}; // Publish distress so an allied capturer can free the exit.
    }
    float shield_credit=0;
    const auto buffs=cambc::self().buffs();
    if(buffs.has_shield()) {
        const auto shield=buffs.get<cambc::buff_shield>();
        if(shield.duration>0)shield_credit=std::min(incoming.current,shield.value);
    }
    if(attack==o.p&&shield_credit==0&&!buffs.has_shield())for(const auto& ability:cambc::self().abilities()) {
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
#if DZ_ECONOMY_V2
    m.siege_moves={static_cast<int>(tc.round),{o.p.x,o.p.y},0};
    const float raw=camp_damage({o.p.x,o.p.y},threats.view());
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
        const Tile p{o.p.x+dx,o.p.y+dy};
        if(siege::backtrack_safe(o.hp,o.max_hp,raw,camp_damage(p,threats.view()),route.damage))
            m.siege_moves.allowed|=1u<<((dx+1)*3+dy+1);
    }
#endif
    if(attack!=o.p){trace_guard(task,o,tc,"approach",started);task.phase=siege::Phase::Approach;return Goal{GoalKind::Farm,g};}
    if(incoming.protected_camps&&!task.support_seen){trace_task(task,tc,"support",o.hp);task.support_seen=true;}
    if(!task.struck){task.visit_hp=m.member_hp[g][k];task.struck=true;}
    task.phase=siege::Phase::Strike;task.last_round=tc.round;
    return Goal{GoalKind::Farm,g};
}
}
#endif
