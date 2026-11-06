// Current-source exclusive graph state; every competing active writer must respect active.
#pragma once
#include "codex_owned_nn_frame.h"
#if !A2_NN_FAST || !A2_NN_LIVE || !A2_NN_LAZY || !A2_NN_NNUE || !A2_NN_Q16 || A2_NN_BEH || A2_NNREC
#error Unsupported neural configuration for exclusive graph ownership
#endif
#if defined(A2_NN_RL) || defined(A2_NN_RLIVE) || defined(A2_NN_STAY) || defined(A2_NN_FCMP) || defined(A2_NN_LAZYFULL) || defined(A2_NN_LAZY_CHOLD)
#error Additional live-graph consumers require an ownership audit
#endif
#if (defined(A2_NN_PIPE) && A2_NN_PIPE) || (defined(A2_NN_RLIN) && A2_NN_RLIN)
#error Additional inference pipeline requires an ownership audit
#endif
static_assert(kNF==500&&kC==10,"Re-audit a different feature/model layout");
static codex_owned::Frame<kNF> cxowned;
static bool cxowned_active=false,cxowned_model_set=false,cxowned_mode=false;
static std::size_t cxowned_groups=0;
static std::uint64_t cxowned_capture_cost=0,cxowned_publish_cost=4000+(kC+1)*sizeof(float);
static std::uint64_t cxowned_cost[5]={30000,12000,6000,12000,3000};
static constexpr std::uint64_t cxowned_floor[5]={30000,12000,6000,12000,3000};
#if CODEX_FINE
static std::uint32_t cxowned_hash=0;
#endif
static void cxowned_drop(){cxowned_active=false;cxowned.release();}
static void cxowned_reset(std::size_t n,bool bridges,int now,int ttl) {
    if(!cxowned_model_set||n!=cxowned_groups||bridges!=cxowned_mode) {
        cxowned_drop();cxowned_model_set=true;cxowned_groups=n;cxowned_mode=bridges;
        cxowned_capture_cost=12000+150*n+25*n*n+900*kC+2000+sizeof(cxowned.features);
        cxowned_publish_cost=4000+(kC+1)*sizeof(float);
        for(int i=0;i<5;++i)cxowned_cost[i]=cxowned_floor[i];
    }
    if(cxowned_active&&(now<cxowned.captured_at||now-cxowned.captured_at>ttl))cxowned_drop();
}
static bool cxowned_fits(std::uint64_t cost,std::uint64_t reserve) {
    const auto left=bc::fuel_remaining();return left>=reserve&&left-reserve>=cost;
}
static void cxowned_learn(std::uint64_t& bound,std::uint64_t used){bound=std::max(bound,used+used/8);}
static std::uint64_t cxowned_remaining() {
    std::uint64_t result=cxowned_active?0:cxowned_capture_cost;
    for(int i=cxowned_active?cxowned.stage:0;i<5;++i)result+=cxowned_cost[i];
    return result+cxowned_publish_cost;
}
