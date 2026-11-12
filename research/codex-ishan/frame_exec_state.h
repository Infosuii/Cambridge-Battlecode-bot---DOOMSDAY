// State and conservative admission costs for one pure optional inference frame.
#pragma once
#include "codex_coherent_nn_frame.h"
static codex_frame2::Frame<kNF> cxframe;
static bool cxframe_pending=false,cxframe_mode=false,cxframe_model_set=false;
static std::size_t cxframe_groups=0;
static std::uint64_t cxframe_capture_cost=0,cxframe_publish_cost=0;
static std::uint64_t cxframe_cost[5]={30000,12000,6000,12000,3000};
static constexpr std::uint64_t cxframe_floor[5]={30000,12000,6000,12000,3000};
#if CODEX_FINE
static std::uint32_t cxframe_hash=0;
#endif
static std::uint64_t cxframe_copy_bound(std::size_t n) {
    return 2000+2*(sizeof(cxframe)+n*sizeof(nn::CampCache));
}
static void cxframe_reset(std::size_t n,bool bridges) {
    if(cxframe_model_set&&n==cxframe_groups&&bridges==cxframe_mode)return;
    cxframe_model_set=true;cxframe_groups=n;cxframe_mode=bridges;cxframe_pending=false;
    cxframe_capture_cost=12000+150*n+25*n*n+900*kC+cxframe_copy_bound(n);
    cxframe_publish_cost=4000+n*sizeof(nn::CampCache)+sizeof(nn_lv.sc)+sizeof(nn_lo.target);
    for(int i=0;i<5;++i)cxframe_cost[i]=cxframe_floor[i];
}
static std::uint64_t cxframe_remaining() {
    std::uint64_t n=cxframe_pending?0:cxframe_capture_cost;
    for(int i=cxframe_pending?cxframe.stage:0;i<5;++i)n+=cxframe_cost[i];
    return n+cxframe_publish_cost;
}
static bool cxframe_fits(std::uint64_t cost,std::uint64_t reserve) {
    const auto left=bc::fuel_remaining();return left>=reserve&&left-reserve>=cost;
}
static void cxframe_learn(std::uint64_t& bound,std::uint64_t used) {
    bound=std::max(bound,used+used/8);
}
