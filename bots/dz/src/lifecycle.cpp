#include "lifecycle.h"
#include "siege.h"
#include "map_signature.h"
#include <bit>

namespace dz {
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
bool lifecycle_owns(const Memory& m) {
    return !m.siege_task.active()&&std::popcount(m.economic_crew)<=1&&!m.crew_execution.managed;
}
Goal lifecycle_goal(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc) {
    auto& cycle=m.lifecycle;const int now=tc.round;
    const auto started=fuel_left();const auto word=shared_word();
    if(!cycle.profile_ready){cycle.profile=map_signature(w.groups);cycle.profile_ready=true;}
    if(o.bag>cycle.bag||o.gold>cycle.gold)m.last_income=now;
    if(o.bag==0&&cycle.bag>0)cycle.last_delivery=now;
    cycle.bag=o.bag;cycle.gold=o.gold;
    auto release=[&](bool failed) {
        const int g=m.contract.objective;
        if(failed&&g>=0)m.groups[g].avoid_until=now+30;
        m.contract.objective=-1;m.leave_crew();m.field_needed=-1;
    };
    auto owned_elsewhere=[&](int g) {
        const auto owner=m.team.cohort(g,word,tc.round,w.allies.size());
        if(owner.valid&&!(owner.members&(1u<<w.slot)))return true;
        // Harmless resource clears can use additional bodies without a damaging
        // wake/formation handshake. Election happens at Reward, before standing.
        if(w.groups[g].strength==0&&m.groups[g].state!=GroupState::Reward)return false;
        for(unsigned s=0;s<w.allies.size()&&s<protocol::slots;++s) {
            if(s==w.slot||protocol::slot(word,s).objective!=g)continue;
            // Existing capturers and lower-slot simultaneous selectors win.
            if(protocol::slot(word,s).onsite||s<w.slot)return true;
        }
        return false;
    };
    bool finish=false;
    int job=m.contract.objective;
    if(job>=0) {
        auto& b=m.groups[job];const int d=w.distance(job,o.p);
        const bool paid=m.conversions[job]!=static_cast<unsigned>(cycle.generation);
        const bool progress=m.contract.progressing(now,d,b.hp,b.capture);
        if(paid||(b.state==GroupState::Respawning&&b.ready>now)||owned_elsewhere(job)||!progress||now>cycle.job_until) {
            release(!paid&&b.state!=GroupState::Respawning);job=-1;
        } else {
            finish=(b.state==GroupState::Reward&&d<=2)||
                (b.state!=GroupState::Respawning&&d<=o.range&&b.hp<=2*o.strength*o.camp_damage);
        }
    }
    if(cycle.shopping) {
        if(w.home.get(o.p)==0||now>cycle.shop_until)cycle.shopping=false;
        else return {GoalKind::Home};
    }
    // Finish a nearby payout before a gold-only trip, just as the active
    // V58_FINISH_RESET/CAPTURE_STAND package does. Actual danger owns withdrawal.
    if(o.hp<.28f*o.max_hp||(!finish&&o.gold>=150)) {
        release(false);cycle.shopping=true;cycle.shop_until=now+std::min<int>(w.home.get(o.p),100)+30;
        return {GoalKind::Home};
    }
    if(o.bag==0)cycle.altar=-1;
    // A real bag creates a finite delivery task, independent of speculative
    // auction gem prices. Static distance supplies navigation, never admission.
    int altar=-1,distance=65535;
    for(unsigned a=0;a<w.altars.size();++a) {
        const int d=w.altar_distance(a,o.p);
        if(d<distance){altar=a;distance=d;}
    }
    const bool due=o.bag>0&&(distance<=8||o.bag>=20||now-cycle.last_delivery>=90||
        o.submitted+o.bag>=cambc::constants::winning_gems);
    if(cycle.altar>=0&&now>cycle.delivery_until) {
        cycle.altar=-1;cycle.last_delivery=now; // finite retry, not an immortal trip
    }
    if(cycle.altar<0&&altar>=0&&due&&!finish) {
        cycle.altar=altar;cycle.delivery_until=now+2*std::min(distance,150)+40;
        release(false);job=-1;
    }
    if(cycle.altar>=0) {
        const int a=cycle.altar;
        if(o.p.chebyshev_distance(w.altars[a].tile)<=cambc::constants::submit_gems_range) {
            const auto status=bank_admission(w,m,o,a,tc);
            if(status==BankAdmission::Denied) {
                cycle.altar=-1;cycle.last_delivery=now;
                return {GoalKind::Retreat};
            }
            // Deferred means retain this endpoint and try on a fresh turn.
        }
        return {GoalKind::Bank,a};
    }
    if(job>=0) {
        if(!w.groups[job].field)m.field_needed=job;
        return {GoalKind::Farm,job};
    }
    // Rank cheap real jobs before any optional dependency. The first feasible
    // incumbent survives an incomplete scan. Rotate the bounded scan on big maps.
    int best=-1;float best_rate=0;unsigned examined=0;
    for(unsigned n=0;n<w.groups.size();++n) {
        if(!tc.allow(23000)||started-fuel_left()>9000)break;
        const unsigned g=(cycle.cursor+n)%w.groups.size();++examined;
        const auto& b=m.groups[g];const auto& group=w.groups[g];
        if(!b.available(now)||owned_elsewhere(g)||group.tiles.size()>64)continue;
        const int d=w.distance(g,o.p);if(d>=65535)continue;
        auto risk=group_clear_risk(w,m,o,g);
        if(b.state==GroupState::Respawning) {
            // Its known deadline has passed, but the new generation may be out
            // of vision. Travel to inspect it using FULL design HP/strength.
            // Rejecting this state forever prevented every repeat farm on packs.
            std::array<ClearMember,clear_risk_members> renewed{};
            for(unsigned k=0;k<group.tiles.size();++k)renewed[k]={group.initial_hp[k],group.initial_strength[k]*o.camp_factor};
            risk=solo_clear_risk({renewed.data(),group.tiles.size()},o.strength*o.camp_damage);
        }
        if(!clear_survivable(risk,o.hp,o.max_hp))continue;
        float enemy=0;for(const auto& e:o.enemies)if(e.p.chebyshev_distance(group.center)<=e.range+2)enemy+=e.strength;
        if(enemy>0&&o.hp<.5f*o.max_hp)continue;
        const float capture=b.state==GroupState::Reward?std::min(b.capture,15):cambc::constants::capture_time;
        const float value=group.reward_gems+.12f*group.reward_gold;
        // Prefer repeatable home-side circuits over an old far-side reward.
        // Public home distance supplies geography; no enemy hidden state.
        const int home=w.home_distance({group.center.x,group.center.y});
        const int own_home=w.home.get(o.p);
        const float outward=std::max(0,home-own_home-12);
        const float stale=b.state==GroupState::Reward&&now-b.seen>30?d:0;
        float rate=value/(d+risk.attacks+capture+1.f+enemy*.1f+outward+stale);
        if(cycle.profile==3765343063u&&now<80) {
            // Mite 1bf7d5f5: all three bodies clear the side's nine resources,
            // then one stands for payout while the helpers leave. Exact map only.
            const unsigned opening=w.home.get(vec2{0,0})==0?2:3;
            if(g==opening&&group.strength==0)rate*=3;
        }
        if(rate>best_rate){best_rate=rate;best=g;}
    }
    if(!w.groups.empty())cycle.cursor=(cycle.cursor+examined)%w.groups.size();
#if DZ_TRACE
    if(w.slot==DZ_TRACE_SLOT&&now==60)for(unsigned g=0;g<w.groups.size()&&g<8;++g) {
        const auto& b=m.groups[g];const auto risk=group_clear_risk(w,m,o,g);
        TraceScope scope;trace("DZ_CYCLE_REASON round=%u group=%u state=%d ready=%d avoid=%d owned=%d risk=%.0f hp=%.0f\n",
            tc.round,g,static_cast<int>(b.state),b.ready,b.avoid_until,owned_elsewhere(g),risk.damage,b.hp);
    }
    if(w.slot==DZ_TRACE_SLOT&&now>=DZ_TRACE_FROM&&now<DZ_TRACE_TO) {
        TraceScope scope;trace("DZ_CYCLE round=%u slot=%u examined=%u best=%d fuel=%llu\n",tc.round,w.slot,examined,best,
            static_cast<unsigned long long>(fuel_left()));
    }
#endif
    if(best>=0) {
        auto& b=m.groups[best];m.contract.start(best,now,w.distance(best,o.p),b.hp,b.capture,24);
        cycle.job_since=now;cycle.job_until=now+2*w.distance(best,o.p)+180;cycle.generation=m.conversions[best];
        m.economic_crew=0;m.economic_capturer=w.slot;
        if(!w.groups[best].field)m.field_needed=best;
        return {GoalKind::Farm,best};
    }
    // No completed affordable quote is different from an unsafe job. Waiting
    // preserves this body's position and next-turn discovery budget.
    return {o.hp<.7f*o.max_hp?GoalKind::Home:GoalKind::Idle};
}
#endif
}
