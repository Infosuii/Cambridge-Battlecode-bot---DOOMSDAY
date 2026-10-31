#include "crew_traffic.h"
#include <cassert>
#include <iostream>
using namespace dz;
int main() {
    const std::array<Tile,3> camps{{{10,12},{11,12},{12,12}}};
    const std::array<Tile,2> crew{{{8,10},{10,11}}};
    auto open=[&](Tile p){return p.x>=0&&p.y>=0&&p.x<31&&p.y<31&&
        std::find(camps.begin(),camps.end(),p)==camps.end()&&std::find(crew.begin(),crew.end(),p)==crew.end();};
    auto home=[](Tile p){return cheb(p,{1,1});};
    auto danger=[&](Tile p){float total=0;for(auto c:camps)if(cheb(p,c)<=1)total+=20;return total;};
    Tile p{9,11};unsigned moved=0;
    while(crew::clearance(p,camps)<=5&&moved<20) {
        const auto next=crew::yield_step(p,camps,5,open,home,danger);assert(next&&open(*next)&&cheb(p,*next)==1);
        assert(danger(*next)<=danger(p));
        assert(crew::clearance(*next,camps)>crew::clearance(p,camps)||home(*next)<home(p));
        p=*next;++moved;
    }
    assert(moved&&moved<20&&!crew::yield_step(p,camps,5,open,home,danger));
    assert(!crew::yield_step({9,11},camps,5,[](Tile){return false;},home,danger));
    assert(!crew::yield_step({9,11},camps,5,open,home,[](Tile){return std::numeric_limits<float>::quiet_NaN();}));
    unsigned checked=0;
    for(int x=4;x<18;++x)for(int y=6;y<20;++y) {
        const Tile from{x,y};if(!open(from))continue;
        const auto next=crew::yield_step(from,camps,5,open,home,danger);if(!next)continue;
        assert(cheb(from,*next)==1&&open(*next)&&danger(*next)<=danger(from));
        const int before=crew::clearance(from,camps),after=crew::clearance(*next,camps);
        assert(after>before||(after==before&&home(*next)<home(from)));++checked;
    }
    std::cout<<checked<<" bounded traffic steps; native jam geometry clears without occupied tiles or increased exposure; trapped/unknown rejection passed\n";
}
