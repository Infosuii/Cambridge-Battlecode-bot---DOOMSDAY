#include "jd_roster.h"
#include <cassert>
#include <cstdio>
#include <vector>
unsigned cases=0;
void check(std::vector<std::uint8_t>& picks) {
    if (!picks.empty()) {
        auto out=jd_roster::encode(picks);assert(out[0]==0x58);
        unsigned n=0;
        for (auto p:picks) {
            if(p==3) {assert(out[2+n++]==3);assert(out[2+n++]==4);}
            else assert(out[2+n++]==(p>=4?p+1:p));
        }
        assert(out[1]==n);assert(n<=6);++cases;
    }
    if(picks.size()==5)return;
    for(std::uint8_t p=0;p<12;++p) {
        bool seen=false;for(auto q:picks)seen|=p==q;
        if(!seen){picks.push_back(p);check(picks);picks.pop_back();}
    }
}
int main(){std::vector<std::uint8_t> p;check(p);
 assert(jd_roster::encode({})[0]==0);
 const std::uint8_t invalid[]={12},dup[]={3,3};
 assert(jd_roster::encode(invalid)[0]==0);assert(jd_roster::encode(dup)[0]==0);
 std::printf("roster_test: %u legal draft prefixes; body ordering/count correct; invalid fallback passed\n",cases);
}
