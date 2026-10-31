#include "macro_value.h"
#include <array>
#include <cassert>
#include <iostream>
using namespace dz::macro;
int main() {
    Context c{100,40,1,.25f};
    std::array<Option,3> q{{
        {Kind::Farm,0,10,10,20,40,0,0,true},
        {Kind::Bank,0,10,0,0,0,0,0,true},
        {Kind::Shop,-1,20,10,0,0,25,0,true}
    }};
    // Explicit schedules, all ending with a deposited bag and a common stream:
    // farm: 60 deposited + 10 gold GE + 80 continuation; bank: 40 + 90;
    // shop: 40 + 25 equipment GE + 70 continuation. The bag counts once each.
    assert(value(c,q[0])==150&&value(c,q[1])==130&&value(c,q[2])==135);
    assert(choose(c,q)==0);
    c.bag+=100;assert(value(c,q[0])==250&&value(c,q[1])==230&&value(c,q[2])==235);
    c.bag=40;c.horizon=15;
    assert(value(c,q[0])==10); // Capture gold exists; no time to deliver gems.
    assert(choose(c,q)==1); // Shop cannot finish at all.
    c.horizon=100;q[2].equipment=50;assert(choose(c,q)==2);
    q[2].work=70;assert(choose(c,q)==0); // A valuable item can cost too much travel.
    q[2].work=20;q[2].equipment=25;q[0].risk_cost=30;assert(choose(c,q)==2);
    q[0].risk_cost=0;q[0].delivery=-1;
    assert(value(c,q[0])==10); // Unknown access grants neither gems nor hypothetical future income.
    q[0].delivery=10;
    q[2].equipment=40.5f; // Score150.5 versus150; one real switching round preserves incumbent.
    assert(choose(c,q,0)==0&&choose(c,q,-1,0)==2);
    for(auto& item:q)item.feasible=false;
    assert(choose(c,q)==-1);
    q[0].feasible=true;q[0].delivery=-2;assert(choose(c,q)==-1);
    q[0].delivery=0;q[0].gems=std::numeric_limits<float>::quiet_NaN();assert(choose(c,q)==-1);
    q[0].gems=10;c.income=std::numeric_limits<float>::infinity();assert(choose(c,q)==-1);
    c.income=1e38f;assert(choose(c,q)==-1); // Overflow never wins the ordering.
    std::cout<<"Macro itinerary accounting, horizon, switching, risk, access and invalid-input checks passed\n";
}
