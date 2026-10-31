#include "team_protocol.h"
#include <cassert>
#include <iostream>
#include <random>
using namespace dz;
int main() {
    std::mt19937 rng(681);unsigned cases=0;
    constexpr std::uint64_t claims=(std::uint64_t{1}<<42)-1;
    for(unsigned count=1;count<=6;++count)for(unsigned round=0;round<=2000;round+=2) {
        const unsigned slot=team::publisher(round,count),gold=rng()%10000,task=rng()%112;
        const auto intent=static_cast<team::Intent>(rng()%4);const auto low=std::uint64_t(rng())&claims;
        const auto word=team::publish(low,round,count,slot,gold,task,intent);
        const auto f=team::decode(word,round+1,count);
        assert(f.valid&&f.slot==slot&&f.round==round&&(word&claims)==low);
        assert(!protocol::compact::lease(word,round).valid&&protocol::compact::lease(word,round).leader==6);
        assert(!team::decode(word,round-1,count).valid); // Unsigned underflow also rejects before round zero.
        if(round+team::lifetime(count)+1<=2047)assert(!team::decode(word,round+team::lifetime(count)+1,count).valid);
        team::Ledger l;l.observe(word,round,count);
        if(f.kind==team::Kind::Cash) {
            const auto cash=l.budget(slot,round,count);assert(cash.valid&&cash.low<=gold&&gold<=cash.high);
        } else {
            const auto p=l.project(slot,round,count);assert(p.valid&&p.task==task&&p.intent==intent);
            const bool busy=intent==team::Intent::Active||intent==team::Intent::Recover;
            assert((l.reservation(slot,task,round,count)>=0)==busy);
            assert(l.reservation(slot,protocol::idle,round,count)<0);
        }
        const auto lease_source=protocol::compact::with_slot(word,0,{9,false});
        const auto lease=protocol::compact::with_lease(lease_source,3,0,round);
        assert(protocol::compact::lease(lease,round).valid&&!team::decode(lease,round,count).valid);
        assert(team::publish(lease,round,count,slot,gold,task,intent)==lease);
        ++cases;
    }
    // Arbitrary actor turn order, including changes on every round. Every record
    // is held over the odd round; all observers receive both kinds per cycle.
    for(unsigned count=1;count<=6;++count) {
        std::array<team::Ledger,6> readers;std::array<unsigned,6> order{0,1,2,3,4,5};std::uint64_t word=0;
        for(unsigned round=0;round<200;++round) {
            std::shuffle(order.begin(),order.begin()+count,rng);
            for(unsigned i=0;i<count;++i) {
                const auto slot=order[i];readers[slot].observe(word,round,count);
                word=protocol::compact::with_slot(word,slot,{static_cast<std::uint8_t>(slot+7),false});
                word=team::publish(word,round,count,slot,slot*80+round,slot+7,team::Intent::Recover);
                readers[slot].observe(word,round,count);
            }
            if(round>4*count+2)for(unsigned observer=0;observer<count;++observer)for(unsigned author=0;author<count;++author) {
                assert(readers[observer].budget(author,round,count).valid);
                assert(readers[observer].project(author,round,count).valid);
            }
        }
        for(auto& reader:readers)for(unsigned author=0;author<count;++author)assert(!reader.budget(author,230,count).valid&&!reader.project(author,230,count).valid);
    }
    auto stale=team::publish(0,12,3,0,100,1,team::Intent::Active);
    assert(!team::decode(stale,1036,3).valid); // No modulo-age alias after 1024 rounds.
    assert(team::publish(0,1,3,6,100,1,team::Intent::Active)==0);
    assert(team::publish(0,2048,3,6,100,1,team::Intent::Active)==0);
    assert(team::publish(0,12,3,0,100,128,team::Intent::Active)==0);
    assert(team::publish(0,12,3,0,100,1,static_cast<team::Intent>(4))==0);
    std::cout<<cases<<" absolute-round frame cases; shuffled-order dissemination, lease priority, quantisation and expiry passed\n";
}
