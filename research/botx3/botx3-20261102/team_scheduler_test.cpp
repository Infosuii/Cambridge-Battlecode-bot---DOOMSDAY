#include "team_scheduler.h"
#include <cassert>
#include <iostream>
using namespace team_scheduler;
int main() {
    std::array<Actor,workers> a{};
    for (int i=0;i<3;++i) a[i]={true,100,10,0,5,60,-1,-1};
    Job j[3];
    for (int k=0;k<3;++k) {j[k].id=k;j[k].gems=20;j[k].travel.fill(3);j[k].bank_distance=4;}
    auto r=assign(a,j,3);
    assert(r.target[0]!=r.target[1] && r.target[1]!=r.target[2] && r.target[0]!=r.target[2]);
    a[0].carried=60;r=assign(a,j,3);assert(r.target[0]==bank);
    a[0].carried=0;a[0].fixed=1;r=assign(a,j,3);
    assert(r.target[0]==1 && r.target[1]!=1 && r.target[2]!=1);
    a[0].fixed=-1;
    j[0].hp=40;j[0].soak=2000;j[0].gems=500;
    r=assign(a,j,1);
    assert(r.target[0]==0 && r.target[1]==0 && r.crew[0]==2);
    assert(r.target[2]==idle); // no gratuitous third clearer
    a[0].available=false;r=assign(a,j,3);assert(r.target[0]==idle);
    for (auto& actor:a)actor.available=false;
    r=assign(a,j,3);for (auto t:r.target)assert(t==idle);
    for (int i=0;i<3;++i)a[i]={true,100,10,0,5,60,-1,-1};
    j[0].hp=0;j[0].soak=0;j[0].travel.fill(unreachable);
    r=assign(a,j,1);for (auto t:r.target)assert(t==idle);
    j[0].travel.fill(1);j[0].risk=0;
    r=assign(a,j,1);for (auto t:r.target)assert(t==idle);
    j[0].risk=1;j[0].hp=0;
    r=assign(a,j,1);int count=0;for (auto t:r.target)count+=t==0;assert(count==1);
    for (int i=0;i<3;++i)a[i]={true,100,10,30,5+i*10,60,-1,-1};
    assert(bank_cohort(a,50)==3u); // earliest two deposits finish together
    assert(bank_cohort(a,100)==0u); // never invent unseen inventory
    a[0].available=false;assert(bank_cohort(a,50)==6u);
    a[1].fixed=0;assert(bank_cohort(a,50)==0u); // preserve an active capture
    assert(bank_cohort(a,0)==0u);
    std::cout<<"Team assignments: distinct jobs, bank, capture ownership, pooled crews, no overstaffing, unavailable, unreachable and risk checks passed\n";
}
