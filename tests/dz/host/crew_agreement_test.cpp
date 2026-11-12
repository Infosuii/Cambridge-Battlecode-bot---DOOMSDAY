#include "crew_agreement.h"
#include <cassert>
#include <iostream>
#include <random>
using namespace dz;

int main() {
    std::mt19937 rng(3187);unsigned wire_checks=0,handshakes=0;
    constexpr auto low_mask=(std::uint64_t{1}<<42)-1;
    // Independently exercise the complete field domains, disjoint prefixes,
    // absolute age and lower-claim preservation, including all64 camp members.
    for(unsigned count=1;count<=6;++count)for(unsigned phase=0;phase<64;++phase)for(unsigned trial=0;trial<12;++trial) {
        const unsigned cycle=rng()%330,author=cycle%count,mask=(rng()%((1u<<count)-1)+1)|(1u<<author);
        const int dx=int(rng()%7)-3,dy=dx?int(rng()%7)-3:1;
        auto word=std::uint64_t(rng())&low_mask;
        word=protocol::compact::with_slot(word,author,{9,false});
        for(unsigned part=0;part<3;++part) {
            const unsigned now=6*cycle+2*part;
            const auto encoded=team::acknowledge(word,now,count,author,mask,phase,dx,dy,true);
            const auto f=team::decode(encoded,now,count);
            assert(f.valid&&f.slot==author&&f.round==now&&f.phase==phase&&f.task==9);
            assert((encoded&low_mask)==word&&!protocol::compact::lease(encoded,now).valid);
            assert(!team::decode(encoded,now-1,count).valid&&!team::decode(encoded,now+team::lifetime(count)+1,count).valid);
            if(part==0)assert(f.kind==team::Kind::Role&&f.dx==dx&&f.dy==dy);
            if(part==1)assert(f.kind==team::Kind::Roster&&f.members==mask);
            if(part==2)assert(f.kind==team::Kind::Ready);
            ++wire_checks;
        }
    }
    assert(!team::decode(0,4,3).valid);
    const std::array<team::Role,6> role{{{-1,0},{0,-1},{1,0},{0,1},{-1,-1},{1,1}}};
    // Random champion turn order; two-stage certificates must converge and may
    // never commit before each author has actually sent a matching Ready.
    for(unsigned count=2;count<=6;++count)for(unsigned trial=0;trial<20;++trial) {
        std::array<crew::Agreement,6> agreement;std::array<team::Ledger,6> readers;
        std::array<unsigned,6> order{0,1,2,3,4,5};const unsigned members=(1u<<count)-1;
        const bool split=count>=4&&trial>=10;
        std::uint64_t word=0;unsigned sent_ready=0;bool all=false;
        for(unsigned s=0;s<count;++s) {
            const unsigned group=split&&s>=2?10:9,mask=split?(s<2?3:members&~3u):members;
            word=protocol::compact::with_slot(word,s,{static_cast<std::uint8_t>(group),false});agreement[s].plan(group,0,mask,group-6,role,0,count);
        }
        word=protocol::compact::with_lease(word,agreement[0].members,0,0);
        for(unsigned round=0;round<160;++round) {
            std::shuffle(order.begin(),order.begin()+count,rng);
            for(unsigned i=0;i<count;++i) {
                const unsigned s=order[i];auto& a=agreement[s];auto& reader=readers[s];
                reader.observe(word,round,count);a.inspect(reader,word,round,count);
                if(a.committed)assert((sent_ready&a.members)==a.members);
                const unsigned coordinator=split&&s>=2?2:0;
                if(s==coordinator&&team::publisher(round,count)==s&&team::scheduled(round)==team::Kind::Lease&&
                    (!team::protected_lease(word,round,count)||protocol::compact::lease(word,round).leader==s))
                    word=protocol::compact::with_lease(word,a.members,s,round);
                word=team::publish(word,round,count,s,100,a.group,team::Intent::Active);
                if(a.announce(round,count)&&(!a.committed||team::scheduled(round)==team::Kind::Lease))
                    word=team::acknowledge(word,round,count,s,a.members,a.phase,role[s].dx,role[s].dy,a.can_ready||a.committed);
                const auto f=team::decode(word,round,count);
                if(f.valid&&f.round==round&&f.slot==s&&f.kind==team::Kind::Ready)sent_ready|=1u<<s;
                reader.observe(word,round,count);
            }
            all=true;for(unsigned s=0;s<count;++s)all&=agreement[s].committed;
            if(all){assert(round<=team::agreement_window(count));++handshakes;break;}
        }
        assert(all);
        // A new local generation cannot inherit a previously committed cycle.
        agreement[0].plan(9,1,agreement[0].members,3,role,170,count);agreement[0].inspect(readers[0],word,170,count);
        assert(!agreement[0].committed&&!agreement[0].can_ready);
    }
    // A changed role plus only old Ready records is never a new consensus.
    team::Ledger ledger;auto word=protocol::compact::with_slot(0,0,{9,false});
    word=protocol::compact::with_slot(word,1,{9,false});
    auto send=[&](unsigned round,unsigned slot,int dx,int dy,bool ready) {
        word=team::acknowledge(word,round,2,slot,3,0,dx,dy,ready);ledger.observe(word,round,2);
    };
    send(0,0,-1,0,false);send(2,0,-1,0,false);send(6,1,0,-1,false);send(8,1,0,-1,false);
    send(10,1,0,-1,true);send(12,0,-1,0,false);send(14,0,-1,0,false);send(16,0,-1,0,true);
    auto status=ledger.agreement(9,3,0,role,0,word,16,2);assert(status.committed(3));
    send(18,1,0,-1,false);send(20,1,0,-1,false);send(22,1,0,-1,true);send(24,0,1,1,false);
    auto moved=role;moved[0]={1,1};
    status=ledger.agreement(9,3,0,moved,0,word,24,2);
    assert(status.declared==3&&!status.committed(3)&&status.ready==0);
    assert(ledger.contradiction(9,3,0,role,0,24,2));
    // Withdrawing then restoring the same task does not resurrect a certificate.
    auto withdrawn=protocol::compact::with_slot(word,0,{protocol::idle,false});ledger.observe(withdrawn,25,2);
    ledger.observe(word,25,2);assert(!ledger.roles[0].valid);
    // Altering low claims under the same dated packet cannot rename its task.
    auto renamed=protocol::compact::with_slot(word,0,{10,false});ledger.observe(renamed,25,2);
    assert(ledger.roles[0].task==9&&!ledger.roles[0].valid);
    // A former coordinator's Ready must not renew ownership after handoff.
    team::Ledger handed;auto hand=protocol::compact::with_slot(0,0,{9,false});
    hand=protocol::compact::with_slot(hand,1,{9,false});hand=protocol::compact::with_lease(hand,3,0,0);handed.observe(hand,0,2);
    hand=team::acknowledge(hand,2,2,0,3,0,-1,0,false);handed.observe(hand,2,2);
    hand=protocol::compact::with_lease(hand,3,1,3);handed.observe(hand,3,2);
    hand=team::acknowledge(hand,4,2,0,3,0,-1,0,true);handed.observe(hand,4,2);
    assert(handed.cohort(9,hand,4,2).capturer==1);
    std::cout<<wire_checks<<" dated role/roster/ready wire checks; "<<handshakes
        <<" shuffled complete handshakes, generation barriers, contradictory roles and revocation passed\n";
}
