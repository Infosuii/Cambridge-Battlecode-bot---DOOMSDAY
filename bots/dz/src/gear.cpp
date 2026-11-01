#include "gear.h"
#if DZ_ECONOMY_V2
#include "gear_value.h"
#endif
#if DZ_JOB_GEAR
#include "basic_clear.h"
#include <optional>
#endif

namespace dz {
namespace {
using F = cambc::item_family;
using S = cambc::item_stat;
struct Step { F family; S stat; };
struct Build { std::array<Step,3> emblems; S power; };
// Per-champion openers from the elite purchase ledger (ELITE_META_RESEARCH,
// 30 top-team games, 2026-10-29): Treasure- or Jungle-led development, then
// the champion's main stat. Variant B keeps Monster in the first three for
// damage dealers: Treasure-first without it slowed clears against idle
// (dz-gear-idle-01). Our clear model prices basic attacks, so Strength.
Build build_for(cambc::champion_type type) {
    using T = cambc::champion_type;
#if DZ_HAS(GEAR_HEALTH)
    if (DZ_ON(GEAR_HEALTH)) {
    // Z9 v1 variant: contested deaths are lost even trades against higher max HP (00ambush R206-221 replay).
    return {{{{F::jungle,S::health},{F::durability,S::health},{F::prospector,S::health}}},S::health};
    }
#endif
#if DZ_HAS(GEAR_SURVIVE)
    // Z9 v1 hypothesis: bigger groups need survivable clears more than early gold.
    if (DZ_ON(GEAR_SURVIVE)) switch (type) {
    case T::heart_of_ruin: case T::ryth: return {{{{F::jungle,S::health},{F::durability,S::health},{F::monster,S::health}}},S::health};
    default: return {{{{F::jungle,S::strength},{F::monster,S::strength},{F::durability,S::health}}},S::strength};
    }
#endif
    switch (type) {
    case T::vesper_vale: return {{{{F::treasure,S::strength},{F::monster,S::strength},{DZ_CAPTURE_GEAR?F::capture:F::jungle,S::strength}}},S::strength};
    case T::marcella: return {{{{F::treasure,S::strength},{F::monster,S::strength},{F::durability,S::health}}},S::strength};
    case T::heart_of_ruin: return {{{{F::jungle,S::health},{F::treasure,S::health},{F::monster,S::health}}},S::health};
    case T::ryth: return {{{{F::treasure,S::health},{F::jungle,S::health},{F::monster,S::health}}},S::health};
    case T::varg: return {{{{F::monster,S::strength},{F::treasure,S::strength},{F::jungle,S::strength}}},S::strength};
    default: return {{{{F::monster,S::strength},{F::treasure,S::strength},{F::jungle,S::strength}}},S::strength};
    }
}
#if DZ_JOB_GEAR
bool cluster_jobs(const StaticWorld& world,const TurnContext& tc,S stat) {
    // A cold-path hypothesis, not calibrated ObjModel: rank full future groups
    // from home with per-member attack rounding. Both best jobs must be pure
    // clusters before changing a Treasure opener. No fitted map names/rows.
    const auto stats=cambc::self().base_stats();
    const float damage=stats.base_strength+(stat==S::strength?5*stats.strength_growth:0);
    struct Job { float rate=-1;bool cluster=false; };
    std::array<Job,2> best{};unsigned found=0;
    const auto started=fuel_left();
    std::array<BasicTarget,256> targets;
    for (const auto& group:world.groups) {
        if (started-fuel_left()>15000||!tc.allow(5000+500*group.tiles.size())||group.tiles.size()>256) return false;
        const int distance=group.home_distance;
        if (!group.home_reachable) continue;
        for (unsigned k=0;k<group.tiles.size();++k) {
            targets[k]={group.initial_hp[k],damage};
        }
        const auto work=basic_attack_work(std::span<const BasicTarget>(targets.data(),group.tiles.size()));
        if (!work.complete()) continue;
        const float value=group.sdk.gem_value()+.1f*group.sdk.gold_value();
        if (value<=0) continue;
        const Job job{value/(distance+work.attacks+cambc::constants::capture_time+1.f),group.cluster};
        ++found;
        if (job.rate>best[0].rate) { best[1]=best[0];best[0]=job; }
        else if(job.rate>best[1].rate) best[1]=job;
    }
    return found>0&&best[0].cluster&&(found==1||best[1].cluster);
}
#endif
}
namespace {
bool buy_build(const TurnContext& tc,Actuator& act,const Build& build) {
    auto& me = cambc::self();
    if (!me.can_buy(cambc::get_item_enum(build.emblems.front().family, build.emblems.front().stat))) return false;
    bool changed = false;
    for (int count = 0; count < 16 && tc.allow(2000); ++count) {
        auto owned = me.item_count();
        auto selected = cambc::get_item_enum(F::power, build.power);
        for (auto step : build.emblems) {
            auto shard = cambc::get_item_enum(step.family, step.stat);
            auto result = shard.result();
            if (!result || owned[*result] == 0) { selected = shard; break; }
        }
#if DZ_CAPTURE_FOURTH
        // Preserve Treasure/Monster/Jungle and their survival/DPS effects.
        // The pinned metadata prices both at five same-stat shards: Capture
        // trades Power's sixth growth point for two capture-timer ticks.
        if(selected==cambc::get_item_enum(F::power,build.power) &&
            me.champion_name()==cambc::champion_type::vesper_vale) {
            const auto capture=cambc::get_item_enum(F::capture,build.power);
            const auto emblem=capture.result();
            if(emblem && !owned[*emblem])selected=capture;
        }
#endif
        if (!me.can_buy(selected) || !act.buy(selected)) break;
        changed = true;
    }
    return changed;
}
}
bool fixed_shop(const TurnContext& tc, Actuator& act) {
    return buy_build(tc,act,build_for(cambc::self().champion_name()));
}
#if DZ_ECONOMY_V2
namespace {
gear::Context purchase_context;
ShopVisit visit_intent;
// Used by both the visit planner and the live shop. SDK item metadata is cached
// by the official wrapper. No different fixed purchasing list hides behind a
// quoted economic visit.
ShopVisit purchase_project(const TurnContext& tc,gear::Context context,float strength,float health) {
    auto& me=cambc::self();const auto design=me.base_stats();const auto owned=me.item_count();const bool ryth=me.champion_name()==cambc::champion_type::ryth;
    const std::array<F,8> families{F::monster,F::jungle,F::durability,F::treasure,F::prospector,F::capture,F::home,F::power};
    const std::array<gear::Passive,8> passives{gear::Passive::Monster,gear::Passive::Jungle,gear::Passive::Durability,
        gear::Passive::Treasure,gear::Passive::Prospector,gear::Passive::Capture,gear::Passive::Home,gear::Passive::Power};
    const std::array<S,3> stats{S::strength,S::health,S::focus};
    gear::Output output;
    const auto& body=cambc::champion_designs[static_cast<unsigned>(me.champion_name())];
    for(const auto& ability:body.abilities())if(ability.info())std::visit([&](const auto& p){
        if(p.max_cooldown<=0)return;
        if constexpr(std::is_same_v<std::decay_t<decltype(p)>,cambc::ability_attack_reset>)output.reset_rate=std::max(output.reset_rate,1.f/p.max_cooldown);
        else if constexpr(requires{p.modifier;}) {
            if((ability.is_damage()||ability.is_cc()||ability.is_aoe_damage())&&p.valid_targets.contains(cambc::ability_target_mask::camps)&&!p.exclusive_with_movement)
                output.focus_rate=std::max(output.focus_rate,p.modifier/p.max_cooldown);
        }
    },*ability.info());
    const float focus=me.state().is_dead()?design.base_focus:me.focus(),base=std::max(1.f,output.rate(strength,focus));
    unsigned unfinished=0;
    for(auto family:families)for(auto stat:stats)unfinished+=owned[cambc::get_item_enum(family,stat)]>0;
    float best=-1,committed=-1;ShopVisit result,finish;
    const auto started=fuel_left();
    static unsigned frontier=0;unsigned examined=0;
    for(unsigned trial=0;trial<stats.size()*families.size();++trial) {
        // Ranking is a bounded search, not an admission proof: a legally
        // affordable evaluated batch remains useful when search is truncated.
        // Resume coverage instead of discarding it and retrying the same prefix
        // forever. No candidate is claimed to be globally optimal.
        if(!tc.allow(6000)||started-fuel_left()>12000)break;
        const unsigned index=(frontier+trial)%(stats.size()*families.size()),f=index/stats.size();
        const auto stat=stats[index%stats.size()];++examined;
        const auto shard=cambc::get_item_enum(families[f],stat);const auto info=shard.info();
        if(!info.result||!info.combine_count||info.cost==0||context.gold<static_cast<int>(info.cost))continue;
        bool passive_owned=false;
        for(auto s:{S::strength,S::focus,S::health})passive_owned|=owned[cambc::get_item_enum(families[f],s,false)]>0;
        if(families[f]!=F::power&&passive_owned)continue;
        if(unfinished>=2&&!owned[shard])continue;
        if(owned[shard]>=info.combine_count)continue;
        gear::Project project;
        project.passive=passives[f];project.magnitude=info.result->passive_magnitude();
        project.cost=info.cost;project.owned=owned[shard];project.shards_left=info.combine_count-owned[shard];
        const float added_strength=info.strength_points*design.strength_growth+(ryth?.01f*info.health_points*design.health_growth:0);
        project.damage_growth=std::max(0.f,output.rate(strength+added_strength,focus+info.focus_points*design.focus_growth)-base)/base;
        project.health_growth=info.health_points*design.health_growth/std::max(1.f,health);
        const auto result_info=info.result->info();
        const float extra_strength=std::max(0,static_cast<int>(result_info.strength_points)-static_cast<int>(info.combine_count)*info.strength_points);
        const float extra_health=std::max(0,static_cast<int>(result_info.health_points)-static_cast<int>(info.combine_count)*info.health_points);
        const float extra_focus=std::max(0,static_cast<int>(result_info.focus_points)-static_cast<int>(info.combine_count)*info.focus_points);
        project.completion_damage=std::max(0.f,output.rate(strength+extra_strength*design.strength_growth+
            (ryth?.01f*extra_health*design.health_growth:0),focus+extra_focus*design.focus_growth)-base)/base;
        project.completion_health=extra_health*design.health_growth/std::max(1.f,health);
        const float utility=gear::utility(context,project);
        const unsigned count=std::min<unsigned>(project.shards_left,context.gold/info.cost);
        ShopVisit quote{shard,count,owned[shard],owned[*info.result],static_cast<int>(count*info.cost),static_cast<int>(tc.round),
            utility*count*info.cost,utility>0&&count>0};
        if(utility>best){best=utility;result=quote;}
        if(owned[shard]>=2&&utility>committed){committed=utility;finish=quote;}
    }
    frontier=(frontier+examined)%(stats.size()*families.size());
    if(committed>=0&&best<1.5f*committed)result=finish;
    result.searched=examined;
    return result;
}
}
ShopVisit shop_visit(const TurnContext& tc,const Observation& o,int horizon,float income,float gold_income) {
    auto context=purchase_context;context.gold=o.gold;context.remaining=std::max(0,horizon);
    // Use the same attainable production stream as macro continuation. Mixing
    // raw capture-rate continuation with realised-income gear values made every
    // necessary home visit look too expensive.
    context.income=std::max(0.f,income);context.gold_income=std::max(0.f,gold_income);
    auto result=purchase_project(tc,context,o.strength,o.max_hp);result.horizon=context.remaining;return result;
}
void commit_shop_visit(const ShopVisit& quote) { visit_intent=quote; }
bool shop_visit_pending(unsigned round) {
    return visit_intent.valid&&visit_intent.purchases&&round<=static_cast<unsigned>(visit_intent.round+80);
}
bool planned_shop(const TurnContext& tc,Actuator& act,const StaticWorld* world) {
    auto& me=cambc::self();
    auto& context=purchase_context;
    static int last_round=-1,last_gold=0,last_bag=0,last_submitted=0;
    static bool was_dead=false,map_read=false;
    const bool dead=me.state().is_dead();const int gold=me.gold_count();
    if(visit_intent.valid&&(tc.round>static_cast<unsigned>(visit_intent.round+80)||gold<static_cast<int>(visit_intent.item.cost())))visit_intent={};
    const int submitted=cambc::global_submitted_gems(cambc::team::ally);
    const int bag=dead?0:static_cast<int>(me.gem_count());
    if(last_round>=0&&static_cast<int>(tc.round)>last_round) {
        const float elapsed=tc.round-last_round;
        context.gold_income=.98f*context.gold_income+.02f*std::max(0,gold-last_gold)/elapsed;
        // Own bags and team banking are not interchangeable progress. Bag loss
        // on bank/death is never counted as negative earning or a new capture.
        context.income=.98f*context.income+.02f*std::max(0,bag-last_bag)/elapsed;
        context.death_rate=.995f*context.death_rate+.005f*(dead&&!was_dead);
    }
    last_round=tc.round;last_gold=gold;last_bag=bag;last_submitted=submitted;was_dead=dead;
    (void)last_submitted;
    context.remaining=std::max(0,static_cast<int>(cambc::constants::max_rounds)-static_cast<int>(tc.round));
    context.gold=gold;context.death_cost=bag+60*std::max(.15f,context.income);
    if(!me.can_buy(cambc::get_item_enum(F::monster,S::strength)))return false;
    if(!map_read&&world&&world->ready) {
        float all=0,clusters=0,damaging=0;
        for(const auto& g:world->groups) {const float v=g.reward_gems+.1f*g.reward_gold;all+=v;clusters+=v*g.cluster;damaging+=v*(g.strength>0);}
        context.cluster_fraction=clusters/std::max(1.f,all);context.camp_pressure=damaging/std::max(1.f,all);
        context.clear_fraction=.25f+.5f*context.camp_pressure;map_read=true;
    }
    if(!dead)context.enemy_pressure=cambc::vision::champions(cambc::team::enemy).empty()?.15f:1.f;
    const auto design=me.base_stats();
    // Dead units can shop, but live-only health/stat queries are unavailable.
    const float strength=dead?design.base_strength:me.strength();
    const float health=dead?design.base_health:me.max_health();
    bool changed=false;
    const auto purchase_start=fuel_left();
    for(unsigned purchase=0;purchase<16&&tc.allow(7000);++purchase) {
        if(purchase_start-fuel_left()>16000)break;
        if(visit_intent.valid&&tc.round>static_cast<unsigned>(visit_intent.round+80))visit_intent={};
        ShopVisit proposal;
        if(visit_intent.valid&&visit_intent.purchases&&tc.round<=static_cast<unsigned>(visit_intent.round+80)) {
            const auto owned=me.item_count();const auto result=visit_intent.item.result();
            if(result&&owned[visit_intent.item]==visit_intent.shards&&owned[*result]==visit_intent.emblems)proposal=visit_intent;
            else visit_intent={}; // Inventory changed: never execute a stale project.
        }
        if(!proposal.valid)proposal=purchase_project(tc,context,dead?strength:me.strength(),dead?health:me.max_health());
        if(!proposal.valid||!me.can_buy(proposal.item)||!act.buy(proposal.item))break;
#if DZ_TRACE
        {TraceScope scope;trace("DZ_SHOP_BUY round=%u body=%u item=%u planned=%d gold=%u\n",tc.round,
            static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),static_cast<unsigned>(proposal.item),
            visit_intent.valid&&proposal.item==visit_intent.item,me.gold_count());}
#endif
        if(visit_intent.valid&&proposal.item==visit_intent.item) {
            --visit_intent.purchases;
            // A purchase can combine its ingredients immediately. Keep the
            // actual post-transaction inventory for batches crossing emblems.
            const auto owned=me.item_count();const auto result=visit_intent.item.result();
            visit_intent.shards=owned[visit_intent.item];
            if(result)visit_intent.emblems=owned[*result];
            if(!visit_intent.purchases)visit_intent={};
        }
        changed=true;context.gold=me.gold_count();last_gold=context.gold;
    }
    return changed;
}
#endif
#if DZ_HAS(GEAR_PROSPECT)
bool map_shop(const TurnContext& tc,Actuator& act,const StaticWorld* world) {
    // Z9 v1 hypothesis: Prospector pays only on cluster rewards, so take it as the
    // third emblem when this map has gem-paying cluster groups. Decided once.
    static int clusters=-1;
    if (clusters<0 && world && world->ready) {
        clusters=0;
        for (const auto& g:world->groups) if (g.cluster && g.sdk.gem_value()>0) { clusters=1; break; }
    }
    auto build=build_for(cambc::self().champion_name());
    if (clusters==1 && DZ_ON(GEAR_PROSPECT)) build.emblems[2]={F::prospector,build.power};
    return buy_build(tc,act,build);
}
#endif
#if DZ_JOB_GEAR
bool job_shop(const TurnContext& tc,Actuator& act,const StaticWorld* world) {
    auto& me=cambc::self();
    auto build=build_for(me.champion_name());
    if (!me.can_buy(cambc::get_item_enum(build.emblems[0].family,build.emblems[0].stat))) return false;
    static std::optional<Build> selected;
    if(!selected) {
        if(build.emblems[0].family==F::treasure) {
            const auto owned=me.item_count();const auto stat=build.emblems[0].stat;
            const auto treasure=cambc::get_item_enum(F::treasure,stat);
            const auto prospector=cambc::get_item_enum(F::prospector,stat);
            const bool started_treasure=owned[treasure]||owned[*treasure.result()];
            const bool started_prospector=owned[prospector]||owned[*prospector.result()];
            if(!started_treasure&&(started_prospector||(world&&world->ready&&cluster_jobs(*world,tc,stat))))
                build.emblems[0].family=F::prospector;
        }
        tc.guard();selected=build; // Keep a partial purchase plan through visits.
#if DZ_TRACE
        {TraceScope scope;trace("DZ_JOB_GEAR selected_first_family=%d world_ready=%d\n",static_cast<int>(selected->emblems[0].family),world&&world->ready);}
#endif
    }
#if DZ_TRACE
    {TraceScope scope;if(tc.round%100==0)trace("DZ_JOB_GEAR round=%u slot_family=%d\n",tc.round,static_cast<int>(selected->emblems[0].family));}
#endif
    return buy_build(tc,act,*selected);
}
#endif
}
