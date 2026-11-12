#include <cambc.h>
#include <algorithm>
#include <cstdio>
#include "config.h"
using namespace cambc;
void check(const char* name,bool pass) { std::printf("CT_CHECK name=%s pass=%d\n",name,pass); }
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::cassi_and_issac,champion_draft::vendetta,champion_draft::marcella,
            champion_draft::ryth,champion_draft::vesper_vale};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    auto roster=champions(team::ally);
    std::sort(roster.begin(),roster.end(),[](auto& a,auto& b) {
        return static_cast<unsigned>(static_cast<handle_champion_t>(a))<static_cast<unsigned>(static_cast<handle_champion_t>(b));
    });
    unsigned slot=0;while (slot<roster.size()&&roster[slot]!=self()) ++slot;
    check("priority_roster",slot<roster.size());
    const unsigned body=static_cast<unsigned>(static_cast<handle_champion_t>(self()));
    unsigned previous_round=0,turn=0;
    for (;;) {
        const auto round=round_number();
        try {
            if (round<=12) {
                check("priority_once_per_round",round==previous_round+1);
                const int before=self().prev_priority(),next=self().priority();
                int desired=next;bool change=false;
                // Different team offsets distinguish per-team ordering from a
                // single global priority sort. Linked bodies have separate slots.
                if (round==3) { desired=100+static_cast<int>(slot)+CT_OPPONENT*1000;change=true; }
                if (round==6) { desired=(slot==0?500:200+static_cast<int>(slot))+CT_OPPONENT*1000;change=true; }
                if (round==9) { desired=-7+CT_OPPONENT*1000;change=true; }
                if (change) self().set_priority(desired);
                std::printf("CT6_TURN round=%u body=%u slot=%u turn=%u previous=%d next_before=%d next_after=%d changed=%d desired=%d opponent=%d\n",
                    round,body,slot,turn,before,next,self().priority(),change,desired,CT_OPPONENT);
                check("priority_deferred_current",self().prev_priority()==before);
                check("priority_next_visible",self().priority()==desired);
                previous_round=round;
            }
        } catch (const std::exception& error) { std::printf("ERROR %s\n",error.what()); }
        ++turn;
        if (round_number()!=round) continue;
        end_turn();
    }
}
