#include "bank_model.h"
#include <cassert>
#include <iostream>
#include <random>
#include <vector>
using namespace dz;
// Independently consume the expiring shield once per camp phase.
float damage(const bank::Context& c,float raw,float exit) {
    float shield=c.shield,total=0;
    for(int phase=0;phase<=c.channel;++phase) {
        if(phase>=c.shield_rounds)shield=0;
        const float absorbed=std::min(shield,raw);shield-=absorbed;total+=raw-absorbed;
    }
    return total+1.25f*exit+.15f*c.max_hp;
}
void check(const bank::Context& c,std::span<const bank::Threat> threats,std::span<const bank::Root> roots,const bank::Plan& p) {
    if(!p.complete())return;
    std::vector<bool> removed(threats.size());float work=0,raw=0;
    for(unsigned k=0;k<p.count;++k){const auto i=p.cuts[k];assert(i<threats.size()&&!removed[i]);removed[i]=true;work+=threats[i].clear_time;}
    for(unsigned i=0;i<threats.size();++i)if(!removed[i]) {
        assert(threats[i].camp.p!=p.root);
        if(cheb(p.root,threats[i].camp.p)<=threats[i].camp.range)raw+=threats[i].camp.strength;
    }
    // Generated roots may share a tile but have different dated routes.
    const auto root=std::find_if(roots.begin(),roots.end(),[&](auto r) {
        return r.tile==p.root&&r.distance==p.travel&&(raw==0||r.escape.found)&&
            c.hp>(raw==0?0:damage(c,raw,r.escape.damage))&&
            work+r.distance+c.channel+1<=std::min(c.horizon,r.until);
    });assert(root!=roots.end());
    assert((p.count==0)==(p.quality==bank::Quality::Bounded));
    assert((p.quality==bank::Quality::Cuts||root->required==0));
    for(unsigned i=0;i<threats.size();++i)if(root->required&(std::uint64_t{1}<<i))assert(removed[i]);
}
int main() {
    std::mt19937 rng(108);unsigned checked=0;
    for(unsigned i=0;i<2000;++i) {
        bank::Context c{1000,1000,float(rng()%2000),int(rng()%30),int(rng()%40),2000};
        const float raw=rng()%150,exit=rng()%500;
        assert(std::abs(bank::channel_loss(c,raw,exit)-damage(c,raw,exit))<.01f);
    }
    bank::Context c{1000,1000,0,0,30,2000};
    std::array roots{bank::Root{{0,0},10,{{0,5},100,5,true},2000}};
    auto p=bank::choose(c,{},roots);assert(p.quality==bank::Quality::Bounded&&p.count==0);
    std::array threats{bank::Threat{0,0,{{-2,0},100,4},10},bank::Threat{1,0,{{2,0},100,4},20}};
    p=bank::choose(c,threats,roots);assert(p.quality==bank::Quality::Cuts&&p.count==2);check(c,threats,roots,p);
    c.channel=1;p=bank::choose(c,threats,roots);assert(p.quality==bank::Quality::Bounded);check(c,threats,roots,p);
    roots[0].escape.found=false;p=bank::choose(c,threats,roots);assert(p.count==2);check(c,threats,roots,p);
    // A sleeping camp does not deal damage, but still occupies a future root.
    std::array sleeping{bank::Threat{3,0,{{0,0},0,0},5}};
    p=bank::choose(c,sleeping,roots);assert(p.count==1);check(c,sleeping,roots,p);
    roots[0].until=1;assert(!bank::choose(c,{},roots).complete());roots[0].until=2000;
    c.horizon=10;assert(!bank::choose(c,{},roots).complete());c.horizon=2000;
    c.channel=30;std::array<bank::Threat,9> crowded{};
    for(unsigned i=0;i<crowded.size();++i)crowded[i]={int(i),0,{{2,0},200,4},1};
    assert(!bank::choose(c,crowded,roots).complete()); // Nine required cuts cannot publish eight.
    for(unsigned trial=0;trial<2000;++trial) {
        std::array<bank::Threat,6> scene{};
        for(unsigned i=0;i<scene.size();++i)scene[i]={int(i),0,{{int(rng()%11)-5,int(rng()%11)-5},float(rng()%120),int(rng()%5)},float(1+rng()%30)};
        std::array<bank::Root,4> candidates{};
        for(auto& r:candidates)r={{int(rng()%7)-3,int(rng()%7)-3},int(rng()%30),{{10,10},float(rng()%300),5,bool(rng()%2)},int(20+rng()%500)};
        c.channel=rng()%40;c.shield=rng()%1000;c.shield_rounds=rng()%20;
        p=bank::choose(c,scene,candidates);check(c,scene,candidates,p);checked+=p.complete();
        int fuel=1+rng()%20;
        p=bank::choose(c,scene,candidates,[&]{return --fuel>=0;});check(c,scene,candidates,p);checked+=p.complete();
    }
    c.hp=0;assert(bank::choose(c,{},roots).quality==bank::Quality::Invalid);
    c.hp=1000;threats[0].clear_time=-1;assert(bank::choose(c,threats,roots).quality==bank::Quality::Invalid);
    // A wall pocket needs its root Golem and a blocking cluster cleared. The
    // opposite Golem may remain alive: the paid exit still leaves enough HP.
    std::array pocket{bank::Threat{0,0,{{14,15},120,4},100},bank::Threat{1,0,{{16,15},120,4},100},bank::Threat{2,0,{{12,15},0,0},2}};
    std::array<bank::Root,9> exits{};
    const auto n=bank::escape_roots({14,15},10,2000,pocket,exits,[](Tile p,int){return p.y==15&&p.x<=14&&p.x>=0;});
    assert(n>=2);c={1000,1000,0,0,3,2000};p=bank::choose(c,pocket,std::span(exits.data(),n));
    assert(p.complete()&&p.count==2&&p.work==102);check(c,pocket,std::span(exits.data(),n),p);
    assert(std::find(p.cuts.begin(),p.cuts.begin()+p.count,1u)==p.cuts.begin()+p.count);
    // A truncated ray never publishes its unfinished occupancy requirements.
    int ray_budget=1;const auto capped=bank::escape_roots({14,15},10,2000,pocket,exits,[](Tile,int){return true;},[&]{return --ray_budget>=0;});
    assert(capped==1&&!exits[0].escape.found);
    std::cout<<"bank_model_test: 2000 independent shield schedules; "<<checked<<" complete/capped feasible plans checked\n";
}
