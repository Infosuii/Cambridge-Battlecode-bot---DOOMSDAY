// Semantic assignments outlive censored log intervals. No SDK or heap state.
#pragma once
#include <cstdint>
namespace nnp {
struct Commitment {
    int round=-1;
    std::uint64_t id=0;
    std::uint32_t action=0xffffffffu;
    bool record_open=false,committed=false,suspended=false;
    void abandon() {*this=Commitment{};}
    void suspend() {id=0;record_open=false;suspended=committed;}
    void start(int now,std::uint64_t option,std::uint32_t selected,bool recorded,bool macro) {
        round=now;id=option;action=selected;record_open=recorded;committed=macro;suspended=false;
    }
};
}
