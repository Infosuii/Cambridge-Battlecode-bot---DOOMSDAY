// Pure staged inference on one owned snapshot. No game/SDK calls or policy decisions.
#pragma once
#include <array>
#include <algorithm>
#include <cstdint>
#include "nn_infer.h"

namespace codex_frame {
template<std::size_t N>
struct Frame {
    std::array<std::int16_t,N> features{};
    nn::Live work{};
    nn::Out output{};
    std::size_t groups=0;
    int captured_at=0;
    int stage=5;
    void begin(const std::int16_t* input,const nn::Live& live,std::size_t count,int at) {
        std::copy(input,input+N,features.begin());
        work=live;
        groups=count;captured_at=at;stage=0;
    }
    bool advance() {
        switch(stage) {
            case 0: nn::live_camps(features.data(),work,groups);break;
            case 1: nn::live_block(features.data(),work,1);break;
            case 2: nn::live_block(features.data(),work,4);break;
            case 3: nn::live_top(work);break;
            case 4: nn::live_target(work,output);break;
            default:return true;
        }
        return ++stage==5;
    }
    bool ready() const { return stage==5 && work.z_ok; }
    bool fresh(int now,int ttl) const { return ready() && now>=captured_at && now-captured_at<=ttl; }
    std::uint32_t input_hash() const {
        std::uint32_t h=2166136261u;
        for(auto v:features) { h=(h^static_cast<std::uint16_t>(v))*16777619u; }
        return h;
    }
};
}
