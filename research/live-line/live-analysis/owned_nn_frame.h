// Pure in-place evaluation view. The production caller must enforce graph ownership.
#pragma once
#include <array>
#include <algorithm>
#include <cstdint>
#include "nn_infer.h"
namespace codex_owned {
template<std::size_t N>
struct Frame {
    std::array<std::int16_t,N> features{};
    nn::Live* work=nullptr;
    nn::Out output{};
    std::size_t groups=0;
    int captured_at=0,stage=5;
    bool admitted=false;
    Frame()=default;
    Frame(const Frame&)=delete;
    Frame& operator=(const Frame&)=delete;
    bool begin(const std::int16_t* input,nn::Live& live,std::size_t count,int at,bool complete_blocks) {
        if(admitted&&stage<5)return false;
        admitted=false;stage=5;captured_at=at;work=nullptr;
        if(!complete_blocks)return false;
        std::copy(input,input+N,features.begin());
        work=&live;groups=count;stage=0;admitted=true;return true;
    }
    bool advance() {
        if(!admitted)return true;
        switch(stage) {
            case 0:nn::live_camps(features.data(),*work,groups);break;
            case 1:nn::live_block(features.data(),*work,1);break;
            case 2:nn::live_block(features.data(),*work,4);break;
            case 3:nn::live_top(*work);break;
            case 4:nn::live_target(*work,output);break;
            default:return true;
        }
        return ++stage==5;
    }
    void release(){admitted=false;work=nullptr;stage=5;}
    bool ready() const{return admitted&&work&&stage==5&&work->z_ok;}
    bool fresh(int now,int ttl) const{return ready()&&now>=captured_at&&now-captured_at<=ttl;}
    std::uint32_t input_hash() const {
        std::uint32_t h=2166136261u;
        for(auto value:features)h=(h^static_cast<std::uint16_t>(value))*16777619u;
        return h;
    }
};
}
