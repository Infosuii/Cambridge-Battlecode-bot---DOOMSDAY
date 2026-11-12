#include "objective_frontier.h"
#include <cassert>
#include <iostream>
#include <vector>
using namespace dz;
int main() {
    for(unsigned total=0;total<400;++total) {
        economy::Frontier frontier;std::array<int,8> retained{0,1,2,3,4,5,6,7};frontier.keep(retained);
        std::vector<bool> seen(total);std::array<int,3> priorities{static_cast<int>(total)-1,-1,2};
        for(unsigned turn=0;turn<1+total;++turn) {
            auto batch=frontier.next(total,priorities);assert(batch.count<=32);
            for(unsigned i=0;i<batch.count;++i) {
                const auto g=batch.groups[i];assert(g>=0&&static_cast<unsigned>(g)<total);seen[g]=true;
                for(unsigned j=0;j<i;++j)assert(batch.groups[j]!=g);
            }
            if(total)assert(batch.groups[0]==static_cast<int>(total)-1);
        }
        assert(std::all_of(seen.begin(),seen.end(),[](bool value){return value;}));
    }
    economy::Frontier frontier;std::array<int,4> repeated{3,3,-1,7};frontier.keep(repeated);assert(frontier.count==2);
    assert(frontier.next(1).count==1);assert(frontier.next(0).count==0);
    std::cout<<"400 bounded objective frontiers: retained priorities, deduplication and complete rotating discovery passed\n";
}
