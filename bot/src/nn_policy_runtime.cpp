// Direct v2 SDK dispatcher. All code is absent from the default teacher build.
#include "nn_policy_config.h"
#if NN_POLICY_V2
#include "bot.h"
#include "nn_policy_runtime.h"
#include "nn_policy_options.h"
#include "nn_policy_schedule.h"
#include "nn_policy_commitment.h"
#include "nn_policy_core.h"
#include "nn_policy_budget.h"
#include "nn_policy_installed.h"
#include "nn_policy_state.h"
#include <cstdio>

#ifndef NN_POLICY_HEAD_MASK
#define NN_POLICY_HEAD_MASK 510
#endif
#ifndef NN_POLICY_SEED
#define NN_POLICY_SEED 20261024
#endif
#ifndef NN_POLICY_LOG_HEAD_MASK
#define NN_POLICY_LOG_HEAD_MASK 510
#endif
namespace {
namespace d=cambc::detail;
using H=nncfg::H;
constinit nnp::Core g_core{};
constinit nnp::OptionsState g_state{};
constinit nnp::Commitment g_options[9]{};
constinit nnp::Opportunity g_coverage[9]{};
constinit Bot* g_bot=nullptr;
constinit bool g_configured=false,g_physical=false,g_abandoned=false;
constinit std::uint32_t g_prepare_failures=0,g_clock_resets=0;
std::uint32_t round_now(){return bc::round_number();}
std::uint32_t elapsed(std::uint64_t start,std::uint32_t round){
    const auto now=bc::fuel_remaining();
    if(now>start||bc::round_number()!=round){++g_clock_resets;return UINT32_MAX;}
    return static_cast<std::uint32_t>(start-now);
}
constinit int g_round=0,g_report=-1,g_report_head=1;
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
void recording(H h) {g_core.logging(NN_POLICY_LOG&&!g_log_closed&&(NN_POLICY_LOG_HEAD_MASK&(1u<<static_cast<int>(h))));}
bool note(H h,std::uint8_t source,nnp::Reason reason) {recording(h);return g_core.note(h,source,reason);}
bool can_shop() {
    int items=0,consumables=0;const auto me=static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(bc::self()));
    return d::sdk_champion_can_shop(me,0,&items)==0&&d::sdk_champion_can_shop(me,1,&consumables)==0&&(items||consumables);
}
void close(H h,nnp::Reason why=nnp::Reason::ok) {
    recording(h);
    auto& o=g_options[static_cast<int>(h)];
    if(o.id&&o.record_open)g_core.close_option(h,o.id,o.action,why);
    o.abandon();
}
void interrupt() {
    g_abandoned=true;
    for(int i=1;i<=8;++i)close(static_cast<H>(i),nnp::Reason::interrupted);
    for(auto& o:g_options)o.round=-1;
    g_state={};
}
void configure(Bot* bot=nullptr) {
    if(g_configured)return;
    // During draft there is no Bot observation. Capture receives the active Bot on gameplay configuration.
    g_bot=bot;
    const auto budget=nnp::kPolicyBudget;
    // Conservative component ceilings from the frozen reused calibration maps; not a strength claim.
    g_core.configure(nnp::kInstalled,{fuel,[](void*,float* out){return capture(g_bot,out);},nullptr,round_now},
                     budget,NN_POLICY_LOG,NN_POLICY_SAMPLE,NN_POLICY_SEED,nnp_log::kSafetyOverride);
    g_configured=true;
}
using Build=bool(*)(const Bot&,const nnp::OptionsState&,nnpc::Decision&);
using Execute=nnp::Execution(*)(Bot&,nnp::OptionsState&,std::uint32_t);
bool choose(Bot& b,H h,int max_k,Build build,Execute execute,bool macro=false) {
    const int hi=static_cast<int>(h);
    close(h);
    if(!enabled(h)){g_inventory->record(h,false);return false;}
    const auto bound=hi<=3?nnp::strategy_candidate_fuel(b,h):h==H::bank?nnp::bank_candidate_fuel(b):
        h==H::shop?24000u:nnp::tactics_candidate_bound(b,g_state,h);
    // Movement is last: reserve its bounded endpoint recheck, with no following world refresh.
    // Macro reserve: strategy execution peaks ~17.5k, and a new objective/goal makes the next movement field cold.
    const auto execution=macro?20000u:h==H::move?6000u+static_cast<std::uint32_t>(field_chunks())*16u:16000u;
    // Movement and combat builders fail closed below a fuel floor, so they are admitted at a typical cost.
    const bool guarded=h==H::move||h==H::combat;
    // Typical measured builds: move ~0.4x and combat ~0.6x of their worst-case bounds.
    const auto ticket=g_core.admit(h,max_k,bound,execution,guarded&&bound<UINT32_MAX?(h==H::move?bound*2/5:bound*3/5):0);
    if(!ticket.admitted){g_inventory->record(h,false);note(h,nnp_log::kSafetyOverride,nnp::Reason::budget);return false;}
    nnpc::Decision decision{};
    const auto candidate_start=fuel();const auto candidate_round=bc::round_number();
    // Even builder failure consumes/settles the admission ticket through the normal failure path.
    const bool built=build(b,g_state,decision);
    const auto candidate_cost=elapsed(candidate_start,candidate_round);
    g_costs[hi].candidate=std::max(g_costs[hi].candidate,candidate_cost);
    if(!built){decision.head=h;decision.K=0;}
    const std::uint64_t option=macro?++g_option_serial:0;
    const auto result=g_core.decide(ticket,decision,option,macro?nnp_log::kOptionStart|nnp_log::kDefinedOption:0);
    const auto cumulative=elapsed(candidate_start,candidate_round);
    const auto decision_cost=cumulative==UINT32_MAX?UINT32_MAX:cumulative>=candidate_cost?cumulative-candidate_cost:0;
    g_costs[hi].decision=std::max(g_costs[hi].decision,decision_cost);
    if(result.choice<0){g_inventory->record(h,false);++g_costs[hi].refused;return false;}
    if(cumulative==UINT32_MAX){g_inventory->record(h,false);return false;}
    const auto before=fuel();nnp::Execution actual{};
    try {actual=execute(b,g_state,result.action);} catch(...) {actual={true,false,false};}
    const auto action_cost=elapsed(before,candidate_round);
    g_costs[hi].execution=std::max(g_costs[hi].execution,action_cost);
    g_costs[hi].total=std::max(g_costs[hi].total,elapsed(candidate_start,candidate_round));
    const bool ok=actual.legal&&actual.executed;
    g_core.acknowledge(result,ok?result.action:nnp_log::kNoAction,
        ok?(macro?nnp_log::kOptionExecuted:nnp_log::kExecuted):
           (actual.legal?nnp_log::kFailed:nnp_log::kGuardRefused),action_cost,
        action_cost==UINT32_MAX?nnp::Reason::clock_reset:ok?nnp::Reason::ok:actual.legal?nnp::Reason::action_failed:nnp::Reason::execution_guard);
    g_inventory->record(h,ok);
    if(!ok){if(macro)interrupt();return false;}
    g_options[hi].start(g_round,option,result.action,macro&&result.recorded,macro);
    // A goal/role change changes the observation, just as a physical move does.
    // Internal intent/role commits retain the first-admitted same-turn snapshot; candidate rows are live.
    // Physical effects invalidate the context before another action decision.
    // Combat never moves the acting champion (dash endpoints belong to the movement head), so the turn-start
    // snapshot stays valid for the movement decision: no ~10k world refresh and ~12k re-encode per attack turn.
    if(actual.changed&&!macro&&h!=H::engage&&h!=H::bank&&h!=H::combat)g_core.invalidate();
    if(!macro&&actual.changed&&h!=H::combat)g_physical=true;
    return true;
}
bool scheduled(H h,int period,bool force=false) {
    (void)period;if(force)g_inventory->force(h);
    return g_inventory->expected(h);
}
bool fallback() {
    for(int i=1;i<=3;++i) {
        auto& o=g_options[i];
        o.defer();
    }
    // Once policy preparation/decisions have used this turn, a fresh whole-teacher run cannot be
    // promised its original fuel budget. Finish safely and resume the same guarded assignment next turn.
    return true;
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
        b.refresh_self();b.w.update(b.round);g_core.invalidate();g_physical=false;
    }
    static bool dispatch(Bot& b) {
        if(!g_core.ready())return fallback();
        bool suspended=false;for(int i=1;i<=3;++i)suspended|=g_options[i].suspended;
        if(suspended&&g_options[static_cast<int>(H::role)].committed) {
            if(!nnp::resume_assignments(b,g_state)) {
                for(int i=1;i<=3;++i)if(g_inventory->continuation(static_cast<H>(i)))++g_coverage[i].interrupted;
                interrupt();g_abandoned=false; // New selections below are distinct from the abandoned old options.
                g_inventory->force(H::role);g_inventory->force(H::strategy);g_inventory->force(H::objective);
            }
            else for(int i=1;i<=3;++i)g_options[i].suspended=false;
        }
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
            if(fuel()>30000) {
                // The same deterministic deposit guard as the teacher; no ranked goal/search fallback.
                for(std::size_t i=0;i<b.w.altars.size()&&i<16&&fuel()>20000;++i) {
                    if(cheb(b.pos,b.w.altars[i])>bc::constants::submit_gems_range)continue;
                    const auto id=2+2*static_cast<std::uint32_t>(i);
                    if(nnp::execute_bank(b,g_state,id).executed) {
                        ++g_coverage[static_cast<int>(H::bank)].overrides;recording(H::bank);
                        g_core.note(H::bank,nnp_log::kSafetyOverride,nnp::Reason::interrupted,id,nnp_log::kOverridden);
                        interrupt();
                        g_inventory->suppress(H::engage);g_inventory->suppress(H::combat);g_inventory->suppress(H::move);
                        return fallback();
                    }
                }
            }
            // A distant carrier still needs a destination and movement. Never freeze its turn
            // simply because the bag could win: refresh the bank choice at the ordinary call site.
            g_inventory->force(H::bank);
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
                // Strategy already set a reachable farming group as the goal; an unavailable objective decision keeps it.
                if(!choose(b,H::objective,std::min(16,static_cast<int>(b.w.groups.size())),nnp::build_objective,nnp::execute_objective,true)&&
                   g_state.objective<0)return fallback();
        } else close(H::objective,nnp::Reason::interrupted);
        if((g_state.intent==0||g_state.intent==3)&&!g_options[static_cast<int>(H::objective)].committed&&g_state.objective<0)return fallback();
        if(b.gems>0&&scheduled(H::bank,nnp::kBankPeriod,macro_start&&g_state.intent==1)) {
            if(!choose(b,H::bank,std::min(16,1+2*static_cast<int>(b.w.altars.size())),nnp::build_bank,nnp::execute_bank))return fallback();
            if(bc::self().state().contains(bc::champion_state::submitting_gems)) {
                // This policy-selected channel completes the current assignment; it is not an
                // external interruption. Close its defined interval before the channel-only turns.
                close(H::role);close(H::strategy);close(H::objective);
                g_inventory->suppress(H::engage);g_inventory->suppress(H::combat);g_inventory->suppress(H::move);return true;
            }
        }
        if(can_shop()&&scheduled(H::shop,nnp::kShopPeriod)) {
            if(!choose(b,H::shop,16,nnp::build_shop,nnp::execute_shop))return fallback();
            if(g_physical){if(fuel()<30000)return fallback();refresh(b);}
        }
        if(!b.w.enemies.empty()) {
            // An unavailable verdict (e.g. budget refusal) is "no verdict", not a lost turn: combat and move
            // keep their own admission checks.
            if(!choose(b,H::engage,3,nnp::build_engage,nnp::execute_engage))g_state.engagement=-1;
            if(g_state.engagement==2){g_inventory->suppress(H::combat);g_inventory->suppress(H::move);return true;}
            if(g_state.engagement==1)g_inventory->suppress(H::combat);
        } else g_state.engagement=-1;
        if(g_state.engagement!=1&&nnp::combat_has_choice(b)) {
            // Hold is explicit even without an attackable entity; it is not a hidden teacher action.
            // A combat decision that is not admitted or fails holds this turn; movement is still decided below.
            if(choose(b,H::combat,16,nnp::build_combat,nnp::execute_combat)&&g_physical) {
                if(fuel()<30000)return fallback();
                refresh(b);
            }
        } else g_inventory->suppress(H::combat); // A forced hold needs no neural inference.
        if(bc::self().can_move()) {
            if(!choose(b,H::move,nnp::tactics_candidate_capacity(b,H::move),nnp::build_move,nnp::execute_move))return fallback();
        } else g_inventory->suppress(H::move);
        return true;
    }
    static bool turn(Bot& b) {
        configure(&b);g_bot=&b;
        g_core.begin_turn(static_cast<std::uint32_t>(bc::round_number()),
            static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(bc::self())));
        // A verified model is required before preparation. Early failure preserves the whole
        // teacher turn; later failures use the bounded safety path, after real neural work.
        if(!g_core.ready())return false;
        // Bound development records per champion, including pending base64 output, below the team log cap.
        if(!g_log_closed&&nnp_log::g_text_written+(nnp_log::g_bytes*4u+2u)/3u>40000) {
            for(int i=1;i<=8;++i)if(g_options[i].id&&g_options[i].record_open) {
                recording(static_cast<H>(i));
                g_core.close_option(static_cast<H>(i),g_options[i].id,g_options[i].action,nnp::Reason::interrupted);
                g_options[i].suspend();
            }
            g_core.logging(false);g_log_closed=true;
        }
        g_physical=false;g_abandoned=false;
        try {prepare(b);}catch(...) {
            ++g_prepare_failures;interrupt();note(H::strategy,nnp_log::kSafetyOverride,nnp::Reason::capture);return true;
        }
        const auto state=bc::self().state();
        const bool channeling=state.contains(bc::champion_state::recalling)||state.contains(bc::champion_state::submitting_gems)||
                              state.contains(bc::champion_state::teleporting);
        nnp::LastOpportunity last[9]{};
        for(int i=1;i<=8;++i)last[i]={g_options[i].round,g_options[i].committed};
        auto inventory=nnp::TurnInventory::plan({b.round,g_state.intent,g_state.objective,!b.was_dead,channeling,
            b.gems>0,can_shop(),!b.w.enemies.empty(),!b.was_dead&&bc::self().can_move()},last);
        g_inventory=&inventory;
        bool handled=false;
        try {handled=dispatch(b);}catch(...) {handled=fallback();}
        for(int i=1;i<=8;++i)if(inventory.expected(static_cast<H>(i))&&!inventory.visited(static_cast<H>(i)))
            note(static_cast<H>(i),nnp_log::kSafetyOverride,nnp::Reason::budget);
        inventory.finish(g_coverage,g_abandoned||!handled);g_inventory=nullptr;
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
void warmup() {configure();if(fuel()>30000)g_core.warmup(128);}
bool play_turn(Bot& b) {return nn_policy_access::turn(b);}
void idle() {
    if(bc::is_draft())return; // There is no acting champion in the draft VM.
    warmup();
    if(g_bot){nn_policy_access::fields(*g_bot);nnp::prepare_strategy(*g_bot,16000);nnp::prepare_tactics(*g_bot,g_state,16000);}
    // Record output and coverage output consume only fuel remaining after gameplay.
    while(g_core.flush_one()){}
#if NN_POLICY_TELEMETRY
    if(g_round!=g_report&&g_round%100==0&&fuel()>20000) {
        g_report=g_round;
        for(int emitted=0;emitted<8&&fuel()>16000;++emitted) {
            const int i=g_report_head;g_report_head=i%8+1;
            const auto& c=g_coverage[i];
            std::printf("NPO2 round=%d champion=%u head=%d starts=%u direct=%u continued=%u fallback=%u overrides=%u skipped=%u interrupted=%u\n",
                        g_round,static_cast<unsigned>(static_cast<bc::handle_champion_t>(bc::self())),i,c.starts,c.direct,c.continued,c.fallback,c.overrides,c.skipped,c.interrupted);
            const auto& m=g_costs[i];
            if(fuel()>16000)std::printf("NPC2 round=%d champion=%u head=%d candidate=%u decision=%u execution=%u total=%u refused=%u resets=%u prepare_failed=%u\n",
                g_round,static_cast<unsigned>(static_cast<bc::handle_champion_t>(bc::self())),i,m.candidate,m.decision,m.execution,m.total,m.refused,g_clock_resets,g_prepare_failures);
        }
    }
#endif
}
}
#endif
