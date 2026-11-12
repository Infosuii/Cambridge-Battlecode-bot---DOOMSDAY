#pragma once
#include <algorithm>
#include <cmath>

namespace dz::crew {
inline int assembly_deadline(int now,int arrival,int agreement,int stall,int limit=2000) {
    if(now<0||now>limit||arrival<0||arrival>=65535||agreement<0||stall<0||limit<0||limit>2000)return -1;
    return static_cast<int>(std::min<long long>(limit,static_cast<long long>(now)+arrival+agreement+stall));
}
// Harmless current work is a common prefix, not a second auction reward.
// Basic-only work and the full capture duration give an availability estimate
// without assuming a reset, better equipment or the ally's cash.
inline int available_after(float hp,float damage,int distance,int range,int capture,int limit) {
    if(!std::isfinite(hp)||hp<0||!std::isfinite(damage)||damage<=0||distance<0||distance>=65535||
        range<1||capture<0||limit<0||limit>2000||hp/damage>limit)return -1;
    const auto work=static_cast<long long>(std::ceil(static_cast<double>(hp)/damage));
    const auto finish=std::max(0,distance-range)+work+capture+1;
    return finish<=limit?static_cast<int>(finish):-1;
}
struct DeferredOffer {
    int group=-1,prefix=-1,deadline=0;
    unsigned members=0,capturer=0,leader=0,generation=0;
    bool active() const {return group>=0;}
    bool start(int task,int current,unsigned roster,unsigned recipient,unsigned coordinator,unsigned cycle,int now,int window) {
        if(task<0||task>=112||current<0||current>=112||task==current||!roster||roster>=64||recipient>=6||coordinator>=6||
            !(roster&(1u<<recipient))||!(roster&(1u<<coordinator))||now<0||now>2000||window<1||window>2000)return false;
        if(active()&&group==task&&prefix==current&&members==roster&&capturer==recipient&&leader==coordinator&&generation==cycle)
            return now<=deadline;
        *this={task,current,std::min(2000,now+window),roster,recipient,coordinator,cycle};return true;
    }
    bool current(int now,unsigned self,unsigned leader_claim,bool leader_alive) const {
        return active()&&self<6&&(members&(1u<<self))&&now>=0&&now<=deadline&&leader_alive&&leader_claim==static_cast<unsigned>(group);
    }
};
}
