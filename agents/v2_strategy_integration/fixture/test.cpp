// Synthetic execution and geometry fixture. No engine, teacher, optimizer or match data.
#include "bot.h"
#include "nn_policy_options.h"
#include <cassert>
#include <cstring>
#include <iostream>
namespace nnp {vec2 canonical(const Bot& b,vec2 p) {return {b.flip_x?b.w.width-1-p.x:p.x,b.flip_y?b.w.height-1-p.y:p.y};}}
static void add(Bot& b,std::uint32_t handle,vec2 pos,int distance,int seen=-1) {
    const int ci=static_cast<int>(b.w.camps.size());b.w.camps.push_back({pos});
    GroupRec g;g.handle=handle;g.camps.push_back(ci);g.seen_round=seen;b.w.groups.push_back(g);
    b.w.distances.push_back(distance);b.w.camp_visible.push_back(1);
}
static bool has(const nnpc::Decision& d,std::uint32_t id) {for(int i=0;i<d.K;++i)if(d.id[i]==id)return d.legal[i];return false;}
static void view(Bot& b,vec2 p) {b.w.visible.value[static_cast<std::size_t>(p.y*64+p.x)]=true;}
int main() {
    Bot b;b.w.spawn_tiles.push_back({2,2});b.w.altars.push_back({8,8});
    add(b,0xf0000000u,{10,10},44);add(b,100,{40,10},20);add(b,3,{12,42},22);add(b,4,{42,42},10);
    add(b,999,{44,44},-1);add(b,998,{43,43},kUnreach);
    nnp::OptionsState s;nnpc::Decision d{};
    assert(nnp::build_objective(b,s,d)&&d.K==4);assert(has(d,0xf0000000u)&&!has(d,999)&&!has(d,998));
    assert(d.id[0]==3&&d.id[3]==0xf0000000u);assert(std::fabs(d.feat[7]-0.15f)<1e-6f);
    assert(nnp::execute_objective(b,s,0xf0000000u).executed&&s.objective==0&&b.published==0);
    const auto before=s;assert(!nnp::execute_objective(b,s,999).legal&&s.objective==before.objective);
    b.w.distances[0]=kUnreach;assert(!nnp::execute_objective(b,s,0xf0000000u).legal);b.w.distances[0]=44;
    assert(nnp::build_strategy(b,s,d)&&d.K==7&&has(d,0)&&has(d,1)&&has(d,2)&&has(d,3)&&!has(d,4)&&!has(d,5)&&has(d,6));
    assert(nnp::build_role(b,s,d)&&d.K==5&&has(d,0)&&has(d,1)&&!has(d,2)&&!has(d,3)&&has(d,4));
    assert(nnp::execute_role(b,s,1).executed&&s.role==1&&s.intent==1);
    b.gems=0;assert(!nnp::execute_role(b,s,1).legal);b.gems=50;
    b.w.allies.push_back({{33,32},100,20,2});view(b,{33,32});
    b.w.enemies.push_back({{34,32},100,30,3,1,2});view(b,{34,32});
    assert(nnp::build_role(b,s,d)&&has(d,2)&&has(d,3));
    assert(nnp::execute_role(b,s,2).executed&&s.intent==5&&s.goal.x==34);
    assert(nnp::execute_role(b,s,3).executed&&s.intent==4&&s.goal.x==33);
    assert(nnp::execute_strategy(b,s,6).executed&&s.intent==6&&s.objective==-1&&s.goal.x==2&&b.published==-1);
    assert(!nnp::execute_strategy(b,s,7).legal&&!nnp::execute_role(b,s,5).legal);
    b.w.enemies.clear();b.w.sightings.push_back({{50,50},39});assert(nnp::execute_strategy(b,s,5).executed);
    b.w.sightings[0].round=-100;assert(!nnp::execute_strategy(b,s,5).legal);
    b.hp=0;assert(!nnp::build_strategy(b,s,d)&&d.K==0&&!nnp::execute_role(b,s,0).legal);b.hp=50;
    // Quota diversity, deterministic tie ordering, and empty-quadrant spillover.
    Bot many;many.w.spawn_tiles.push_back({2,2});
    for(int q=0;q<4;++q)for(int j=0;j<6;++j)add(many,static_cast<std::uint32_t>(100*q+j+1),{q&1?40+j:10+j,q&2?40:10},5+j);
    s={};assert(nnp::build_objective(many,s,d)&&d.K==16);
    for(int q=0;q<4;++q)for(int j=0;j<6;++j)assert(has(d,100*q+j+1)==(j<4));
    nnpc::Decision normal=d;Bot mirrored=many;mirrored.flip_x=true;mirrored.pos.x=63-many.pos.x;
    for(auto& c:mirrored.w.camps)c.pos.x=63-c.pos.x;
    assert(nnp::build_objective(mirrored,s,d)&&d.K==normal.K);
    assert(std::memcmp(normal.id,d.id,d.K*sizeof(std::uint32_t))==0);
    assert(std::memcmp(normal.feat,d.feat,d.K*12*sizeof(float))==0);
    Bot one;for(int j=0;j<24;++j)add(one,static_cast<std::uint32_t>(j+1),{40,40},j);
    assert(nnp::build_objective(one,s,d)&&d.K==16&&has(d,16)&&!has(d,17));
    Bot scout;add(scout,11,{10,10},50,1);add(scout,12,{40,40},10,10);
    assert(nnp::execute_role(scout,s,4).executed&&s.objective==0&&s.intent==0);
    assert(nnp::execute_strategy(scout,s,6).legal==false); // no home endpoint advertised
    Bot huge;for(int j=0;j<127;++j)add(huge,static_cast<std::uint32_t>(j+1),{40,40},1);
    s={};assert(nnp::execute_objective(huge,s,127).executed&&s.objective==126&&huge.published==-1);
    // Transient whole-teacher fallback can alter local/shared assignments. Resume only the SAME option.
    Bot resumed;add(resumed,101,{10,10},20);add(resumed,102,{40,40},5);
    s={};assert(nnp::execute_objective(resumed,s,101).executed);
    resumed.target_group=1;resumed.write_claim(1);const int writes=resumed.claim_writes;
    const auto selected=s;assert(nnp::resume_assignments(resumed,s));
    assert(resumed.target_group==0&&resumed.published==0&&resumed.claim_writes==writes+1);
    assert(s.role==selected.role&&s.intent==selected.intent&&s.objective==selected.objective&&s.goal.x==selected.goal.x);
    assert(nnp::resume_assignments(resumed,s)&&resumed.claim_writes==writes+1); // no redundant write
    resumed.w.distances[0]=kUnreach;assert(!nnp::resume_assignments(resumed,s));
    assert(s.objective==0); // reachable group1 must not become an implicit replacement objective
    resumed.w.distances[0]=20;resumed.w.altars.push_back({8,8});
    assert(nnp::execute_role(resumed,s,1).executed&&s.intent==1&&s.objective==-1);
    assert(nnp::resume_assignments(resumed,s)); // bootstrap banking does not need a camp objective
    resumed.gems=0;assert(!nnp::resume_assignments(resumed,s)); // carrier availability changed
    std::cout<<"synthetic strategy SDK fixture passed\n";
}
