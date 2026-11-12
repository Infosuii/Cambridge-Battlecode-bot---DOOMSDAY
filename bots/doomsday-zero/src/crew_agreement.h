#pragma once
#include "team_protocol.h"

namespace dz::crew {
// Explicit roster, target member and each member's exact attack-tile offset.
// Ready means the author checked ALL declarations against its local plan.
// A changed declaration invalidates older Ready records through a dated barrier.
struct Agreement {
    int group=-1,since=-1,deadline=-1,committed_round=-1;
    unsigned generation=0,members=0,phase=0;
    std::array<team::Role,protocol::slots> roles{};
    bool committed=false,can_ready=false;
    team::AgreementStatus status;
    void plan(int job,unsigned cycle,unsigned roster,unsigned target,const std::array<team::Role,protocol::slots>& proposed,
              unsigned now,unsigned count) {
        if(group==job&&generation==cycle&&members==roster&&phase==target&&roles==proposed)return;
        group=job;generation=cycle;members=roster;phase=target;roles=proposed;
        since=now;deadline=now+team::agreement_window(count);committed_round=-1;
        committed=can_ready=false;status={};
    }
    void inspect(const team::Ledger& ledger,std::uint64_t word,unsigned now,unsigned count) {
        if(group<0)return;
        if(committed) {
            if(!ledger.contradiction(group,members,phase,roles,since,now,count))return;
            committed=can_ready=false;since=now;deadline=now+team::agreement_window(count);committed_round=-1;
        }
        status=ledger.agreement(group,members,phase,roles,since,word,now,count);
        can_ready=status.declared==members&&members;
        if(status.committed(members)){committed=true;committed_round=now;}
    }
    bool pending(unsigned now) const {return group>=0&&!committed&&since>=0&&now<=static_cast<unsigned>(deadline);}
    bool announce(unsigned now,unsigned count) const {
        return group>=0&&(!committed||(committed_round>=0&&now<=static_cast<unsigned>(committed_round)+team::lifetime(count)));
    }
};
}
