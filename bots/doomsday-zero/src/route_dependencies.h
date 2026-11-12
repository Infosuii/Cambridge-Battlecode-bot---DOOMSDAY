#pragma once
#include <array>
#include <algorithm>
#include <cstdint>

namespace dz::crew {
struct RouteDependency { int group=-1,member=-1;bool operator==(const RouteDependency&) const=default; };
struct RouteDependencies {
    std::array<RouteDependency,128> entries{};unsigned count=0;
    unsigned revision=~0u;int until=0;
    void reset(unsigned current) {count=0;revision=current;until=2001;}
    bool add(int group,int member,int expiry) {
        if(group<0||member<0||expiry<=0)return false;
        const RouteDependency key{group,member};
        if(std::find(entries.begin(),entries.begin()+count,key)==entries.begin()+count) {
            if(count==entries.size())return false;entries[count++]=key;
        }
        until=std::min(until,expiry);return true;
    }
    // -1 means deferred work, 0 a closed dependency, 1 a valid complete set.
    template<class Expiry,class Budget>
    int refresh(unsigned current,int now,Expiry expiry,Budget budget) {
        if(revision==current&&now<until)return 1;
        int next=2001;
        for(unsigned i=0;i<count;++i) {
            if((i&7u)==0&&!budget())return -1;
            const int end=expiry(entries[i]);if(end<=now)return 0;next=std::min(next,end);
        }
        revision=current;until=next;return 1;
    }
    template<class Used,class Budget>
    void trim(Used used,Budget budget) {
        unsigned out=0;
        for(unsigned i=0;i<count;++i) {
            if(!budget()) {while(i<count)entries[out++]=entries[i++];break;}
            if(used(entries[i]))entries[out++]=entries[i];
        }
        count=out;revision=~0u; // Recompute the expiry of the reduced set.
    }
};
}
