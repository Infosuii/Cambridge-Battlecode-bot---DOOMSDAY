#include "bank_commit.h"
#include "team_scheduler.h"
#include <cassert>
#include <iostream>
int main() {
    bank_delivery::Commitment c;
    assert(!c.active(100,20,false,false));
    assert(!c.begin(100,-1,20));assert(!c.begin(100,10,0));
    assert(c.begin(100,10,20));const int end=c.until;
    assert(end==132 && c.active(101,20,false,false));
    assert(c.begin(110,20,20) && c.until==end); // failed steps never renew a deadline
    assert(c.active(end,1,false,false));assert(!c.active(end+1,1,false,false));
    assert(c.begin(200,10,20));assert(!c.active(201,0,false,false)); // deposit/death clears
    assert(c.begin(200,10,20));assert(!c.active(201,20,true,false)); // blocked bank
    assert(c.begin(200,10,20));assert(!c.active(201,20,false,true)); // native stuck cooldown
    std::array<team_scheduler::Actor,team_scheduler::workers> actors{};
    actors[0]={true,100,10,10,5,60,-1,-1,true}; // small bag, existing delivery commitment
    actors[1]={true,100,10,0,5,60,-1,-1,false};
    team_scheduler::Job j;j.id=0;j.gems=100;j.travel.fill(1);j.bank_distance=1;
    auto result=team_scheduler::assign(actors,&j,1);
    assert(result.target[0]==team_scheduler::bank && result.target[1]==0);
    actors[0].fixed=0;result=team_scheduler::assign(actors,&j,1);
    assert(result.target[0]==0); // actual capture ownership still takes priority
    std::cout<<"Bank delivery: finite lease, non-renewal, completion/death, blocked/cooldown and teammate reservation passed\n";
}
