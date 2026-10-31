#include "protocol.h"
#include <cassert>
#include <iostream>
using namespace dz::protocol;
int main() {
    unsigned cases=0;
    for(unsigned round=0;round<=2000;round+=7)for(unsigned mask=1;mask<64;++mask)for(unsigned cap=0;cap<6;++cap)if(mask&(1u<<cap)) {
        std::uint64_t word=0;
        for(unsigned slot=0;slot<6;++slot)word=compact::with_slot(word,slot,{static_cast<std::uint8_t>(slot+10),false});
        const auto leased=compact::with_lease(word,mask,cap,round);
        const auto plan=compact::lease(leased,round);
        assert(plan.valid&&plan.members==mask&&plan.capturer==cap&&plan.round==round);
        assert(compact::lease(leased,round+3).valid==(round+3<=2047));
        assert(!compact::lease(leased,round+4).valid);
        assert(!compact::lease(leased,round+512).valid);
        assert(!compact::lease(leased,round+2048).valid);
        if(round>0)assert(!compact::lease(leased,round-1).valid);
        for(unsigned slot=0;slot<6;++slot)assert(compact::slot(leased,slot).objective==slot+10);
        auto changed=compact::with_slot(leased,plan.leader,{retreat,false});assert(!compact::lease(changed,round).valid);
        assert(!compact::lease(compact::with_lease(leased,0,0,round,false),round).valid);
        ++cases;
    }
    assert(!compact::lease(compact::with_lease(0,1,0,2048),2048).valid);
    std::cout<<cases<<" compact crew-lease preservation/freshness cases passed\n";
}
