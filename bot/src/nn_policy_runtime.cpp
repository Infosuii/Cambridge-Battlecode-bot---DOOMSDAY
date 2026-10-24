// Direct v2 SDK dispatcher. All code is absent from the default teacher build.
#include "nn_policy_config.h"
#if NN_POLICY_V2
#include "bot.h"
#include "nn_policy_runtime.h"
#include "nn_policy_options.h"
#include "nn_policy_schedule.h"
#include "nn_policy_core.h"
#include "nn_policy_installed.h"
#include "nn_policy_state.h"
#include <cstdio>

#ifndef NN_POLICY_HEAD_MASK
#define NN_POLICY_HEAD_MASK 510
#endif
namespace {
namespace d=cambc::detail;
using H=nncfg::H;
constinit nnp::Core g_core{};
constinit nnp::OptionsState g_state{};
struct Commitment { int round=-1; std::uint64_t id=0; std::uint32_t action=nnp_log::kNoAction; bool record_open=false; };
constinit Commitment g_options[9]{};
constinit nnp::Opportunity g_coverage[9]{};
constinit Bot* g_bot=nullptr;
constinit bool g_configured=false,g_physical=false;
constinit int g_round=0,g_report=-1;
constinit std::uint64_t g_option_serial=0;
struct Frame { bool ready=false,fx=false,fy=false; int w=0,h=0; };
constinit Frame g_frame{};
constinit bool g_log_closed=false;
struct Costs { std::uint32_t candidate=0,decision=0,execution=0,total=0,refused=0; };
constinit Costs g_costs[9]{};
constinit nnp::TurnInventory* g_inventory=nullptr;
std::uint64_t fuel() {return bc::fuel_remaining();}
bool capture(void* b,float* out) {return b&&nnpobs::capture(*static_cast<Bot*>(b),out);}
bool enabled(H h) {return (NN_POLICY_HEAD_MASK&(1u<<static_cast<int>(h)))!=0;}
bool can_shop() {
    int items=0,consumables=0;const auto me=static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(bc::self()));
    return d::sdk_champion_can_shop(me,0,&items)==0&&d::sdk_champion_can_shop(me,1,&consumables)==0&&(items||consumables);
}
void close(H h,nnp::Reason why=nnp::Reason::ok) {
    auto& o=g_options[static_cast<int>(h)];
    if(o.id){if(o.record_open)g_core.close_option(h,o.id,o.action,why);o.round=-1;}
    o.id=0;o.action=nnp_log::kNoAction;
    o.record_open=false;
}
void interrupt() {
    for(int i=1;i<=8;++i)close(static_cast<H>(i),nnp::Reason::interrupted);
    for(auto& o:g_options)o.round=-1;
    g_state={};
}
void configure(Bot* bot=nullptr) {
    if(g_configured)return;
    // During draft there is no Bot observation. Capture receives the active Bot on gameplay configuration.
    g_bot=bot;
    g_core.configure(nnp::kInstalled,{fuel,[](void*,float* out){return capture(g_bot,out);},nullptr},
                     {},NN_POLICY_LOG,NN_POLICY_SAMPLE,20261024);
    g_configured=true;
}
using Build=bool(*)(const Bot&,const nnp::OptionsState&,nnpc::Decision&);
using Execute=nnp::Execution(*)(Bot&,nnp::OptionsState&,std::uint32_t);
bool choose(Bot& b,H h,int max_k,Build build,Execute execute,bool macro=false) {
    const int hi=static_cast<int>(h);
    close(h);
    if(!enabled(h)){g_inventory->record(h,false);return false;}
    const auto ticket=g_core.admit(h,max_k);
    if(!ticket.admitted){g_inventory->record(h,false);return false;}
    nnpc::Decision decision{};
    const auto candidate_start=fuel();
    // Even builder failure consumes/settles the admission ticket through the normal failure path.
    const bool built=build(b,g_state,decision);
    const auto candidate_cost=static_cast<std::uint32_t>(candidate_start-fuel());
    g_costs[hi].candidate=std::max(g_costs[hi].candidate,candidate_cost);
    if(!built){decision.head=h;decision.K=0;}
    const std::uint64_t option=macro?++g_option_serial:0;
    const auto result=g_core.decide(ticket,decision,option,macro?nnp_log::kOptionStart|nnp_log::kDefinedOption:0);
    const auto decision_cost=static_cast<std::uint32_t>(candidate_start-fuel())-candidate_cost;
    g_costs[hi].decision=std::max(g_costs[hi].decision,decision_cost);
    if(result.choice<0){g_inventory->record(h,false);++g_costs[hi].refused;return false;}
    const auto before=fuel();nnp::Execution actual{};
    try {actual=execute(b,g_state,result.action);} catch(...) {actual={true,false,false};}
    const auto action_cost=static_cast<std::uint32_t>(before-fuel());
    g_costs[hi].execution=std::max(g_costs[hi].execution,action_cost);
    g_costs[hi].total=std::max(g_costs[hi].total,static_cast<std::uint32_t>(candidate_start-fuel()));
    const bool ok=actual.legal&&actual.executed;
    g_core.acknowledge(result,ok?result.action:nnp_log::kNoAction,
        ok?(macro?nnp_log::kOptionExecuted:nnp_log::kExecuted):
           (actual.legal?nnp_log::kFailed:nnp_log::kGuardRefused),action_cost,
        ok?nnp::Reason::ok:actual.legal?nnp::Reason::action_failed:nnp::Reason::execution_guard);
    g_inventory->record(h,ok);
    if(!ok)return false;
    g_options[hi]={g_round,option,result.action,macro&&!g_log_closed&&bool(NN_POLICY_LOG)};
    // A goal/role change changes the observation, just as a physical move does.
    // Internal intent/role commits retain the first-admitted same-turn snapshot; candidate rows are live.
    // Physical effects invalidate the context before another action decision.
    if(actual.changed&&!macro&&h!=H::engage&&h!=H::bank)g_core.invalidate();
    if(!macro&&actual.changed)g_physical=true;
    return true;
}
bool scheduled(H h,int period,bool force=false) {
    (void)period;if(force)g_inventory->force(h);
    return g_inventory->expected(h);
}
bool fallback() {
    // A transient teacher turn suspends already committed intents until their fixed deadline. Their logged
    // trajectories are interrupted and ineligible for PPO; suspension never creates another neural start.
    for(int i=1;i<=8;++i) {
        auto& o=g_options[i];if(o.id&&o.record_open)g_core.close_option(static_cast<H>(i),o.id,o.action,nnp::Reason::interrupted);
        o.record_open=false;
    }
    return false;
}
}

