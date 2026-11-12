#pragma once
#include <cstdint>
namespace draft_alias {
struct Consumed {
    std::uint32_t mask=0;
    bool contains(int original) const {return original>=0 && original<32 && (mask&(std::uint32_t{1}<<original));}
    void picked(int original,int actual) {
        if (original!=actual && original>=0 && original<32) mask|=std::uint32_t{1}<<original;
    }
};
struct Projection {
    std::uint32_t mask=0;
    int count=0,front=0;
    void add(int id,bool frontline) {
        if (id<0 || id>=32 || (mask&(std::uint32_t{1}<<id))) return;
        mask|=std::uint32_t{1}<<id;++count;front+=frontline;
    }
};
}
