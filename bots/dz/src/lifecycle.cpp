#include "lifecycle.h"
#include "siege.h"
#include "map_signature.h"
#include "crew.h"
#include "economy.h"
#include <bit>

namespace dz {
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
bool lifecycle_owns(const Memory& m) {
    return !m.siege_task.active()&&std::popcount(m.economic_crew)<=1&&!m.crew_execution.managed;
}
Goal lifecycle_goal(StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc) {
    auto& cycle=m.lifecycle;const int now=tc.round;
    const auto word=shared_word();
    if(!cycle.profile_ready){cycle.profile=map_signature(w.groups);cycle.profile_ready=true;}
    const int opening=cycle.profile==3765343063u?(w.home.get(vec2{0,0})==0?2:3):-1;
    const bool opening_prefix=opening>=0&&opening<static_cast<int>(m.groups.size())&&now<80&&
        m.conversions[opening]==0&&m.groups[opening].state!=GroupState::Reward&&m.groups[opening].state!=GroupState::Respawning;
    const int next_camp=opening==2?0:opening==3?1:-1;
    // Observed Mite sequence: resource clear, then the home-side elk group
    // together. Banking the first 28 gems separated the carrier from helpers.
    const bool resource_finished=opening>=0&&opening<static_cast<int>(m.groups.size())&&
        (m.conversions[opening]>0||m.groups[opening].state==GroupState::Reward);
    if(resource_finished&&!cycle.opening_team_done&&cycle.opening_team_until==0&&now<80)
        cycle.opening_team_until=now+30;
    if(cycle.opening_team_until&&(now>cycle.opening_team_until||m.conversions[next_camp]>0||!m.groups[next_camp].available(now)))
        cycle.opening_team_done=true;
    const bool opening_team=cycle.opening_team_until>0&&!cycle.opening_team_done&&o.hp>=.55f*o.max_hp;
#if DZ_TRACE
    if(opening>=0&&w.slot==0&&now<80&&now%5==0){TraceScope scope;trace("DZ_OPENING_STATE round=%u resource=%d state=%d conversion=%u team=%d until=%d allies=%zu\n",
        tc.round,opening,static_cast<int>(m.groups[opening].state),m.conversions[opening],opening_team,cycle.opening_team_until,o.allies.size());}
#endif
    if(o.bag>cycle.bag||o.gold>cycle.gold)m.last_income=now;
    if(o.bag==0&&cycle.bag>0)cycle.last_delivery=now;
    cycle.bag=o.bag;cycle.gold=o.gold;
    auto release=[&](bool failed) {
        const int g=m.contract.objective;
        if(failed&&g>=0)m.groups[g].avoid_until=now+30;
        m.contract.objective=-1;m.leave_crew();m.field_needed=-1;
        cycle.crew_prefix=false;cycle.crew_exit_group=-1;
    };
    auto owned_elsewhere=[&](int g) {
        const auto owner=m.team.cohort(g,word,tc.round,w.allies.size());
        if(owner.valid)return !(owner.members&(1u<<w.slot));
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
        const bool assembling=std::popcount(m.economic_crew)>1&&now<=m.rendezvous_until;
        if(paid||(b.state==GroupState::Respawning&&b.ready>now)||owned_elsewhere(job)||(!progress&&!assembling)||now>cycle.job_until) {
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
    const bool active_crew=job>=0&&std::popcount(m.economic_crew)>1;
    // Finish a nearby payout before a gold-only trip, just as the active
    // V58_FINISH_RESET/CAPTURE_STAND package does. Actual danger owns withdrawal.
    if(o.hp<.28f*o.max_hp||(!finish&&!active_crew&&o.gold>=150)) {
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
    const bool winning=o.submitted+o.bag>=cambc::constants::winning_gems;
    const bool due=o.bag>0&&(winning||(!opening_team&&!active_crew&&(distance<=8||o.bag>=20||now-cycle.last_delivery>=90)));
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
    // A real invitation reaches the same crew executor without first paying
    // for the optional economy/bank pipeline. Finish the current job first.
    const auto lease=protocol::compact::lease(word,tc.round);
    if(lease.valid&&lease.leader!=w.slot&&(lease.members&(1u<<w.slot))&&
       lease.leader<w.allies.size()&&lease.capturer<w.allies.size()&&lease.objective>=0&&
       lease.objective<static_cast<int>(w.groups.size())&&!(lease.members&~((1u<<w.allies.size())-1u))&&
       m.groups[lease.objective].available(now)&&m.groups[lease.objective].state!=GroupState::Reward&&
       !(m.crew_decline.group==lease.objective&&m.crew_decline.members==lease.members&&m.crew_decline.until>now)&&
       o.hp>=.5f*o.max_hp&&w.allies[lease.leader].is_alive()) {
        const int g=lease.objective,d=w.distance(g,o.p);const auto& b=m.groups[g];
        if(d<65535) {
            m.contract.start(g,now,d,b.hp,b.capture,config::crew_window);
            m.economic_crew=lease.members;m.economic_capturer=lease.capturer;
            cycle.crew_prefix=opening_team&&g==next_camp;
            m.rendezvous_until=crew::assembly_deadline(now,d,team::agreement_window(w.allies.size()),config::crew_window);
            cycle.job_since=now;cycle.job_until=m.rendezvous_until+240;cycle.generation=m.conversions[g];
            return {GoalKind::Farm,g};
        }
    }
    // Price every group's cheap bound before doing exact work. Metadata order
    // must not hide the closest opening or a large resource group.
    struct Candidate {unsigned group;float bound;};std::vector<Candidate> candidates;
    const float gold_weight=.12f+.08f*std::max(0.f,1-now/400.f);
    for(unsigned g=0;g<w.groups.size();++g) {
        const auto& group=w.groups[g];const auto& b=m.groups[g];
        if(opening_team&&g!=static_cast<unsigned>(next_camp))continue;
        if(!b.available(now)||owned_elsewhere(g)||(group.strength>0&&group.tiles.size()>clear_risk_members))continue;
        const int approach=std::max(0,static_cast<int>(o.p.chebyshev_distance(group.center))-group.radius-o.range);
        const float hp=b.state==GroupState::Respawning?group.max_hp:b.hp;
        const float work=hp/std::max(1.f,o.strength*o.camp_damage);
        const float value=group.reward_gems+gold_weight*group.reward_gold;
        candidates.push_back({g,opening_prefix&&g==static_cast<unsigned>(opening)?1e6f:value/(approach+work+1)});
    }
    std::sort(candidates.begin(),candidates.end(),[](auto a,auto b){return a.bound!=b.bound?a.bound>b.bound:a.group<b.group;});
    const auto scan_started=fuel_left();
    int best=-1;float best_rate=0;unsigned examined=0;
    int crew_best=-1;float crew_rate=0;
    for(const auto candidate:candidates) {
        if(!tc.allow(23000)||scan_started-fuel_left()>16000)break;
        const unsigned g=candidate.group;++examined;
        const auto& b=m.groups[g];const auto& group=w.groups[g];
        const int d=w.distance(g,o.p);if(d>=65535)continue;
        auto risk=group_clear_risk(w,m,o,g);
        if(b.state==GroupState::Respawning) {
            // Its known deadline has passed, but the new generation may be out
            // of vision. Travel to inspect it using FULL design HP/strength.
            // Rejecting this state forever prevented every repeat farm on packs.
            if(group.strength==0)risk=harmless_clear_risk(group.initial_hp,o.strength*o.camp_damage);
            else {
                std::array<ClearMember,clear_risk_members> renewed{};
                for(unsigned k=0;k<group.tiles.size();++k)renewed[k]={group.initial_hp[k],group.initial_strength[k]*o.camp_factor};
                risk=solo_clear_risk({renewed.data(),group.tiles.size()},o.strength*o.camp_damage);
            }
        }
        if(!clear_survivable(risk,o.hp,o.max_hp)) {
            // Retain the best unaffordable monster job for an actual joint
            // quote; rejection of its solo price is not rejection of the job.
            if(group.strength>0&&b.state!=GroupState::Respawning&&d<=20&&candidate.bound>crew_rate) {
                crew_rate=candidate.bound;crew_best=g;
            }
            continue;
        }
        float enemy=0;for(const auto& e:o.enemies)if(e.p.chebyshev_distance(group.center)<=e.range+2)enemy+=e.strength;
        if(enemy>0&&o.hp<.5f*o.max_hp)continue;
        const float capture=b.state==GroupState::Reward?std::min(b.capture,15):cambc::constants::capture_time;
        const float value=group.reward_gems+gold_weight*group.reward_gold;
        // Prefer repeatable home-side circuits over an old far-side reward.
        // Public home distance supplies geography; no enemy hidden state.
        const int home=w.home_distance({group.center.x,group.center.y});
        const int own_home=w.home.get(o.p);
        const float outward=std::max(0,home-own_home-12);
        const float stale=b.state==GroupState::Reward&&now-b.seen>30?d:0;
        float rate=value/(d+risk.attacks+capture+1.f+enemy*.1f+outward+stale);
        if(opening_prefix) {
            // Mite 1bf7d5f5: all three bodies clear the side's nine resources,
            // then one stands for payout while the helpers leave. Exact map only.
            // A multiplier was insufficient: a helper could commit to the
            // far resource before the opening even received its detail quote.
            // Treat the observed three-body clear as a finite first job.
            if(g==static_cast<unsigned>(opening)&&group.strength==0)rate=1e6f;
        }
        if(rate>best_rate){best_rate=rate;best=g;}
    }
    if(!w.groups.empty())cycle.cursor=(cycle.cursor+examined)%w.groups.size();
#if DZ_TRACE
    if(opening_team&&w.slot==0){TraceScope scope;trace("DZ_OPENING_BID round=%u best=%d crew=%d fuel=%llu\n",tc.round,best,crew_best,
        static_cast<unsigned long long>(fuel_left()));}
#endif
    // Price an executable raw team before optional equipment/kit projections.
    // Publish only a completed executable quote; existing consent/formation
    // rules still own every move and strike.
    // strategic_goal already handles losing contact. A visible enemy outside
    // that contact cannot veto even COMPUTING a team plan indefinitely.
    if(crew_best>=0&&crew_rate>best_rate&&tc.allow(30000)) {
        if(cycle.crew_candidate<0||now>cycle.crew_until||!m.groups[cycle.crew_candidate].available(now)) {
            cycle.crew_candidate=crew_best;cycle.crew_until=now+config::crew_window;
        }
        const int g=cycle.crew_candidate;
        std::array<crew::Unit,crew::max_units> units{};unsigned count=0;
        auto add=[&](const SeenChampion& seen,unsigned slot) {
            const int d=w.distance(g,seen.p);
            if(seen.hp<.55f*seen.max_hp||d>24||count>=units.size()||!tc.allow(23000))return;
            // No hidden inventory or speculative ability credit: factor 1
            // and observed basic strength are conservative for camp gear.
            // The accepted crew executor reads its actual kit and equipment.
            crew::Unit unit{slot,static_cast<unsigned>(static_cast<cambc::handle_champion_t>(seen.sdk)),{seen.p.x,seen.p.y},
                seen.hp,seen.max_hp,seen.strength,1,seen.range,std::max(0,d-seen.range),
                seen.sdk.champion_name()==cambc::champion_type::vesper_vale?1.33f:1.f,static_cast<int>(cambc::constants::capture_time)};
            units[count++]=unit;
        };
        add({cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range},w.slot);
        for(const auto& ally:o.allies) {
            unsigned slot=0;while(slot<w.allies.size()&&w.allies[slot]!=ally.sdk)++slot;
            if(slot>=w.allies.size()||slot<w.slot)continue; // One deterministic nearby recruiter.
            const auto intent=protocol::slot(word,slot).objective;
            if(intent>=112&&intent!=protocol::idle)continue;
            if(intent<112&&intent!=g&&(intent>=m.groups.size()||m.groups[intent].state!=GroupState::Respawning))continue;
            add(ally,slot);
        }
#if DZ_TRACE
        if(opening_team&&w.slot==0){TraceScope scope;trace("DZ_OPENING_ROSTER round=%u count=%u enemies=%zu fuel=%llu\n",tc.round,count,o.enemies.size(),
            static_cast<unsigned long long>(fuel_left()));}
#endif
        if(count>=2) {
            std::sort(units.begin(),units.begin()+count,[](auto a,auto b){return a.slot<b.slot;});
            const auto quote=crew_quote(w,m,g,{units.data(),count},cambc::constants::capture_time+1,tc,false,opening_team);
#if DZ_TRACE
            if(opening_team&&w.slot==0){TraceScope scope;trace("DZ_OPENING_TEAM round=%u group=%d count=%u result=%d stage=%d phases=%u fuel=%llu\n",tc.round,g,count,
                static_cast<int>(quote.status),static_cast<int>(m.crew_layout().search.stage),m.crew_layout().search.count,static_cast<unsigned long long>(fuel_left()));}
#endif
            if((quote.complete||quote.prefix)&&quote.members&&(quote.members&(1u<<w.slot))) {
                const auto& b=m.groups[g];const int d=w.distance(g,o.p);
                m.contract.start(g,now,d,b.hp,b.capture,config::crew_window);
                m.economic_crew=quote.members;m.economic_capturer=w.slot;
                cycle.crew_prefix=quote.prefix;
                m.rendezvous_until=crew::assembly_deadline(now,d,team::agreement_window(w.allies.size()),config::crew_window);
                cycle.job_since=now;cycle.job_until=m.rendezvous_until+std::max(180,2*quote.finish);cycle.generation=m.conversions[g];
                return {GoalKind::Farm,g};
            }
        }
    }
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
        const auto risk=group_clear_risk(w,m,o,best);
        cycle.job_since=now;cycle.job_until=now+2*w.distance(best,o.p)+std::max(180,2*static_cast<int>(risk.attacks)+40);cycle.generation=m.conversions[best];
        m.economic_crew=0;m.economic_capturer=w.slot;
        if(!w.groups[best].field)m.field_needed=best;
        return {GoalKind::Farm,best};
    }
    if(opening_team) {
        // Reunite on the approach side while the retained quote resumes. An
        // idle meeting beside the enemy resource never became a real crew.
        const auto& group=w.groups[next_camp];int reach=0;
        for(int range:group.attack_ranges)reach=std::max(reach,range);
        vec2 staging=o.p;int nearest=65535;
        for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
            if(!dx&&!dy)continue;
            const auto p=group.center+vec2{dx*(group.radius+reach+2),dy*(group.radius+reach+2)};
            if(!w.walkable(p)||w.is_spawn(p))continue;
            const int d=p.chebyshev_distance(w.groups[opening].center);
            if(d<nearest||(d==nearest&&w.home_side_distance(p)<w.home_side_distance(staging))){nearest=d;staging=p;}
        }
        if(nearest<65535)for(int offset=0;offset<9;++offset) {
            const int cell=(offset+w.slot)%9;const auto p=staging+vec2{cell%3-1,cell/3-1};
            if(!w.walkable(p)||w.is_spawn(p)||(p!=o.p&&o.is_occupied(p)))continue;
            bool safe=true;
            for(unsigned k=0;k<group.tiles.size();++k)if(p.chebyshev_distance(group.tiles[k])<=group.attack_ranges[k]+1){safe=false;break;}
            if(safe&&enemy_danger(p,o)<=enemy_danger(o.p,o))return {GoalKind::YieldSpawn,-1,p};
        }
        return {GoalKind::Idle}; // Finite window; no phantom helper damage.
    }
    // No completed affordable quote is different from an unsafe job. Waiting
    // preserves this body's position and next-turn discovery budget.
    return {o.hp<.7f*o.max_hp?GoalKind::Home:GoalKind::Idle};
}
#endif
}
