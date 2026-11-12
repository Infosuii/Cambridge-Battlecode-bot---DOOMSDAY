// Frozen v2 development opportunity cadence. Counts are decision starts, never API calls.
#pragma once
#include <cstdint>
#include "nn_config.h"
namespace nnp {
inline constexpr int kRolePeriod=32,kStrategyPeriod=8,kObjectivePeriod=8,kBankPeriod=4,kShopPeriod=16;
struct Opportunity {
    std::uint32_t starts=0,direct=0,continued=0,fallback=0,overrides=0;
    // A skipped start remains in the denominator. Interrupted commitments are not continued ownership.
    std::uint32_t skipped=0,interrupted=0;
};
constexpr bool due(int round,int last,int period) { return last<0||round-last>=period; }
// live means a currently valid semantic commitment, including a revalidated suspended one. It is not a log
// option ID: a censored NFS2 interval can end while its selected assignment remains available for resumption.
struct LastOpportunity { int round=-1; bool live=false; };
constexpr bool due(int round,const LastOpportunity& last,int period,bool macro) {
    return (macro&&!last.live)||due(round,last.round,period);
}
struct ScheduleInput {
    int round=0,intent=0,objective=-1;
    bool alive=true,channeling=false,has_gems=false,shop=false,enemies=false,move=false;
};

// Freeze the eligible inventory before any admission/inference. It does not depend on model readiness or
// builder success. Conditional eligibility can change only after an upstream policy actually executes:
// e.g. a selected non-farm strategy suppresses objective, and engage-hold suppresses combat/movement.
// Finish exactly once at every turn exit. Expected but unvisited starts count as fallback, never disappear.
class TurnInventory {
    bool expected_[9]{},continued_[9]{},visited_[9]{},success_[9]{},done_=false;
    bool objective_due_=true;
    static constexpr int index(nncfg::H h) { return static_cast<int>(h); }
    static constexpr bool supported(int i) { return i>=1&&i<=8; }
    void schedule(nncfg::H h,bool eligible,bool start) {
        const int i=index(h);expected_[i]=eligible&&start;continued_[i]=eligible&&!start;
    }
public:
    static TurnInventory plan(const ScheduleInput& in,const LastOpportunity (&last)[9]) {
        using H=nncfg::H;TurnInventory out;
        const bool gameplay=in.alive&&!in.channeling;
        const bool role_due=due(in.round,last[index(H::role)],kRolePeriod,true);
        const bool strategy_due=role_due||due(in.round,last[index(H::strategy)],kStrategyPeriod,true);
        out.objective_due_=due(in.round,last[index(H::objective)],kObjectivePeriod,true);
        out.schedule(H::role,gameplay,role_due);
        out.schedule(H::strategy,gameplay,strategy_due);
        out.schedule(H::objective,gameplay&&(in.intent==0||in.intent==3),strategy_due||out.objective_due_||in.objective<0);
        out.schedule(H::bank,gameplay&&in.has_gems,due(in.round,last[index(H::bank)],kBankPeriod,false));
        // The economy head can legally act while dead; active channels exclude ordinary starts.
        out.schedule(H::shop,in.shop&&(!in.alive||!in.channeling),due(in.round,last[index(H::shop)],kShopPeriod,false));
        out.schedule(H::engage,gameplay&&in.enemies,true);
        out.schedule(H::combat,gameplay,true);
        out.schedule(H::move,gameplay&&in.move,true);
        return out;
    }
    bool expected(nncfg::H h) const {const int i=index(h);return supported(i)&&expected_[i];}
    bool continuation(nncfg::H h) const {const int i=index(h);return supported(i)&&continued_[i];}
    bool visited(nncfg::H h) const {const int i=index(h);return supported(i)&&visited_[i];}
    void force(nncfg::H h) {
        const int i=index(h);if(done_||!supported(i)||visited_[i])return;
        expected_[i]=true;continued_[i]=false;
    }
    void suppress(nncfg::H h) {
        const int i=index(h);if(done_||!supported(i)||visited_[i])return;
        expected_[i]=continued_[i]=false;
    }
    void conditional_objective(bool farming,bool new_strategy,bool missing_objective=false) {
        if(done_||visited_[index(nncfg::H::objective)])return;
        if(!farming)suppress(nncfg::H::objective);
        else if(new_strategy||objective_due_||missing_objective)force(nncfg::H::objective);
        else schedule(nncfg::H::objective,true,false);
    }
    // Returns false on duplicate accounting, so integration errors cannot inflate starts/direct counts.
    bool record(nncfg::H h,bool success) {
        const int i=index(h);if(done_||!supported(i)||visited_[i])return false;
        expected_[i]=visited_[i]=true;continued_[i]=false;success_[i]=success;return true;
    }
    bool finish(Opportunity (&counts)[9],bool teacher_fallback) {
        if(done_)return false;done_=true;
        for(int i=1;i<=8;++i) {
            if(expected_[i]) {
                ++counts[i].starts;
                const bool aborted_macro=teacher_fallback&&i<=3&&visited_[i]&&success_[i];
                if(visited_[i]&&success_[i]&&!aborted_macro)++counts[i].direct;
                else {
                    ++counts[i].fallback;if(!visited_[i])++counts[i].skipped;
                    if(aborted_macro)++counts[i].interrupted;
                }
            } else if(continued_[i]) {
                if(teacher_fallback)++counts[i].interrupted;else ++counts[i].continued;
            }
        }
        return true;
    }
};
}
