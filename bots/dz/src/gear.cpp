#include "gear.h"
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
#if DZ_GEAR_HEALTH
    // Z9 v1 variant: contested deaths are lost even trades against higher max HP (00ambush R206-221 replay).
    (void)type;
    return {{{{F::jungle,S::health},{F::durability,S::health},{F::prospector,S::health}}},S::health};
#endif
#if DZ_GEAR_SURVIVE
    // Z9 v1 hypothesis: bigger groups need survivable clears more than early gold.
    switch (type) {
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
#if DZ_GEAR_PROSPECT
bool map_shop(const TurnContext& tc,Actuator& act,const StaticWorld* world) {
    // Z9 v1 hypothesis: Prospector pays only on cluster rewards, so take it as the
    // third emblem when this map has gem-paying cluster groups. Decided once.
    static int clusters=-1;
    if (clusters<0 && world && world->ready) {
        clusters=0;
        for (const auto& g:world->groups) if (g.cluster && g.sdk.gem_value()>0) { clusters=1; break; }
    }
    auto build=build_for(cambc::self().champion_name());
    if (clusters==1) build.emblems[2]={F::prospector,build.power};
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
