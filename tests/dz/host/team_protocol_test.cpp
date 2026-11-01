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
        if(team::scheduled(round)==team::Kind::Lease){assert(word==low&&!team::decode(word,round,count).valid);++cases;continue;}
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
            if(round>6*count+2)for(unsigned observer=0;observer<count;++observer)for(unsigned author=0;author<count;++author) {
                assert(readers[observer].budget(author,round,count).valid);
                assert(readers[observer].project(author,round,count).valid);
            }
        }
        for(auto& reader:readers)for(unsigned author=0;author<count;++author)assert(!reader.budget(author,250,count).valid&&!reader.project(author,250,count).valid);
    }
    // Two disjoint active crews, cash/project reports and changing actor order.
    // Scheduled cohort frames cannot starve the following metadata publisher.
    for(unsigned count=4;count<=6;++count) {
        std::array<team::Ledger,6> readers;std::array<unsigned,6> order{0,1,2,3,4,5};std::uint64_t word=0;
        for(unsigned s=0;s<count;++s)word=protocol::compact::with_slot(word,s,{static_cast<std::uint8_t>(s<2?9:s<4?10:127),false});
        for(unsigned r=0;r<250;++r) {
            std::shuffle(order.begin(),order.begin()+count,rng);
            for(unsigned i=0;i<count;++i) {
                const unsigned s=order[i];readers[s].observe(word,r,count);
                word=team::publish(word,r,count,s,120,s<2?9:s<4?10:127,team::Intent::Active);
                if((s==0||s==2)&&team::publisher(r,count)==s&&team::scheduled(r)==team::Kind::Lease&&
                    !team::protected_lease(word,r,count))word=protocol::compact::with_lease(word,s==0?3:12,s,r);
                readers[s].observe(word,r,count);
            }
            if(r>2*team::lifetime(count))for(unsigned s=0;s<count;++s) {
                assert(readers[s].cohort(9,word,r,count).members==3&&readers[s].cohort(10,word,r,count).members==12);
                for(unsigned a=0;a<count;++a)assert(readers[s].budget(a,r,count).valid&&readers[s].project(a,r,count).valid);
            }
        }
        auto removed=protocol::compact::with_slot(word,1,{protocol::dead,false});
        assert(!readers[0].cohort(9,removed,249,count).valid);
        readers[0].observe(removed,249,count);
        // Returning to the same objective code does not resurrect an old
        // acknowledged roster after an explicit withdrawal.
        readers[0].observe(word,249,count);assert(!readers[0].cohort(9,word,249,count).valid);
        auto capture=protocol::compact::with_lease(word,1,0,250);readers[0].observe(capture,250,count);
        capture=protocol::compact::with_slot(capture,1,{protocol::idle,false});
        assert(readers[0].cohort(9,capture,250,count).members==1);
        auto changed=protocol::compact::with_slot(capture,0,{11,false});readers[0].observe(changed,251,count);
        assert(!readers[0].cohort(9,changed,251,count).valid&&!readers[0].cohort(11,changed,251,count).valid);
        assert(!readers[0].cohort(9,capture,250+team::lifetime(count)+1,count).valid);
    }
    // A higher-slot initiator can invite lower slots that have not accepted
    // yet; it names the job through its own claim. Only actual acceptance
    // establishes the retained cohort, then a formed crew can relay capture.
    auto invitation=protocol::compact::with_slot(0,2,{7,false});
    invitation=protocol::compact::with_slot(invitation,0,{protocol::idle,false});
    invitation=protocol::compact::with_slot(invitation,1,{protocol::idle,false});
    invitation=protocol::compact::with_lease(invitation,7,2,10);
    const auto offer=protocol::compact::lease(invitation,10);
    assert(offer.valid&&offer.leader==2&&offer.objective==7);
    team::Ledger accepted;accepted.observe(invitation,10,3);
    assert(!accepted.cohort(7,invitation,10,3).valid);
    for(unsigned s=0;s<2;++s)invitation=protocol::compact::with_slot(invitation,s,{7,false});
    accepted.observe(invitation,11,3);assert(accepted.cohort(7,invitation,11,3).leader==2);
    invitation=protocol::compact::with_lease(invitation,7,0,12);accepted.observe(invitation,12,3);
    assert(accepted.cohort(7,invitation,12,3).leader==0&&accepted.cohort(7,invitation,12,3).members==7);
    const auto existing=protocol::compact::lease(protocol::compact::with_lease(invitation,3,0,12),12);
    assert(team::extends(existing,2,7,2));
    assert(!team::extends(existing,2,5,2)&&!team::extends(existing,2,7,0));
    assert(!team::extends(existing,0,7,0)&&!team::extends({},2,7,2)&&!team::extends(existing,6,127,6));
    auto stale=team::publish(0,12,3,team::publisher(12,3),100,1,team::Intent::Active);
    assert(team::decode(stale,12,3).valid);
    assert(!team::decode(stale,1036,3).valid); // No modulo-age alias after 1024 rounds.
    assert(team::publish(0,1,3,6,100,1,team::Intent::Active)==0);
    assert(team::publish(0,2048,3,6,100,1,team::Intent::Active)==0);
    assert(team::publish(0,12,3,0,100,128,team::Intent::Active)==0);
    assert(team::publish(0,12,3,0,100,1,static_cast<team::Intent>(4))==0);
    // Fight targets occupy unused metadata prefixes, preserve all compact
    // claims, and cannot survive withdrawal or alias after a timestamp wrap.
    for(unsigned count=1;count<=6;++count)for(unsigned r=0;r<2000;r+=2) {
        unsigned s=team::publisher(r,count);auto base=protocol::compact::with_slot(0,s,{protocol::fight,false});
        auto packet=team::focus(base,r,count,s,r%64);
        if(team::scheduled(r)==team::Kind::Project){assert(packet==base);continue;}
        auto f=team::decode(packet,r,count);assert(f.valid&&f.kind==team::Kind::Focus&&f.phase==r%64&&f.slot==s);
        assert((packet&claims)==(base&claims));assert(!protocol::compact::lease(packet,r).valid);
        team::Ledger ledger;ledger.observe(packet,r,count);assert(ledger.focus(s,packet,r,count).valid);
        if(r+5<2048){assert(ledger.focus(s,packet,r+4,count).valid);assert(!ledger.focus(s,packet,r+5,count).valid);}
        assert(!ledger.focus(s,packet,r+team::lifetime(count)+1,count).valid);
        auto released=protocol::compact::with_slot(packet,s,{protocol::idle,false});ledger.observe(released,r,count);
        ledger.observe(packet,r,count);assert(!ledger.focus(s,packet,r,count).valid);
        if(r+1024<2048)assert(!team::decode(packet,r+1024,count).valid);
    }
    team::WorkRecord work;
    assert(work.update(1,0,10,5,100,6,false,6));
    assert(work.update(1,0,15,4,100,6,false,6));
    // Local Contract restarts and walking back to a previously reached tile
    // never keep an unproductive claim fresh forever.
    assert(!work.update(1,0,21,4,100,6,false,6));
    assert(!work.update(1,0,22,6,100,6,false,6));
    assert(!work.update(1,0,23,4,100,6,false,6));
    assert(work.update(1,0,24,4,90,6,false,6));
    assert(work.update(1,0,30,4,90,5,false,6));
    assert(work.update(1,1,40,4,100,6,false,6));
    assert(!work.update(1,1,46,4,100,6,false,6));
    assert(work.update(1,1,47,4,100,6,true,6));
    std::cout<<cases<<" absolute-round frame cases; shuffled-order independent cohorts, report fairness, capture handoff and revocation passed\n";
}
