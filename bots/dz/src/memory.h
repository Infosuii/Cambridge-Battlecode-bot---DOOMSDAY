#pragma once
#include "observation.h"
#include "clear_risk.h"
#if DZ_SIEGE || DZ_ECONOMY_V2
#include "siege_model.h"
#endif
#if DZ_ECONOMY_V2
#include "race.h"
#endif

namespace dz {
struct Memory {
    std::vector<GroupBelief> groups;
    std::vector<std::vector<float>> member_hp;
    Contract contract;
    int field_needed=-1; // Deferred cold goal field, built before next planner work.
    std::size_t cursor = 0;
    // Memoized clear risk per group and per damage key. Member HP and own
    // damage rarely change between turns; recomputing every group each turn
    // cost 50-68k fuel. Keyed by remembered HP sum and both multipliers.
    std::vector<unsigned> hp_version; // Bumped only when remembered member HP changes.
    struct RiskEntry { unsigned version=~0u; float damage=-1, factor=-1; ClearRisk risk; };
    mutable std::vector<std::array<RiskEntry,2>> risk_cache;
    mutable float quantize_raw=-1, quantize_out=0; // Last damage quantization (libm is costly).
    int idle_until = 0;
    // Starvation fallback: no team income for a while reverts this champion
    // to the plain nearest-group policy (no feasibility/crew gates) for a spell.
    int last_income = 0, last_bag = 0, last_submitted = 0, legacy_until = 0;
    int last_gold=0;
#if DZ_SIEGE || DZ_ECONOMY_V2
    siege::Task siege_task;
    std::array<std::pair<int,int>,8> route_gates{};
    unsigned route_gate_count=0;
    unsigned topology_revision=0;
    struct AccessField { std::unique_ptr<cambc::distance_field> field;unsigned revision=~0u;int expires=0;bool closed=false; };
    std::vector<AccessField> access_fields;
    struct AccessBuild {
        LocalMask mask;int altar=-1,expires=0;unsigned revision=~0u;
        std::size_t group=0,member=0;
    } access_build;
#endif
#if DZ_ECONOMY_V2
    unsigned economic_crew=0, economic_capturer=0;
    int rendezvous_until=0;
    int economic_retry_after=0;
    float economic_rate=0;
    RaceClock race;
    int access_group=-1,access_member=-1;
    struct EnemyTrack { unsigned handle=~0u;vec2 p{};int seen=-10000; };
    std::array<EnemyTrack,8> enemy_tracks{};
    void track_enemies(const Observation& obs,int round) {
        for(const auto& enemy:obs.enemies) {
            const unsigned handle=static_cast<unsigned>(static_cast<cambc::handle_champion_t>(enemy.sdk));
            auto slot=std::min_element(enemy_tracks.begin(),enemy_tracks.end(),[](auto& a,auto& b){return a.seen<b.seen;});
            for(auto it=enemy_tracks.begin();it!=enemy_tracks.end();++it)if(it->handle==handle){slot=it;break;}
            *slot={handle,enemy.p,round};
        }
    }
    float pressure(vec2 p,int radius,int round) const {
        float exposure=0;
        for(const auto& enemy:enemy_tracks) {
            const int age=round-enemy.seen;if(age<0||age>40)continue;
            const float distance=enemy.p.chebyshev_distance(p);
            // Reachable-envelope index, not a calibrated location probability.
            exposure+=std::clamp((radius+age+1-distance)/(age+1.f),0.f,1.f)*(age==0?1.f:.5f);
        }
        return exposure;
    }
#endif
#if DZ_EE
    // DZ_EE: recent personal enemy sightings (position, round), oldest replaced first.
    struct Sighting { vec2 p{-1,-1}; int round=-100000; };
    std::array<Sighting,8> sightings{};
    void remember_enemies(const Observation& obs,int round) {
        for (const auto& e:obs.enemies) {
            auto slot=std::min_element(sightings.begin(),sightings.end(),[](auto& a,auto& b){return a.round<b.round;});
            for (auto it=sightings.begin();it!=sightings.end();++it) if (it->p.chebyshev_distance(e.p)<=2) { slot=it; break; }
            *slot={e.p,round};
        }
    }
    bool recently_seen_near(vec2 c,int radius,int round,int horizon) const {
        for (const auto& s:sightings) if (round-s.round<=horizon && static_cast<int>(s.p.chebyshev_distance(c))<=radius) return true;
        return false;
    }
#endif
    bool legacy(int round) const { return round < legacy_until; } // An idle champion re-plans every few rounds, not every turn.
    bool initialized = false;
    void init(const StaticWorld&);
    void observe_group(const StaticWorld&, int index, const TurnContext&);
    void update(const StaticWorld&, const TurnContext&);
    void release(int round);
};
}
