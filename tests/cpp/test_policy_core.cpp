// Synthetic protocol/fuel-clock scenarios for the pure direct-policy core. No SDK, games or learning.
#include "nn_policy_core.h"
#include "nn_policy_weights_core_random.h"
#include "nn_policy_weights_core_zero.h"
#include <cstdio>
#include <cstring>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

namespace {
struct Host {std::uint64_t fuel=500000;int captures=0;int invalid=0;std::uint64_t capture_cost=50;float hp=.5f;} host;
std::uint64_t fuel(){return host.fuel;}
bool capture(void*,float* x){
    ++host.captures;host.fuel=host.fuel>host.capture_cost?host.fuel-host.capture_cost:0;
    for(int i=0;i<nnpobs::kObsDim;++i)x[i]=0;x[0]=host.hp;
    if(host.invalid==1)return false;
    if(host.invalid==2)x[0]=std::numeric_limits<float>::quiet_NaN();
    if(host.invalid==3)x[90]=.5f;
    if(host.invalid==4)x[40]=1; // Padded ally row must remain zero.
    if(host.invalid==5)x[0]=4.01f;
    return true;
}
nnp::Budget budget(){nnp::Budget b;b.turn_allowance=200000;b.action_reserve=2000;b.tail_reserve=500;
    b.observation=4000;b.candidate=500;b.head_base=500;b.per_candidate=200;b.log=2000;return b;}
bool verified(nnp::Core& c,const nnpm::PolicyDesc& p=nnpw_core_random::kDesc,bool logs=false,bool sample=false){
    c.configure(p,{fuel,capture,nullptr},budget(),logs,sample,49264);
    for(int i=0;i<1000&&!c.ready()&&!c.bad();++i)c.warmup(17);
    return c.ready();
}
nnpc::Decision decision(nncfg::H head=nncfg::H::move,int n=3){
    nnpc::Decision d;d.head=head;d.K=n;d.F=12;d.context=1;
    for(int i=0;i<n;++i){d.id[i]=10+10*i;d.legal[i]=i!=0;
        for(int j=0;j<12;++j)d.feat[i*12+j]=.01f*(i+j);}
    return d;
}
bool ok(int choice){return choice>=0;}
int failures=0;
void check(bool yes,const char* label){std::cout<<"CHECK "<<label<<' '<<(yes?"PASS":"FAIL")<<'\n';if(!yes)++failures;}
void reset(){host={};nnp_log::reset();}

void warmup_checks(){
    reset();nnp::Core c;c.configure(nnpw_core_random::kDesc,{fuel,capture,nullptr},budget());
    c.begin_turn(1,22);check(!c.admit(nncfg::H::move,3).admitted,"unverified_refuses");
    check(!c.warmup(1)&&!c.ready(),"warmup_resumable_not_instant");
    for(int i=0;i<1000&&!c.ready();++i)c.warmup(17);
    check(c.ready()&&host.captures==0,"warmup_all_segments_no_capture");
    auto m=nnpw_core_random::kKernel;nnpm::PolicyDesc p{2,&m};m.checksum^=1;
    c.configure(p,{fuel,capture,nullptr},budget());
    check(!c.ready(),"reconfigure_resets_verified_state");c.warmup(20000);check(c.bad(),"bad_whole_checksum");
    // Whole-blob checksum is still correct: each individual segment must independently be verified.
    for(int head=1;head<=8;++head){m=nnpw_core_random::kKernel;m.head[head].seg.checksum^=1;
        c.configure(p,{fuel,capture,nullptr},budget());c.warmup(20000);check(c.bad(),"bad_head_segment_checksum");}
    m=nnpw_core_random::kKernel;m.enc.checksum^=1;c.configure(p,{fuel,capture,nullptr},budget());c.warmup(20000);
    check(c.bad(),"bad_encoder_segment_checksum");
    std::vector<float> data(nnpw_core_random::kBlob,nnpw_core_random::kBlob+m.n_params);
    data[0]=std::numeric_limits<float>::quiet_NaN();m=nnpw_core_random::kKernel;m.blob=data.data();
    c.configure(p,{fuel,capture,nullptr},budget());c.warmup(20000);check(c.bad(),"nan_weight_refused");
    m=nnpw_core_random::kKernel;m.obs_schema_hash^=1;c.configure(p,{fuel,capture,nullptr},budget());check(c.bad(),"wrong_obs_schema");
    m=nnpw_core_random::kKernel;m.action_schema_hash^=1;c.configure(p,{fuel,capture,nullptr},budget());check(c.bad(),"wrong_action_schema");
    m=nnpw_core_random::kKernel;m.head[6].action_hash^=1;c.configure(p,{fuel,capture,nullptr},budget());check(c.bad(),"wrong_head_schema");
    p.interpretation_version=1;c.configure(p,{fuel,capture,nullptr},budget());check(c.bad(),"v1_interpretation_refused");
}

void budgets(){
    reset();nnp::Core c;check(verified(c),"verified");c.begin_turn(2,22);host.fuel=100;
    auto t=c.admit(nncfg::H::move,3);check(!t.admitted&&host.captures==0,"low_fuel_gate_before_capture");
    host.fuel=500000;t=c.admit(nncfg::H::move,3);host.fuel-=321;
    auto r=c.decide(t,decision());check(ok(r.choice)&&c.used()>=371,"candidate_and_capture_cost_charged");
    check(c.acknowledge(r,r.action,nnp_log::kExecuted),"valid_execution_ack");
    c.begin_turn(3,22);host.fuel=20000;t=c.admit(nncfg::H::move,3);check(t.admitted,"initial_budget_admitted");
    host.fuel=3000;int before=host.captures;r=c.decide(t,decision());
    check(r.choice==-1&&r.reason==nnp::Reason::bound_exceeded&&host.captures==before,"candidate_bound_violation_rejected_before_capture");
    c.begin_turn(4,22);host.fuel=500000;
    check(!c.admit(nncfg::H::move,3,UINT64_MAX).admitted,"unsupported_bound_cannot_wrap_into_admission");
    t=c.admit(nncfg::H::move,3,1000);host.fuel+=1;
    r=c.decide(t,decision());
    check(r.choice<0&&r.reason==nnp::Reason::clock_reset&&c.clock_bad(),"fuel_counter_reset_fails_closed");
    c.begin_turn(5,22);check(!c.clock_bad(),"new_turn_clears_clock_failure");
    auto small=budget();small.turn_allowance=1000;c.configure(nnpw_core_random::kDesc,{fuel,capture,nullptr},small);
    c.warmup(20000);host.fuel=500000;c.begin_turn(4,22);
    check(!c.admit(nncfg::H::move,3).admitted,"allowance_refuses_despite_host_fuel");
    auto trajectory=[](unsigned champion) {
        host={};nnp::Core sampled;verified(sampled,nnpw_core_zero::kDesc,false,true);std::string sequence;
        for(unsigned round=1;round<=24;++round) {
            sampled.begin_turn(round,champion);
            auto r=sampled.decide(sampled.admit(nncfg::H::move,3),decision());
            sequence+=static_cast<char>('0'+r.choice);sampled.acknowledge(r,r.action,nnp_log::kExecuted);
        }
        return sequence;
    };
    const auto first=trajectory(11);
    check(first==trajectory(11),"champion_rng_reproducible_across_episode_reset");
    check(first!=trajectory(12),"champion_rng_streams_are_distinct_and_persist_across_turns");
}

void cache(){
    reset();nnp::Core c;verified(c);c.begin_turn(4,22);
    auto t=c.admit(nncfg::H::move,3);auto a=c.decide(t,decision());c.acknowledge(a,a.action,nnp_log::kExecuted);
    t=c.admit(nncfg::H::combat,3);auto b=c.decide(t,decision(nncfg::H::combat));c.acknowledge(b,b.action,nnp_log::kExecuted);
    check(host.captures==1&&a.header.snapshot==b.header.snapshot,"shared_snapshot_cached_across_heads");
    c.invalidate();host.hp=.25f;t=c.admit(nncfg::H::move,3);auto d=c.decide(t,decision());
    c.acknowledge(d,d.action,nnp_log::kExecuted);
    check(host.captures==2&&d.header.snapshot!=b.header.snapshot,"action_invalidation_recaptures");
    c.begin_turn(5,22);t=c.admit(nncfg::H::move,3);auto e=c.decide(t,decision());c.acknowledge(e,e.action,nnp_log::kExecuted);
    check(host.captures==3&&e.header.round==5&&e.header.snapshot!=d.header.snapshot,"new_turn_resets_snapshot");
    for(int bad=1;bad<=5;++bad){reset();host.invalid=bad;nnp::Core f;verified(f);f.begin_turn(6,22);
        auto ft=f.admit(nncfg::H::move,3);auto fr=f.decide(ft,decision());
        check(fr.choice==-1&&fr.reason==nnp::Reason::capture,"invalid_or_missing_observation_fallback");}
}

void tickets(){
    reset();nnp::Core c;verified(c,nnpw_core_zero::kDesc);c.begin_turn(8,22);
    auto t=c.admit(nncfg::H::move,3);check(t.admitted,"first_ticket_admitted");
    check(!c.admit(nncfg::H::combat,3).admitted,"overlapping_ticket_refused");
    auto r=c.decide(t,decision());check(r.choice==1&&r.action==20,"first_illegal_zero_logits_choose_canonical_legal");
    check(c.decide(t,decision()).reason==nnp::Reason::stale_ticket,"ticket_replay_refused");
    check(!c.admit(nncfg::H::move,3).admitted,"missing_ack_blocks_new_start");
    check(!c.acknowledge(r,30,nnp_log::kExecuted),"wrong_execution_id_refused");
    auto wrong=r;wrong.header.decision_id++;
    check(!c.acknowledge(wrong,r.action,nnp_log::kExecuted),"wrong_ack_decision_refused");
    check(c.acknowledge(r,r.action,nnp_log::kExecuted),"matching_ack_accepted");
    check(!c.acknowledge(r,r.action,nnp_log::kExecuted),"duplicate_ack_refused");
    t=c.admit(nncfg::H::move,3);r=c.decide(t,decision());c.begin_turn(9,22);
    check(c.counters.missing_ack==1&&!c.acknowledge(r,r.action,nnp_log::kExecuted),"turn_end_missing_ack_counted");
    t=c.admit(nncfg::H::move,3);c.begin_turn(10,22);
    check(c.decide(t,decision()).reason==nnp::Reason::stale_ticket,"previous_turn_ticket_refused");
}

void ticket_integrity(){
    reset();nnp::Core c;verified(c);c.begin_turn(11,22);
    auto t=c.admit(nncfg::H::move,1);t.max_k=3;
    check(c.decide(t,decision()).choice<0,"ticket_cannot_expand_reserved_candidate_budget");
    c.begin_turn(12,22);t=c.admit(nncfg::H::move,3);t.head=nncfg::H::bank;
    check(c.decide(t,decision(nncfg::H::bank)).choice<0,"ticket_cannot_change_admitted_head");
    c.begin_turn(13,22);t=c.admit(nncfg::H::move,3);c.invalidate();
    check(c.decide(t,decision()).reason==nnp::Reason::stale_ticket,"invalidated_ticket_refused");
    check(c.admit(nncfg::H::move,3).admitted,"invalidation_releases_pending_ticket");
    c.begin_turn(14,22);t=c.admit(nncfg::H::move,3,500,3000);t.execution_reserve=1;
    check(c.decide(t,decision()).reason==nnp::Reason::stale_ticket,"ticket_authenticates_execution_reserve");
}

void ack_integrity(){
    reset();nnp::Core c;verified(c,nnpw_core_zero::kDesc);c.begin_turn(14,22);
    auto r=c.decide(c.admit(nncfg::H::move,3),decision());auto forged=r;forged.action=30;
    check(!c.acknowledge(forged,30,nnp_log::kExecuted),"ack_binds_original_selected_action");
    c.begin_turn(15,22);r=c.decide(c.admit(nncfg::H::move,3),decision());forged=r;forged.header.round++;
    check(!c.acknowledge(forged,r.action,nnp_log::kExecuted),"ack_binds_round");
    c.begin_turn(16,22);r=c.decide(c.admit(nncfg::H::move,3),decision());forged=r;forged.header.champion++;
    check(!c.acknowledge(forged,r.action,nnp_log::kExecuted),"ack_binds_champion");
    c.begin_turn(17,22);r=c.decide(c.admit(nncfg::H::move,3),decision());forged=r;forged.header.action_hash^=1;
    check(!c.acknowledge(forged,r.action,nnp_log::kExecuted),"ack_binds_schema");
}

void records(bool sample){
    reset();nnp::Core c;if(!verified(c,nnpw_core_random::kDesc,true,sample))return;
    for(int i=0;i<8;++i){host.fuel=500000;c.begin_turn(30+i,22);
        auto head=static_cast<nncfg::H>(i+1);auto d=decision(head,4);d.context=i%4;
        auto t=c.admit(head,4);host.fuel-=123;
        auto r=c.decide(t,d);
        if(i==6){c.begin_turn(100,22);} // Deliberately leave this choice unacknowledged.
        else c.acknowledge(r,r.action,i==5?nnp_log::kGuardRefused:nnp_log::kExecuted,75,
                           i==5?nnp::Reason::execution_guard:nnp::Reason::ok);
        host.fuel=500000;while(c.flush_one(stdout)){}
    }
}

void flush_boundary(const char* filename){
    reset();nnp::Core c;verified(c,nnpw_core_zero::kDesc,true,false);c.begin_turn(50,22);
    auto r=c.decide(c.admit(nncfg::H::move,3),decision());c.acknowledge(r,r.action,nnp_log::kExecuted);
    const auto line=nnp_log::next_line_bytes(),raw=nnp_log::next_bytes();const auto bytes=nnp_log::g_bytes;
    auto* file=std::fopen(filename,"wb");check(file!=nullptr,"workspace_output_opened");if(!file)return;
    host.fuel=budget().tail_reserve+1500+std::uint64_t(raw)*40;
    check(line>raw&&!c.flush_one(file)&&nnp_log::g_bytes==bytes,"flush_gates_text_bytes_not_raw_payload");
    host.fuel=budget().tail_reserve+1500+std::uint64_t(line)*40-1;
    check(!c.flush_one(file),"flush_refuses_one_fuel_below_boundary");
    ++host.fuel;c.logging(false);check(c.flush_one(file),"pending_rows_flush_after_recording_closes");std::fclose(file);
}
} // namespace

int main(int argc,char** argv){
    const std::string mode=argc>1?argv[1]:"warmup";
    if(mode=="warmup")warmup_checks();else if(mode=="budget")budgets();else if(mode=="cache")cache();
    else if(mode=="tickets")tickets();else if(mode=="ticket_integrity")ticket_integrity();
    else if(mode=="ack_integrity")ack_integrity();else if(mode=="sample_records")records(true);
    else if(mode=="argmax_records")records(false);else if(mode=="flush"&&argc>2)flush_boundary(argv[2]);else return 2;
    return failures?1:0;
}
