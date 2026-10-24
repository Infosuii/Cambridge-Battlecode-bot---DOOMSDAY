// Pure direct-policy admission, snapshot cache, inference and execution accounting. No SDK.
#pragma once
#include "nn_policy_candidates.h"
#include "nn_policy_model.h"
#include "nn_policy_observation.h"
#include "nn_policy_log.h"

namespace nnp {
enum class Reason : std::uint16_t {
    ok=0, unverified=1, budget=2, invalid_candidates=3, capture=4, nonfinite=5,
    stale_ticket=6, wrong_model=7, execution_guard=8, action_failed=9, interrupted=10
};
// PROVISIONAL estimates, deliberately separate from legacy residual-v1 budgets. Engine calibration pending.
struct Budget {
    std::uint32_t turn_allowance=65000, action_reserve=20000, tail_reserve=8000;
    std::uint32_t observation=12000, candidate=3500, head_base=1500, per_candidate=850, log=6000;
};
struct Hooks {
    std::uint64_t (*fuel)()=nullptr;
    bool (*capture)(void*,float*)=nullptr;
    void* userdata=nullptr;
};
struct Ticket {
    nncfg::H head=nncfg::H::count;
    int max_k=0;
    std::uint32_t snapshot=0,turn=0;
    std::uint64_t id=0,start=0;
    bool admitted=false;
};
struct Result {
    int choice=-1;
    std::uint32_t action=nnp_log::kNoAction;
    Reason reason=Reason::unverified;
    nnp_log::Header header{};
    bool sampled=false,recorded=false;
    float logp=0;
    std::uint64_t option_id=0;
    std::uint8_t source=nnp_log::kDirectPolicy;
};
struct Counters {
    std::uint32_t attempted[9]{}, admitted[9]{}, chosen[9]{}, refused[9]{}, executed[9]{};
    std::uint32_t contexts=0, invalid=0, acknowledgements=0, missing_ack=0;
};

class Core {
    const nnpm::PolicyDesc* model_=nullptr;
    Hooks hooks_{}; Budget budget_{};
    bool logging_=false,sampling_=false,ready_=false,bad_=false,encoded_=false,context_logged_=false;
    std::uint32_t round_=0,champion_=0,snapshot_=0,turn_=0;
    std::uint64_t serial_=0,used_=0;
    nnrt::SplitMix64 random_{0};
    float observation_[nnpobs::kObsDim]{},h_[nnm::kMaxCtx]{};
    nnm::Scratch scratch_{};
    nnm::SegState verify_[10]{};
    Ticket pending_{};
    Result selected_{};
    bool unacknowledged_=false;
    nnp_log::Header header(std::uint64_t id) const {
        return {nnpobs::kObsSchemaHash,nnpc::kActionSchemaHash,static_cast<std::int32_t>(round_),champion_,snapshot_,id};
    }
    std::uint64_t spent(std::uint64_t start) const { auto now=fuel();return start>now?start-now:0; }
    void charge(std::uint64_t start) {used_+=spent(start);}
    std::uint64_t estimate(int k) const {
        return budget_.candidate+budget_.head_base+std::uint64_t(k)*budget_.per_candidate+
               (encoded_?0:budget_.observation)+(logging_?budget_.log:0);
    }
    bool affordable(int k) const {
        const auto cost=estimate(k);
        return fuel()>=cost+budget_.action_reserve+budget_.tail_reserve && cost<=budget_.turn_allowance &&
               used_<=budget_.turn_allowance-cost;
    }
    // Normalized snapshots still require strict masks/padding before any inference or context record.
    static bool valid_observation(const float* x) {
        if(!nnrt::all_finite(x,nnpobs::kObsDim))return false;
        for(int j=0;j<nnpobs::kObsDim;++j)if(x[j]<-4||x[j]>4)return false;
        for(int i=0;i<5;++i){const auto m=x[90+i];if(m!=0&&m!=1)return false;
            if(!m)for(int j=0;j<10;++j)if(x[40+10*i+j]!=0)return false;}
        for(int i=0;i<6;++i){const auto m=x[167+i];if(m!=0&&m!=1)return false;
            if(!m)for(int j=0;j<12;++j)if(x[95+12*i+j]!=0)return false;}
        return true;
    }
    bool context(std::uint32_t& cost) {
        if(encoded_){cost=0;return true;}
        const auto start=fuel();
        if(!hooks_.capture||!hooks_.capture(hooks_.userdata,observation_)||!valid_observation(observation_))return false;
        nnm::encode(*model_->kernel,observation_,h_,scratch_);
        if(!nnrt::all_finite(h_,model_->kernel->ctx))return false;
        cost=static_cast<std::uint32_t>(spent(start));encoded_=true;++counters.contexts;
        return true;
    }
    static bool valid(const nnpc::Decision& d) {
        if(!nnpc::supported(d.head)||d.K<1||d.K>16||d.F!=12||d.context>3||
           !nnrt::all_finite(d.feat,d.K*12))return false;
        bool any=false;
        for(int i=0;i<d.K;++i){if(d.legal[i]>1||d.id[i]==nnp_log::kNoAction||(i&&d.id[i-1]>=d.id[i]))return false;
            any|=d.legal[i]!=0;}
        return any;
    }
    Result failure(const Ticket& t,Reason why) {
        Result r;r.reason=why;r.header=header(t.id);r.source=nnp_log::kTeacherFallback;
        if(logging_&&t.id){nnp_log::DecisionRec d;d.h=r.header;d.head=static_cast<std::uint16_t>(t.head);
            d.source=r.source;d.reason=static_cast<std::uint16_t>(why);r.recorded=nnp_log::enqueue_decision(d);}
        return r;
    }
public:
    Counters counters{};
    Core()=default;
    void configure(const nnpm::PolicyDesc& model,Hooks hooks,Budget budget={},bool logging=false,
                   bool sampling=false,std::uint64_t seed=0) {
        // Configuration happens once before decisions. Explicit reset prevents reuse of a verified old blob.
        *this=Core{};model_=&model;hooks_=hooks;budget_=budget;logging_=logging;sampling_=sampling;random_.s=seed;
        bad_=!hooks.fuel||!nnpm::desc_ok(model,nnpobs::kObsSchemaHash,nnpc::kActionSchemaHash,nnpc::kHeadActionHash)||
             nnm::obs_dim(*model.kernel)!=nnpobs::kObsDim;
    }
    std::uint64_t fuel() const {return hooks_.fuel?hooks_.fuel():0;}
    bool ready() const {return ready_&&!bad_;}
    bool bad() const {return bad_;}
    std::uint64_t used() const {return used_;}
    // Resumable checks include the whole blob AND each segment. Only call after teacher decisions.
    bool warmup(std::uint32_t float_budget=256) {
        if(bad_||!model_)return false;
        const auto& m=*model_->kernel;
        for(int i=0;i<10&&float_budget;++i){
            const nnm::Seg seg=i==0?nnm::Seg{0,m.n_params,m.checksum}:i==1?m.enc:m.head[i-1].seg;
            if(verify_[i].state==2){bad_=true;return false;}
            if(verify_[i].state==1)continue;
            auto left=seg.end-(verify_[i].started?verify_[i].pos:seg.begin);
            const auto n=left<float_budget?left:float_budget;
            if(nnm::verify_step(m.blob,seg,verify_[i],n)==2){bad_=true;return false;}
            float_budget-=n;
        }
        ready_=true;for(const auto& v:verify_)ready_&=v.state==1;
        return ready_;
    }
    void begin_turn(std::uint32_t round,std::uint32_t champion) {
        if(unacknowledged_){++counters.missing_ack;unacknowledged_=false;}
        round_=round;champion_=champion;++turn_;used_=0;pending_={};invalidate();
    }
    // Caller must refresh visible/self state before the next capture after an executed action.
    void invalidate() {
        if(pending_.admitted){charge(pending_.start);pending_={};}
        ++snapshot_;encoded_=context_logged_=false;
    }
    Ticket admit(nncfg::H head,int max_k) {
        Ticket t;t.head=head;t.max_k=max_k;t.turn=turn_;t.snapshot=snapshot_;
        if(!nnpc::supported(head)||max_k<1||max_k>16){++counters.invalid;return t;}
        auto hi=static_cast<int>(head);++counters.attempted[hi];
        if(pending_.admitted||unacknowledged_||!ready()||!affordable(max_k)){++counters.refused[hi];return t;}
        t.id=++serial_;t.start=fuel();t.admitted=true;pending_=t;++counters.admitted[hi];return t;
    }
    Result decide(const Ticket& t,const nnpc::Decision& d,std::uint64_t option_id=0,std::uint8_t flags=0) {
        if(!t.admitted||t.id!=pending_.id||t.turn!=turn_||t.snapshot!=snapshot_||!pending_.admitted||
           t.head!=pending_.head||t.max_k!=pending_.max_k||t.start!=pending_.start||
           t.snapshot!=pending_.snapshot||t.turn!=pending_.turn)
        {
            Result stale;stale.reason=Reason::stale_ticket;stale.header=header(t.id);
            stale.source=nnp_log::kTeacherFallback;return stale; // Never emit a duplicate call ID for a replayed ticket.
        }
        pending_={};
        if(!valid(d)||d.head!=t.head||d.K>t.max_k||(flags&&(!option_id||flags>7))){charge(t.start);return failure(t,Reason::invalid_candidates);}
        // Candidate construction already spent real fuel; recheck the remaining estimate before encoding.
        charge(t.start);
        if(!affordable(d.K))return failure(t,Reason::budget);
        const auto start=fuel();std::uint32_t obs_cost=0;
        if(!context(obs_cost)){charge(start);return failure(t,Reason::capture);}
        float logits[16];const auto infer_start=fuel();
        nnpm::direct_logits(*model_,static_cast<int>(d.head),d.context,h_,d.feat,d.K,d.legal,logits);
        for(int i=0;i<d.K;++i)if(d.legal[i]&&!nnrt::is_finite(logits[i])){charge(start);return failure(t,Reason::nonfinite);}
        Result r;r.header=header(t.id);r.reason=Reason::ok;r.option_id=option_id;r.sampled=sampling_;
        r.choice=sampling_?nnrt::masked_sample(logits,d.legal,d.K,random_.uniform(),&r.logp):
                          nnrt::masked_argmax(logits,d.legal,d.K);
        if(r.choice<0){charge(start);return failure(t,Reason::invalid_candidates);}
        // Argmax is deterministic behavior, with probability one. Sampling records the true categorical logp.
        if(!sampling_)r.logp=0;
        r.action=d.id[r.choice];
        const auto infer_cost=static_cast<std::uint32_t>(spent(infer_start));
        if(logging_){
            if(!context_logged_)context_logged_=nnp_log::enqueue_context({header(0),observation_,sizeof(observation_)});
            nnp_log::DecisionRec rec;rec.h=r.header;rec.head=static_cast<std::uint16_t>(d.head);rec.K=d.K;
            rec.chosen=r.choice;rec.context=d.context;rec.sampled=r.sampled;rec.logp=r.logp;
            rec.flags=flags;rec.option_id=option_id;rec.selected_id=r.action;
            rec.fuel.candidate=static_cast<std::uint32_t>(t.start>start?t.start-start:0);
            rec.fuel.observation=obs_cost;rec.fuel.inference=infer_cost;
            rec.id=d.id;rec.legal=d.legal;rec.feat=d.feat;rec.logits=logits;
            // A dropped context makes this decision deliberately unusable for training (dataset rejects it).
            r.recorded=nnp_log::enqueue_decision(rec);
        }
        charge(start);++counters.chosen[static_cast<int>(d.head)];
        pending_=t;pending_.admitted=false;selected_=r;unacknowledged_=true;return r;
    }
    // No execution is inferred from selection. The SDK caller must acknowledge the exact observed outcome.
    bool acknowledge(const Result& r,std::uint32_t actual,nnp_log::Outcome outcome,
                     std::uint32_t action_fuel=0,Reason reason=Reason::ok) {
        if(!unacknowledged_||r.header.decision_id!=pending_.id||r.header.snapshot!=pending_.snapshot||
           r.header.obs_hash!=selected_.header.obs_hash||r.header.action_hash!=selected_.header.action_hash||
           r.header.champion!=selected_.header.champion||r.header.round!=selected_.header.round||
           r.action!=selected_.action||r.option_id!=selected_.option_id||r.source!=selected_.source||
           outcome==nnp_log::kPending||outcome>nnp_log::kFailed){++counters.invalid;return false;}
        if((outcome==nnp_log::kExecuted||outcome==nnp_log::kOptionExecuted)&&actual!=r.action){++counters.invalid;return false;}
        nnp_log::ExecutionRec rec;rec.h=r.header;rec.executed_id=actual;rec.outcome=outcome;
        rec.source=outcome==nnp_log::kOverridden?nnp_log::kSafetyOverride:r.source;
        rec.reason=static_cast<std::uint16_t>(reason);rec.option_id=r.option_id;rec.action_fuel=action_fuel;
        if(logging_)nnp_log::enqueue_execution(rec);
        if(outcome==nnp_log::kExecuted||outcome==nnp_log::kOptionExecuted)++counters.executed[static_cast<int>(pending_.head)];
        ++counters.acknowledgements;unacknowledged_=false;pending_={};return true;
    }
    // Flush only after gameplay; charge textual base64 bytes (larger than the raw record).
    bool flush_one(std::FILE* out=stdout,std::uint32_t fixed=1500,std::uint32_t per_byte=40) {
        if(!logging_||nnp_log::queue_empty())return false;
        const auto line=nnp_log::next_line_bytes();
        if(fuel()<budget_.tail_reserve+fixed+std::uint64_t(line)*per_byte)return false;
        return nnp_log::flush_one(out);
    }
};
} // namespace nnp