struct nn_policy_access {
    static vec2 canonical(const Bot& b,vec2 q) {
        if(g_frame.ready)return {g_frame.fx?g_frame.w-1-q.x:q.x,g_frame.fy?g_frame.h-1-q.y:q.y};
        d::aabb box{};const int team=d::sdk_my_team();
        if(d::sdk_spawn_region(team,&box)!=0)return {-1,-1};
        const int sx=box.min_x+box.max_x-1,sy=box.min_y+box.max_y-1;
        const int w=b.w.width,h=b.w.height,sym=static_cast<int>(bc::map::symmetry());
        const bool flip=sym==0?(sx!=w-1?sx>w-1:team==1):sym==1?(sy!=h-1?sy>h-1:team==1):
                        sym==2?(sx!=w-1?sx>w-1:(sy!=h-1?sy>h-1:team==1)):false;
        g_frame={true,flip&&(sym==0||sym==2),flip&&(sym==1||sym==2),w,h};
        return {g_frame.fx?w-1-q.x:q.x,g_frame.fy?h-1-q.y:q.y};
    }
    static void prepare(Bot& b) {
        b.round=static_cast<int>(bc::round_number());g_round=b.round;
        if(!b.inited)b.init();
        b.cast_done=false;b.walked=false;b.keep_channel=false;b.force_tribute=false;
        b.shared=b.read_shared();b.track_claims();
        const auto state=bc::self().state();
        if(state.is_dead()) {
            if(!b.was_dead)interrupt();
            b.hp=0;b.gold=static_cast<int>(bc::self().gold_count());b.type=bc::self().champion_name();
            b.was_dead=true;b.target_group=kClaimDead;b.write_claim(kClaimDead);
            return;
        }
        b.was_dead=false;b.refresh_self();
        b.w.update(b.round);
        b.read_sighting(); // own team memory and public map state only
    }
    static bool channel(Bot& b) {
        const auto state=bc::self().state();
        if(!state.contains(bc::champion_state::recalling)&&!state.contains(bc::champion_state::submitting_gems)&&
           !state.contains(bc::champion_state::teleporting))return false;
        // Preserve channels; teleport cannot be cancelled. Channels are excluded from ordinary starts.
        interrupt();return true;
    }
    static void refresh(Bot& b) {
        b.refresh_self();b.w.update(b.round);g_core.invalidate();
    }
    static bool dispatch(Bot& b) {
        if(!g_core.ready())return fallback();
        if(b.was_dead) {
            if(g_inventory->expected(H::shop))return choose(b,H::shop,16,nnp::build_shop,nnp::execute_shop);
            return true;
        }
        if(channel(b))return true;
        // Winning-bag and last-round guards are narrow deterministic overrides, reported separately.
        const int deposit_rounds=std::max(bc::constants::submit_gem_minimum_duration,
            bc::constants::submit_gem_base_duration+static_cast<int>(std::ceil(b.gems*bc::constants::submit_gem_duration_multiplier)));
        if(b.gems>0&&(b.ally_score+b.gems>=static_cast<int>(bc::constants::winning_gems)||
                      b.round>=static_cast<int>(bc::constants::max_rounds)-deposit_rounds-1)) {
            ++g_coverage[static_cast<int>(H::bank)].overrides;return fallback();
        }
        bool macro_start=false;
        if(scheduled(H::role,nnp::kRolePeriod)) {
            if(!choose(b,H::role,5,nnp::build_role,nnp::execute_role,true))return fallback();
            macro_start=true;
        }
        if(scheduled(H::strategy,nnp::kStrategyPeriod,macro_start)) {
            if(!choose(b,H::strategy,7,nnp::build_strategy,nnp::execute_strategy,true))return fallback();
            macro_start=true;
        }
        g_inventory->conditional_objective(g_state.intent==0||g_state.intent==3,macro_start,g_state.objective<0);
        if(g_state.intent==0||g_state.intent==3) {
            if(scheduled(H::objective,nnp::kObjectivePeriod,macro_start||g_state.objective<0))
                if(!choose(b,H::objective,std::min(16,static_cast<int>(b.w.groups.size())),nnp::build_objective,nnp::execute_objective,true))return fallback();
        } else close(H::objective,nnp::Reason::interrupted);
        if(b.gems>0&&scheduled(H::bank,nnp::kBankPeriod,macro_start&&g_state.intent==1)) {
            if(!choose(b,H::bank,std::min(16,1+2*static_cast<int>(b.w.altars.size())),nnp::build_bank,nnp::execute_bank))return fallback();
            if(bc::self().state().contains(bc::champion_state::submitting_gems)) {
                g_inventory->suppress(H::engage);g_inventory->suppress(H::combat);g_inventory->suppress(H::move);return true;
            }
        }
        if(can_shop()&&scheduled(H::shop,nnp::kShopPeriod)) {
            if(!choose(b,H::shop,16,nnp::build_shop,nnp::execute_shop))return fallback();
            refresh(b);
        }
        if(!b.w.enemies.empty()) {
            if(!choose(b,H::engage,3,nnp::build_engage,nnp::execute_engage))return fallback();
            if(g_state.engagement==2){g_inventory->suppress(H::combat);g_inventory->suppress(H::move);return true;}
            if(g_state.engagement==1)g_inventory->suppress(H::combat);
        } else g_state.engagement=-1;
        if(g_state.engagement!=1) {
            // Hold is explicit even without an attackable entity; it is not a hidden teacher action.
            if(!choose(b,H::combat,16,nnp::build_combat,nnp::execute_combat))return fallback();
            if(g_physical)refresh(b);
        }
        if(bc::self().can_move()) {
            if(!choose(b,H::move,16,nnp::build_move,nnp::execute_move))return fallback();
        } else g_inventory->suppress(H::move);
        return true;
    }
    static bool turn(Bot& b) {
        configure(&b);g_bot=&b;
        g_core.begin_turn(static_cast<std::uint32_t>(bc::round_number()),
            static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(bc::self())));
        // Bound development records per champion, including pending base64 output, below the team log cap.
        if(!g_log_closed&&nnp_log::g_text_written+(nnp_log::g_bytes*4u+2u)/3u>40000) {
            for(int i=1;i<=8;++i)if(g_options[i].id&&g_options[i].record_open) {
                g_core.close_option(static_cast<H>(i),g_options[i].id,g_options[i].action,nnp::Reason::interrupted);
                g_options[i].record_open=false;
            }
            g_core.logging(false);g_log_closed=true;
        }
        g_physical=false;prepare(b);
        const auto state=bc::self().state();
        const bool channeling=state.contains(bc::champion_state::recalling)||state.contains(bc::champion_state::submitting_gems)||
                              state.contains(bc::champion_state::teleporting);
        nnp::LastOpportunity last[9]{};
        for(int i=1;i<=8;++i)last[i]={g_options[i].round,g_options[i].id!=0};
        auto inventory=nnp::TurnInventory::plan({b.round,g_state.intent,g_state.objective,!b.was_dead,channeling,
            b.gems>0,can_shop(),!b.w.enemies.empty(),!b.was_dead&&bc::self().can_move()},last);
        g_inventory=&inventory;
        bool handled=false;
        try {handled=dispatch(b);}catch(...) {fallback();}
        inventory.finish(g_coverage,!handled);g_inventory=nullptr;
        return handled;
    }
    static void fields(Bot& b) {
        if(!b.inited||b.w.fields_ready())return;
        // Geometry preprocessing follows all decisions, from spare fuel; never a teacher score/search.
        const auto full=std::uint64_t(b.w.width+b.w.height+40)*field_chunks()+3000;
        if(fuel()>full+16000)b.w.build_next_group_field(full);
    }
};

