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
    // Each visible inventory is decoded once per planning turn. Macro quotes,
    // crew layout and gear counterfactuals used to repeat the same SDK scans.
    // No cross-turn equipment inference or hidden inventory is introduced.
    struct Cached { unsigned id=~0u,round=~0u;float strength=0,max_hp=0;objective::Actor actor; };
    static std::array<Cached,objective::max_crew> cached{};
    const unsigned id=static_cast<unsigned>(static_cast<cambc::handle_champion_t>(c.sdk)),round=cambc::round_number();
    auto entry=std::find_if(cached.begin(),cached.end(),[&](const auto& e){return e.id==id;});
    if(entry==cached.end())entry=std::find_if(cached.begin(),cached.end(),[&](const auto& e){return e.round!=round;});
    if(entry==cached.end())entry=cached.begin();
    if(entry->id==id&&entry->round==round&&entry->strength==c.strength&&entry->max_hp==c.max_hp) {
        auto actor=entry->actor;actor.hp=c.hp;return actor;
    }
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
    *entry={id,round,c.strength,c.max_hp,actor};return actor;
}
namespace {
objective::Kit self_kit(const TurnContext& tc) {
    static int round=-1;static objective::Kit saved;
    if(round==static_cast<int>(tc.round))return saved;
    if(!tc.allow(12000))return {};
    auto& me=cambc::self();objective::Kit kit;
    if(me.restrictions().contains(cambc::buff_restrictions::cast))return {};
    kit.can_cast=me.state().contains(cambc::champion_state::can_cast);
    kit.refresh_on_monster=me.champion_name()==cambc::champion_type::vendetta;
    const auto buffs=me.buffs();
    if(buffs.has_shield()){const auto b=buffs.get<cambc::buff_shield>();kit.shield=b.value;kit.shield_duration=std::max(0,b.duration);}
    unsigned slot=0;bool earlier_unmodelled=false;
    for(const auto& ability:me.abilities()) {
        auto& c=kit.casts[slot++];if(!ability.info())continue;
        const auto& info=*ability.info();bool exclusive=false;float range=0;
        std::visit([&](auto p){
            c.period=std::max(0,p.max_cooldown);exclusive=p.exclusive_with_movement;
            if constexpr(requires{p.range;})range=p.range;
            if constexpr(requires{p.duration;})c.duration=std::max(0,p.duration);
        },info);
        if(ability.is_attack_reset())c.kind=objective::CastKind::Reset;
        else if(ability.is_shield()&&ability.can_target_self()){c.kind=objective::CastKind::Shield;c.amount=ability.shield_amount();}
        else if(!exclusive&&range>=me.attack_range()&&ability.can_target_camps()&&ability.is_damage()) {
            c.kind=objective::CastKind::Damage;c.amount=ability.damage_amount();
        }
        if(earlier_unmodelled&&(c.kind==objective::CastKind::Reset||c.kind==objective::CastKind::Damage))c.kind=objective::CastKind::None;
        earlier_unmodelled|=(ability.is_damage()||ability.is_cc()||ability.is_aoe_damage())&&c.kind==objective::CastKind::None;
        // AoE/CC/dash and enhanced-attack passives get no speculative credit.
        if(c.kind!=objective::CastKind::None)c.cooldown=std::max(0,ability.cooldown());
    }
    tc.guard();saved=kit;round=tc.round;return saved;
}
objective::Quote self_quote(const objective::Encounter& e,const objective::Actor& actor,const TurnContext& tc,bool future=false) {
    if(!tc.allow(14000))return objective::forecast(e,std::span<const objective::Actor>(&actor,1),0);
    auto kit=self_kit(tc);
    if(future) {
        kit.shield=0;kit.shield_duration=0;kit.can_cast=true;
        for(auto& c:kit.casts)c.cooldown=c.period;
    }
    const auto started=fuel_left();
    return objective::forecast_casts(e,actor,kit,[&]{return tc.allow(10000)&&started-fuel_left()<4500;});
}
struct Participant { objective::Actor actor;vec2 p;unsigned slot;int range=1;unsigned handle=0; };
objective::Encounter encounter(const StaticWorld& w,const Memory& m,int g,std::span<ClearMember> members,std::span<unsigned> counts,int round,int horizon,bool full_generation=false) {
    const auto& group=w.groups[g];const auto& belief=m.groups[g];
    unsigned distinct=0;
    for(unsigned k=0;k<m.member_hp[g].size();++k) {
        const float hp=full_generation?group.initial_hp[k]:m.member_hp[g][k];if(hp<=0)continue;
        const ClearMember member{hp,m.member_strength[g][k]};
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
    e.ready_in=!full_generation&&belief.state==GroupState::Respawning ? std::max(0,belief.ready-round) : 0;
    // Multi-member geometry is not stationary: include travel between members.
    // This explicit conservative bound can reject large groups; it never prices
    // them as one monster. Later exact geometry calibration may tighten it.
    e.reposition_rounds=group.radius*2;
    return e;
}
bool reserved_job(const StaticWorld& w,const Memory& m,const Observation& o,int g,const TurnContext& tc) {
    const auto word=shared_word();const auto lease=protocol::compact::lease(word,tc.round);
    if(lease.valid&&lease.objective==g&&!(lease.members&(1u<<w.slot)))return true;
    for(const auto& ally:o.allies) {
        const auto it=std::find(w.allies.begin(),w.allies.end(),ally.sdk);
        if(it==w.allies.end())continue;
        const unsigned slot=it-w.allies.begin();
        if(protocol::slot(word,slot).objective==g&&w.distance(g,ally.p)<=ally.range+1&&
            (m.groups[g].state==GroupState::Partial||m.groups[g].state==GroupState::Reward||m.groups[g].state==GroupState::Respawning)&&
            (m.contract.objective!=g||w.distance(g,o.p)>o.range+1||slot<w.slot))return true;
    }
    return false;
}
float upgraded_job_value(const ShopVisit& shop,const StaticWorld& w,const Memory& m,const Observation& o,const TurnContext& tc,int horizon) {
    if(!shop.valid||!tc.allow(16000)||horizon<=0)return 0;
    auto before=economic_actor({cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range});
    before.hp=before.max_hp;auto after=before;const auto design=cambc::self().base_stats();
    const auto info=shop.item.info();if(!info.result||shop.purchases>info.combine_count)return 0;
    const auto result=info.result->info();const bool complete=shop.shards+shop.purchases==info.combine_count;
    const int strength_points=shop.purchases*info.strength_points+(complete?std::max(0,static_cast<int>(result.strength_points)-static_cast<int>(info.combine_count)*info.strength_points):0);
    const int health_points=shop.purchases*info.health_points+(complete?std::max(0,static_cast<int>(result.health_points)-static_cast<int>(info.combine_count)*info.health_points):0);
    const float health=health_points*design.health_growth;
    const float strength=strength_points*design.strength_growth+(cambc::self().champion_name()==cambc::champion_type::ryth?.01f*health:0);
    after.hp=after.max_hp=before.max_hp+health;after.damage*=1+strength/std::max(1.f,o.strength);
    if(complete&&result.passive) {
        using P=cambc::item_passive;const auto magnitude=result.passive_magnitude;
        switch(*result.passive) {
        case P::monster:after.damage*=1+magnitude;break;
        case P::jungle:case P::durability:after.incoming_factor*=1-magnitude;break;
        case P::treasure:after.gold_multiplier+=magnitude;break;
        case P::prospector:after.prospector=true;break;
        case P::capture:after.capture_rounds=3;break;
        default:break;
        }
    }
    float value=0;unsigned checked=0;const auto started=fuel_left();
    const float baseline=m.economic_gem_rate+objective::gold_price(horizon)*m.economic_gold_rate;
    for(unsigned g=0;g<w.groups.size()&&checked<4;++g) {
        if(!tc.allow(11000)||started-fuel_left()>5000)break;
        const auto& group=w.groups[g];
        if(!group.field||group.strength<=0||group.tiles.empty()||group.tiles.size()>8||!m.groups[g].available(tc.round))continue;
        ++checked;
        int home=0,delivery=65535;
        for(auto p:group.tiles)home=std::max(home,static_cast<int>(w.home.get(p)));
        for(unsigned a=0;a<w.altars.size();++a) {
            int distance=0;for(auto p:group.tiles)distance=std::max(distance,w.altar_distance(a,p));
            delivery=std::min(delivery,distance);
        }
        if(home>=65535||delivery>=65535)continue;
        before.arrival=after.arrival=home;
        std::array<ClearMember,clear_risk_members> members{};std::array<unsigned,clear_risk_members> counts{};
        auto e=encounter(w,m,g,members,counts,tc.round,horizon);
        const auto old=objective::forecast(e,std::span<const objective::Actor>(&before,1),0);
        if(old.complete()&&old.survivable)continue; // Generic utility already prices speed/health on existing work.
        const auto improved=objective::forecast(e,std::span<const objective::Actor>(&after,1),0);
        if(!improved.complete()||!improved.survivable)continue;
        const auto bank=tribute_delay(static_cast<int>(improved.gems),cambc::constants::submit_gem_base_duration,
            cambc::constants::submit_gem_minimum_duration,cambc::constants::submit_gem_duration_multiplier,0);
        if(!bank.supported())continue;
        const int cycle=std::max(improved.finish+2*delivery+bank.rounds,group.sdk.max_respawn_timer()+improved.clear+improved.capture);
        const float rate=improved.reward(objective::gold_price(horizon))/std::max(1,cycle)/(1+m.pressure(group.center,6+group.radius,tc.round));
        value=std::max(value,std::max(0.f,rate-baseline)*std::max(0,horizon-improved.finish-delivery-bank.rounds));
    }
    return value; // Conditional access/unlock estimate, not certified future ownership.
}
void refresh_shop_quote(const StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc,int remaining) {
    if(o.gold<static_cast<int>(cambc::item_type::monster_shard_of_strength.cost())||!o.enemies.empty()||!tc.allow(20000))return;
    if(m.shop_quote_gold==o.gold&&m.shop_quote_income==m.economic_gem_rate&&m.shop_quote_gold_income==m.economic_gold_rate&&
        static_cast<int>(tc.round)-m.shop_quote_round<16)return;
    const int home=w.home.get(o.p);if(home>=65535)return;
    // Scheduled before objective/circuit search; their bounded work must not
    // make the gear alternative permanently disappear from the action set.
    const int visit=2*home+1;
    auto quote=shop_visit(tc,o,std::max(0,remaining-visit),m.economic_gem_rate,m.economic_gold_rate);
    quote.value=std::max(quote.value,upgraded_job_value(quote,w,m,o,tc,std::max(0,remaining-visit)));
    m.shop_quote=quote;m.shop_quote_gold=o.gold;m.shop_quote_round=tc.round;
    m.shop_quote_income=m.economic_gem_rate;m.shop_quote_gold_income=m.economic_gold_rate;
#if DZ_TRACE
    {TraceScope scope;trace("DZ_SHOP_QUOTE round=%u body=%u valid=%d searched=%u value=%.2f cost=%d gold=%d income=%.3f gold_income=%.3f fuel=%llu\n",tc.round,
        static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),quote.valid,quote.searched,quote.value,quote.cost,o.gold,
        m.economic_gem_rate,m.economic_gold_rate,static_cast<unsigned long long>(fuel_left()));}
#endif
}
std::optional<Goal> resume_trip(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc,int altar) {
    auto& route=m.delivery_trip;if(!route.active())return std::nullopt;
    // Access/topology changes invalidate the static delivery quote; gates and
    // emergency recovery can then take ownership through their existing paths.
    if(altar!=route.plan.altar){route={};return std::nullopt;}
    for(unsigned skipped=0;skipped<=trip::max_jobs&&route.active();++skipped) {
        const int g=route.job();
        if(g<0) {
            route.advance(tc.round,o.bag,false,true,w.home.get(o.p)==0);
            if(route.phase==trip::Phase::Deliver) {m.contract.objective=-1;m.economic_crew=0;return Goal{GoalKind::Bank,altar};}
            if(route.phase==trip::Phase::Shop) {
                // The counterfactual future visit is an executable itinerary,
                // not a promise that can be pushed back by every new capture.
                auto quote=m.delivery_shop;quote.round=tc.round;commit_shop_visit(quote);
#if DZ_TRACE
                if(tc.round%10==0){TraceScope scope;trace("DZ_TRIP_HOME round=%u body=%u item=%u purchases=%u\n",tc.round,
                    static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),static_cast<unsigned>(quote.item),quote.purchases);}
#endif
                m.contract.objective=-1;m.economic_crew=0;return Goal{GoalKind::Home};
            }
            break;
        }
        if(g>=static_cast<int>(m.groups.size())){route={};break;}
        const auto& b=m.groups[g];
        const bool converted=m.conversions[g]>static_cast<unsigned>(route.generations[route.next]);
        const bool waiting=!converted&&b.state==GroupState::Respawning;
        const bool available=(b.available(tc.round)||waiting)&&!reserved_job(w,m,o,g,tc);
        const int distance=w.distance(g,o.p);
        if(!waiting&&route.waiting) {m.contract.start(g,tc.round,distance,b.hp,b.capture,config::contract_window);route.waiting=false;}
        const bool stalled=!waiting&&m.contract.objective==g&&!m.contract.progressing(tc.round,distance,b.hp,b.capture);
        const unsigned old=route.next;route.advance(tc.round,o.bag,converted,available&&!stalled&&distance<65535);
        if(old!=route.next)route.refresh_repeat(g,m.conversions[g]);
#if DZ_TRACE
        if(old!=route.next||route.phase!=trip::Phase::Work) {TraceScope scope;trace("DZ_TRIP_STEP round=%u body=%u group=%d next=%u phase=%d bag=%d converted=%d available=%d\n",tc.round,
            static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,route.next,static_cast<int>(route.phase),o.bag,converted,available&&!stalled);}
#endif
        if(!route.active()){m.contract.objective=-1;break;}
        if(route.phase==trip::Phase::Deliver) {m.contract.objective=-1;m.economic_crew=0;return Goal{GoalKind::Bank,altar};}
        if(old!=route.next){m.contract.objective=-1;continue;}
        if(waiting) {
            // A planned cooldown is productive waiting, not stalled work. Free
            // every spawn tile before waiting so the next generation can exist.
            m.contract.objective=g;m.contract.checked=tc.round;
            route.waiting=true;
            m.economic_crew=1u<<w.slot;m.economic_capturer=w.slot;
            return Goal{w.group_at(o.p)==g?GoalKind::YieldSpawn:GoalKind::Farm,g};
        }
        if(m.contract.objective!=g)m.contract.start(g,tc.round,distance,b.hp,b.capture,config::contract_window);
        m.economic_crew=1u<<w.slot;m.economic_capturer=w.slot;
        return Goal{GoalKind::Farm,g};
    }
    return std::nullopt;
}
template<class BankTime>
trip::Plan collection_trip(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc,
                           const macro::Context& context,int first,int altar,const objective::Quote& initial,BankTime bank_time) {
    trip::Network graph;
    for(auto& row:graph.travel)row.fill(trip::unreachable);
    if(first<0||altar<0||!w.groups[first].field||w.groups[first].tiles.empty()||w.groups[first].tiles.size()>8||
        std::popcount(m.economic_crew)>1||!initial.complete()||!initial.survivable||!tc.allow(19000))return {};
    auto actor=economic_actor({cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range});
    graph.loss_budget=std::max(0.f,o.hp-.15f*o.max_hp);
    auto add=[&](int g,const objective::Quote& q) {
        const auto& group=w.groups[g];const unsigned i=graph.count++;
        graph.nodes[i]={g,q.clear+q.capture,std::max(0,m.groups[g].ready-static_cast<int>(tc.round)),q.gems,q.gold_low,
            1-1/(1+m.pressure(group.center,6+group.radius,tc.round))};
        auto& node=graph.nodes[i];node.loss=1.25f*q.loss_upper[0];
        graph.arrival[i]=q.arrival;graph.delivery[i]=0;
        // Worst static exit over all supported capture tiles, not one arbitrarily
        // chosen favourable corner. Dynamic camps/actors remain executor checks.
        for(auto p:group.tiles)graph.delivery[i]=std::max(graph.delivery[i],w.altar_distance(altar,p));
        if(tc.allow(14000)) {
            std::array<ClearMember,clear_risk_members> members{};std::array<unsigned,clear_risk_members> counts{};
            auto full=encounter(w,m,g,members,counts,tc.round,context.horizon,true);
            auto fresh=actor;fresh.arrival=0;
            const auto repeat=self_quote(full,fresh,tc,true);
            if(repeat.complete()&&repeat.survivable&&group.sdk.max_respawn_timer()>0) {
                node.renewal=group.sdk.max_respawn_timer();node.repeat_work=repeat.clear+repeat.capture;
                node.repeat_loss=1.25f*repeat.loss_upper[0];
                graph.travel[i][i]=2; // Step off the captured spawn, then re-enter after renewal.
            }
        }
    };
    add(first,initial);
    const auto started=fuel_left();
    // Harmless resources may be approached during their observed cooldown.
    // Other combat jobs need joint geometry/HP progression before chaining.
    std::array<int,trip::max_nodes-1> shortlist{};std::array<float,trip::max_nodes-1> rates{};unsigned found=0;
    for(unsigned g=0;g<w.groups.size();++g) {
        if(!tc.allow(16000)||started-fuel_left()>5500)break;
        const auto& group=w.groups[g];const auto& b=m.groups[g];
        if(static_cast<int>(g)==first||group.strength>0||!group.field||group.tiles.empty()||group.tiles.size()>8||
            (!b.available(tc.round)&&b.state!=GroupState::Respawning)||reserved_job(w,m,o,g,tc))continue;
        const int d=w.distance(g,w.groups[first].tiles.front());if(d>=65535)continue;
        const float rate=(group.reward_gems+context.gold_price*group.reward_gold)/(std::max(d,b.ready-static_cast<int>(tc.round))+6.f);
        unsigned at=0;while(at<found&&rates[at]>=rate)++at;
        if(at==shortlist.size())continue;
        found=std::min<unsigned>(found+1,shortlist.size());
        for(unsigned k=found-1;k>at;--k){shortlist[k]=shortlist[k-1];rates[k]=rates[k-1];}
        shortlist[at]=g;rates[at]=rate;
    }
    for(unsigned k=0;k<found&&tc.allow(15000)&&started-fuel_left()<8500;++k) {
        const int g=shortlist[k];std::array<ClearMember,clear_risk_members> members{};std::array<unsigned,clear_risk_members> counts{};
        auto e=encounter(w,m,g,members,counts,tc.round,context.horizon);actor.arrival=0;
        const auto q=self_quote(e,actor,tc);
        if(q.complete()&&q.survivable)add(g,q);
    }
    const auto matrix_start=fuel_left();
    for(unsigned i=0;i<graph.count;++i)for(unsigned j=0;j<graph.count;++j)if(i!=j) {
        int distance=0;
        for(auto p:w.groups[graph.nodes[i].id].tiles) {
            if(!tc.allow(10000)||matrix_start-fuel_left()>5000){distance=trip::unreachable;break;}
            distance=std::max(distance,w.distance(graph.nodes[j].id,p));
        }
        graph.travel[i][j]=distance;
    }
    return trip::best(context,graph,0,altar,bank_time,[&]{return tc.allow(10000);});
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
        m.contract.objective=-1;m.leave_crew();m.delivery_trip={};
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
    if(auto retained=resume_trip(w,m,o,tc,altar))return *retained;
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
    trip::Plan circuit;
    ShopVisit circuit_shop;
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
        const auto q=n==1?self_quote(e,actors[0],tc):objective::forecast(e,std::span<const objective::Actor>(actors.data(),n),cap);
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
            if(altar>=0&&!commitment.active()) {
                circuit=collection_trip(w,m,o,tc,context,g,altar,q,[&](float bag){return bank_time(static_cast<int>(std::ceil(bag)));});
                DZ_PROF('V');
                if(circuit.count)choices[0]=circuit.option;
            }
        } else if(roster&&q.quality==objective::Quality::BeyondHorizon&&direct_bank<=remaining)
            return relinquish({GoalKind::Bank,altar});
        // A missing crew view / incomplete quote retains the contract. It does
        // not invent zero work and induce a spurious bank/shop interruption.
    }
    const float local_loss=enemy_danger(o.p,o);
    if(circuit.count&&o.enemies.empty()&&m.shop_quote.valid&&m.shop_quote_gold==o.gold) {
        const int from_bank=w.home.get(w.altars[altar].tile);
        if(from_bank<65535&&circuit.finish+2*from_bank+1<remaining) {
            // Compare bank->continue with bank->home/shop->return to the same
            // continuation position. Cash spent is an explicit opportunity cost.
            auto quote=m.shop_quote;
            quote.value*=std::clamp((remaining-circuit.finish-from_bank-1)/static_cast<float>(std::max(1,quote.horizon)),0.f,1.f);
            auto upgraded=choices[0];upgraded.delivery+=2*from_bank+1;
            const float net=quote.value-context.gold_price*quote.cost;
            if(quote.valid&&net>0) {
                upgraded.equipment=net;
                if(macro::value(context,upgraded)>macro::value(context,choices[0])) {
                    circuit_shop=quote;circuit.shop=true;circuit.option=upgraded;
                    circuit.finish=upgraded.work+upgraded.delivery;choices[0]=upgraded;
                }
            }
        }
    }
    if(direct_bank<=remaining)choices[1]={macro::Kind::Bank,altar,direct_bank,0,0,0,0,
        std::min(1.f,local_loss*direct_bank/std::max(1.f,o.hp))*o.bag,true};
    if(home<65535&&o.enemies.empty()&&m.shop_quote.valid&&o.gold>=static_cast<int>(cambc::item_type::monster_shard_of_strength.cost())) {
        const int recall=std::max(1,static_cast<int>(std::ceil(cambc::constants::recall_time*(1-reduction(cambc::item_family::home)))));
        const int outward=home>recall&&channel_safe(w,o,tc)?recall:home;
        const int visit=opening?outward+1:outward+home+1;
        if(m.shop_quote.valid&&m.shop_quote_gold==o.gold&&visit<=remaining) {
            // A cached value cannot retain more horizon than its original quote.
            const float age_scale=std::clamp((remaining-visit)/static_cast<float>(std::max(1,m.shop_quote.horizon)),0.f,1.f);
            const int after=altar>=0?altar_distance+bank_time(std::max(1,o.bag)):
                opening&&opening->quality==gate::Quality::Ready?opening_work+opening->delivery+bank_time(std::max(1,o.bag)):-1;
            // Both paths now price their actual inventory at its actual arrival:
            // choices[0] includes a deferred batch only when its home visit is
            // queued. Comparing the two full schedules yields the advance value
            // without repeatedly inventing an unexecuted future purchase.
            const float net=std::max(0.f,m.shop_quote.value*age_scale-context.gold_price*m.shop_quote.cost);
            choices[2]={macro::Kind::Shop,-1,visit,o.bag>0?after:(altar>=0?0:after),0,0,net,0,true};
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
    if(selected==0&&circuit.count) {
        m.delivery_trip.start(circuit,tc.round,o.bag,2*config::contract_window);
        m.delivery_shop=circuit_shop;
        for(unsigned i=0;i<circuit.count;++i)m.delivery_trip.generations[i]=m.conversions[circuit.jobs[i]]+circuit.ordinals[i];
#if DZ_TRACE
        {TraceScope scope;trace("DZ_TRIP round=%u body=%u jobs=%u first=%d second=%d third=%d altar=%d finish=%d deadline=%d\n",tc.round,
            static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),circuit.count,circuit.jobs[0],circuit.jobs[1],circuit.jobs[2],
            circuit.altar,circuit.finish,m.delivery_trip.deadline);}
#endif
    }
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
bool crew_ready(const StaticWorld& w,Memory& m,const Observation& o,int g,const TurnContext& tc) {
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
    if(std::popcount(present)==1&&tc.allow(14000)) {
        std::array<ClearMember,clear_risk_members> members{};std::array<unsigned,clear_risk_members> counts{};
        const auto e=encounter(w,m,g,members,counts,tc.round,cambc::constants::max_rounds-tc.round);
        const objective::Actor tank{o.hp,o.max_hp,damage,o.camp_factor};
        const auto q=self_quote(e,tank,tc);
        if(q.cast_policy&&q.complete()&&q.survivable) {
#if DZ_TRACE
            {TraceScope scope;trace("DZ_CAST_WAKE round=%u body=%u group=%d clear=%d loss=%.1f shield=%.1f\n",tc.round,
                static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),g,q.clear,q.loss_upper[0],q.opening_shield);}
#endif
            m.cast_admission={static_cast<int>(tc.round),g,q.opening_shield};return true;
        }
    }
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
    auto& crew=m.crew_execution;
    if(crew.recovering&&incoming_lease.valid&&incoming_lease.leader!=w.slot&&
        (((incoming_lease.members&(1u<<w.slot))&&(incoming_lease.members!=m.economic_crew||incoming_lease.objective!=crew.group))||
         (incoming_lease.objective==crew.group&&!(incoming_lease.members&(1u<<w.slot))))) {
        // A new exact-round assignment replaces the old recovery project.
        // Otherwise one champion could promise two different crews at once.
        m.contract.objective=-1;m.leave_crew();
    }
    m.race.observe(tc.round,o.submitted,cambc::global_submitted_gems(cambc::team::enemy));
    float bags=o.bag;for(const auto& a:o.allies)bags+=a.sdk.gem_count();
    const int remaining=m.race.remaining(tc.round,cambc::constants::max_rounds,cambc::constants::winning_gems,bags);
    const float gold_price=objective::gold_price(remaining);
    if(crew.recovering&&crew.group>=0&&crew.group<static_cast<int>(m.groups.size())&&std::popcount(m.economic_crew)>1) {
        if(o.bag>0&&altar>=0&&altar_distance<65535) {
            const auto bank=tribute_delay(o.bag,cambc::constants::submit_gem_base_duration,cambc::constants::submit_gem_minimum_duration,
                cambc::constants::submit_gem_duration_multiplier,0);
            if(bank_now(o.bag,altar_distance,o.submitted,cambc::constants::winning_gems)||
                (bank.supported()&&altar_distance+bank.rounds<=remaining&&remaining-altar_distance-bank.rounds<=config::contract_window)) {
                m.contract.objective=-1;m.leave_crew();m.delivery_trip={};return Goal{GoalKind::Bank,altar};
            }
        }
        if(static_cast<int>(tc.round)<=crew.recovery_deadline&&m.groups[crew.group].available(tc.round)) {
            const int distance=w.distance(crew.group,o.p);
            m.contract.start(crew.group,tc.round,distance,m.groups[crew.group].hp,m.groups[crew.group].capture,config::crew_window);
            return Goal{GoalKind::Farm,crew.group};
        }
        m.contract.objective=-1;m.leave_crew();
    }
    if(m.delivery_trip.active()&&incoming_lease.valid&&incoming_lease.leader!=w.slot&&(incoming_lease.members&(1u<<w.slot)))
        m.delivery_trip={}; // A fresh coordinated crew can reassign a solo circuit.
    if(m.delivery_trip.active())return macro_goal(w,m,o,tc,{GoalKind::Home},altar,altar_distance,remaining);
    refresh_shop_quote(w,m,o,tc,remaining);
    const auto& geometry=m.crew_layout;
    const bool priced_crew=geometry.group>=0&&geometry.group<static_cast<int>(m.groups.size())&&
        geometry.search.stage==crew::SequenceSearch::Stage::Done&&m.groups[geometry.group].available(tc.round)&&
        geometry.topology==m.topology_revision-m.group_topology[geometry.group]&&geometry.generation==m.conversions[geometry.group];
    if(m.legacy(tc.round)&&altar>=0&&(m.contract.objective<0||std::popcount(m.economic_crew)<2)&&
        !(incoming_lease.valid&&(incoming_lease.members&(1u<<w.slot)))) {
        if(!priced_crew)return std::nullopt;
        // Legacy navigation is still the fallback. A completed coordinated
        // alternative gets an auction instead of waiting out a 300-turn latch.
        if(std::popcount(m.economic_crew)<2&&static_cast<int>(tc.round)-m.last_work>config::crew_window) {
            m.contract.objective=-1;m.leave_crew();
        }
    }
    m.access_group=-1;m.access_member=-1;
    if(altar<0&&o.enemies.empty())quote_opening(w,m,o,tc);
    if(m.shopping_since>=0||o.hp<.3f*o.max_hp)
        return macro_goal(w,m,o,tc,{GoalKind::Home},altar,altar_distance,remaining);
    const int occupied=w.group_at(o.p);
    if(occupied>=0&&m.groups[occupied].state==GroupState::Respawning) {
        m.contract.objective=-1;m.leave_crew();return Goal{GoalKind::YieldSpawn};
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
        if(m.crew_execution.group==current&&std::popcount(m.economic_crew)>1)
            m.contract.checked=std::max(m.contract.checked,m.crew_execution.last_progress);
        const bool helper_done=b.state==GroupState::Reward&&m.economic_capturer!=w.slot;
        const bool timed_out=std::popcount(m.economic_crew)>1&&static_cast<int>(tc.round)>m.rendezvous_until&&
            b.state!=GroupState::Partial&&b.state!=GroupState::Reward;
        if(!helper_done&&!timed_out&&b.available(tc.round)&&
            m.contract.progressing(tc.round,distance,b.hp,b.capture)) return macro_goal(w,m,o,tc,{GoalKind::Farm,current},altar,altar_distance,remaining);
        if(helper_done||!b.available(tc.round)){m.contract.objective=-1;m.leave_crew();}
        else m.release(tc.round);
    }
    if(static_cast<int>(tc.round)<m.economic_retry_after||!tc.allow(28000))
        return macro_goal(w,m,o,tc,{GoalKind::Home},altar,altar_distance,remaining);
    const auto start=fuel_left();
#if DZ_TRACE
    static unsigned next_auction_trace=0;
    const bool trace_auction=w.slot==0&&tc.round>=next_auction_trace;
    if(trace_auction)next_auction_trace=tc.round+50;
#endif
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
        if(!economy::available_for_offer(claim.objective,ally.hp>=ally.max_hp-.01f&&w.home.get(ally.p)==0))continue;
        // Gold is self-only in the SDK; shopping intent comes from the visible
        // body's claim. Visible carried bags are legal to read.
        if(ally.sdk.gem_count()>=config::bank_bag)continue;
        if(protocol::is_group_code(claim.objective)&&claim.objective<w.groups.size()&&
            w.distance(claim.objective,ally.p)<=std::max(1,ally.range)+1&&
            (m.groups[claim.objective].state==GroupState::Partial||m.groups[claim.objective].state==GroupState::Reward||
             m.groups[claim.objective].state==GroupState::Respawning))
            reserved[slot]=claim.objective;
        // Reserve exact inventory decoding for the executable crew controller.
        // Visible basic strength/HP with no armour or Monster credit is a legal
        // conservative bid. Decoding every ally's inventory here exhausted the
        // first-quote budget on five-body maps and produced no bids at all.
        objective::Actor observed{ally.hp,ally.max_hp,ally.strength};
        if(ally.sdk.champion_name()==cambc::champion_type::vesper_vale)observed.gold_multiplier=1.33f;
        team[n++]={observed,ally.p,slot,ally.range,static_cast<unsigned>(static_cast<cambc::handle_champion_t>(ally.sdk))};
        if(reserved[slot]<0)available|=1u<<slot;
    }
    DZ_PROF('T');
    struct Candidate { int g;float bound; };
    std::vector<Candidate> candidates;candidates.reserve(w.groups.size());
    int cold_resource=-1;float cold_rate=0;
    for(unsigned g=0;g<w.groups.size();++g) {
        auto& b=m.groups[g];auto& group=w.groups[g];
        if(lease.valid&&lease.objective==static_cast<int>(g)&&!(lease.members&(1u<<w.slot)))continue;
        // A visible worker's progressing task is fixed. In particular a live
        // gate worker cannot be sold into a crew whose role controller it never
        // joined. The existing exact-round invitation path handles consent.
        if(std::find(reserved.begin(),reserved.end(),static_cast<int>(g))!=reserved.end())continue;
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
    if(m.crew_layout.search.pending()&&m.crew_layout.expires>static_cast<int>(tc.round)) {
        const auto pending=std::find_if(candidates.begin(),candidates.end(),[&](auto c){return c.g==m.crew_layout.group;});
        if(pending!=candidates.end())std::rotate(candidates.begin(),pending,pending+1);
    }
    DZ_PROF('C');
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
        // Price a real owned crew before all allied solo counterfactuals.
        // Otherwise their SDK/model work can exhaust the entire budget before
        // the crew alternative is ever admitted to the auction.
        if(group.strength>0&&m.groups[g].state!=GroupState::Reward&&n>=2&&(eligible&1u)) {
        // Nearby crew subsets, up to six actors. Each gets real damage and its
        // own incoming mitigation, not the caller's stats multiplied by count.
        std::array<unsigned,objective::max_crew> order{};for(unsigned a=0;a<n;++a)order[a]=a;
        std::sort(order.begin(),order.begin()+n,[&](auto a,auto b){
            if(a==0||b==0)return a==0&&b!=0;
            return arrival[a]<arrival[b]||(arrival[a]==arrival[b]&&team[a].slot<team[b].slot);
        });
        std::array<objective::Actor,objective::max_crew> crew_actors{};
        std::array<crew::Unit,objective::max_crew> spatial{};
        std::array<unsigned,objective::max_crew> crew_slots{};unsigned count=0;
        unsigned eligible_count=0;
        for(unsigned a=0;a<n;++a)if((eligible&(1u<<a))&&team[a].slot>=w.slot)++eligible_count;
        const unsigned trial=m.crew_layout.group==g&&m.crew_layout.search.pending()?m.crew_layout.units:m.coalition_cursor[g];
        const unsigned first_trial=std::clamp(trial,2u,std::max(2u,eligible_count));
        for(unsigned k=0;k<n;++k) {
            if(!tc.allow(18000+200*e.members.size())||start-fuel_left()>18000)break;
            const auto a=order[k];if(!(eligible&(1u<<a))||team[a].slot<w.slot)continue;
            crew_slots[count]=team[a].slot;crew_actors[count]=actors[a];
            spatial[count]={team[a].slot,team[a].handle,{team[a].p.x,team[a].p.y},actors[a].hp,actors[a].max_hp,actors[a].damage,
                actors[a].incoming_factor,team[a].range,actors[a].arrival};
            ++count;
            if(count<first_trial)continue;
            if(spatial_quotes>=2)break;
            ++spatial_quotes;
            const auto quote=crew_quote(w,m,g,std::span<const crew::Unit>(spatial.data(),count),cambc::constants::capture_time+1,tc);
#if DZ_TRACE
            if(trace_auction){TraceScope scope;trace("DZ_CREW_BID round=%u group=%d units=%u result=%d fuel=%llu\n",tc.round,g,count,static_cast<int>(quote.status),static_cast<unsigned long long>(fuel_left()));}
#endif
            if(quote.status==CrewQuoteStatus::Budget)break;
            m.coalition_cursor[g]=economy::next_coalition_size(count,eligible_count);
            if(!quote.complete||!(quote.members&(1u<<w.slot)))continue;
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
        for(unsigned a=0;a<n;++a)if(eligible&(1u<<a)) {
            if(!tc.allow(18000+200*e.members.size())||start-fuel_left()>18000)break;
            if(active_capturer>=0&&a!=static_cast<unsigned>(active_capturer))continue;
            auto solo_encounter=e;
            if(active_capturer==static_cast<int>(a)&&m.groups[g].capture_phase==static_cast<int>(cambc::map::camp_group_capture_type::ally_capturing))
                solo_encounter.capture_remaining=m.groups[g].capture;
            if(m.groups[g].capture_phase==static_cast<int>(cambc::map::camp_group_capture_type::contested)||
                m.groups[g].capture_phase==static_cast<int>(cambc::map::camp_group_capture_type::enemy_capturing))solo_encounter.contested=true;
            auto quote=team[a].slot==w.slot?self_quote(solo_encounter,actors[a],tc):
                objective::forecast(solo_encounter,std::span<const objective::Actor>(&actors[a],1),0);
            if(!quote.complete()||!quote.survivable)continue;
            const float rate=contested*quote.reward(gold_price)/std::max(1,quote.finish);
            alternatives[team[a].slot]=std::max(alternatives[team[a].slot],rate);
            if(team[a].slot==w.slot&&rate>continuation_rate) {
                continuation_rate=rate;
                // Continuation needs delivery, return travel and replenishment;
                // a camp's clear-only rate cannot run forever without those costs.
                int delivery=65535;
                if(altar>=0&&!group.tiles.empty())delivery=w.altar_distance(altar,group.tiles.front());
                const auto bank=tribute_delay(static_cast<int>(quote.gems),cambc::constants::submit_gem_base_duration,
                    cambc::constants::submit_gem_minimum_duration,cambc::constants::submit_gem_duration_multiplier,0);
                const int cycle=delivery<65535&&bank.supported()?std::max(quote.finish+2*delivery+bank.rounds,
                    group.sdk.max_respawn_timer()+quote.clear+quote.capture):std::max(quote.finish,group.sdk.max_respawn_timer()+quote.clear+quote.capture);
                gem_rate=delivery<65535?contested*quote.gems/std::max(1,cycle):0;
                gold_rate=contested*quote.gold_low/std::max(1,cycle);
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

    }
    m.economic_gem_rate=gem_rate;m.economic_gold_rate=gold_rate;
    DZ_PROF('B');
    const auto allocation_start=fuel_left();
    const auto assignments=economy::allocate(bids,available,[&]{return tc.allow(10000)&&allocation_start-fuel_left()<6000;});
    const auto chosen=assignments[w.slot];
    DZ_PROF('U');
#if DZ_TRACE
    if(trace_auction){TraceScope scope;trace("DZ_AUCTION round=%u units=%u bids=%zu chosen=%d crew=%u fuel=%llu\n",tc.round,n,bids.size(),chosen.objective,chosen.crew,static_cast<unsigned long long>(fuel_left()));}
#endif
    if(chosen.objective<0){
        m.leave_crew();
        if(cold_resource>=0)m.field_needed=cold_resource;
        m.economic_retry_after=tc.round+(cold_resource>=0?1:8);
        if(m.legacy(tc.round))return std::nullopt;
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
