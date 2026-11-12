#include "synthetic_shim.h"
#include "economy_under_test.cpp"
#include <iostream>
using namespace cambc::detail;
int row(const nnpc::Decision& d,unsigned id) { for(int i=0;i<d.K;++i)if(d.id[i]==id)return i;return -1; }
float feat(const nnpc::Decision& d,unsigned id,int j) { const int r=row(d,id);assert(r>=0);return d.feat[r*12+j]; }
void close(float actual,float expected) { assert(std::abs(actual-expected)<1e-5); }
int main() {
    Bot b;nnp::OptionsState state;nnpc::Decision decision{};
    assert(nnp::build_shop(b,state,decision));assert(decision.K==16);assert(row(decision,0)==0);
    for(int f=0;f<7;++f)assert(row(decision,1+f*6)>=0);
    assert(row(decision,1000)>=0&&row(decision,1002)>=0&&row(decision,1001)<0&&row(decision,2)<0);
    close(feat(decision,0,3),.1f);close(feat(decision,1002,11),.2f);
    for(int i=1;i<decision.K;++i)assert(decision.id[i]>decision.id[i-1]);
    counts[6]=4;assert(nnp::build_shop(b,state,decision));close(feat(decision,7,6),.2f);counts[6]=0;
    consumables[2]=1;consumables[1]=999;assert(nnp::build_shop(b,state,decision));assert(row(decision,1002)<0&&row(decision,1000)>=0);
    assert(!nnp::execute_shop(b,state,1002).executed);consumables[2]=0;
    auto result=nnp::execute_shop(b,state,1002);assert(result.executed&&last_consumable==2&&b.refreshed==1);
    const int before=buy_calls;assert(!nnp::execute_shop(b,state,1001).executed&&buy_calls==before);
    assert(!nnp::execute_shop(b,state,2).executed);gold=0;assert(!nnp::execute_shop(b,state,1).executed);
    assert(nnp::execute_shop(b,state,0).executed);gold=100;buy_error=1;assert(!nnp::execute_shop(b,state,1).executed);buy_error=0;
    me.state=0;assert(nnp::build_shop(b,state,decision));assert(nnp::execute_shop(b,state,1).executed);me.state=1;
    b.refresh_error=true;assert(nnp::execute_shop(b,state,1).executed);b.refresh_error=false; // successful buy stays acknowledged if follow-up state read fails
    b.w.altars={{4,2},{12,2}};
    for(int y=0;y<32;++y)if(y!=20)sdk_Bitboard_Set(b.w.static_blocked.data,8,y,1);
    const int before_bound=fields;const auto cold_bound=nnp::bank_candidate_fuel(b);assert(fields==before_bound);
    assert(nnp::build_bank(b,state,decision));assert(decision.K==3);
    assert(last_cap==64&&nnp::bank_candidate_fuel(b)<cold_bound);
    close(feat(decision,1,3),1.f/50);assert(feat(decision,3,3)>.5f); // same field, different per-altar distances
    const int fields_before=fields;result=nnp::execute_bank(b,state,3);assert(result.executed&&result.changed&&state.altar==1&&fields==fields_before);
    assert(cheb(state.goal,b.w.altars[1])<=1);assert(!nnp::execute_bank(b,state,99999).executed);
    nnp::flip=true;assert(nnp::build_bank(b,state,decision));assert(feat(decision,1,1)<0);nnp::flip=false;
    ++b.round;sdk_Bitboard_Set(b.w.static_blocked.data,8,20,1);assert(nnp::build_bank(b,state,decision));assert(row(decision,3)<0);
    ++b.round;me.x=3;b.pos={3,2};lock=1;assert(nnp::build_bank(b,state,decision));assert(row(decision,2)<0);assert(!nnp::execute_bank(b,state,2).executed);
    lock=0;assert(nnp::build_bank(b,state,decision));assert(row(decision,2)>=0);submit_error=1;assert(!nnp::execute_bank(b,state,2).executed);
    submit_error=0;assert(nnp::execute_bank(b,state,2).executed);assert(!nnp::execute_bank(b,state,2).executed);me.state=1;
    lock=-1;assert(nnp::build_bank(b,state,decision));close(feat(decision,2,11),-1);lock=0;
    gems=0;assert(nnp::build_bank(b,state,decision));assert(decision.K==1&&row(decision,0)==0);gems=20;
    meta.field_bytes=999999;assert(!nnp::build_bank(b,state,decision)&&decision.K==0);meta.field_bytes=2048;
    // >16 public altars: keep far canonical quadrants even when nearby alternatives dominate.
    b=Bot{};++b.round;me.x=16;me.y=16;b.pos={16,16};b.my_id=2;
    for(int i=0;i<16;++i)b.w.altars.push_back({18+i%7,17+i/7});
    b.w.altars.push_back({1,1});b.w.altars.push_back({1,30});b.w.altars.push_back({30,1});
    assert(nnp::build_bank(b,state,decision));assert(decision.K==16);
    assert(row(decision,1+2*16)>=0&&row(decision,1+2*17)>=0&&row(decision,1+2*18)>=0);
    for(int i=1;i<decision.K;++i)assert(decision.id[i]>decision.id[i-1]);
    // Synthetic serpentine corridor has diameter>64 despite its32x32 bounding box.
    b=Bot{};b.my_id=3;me.x=1;me.y=1;b.pos={1,1};
    for(int y=0;y<32;++y)for(int x=0;x<32;++x)sdk_Bitboard_Set(b.w.static_blocked.data,x,y,1);
    for(int y:{1,4,7})for(int x=1;x<=30;++x)sdk_Bitboard_Set(b.w.static_blocked.data,x,y,0);
    for(int y:{2,3})sdk_Bitboard_Set(b.w.static_blocked.data,30,y,0);
    for(int y:{5,6})sdk_Bitboard_Set(b.w.static_blocked.data,1,y,0);
    b.w.altars={{4,1},{30,7}};
    assert(!nnp::build_bank(b,state,decision)&&decision.K==0&&g_bank.expansions==64); // whole refusal, no truncated option set
    b.w.altars.pop_back();assert(nnp::build_bank(b,state,decision)&&g_bank.expansions==64); // every altar proven reached despite cap
    assert(row(decision,1)>=0);const int before_stale=fields;me.x=2;assert(!nnp::build_bank(b,state,decision)&&decision.K==0&&fields==before_stale);
    assert(!nnp::execute_bank(b,state,1).executed&&fields==before_stale); // no cold search in execution reserve
    std::cout<<"synthetic economy: candidate narrowing, per-altar maze distances, masks, raw ABI slots, combinations and execution checks passed\n";
}