namespace nnp {
vec2 canonical(const Bot& b,vec2 q) {return nn_policy_access::canonical(b,q);}
int observation_role() {return g_state.role;}
vec2 observation_goal() {return g_state.goal;}
void warmup() {configure();if(fuel()>40000)g_core.warmup(1024);}
bool play_turn(Bot& b) {return nn_policy_access::turn(b);}
void idle() {
    warmup();
    if(g_bot)nn_policy_access::fields(*g_bot);
    // Record output and coverage output consume only fuel remaining after gameplay.
    while(g_core.flush_one()){}
#if NN_POLICY_TELEMETRY
    if(g_round!=g_report&&g_round%100==0&&fuel()>20000) {
        g_report=g_round;
        for(int i=1;i<=8&&fuel()>16000;++i) {
            const auto& c=g_coverage[i];
            std::printf("NPO2 round=%d head=%d starts=%u direct=%u continued=%u fallback=%u overrides=%u\n",
                        g_round,i,c.starts,c.direct,c.continued,c.fallback,c.overrides);
            const auto& m=g_costs[i];
            if(fuel()>16000)std::printf("NPC2 round=%d head=%d candidate=%u decision=%u execution=%u total=%u refused=%u\n",
                g_round,i,m.candidate,m.decision,m.execution,m.total,m.refused);
        }
    }
#endif
}
}
#endif
