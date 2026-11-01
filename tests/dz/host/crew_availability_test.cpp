#include "crew_availability.h"
#include <cassert>
#include <iostream>
#include <limits>
using namespace dz::crew;
int main() {
    assert(assembly_deadline(100,60,70,40)==270); // Paid travel precedes agreement expiry.
    assert(assembly_deadline(1950,60,70,40)==2000);
    assert(assembly_deadline(100,65535,70,40)==-1);
    assert(available_after(150,50,1,1,5,36)==9);
    assert(available_after(150,50,4,1,5,36)==12);
    assert(available_after(150,50,4,1,5,11)==-1);
    assert(available_after(0,50,0,1,5,36)==6);
    assert(available_after(150,0,1,1,5,36)==-1);
    assert(available_after(std::numeric_limits<float>::quiet_NaN(),50,1,1,5,36)==-1);
    DeferredOffer offer;
    assert(offer.start(5,2,3,0,0,4,100,80)&&offer.deadline==180);
    assert(offer.current(150,1,5,true));
    assert(offer.start(5,2,3,0,0,4,150,80)&&offer.deadline==180);
    assert(!offer.start(5,2,3,0,0,4,181,80)&&offer.deadline==180);
    assert(!offer.current(181,1,5,true)&&!offer.current(150,2,5,true));
    assert(!offer.current(150,1,7,true)&&!offer.current(150,1,5,false));
    assert(!offer.start(5,5,3,0,0,4,100,80));
    assert(!offer.start(5,2,3,2,0,4,100,80));
    assert(!offer.start(5,2,3,0,6,4,100,80));
    // A different authorised roster is a different assembly, with a new bound.
    assert(offer.start(5,2,7,0,0,4,150,80)&&offer.deadline==230);
    for(int health=1;health<=400;++health)for(int damage=1;damage<=100;++damage) {
        int hits=0,left=health;while(left>0){left-=damage;++hits;}
        const int expected=hits+6;const int got=available_after(health,damage,1,1,5,36);
        assert(got==(expected<=36?expected:-1));
    }
    std::cout<<"40000 independent resource-release times; deferred ownership, expiry and non-sliding invitations passed\n";
}
