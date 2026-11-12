#pragma once
#include <array>
#include <cstdint>
#include <deque>
namespace feed_control {
struct DeathWindow {
    struct Slot {std::uint32_t handle=0;bool initialized=false,alive=false;};
    std::array<Slot,8> slots{};
    std::deque<int> events;
    void observe(int slot,std::uint32_t handle,bool alive,int round) {
        if (slot<0 || slot>=static_cast<int>(slots.size())) return;
        auto& s=slots[slot];
        if (s.initialized && s.handle==handle && s.alive && !alive) events.push_back(round);
        s={handle,true,alive};
    }
    int recent(int round,int window) {
        while (!events.empty() && events.front()<round-window) events.pop_front();
        return static_cast<int>(events.size());
    }
};
inline bool collapsing(int own,int enemy,int threshold,bool net) {
    return own>=threshold && (!net || own-enemy>=threshold);
}
}
