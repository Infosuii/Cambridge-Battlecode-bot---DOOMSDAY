#pragma once
#include <algorithm>
#include <array>
#include <span>

namespace dz::economy {
// Keep useful estimates while guaranteeing fresh discovery. The frontier
// stores identities only: availability, ownership, rewards and bids are always
// recomputed from the current legal frame.
struct Frontier {
    struct Batch {std::array<int,32> groups{};unsigned count=0;};
    std::array<int,8> retained{};unsigned count=0,cursor=0;
    Batch next(unsigned groups,std::span<const int> priorities={}) {
        Batch result;
        auto add=[&](int g) {
            if(g<0||static_cast<unsigned>(g)>=groups||result.count==result.groups.size()||
                std::find(result.groups.begin(),result.groups.begin()+result.count,g)!=result.groups.begin()+result.count)return;
            result.groups[result.count++]=g;
        };
        for(auto g:priorities)add(g);
        for(unsigned i=0;i<count;++i)add(retained[i]);
        for(unsigned i=0;i<std::min(24u,groups)&&result.count<result.groups.size();++i){add(cursor%groups);cursor=(cursor+1)%groups;}
        return result;
    }
    void keep(std::span<const int> ranked) {
        count=0;
        for(auto g:ranked)if(g>=0&&std::find(retained.begin(),retained.begin()+count,g)==retained.begin()+count) {
            retained[count++]=g;if(count==retained.size())break;
        }
    }
};
}
