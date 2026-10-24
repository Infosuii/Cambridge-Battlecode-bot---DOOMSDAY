// Pure synthetic opportunity accounting. No SDK, model, engine, or match data.
#include "nn_policy_schedule.h"
#include <cassert>
#include <iostream>
using H=nncfg::H;
constexpr int ix(H h){return static_cast<int>(h);}
int main() {
    nnp::LastOpportunity last[9]{};nnp::Opportunity counts[9]{};
    nnp::ScheduleInput in;in.round=40;in.has_gems=in.shop=in.enemies=in.move=true;
    auto turn=nnp::TurnInventory::plan(in,last);
    for(int i=1;i<=8;++i)assert(turn.expected(static_cast<H>(i)));
    assert(turn.record(H::role,false));assert(!turn.record(H::role,true));
    assert(turn.finish(counts,true));assert(!turn.finish(counts,true));
    for(int i=1;i<=8;++i)assert(counts[i].starts==1&&counts[i].fallback==1&&counts[i].direct==0);
    assert(counts[ix(H::role)].skipped==0&&counts[ix(H::move)].skipped==1);
    // A timestamp alone cannot resurrect an interrupted macro as a continuation.
    for(int i=1;i<=8;++i)last[i]={40,false};
    in.round=41;auto interrupted=nnp::TurnInventory::plan(in,last);
    assert(interrupted.expected(H::role)&&interrupted.expected(H::strategy)&&interrupted.expected(H::objective));
    // Live macros continue; a role expiry forces fresh strategy and conditional objective opportunities.
    for(int i=1;i<=8;++i)last[i]={40,true};
    auto continued=nnp::TurnInventory::plan(in,last);
    assert(!continued.expected(H::role)&&continued.continuation(H::role));
    assert(!continued.expected(H::strategy)&&continued.continuation(H::strategy));
    assert(!continued.expected(H::bank)&&continued.continuation(H::bank));
    assert(!continued.expected(H::shop)&&continued.continuation(H::shop));
    in.round=72;last[ix(H::strategy)]={70,true};last[ix(H::objective)]={70,true};
    auto role_due=nnp::TurnInventory::plan(in,last);
    assert(role_due.expected(H::role)&&role_due.expected(H::strategy)&&role_due.expected(H::objective));
    // A successful strategy can add a newly applicable objective, or remove an inapplicable one.
    in.round=41;in.intent=5;in.objective=-1;auto conditional=nnp::TurnInventory::plan(in,last);
    assert(!conditional.expected(H::objective));conditional.conditional_objective(true,true);
    assert(conditional.expected(H::objective));conditional.conditional_objective(false,true);
    assert(!conditional.expected(H::objective)&&!conditional.continuation(H::objective));
    // Successful engage-hold makes downstream actions ineligible; early engage failure must not suppress them.
    conditional.record(H::engage,true);conditional.suppress(H::combat);conditional.suppress(H::move);
    assert(!conditional.expected(H::combat)&&!conditional.expected(H::move));
    nnp::Opportunity separate[9]{};conditional.finish(separate,false);
    assert(separate[ix(H::combat)].starts==0&&separate[ix(H::move)].starts==0);
    // Continuations interrupted by fallback never inflate continued ownership.
    nnp::Opportunity cont_count[9]{};continued.finish(cont_count,true);
    assert(cont_count[ix(H::role)].interrupted==1&&cont_count[ix(H::role)].continued==0);
    // A macro assigned then discarded before the whole-bot teacher is not direct ownership.
    auto aborted=nnp::TurnInventory::plan({},last);aborted.record(H::role,true);aborted.record(H::combat,true);
    nnp::Opportunity aborted_counts[9]{};aborted.finish(aborted_counts,true);
    assert(aborted_counts[ix(H::role)].direct==0&&aborted_counts[ix(H::role)].fallback==1&&aborted_counts[ix(H::role)].interrupted==1);
    assert(aborted_counts[ix(H::combat)].direct==1); // the physical action really executed before fallback
    // A log interval can be censored while a separately revalidated semantic commitment is suspended.
    // Resuming it never creates another direct start; abandoning it must clear the live flag.
    nnp::ScheduleInput resume_input;resume_input.round=41;resume_input.intent=0;resume_input.objective=2;
    nnp::LastOpportunity suspended_last[9]{};
    suspended_last[ix(H::role)]={40,true};suspended_last[ix(H::strategy)]={40,true};
    suspended_last[ix(H::objective)]={40,true};
    auto resume=nnp::TurnInventory::plan(resume_input,suspended_last);
    nnp::Opportunity resume_counts[9]{};resume.record(H::combat,true);resume.finish(resume_counts,false);
    assert(resume_counts[ix(H::role)].starts==0&&resume_counts[ix(H::role)].direct==0&&resume_counts[ix(H::role)].continued==1);
    suspended_last[ix(H::role)].live=false;
    auto abandoned=nnp::TurnInventory::plan(resume_input,suspended_last);
    assert(abandoned.expected(H::role)&&abandoned.expected(H::strategy)&&abandoned.expected(H::objective));
    // No ordinary starts during a live channel; dead shopping remains an explicit opportunity.
    in.channeling=true;in.alive=true;auto channel=nnp::TurnInventory::plan(in,last);
    for(int i=1;i<=8;++i)assert(!channel.expected(static_cast<H>(i)));
    in.alive=false;in.round=100;auto dead=nnp::TurnInventory::plan(in,last);
    for(int i=1;i<=8;++i)assert(dead.expected(static_cast<H>(i))==(i==ix(H::shop)&&nnp::due(in.round,last[i].round,nnp::kShopPeriod)));
    // Physical hold/save still counts a real direct start; repeating record/finish cannot duplicate it.
    auto hold=nnp::TurnInventory::plan({},last);assert(hold.record(H::combat,true));hold.finish(counts,false);
    assert(counts[ix(H::combat)].direct==1);
    std::cout<<"synthetic policy schedule fixture passed\n";
}
