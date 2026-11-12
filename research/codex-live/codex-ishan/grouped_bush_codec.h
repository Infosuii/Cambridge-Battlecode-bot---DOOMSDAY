#pragma once
#include <algorithm>
#include <cstdint>
#include <utility>
#include <vector>
namespace codex_bush_codec {
constexpr std::uint16_t absent=65535;
inline bool bit(const std::vector<std::uint8_t>& b,std::size_t i){return (b[i>>3]>>(i&7))&1;}
inline void mark(std::vector<std::uint8_t>& b,std::size_t i){b[i>>3]|=static_cast<std::uint8_t>(1u<<(i&7));}
inline void put(std::vector<std::uint8_t>& b,std::uint32_t n){while(n>=128){b.push_back(static_cast<std::uint8_t>((n&127)|128));n>>=7;}b.push_back(static_cast<std::uint8_t>(n));}
inline bool get(const std::vector<std::uint8_t>& b,std::size_t& p,std::uint32_t& n){
    n=0;
    for(unsigned shift=0;shift<=28;shift+=7){
        if(p>=b.size())return false;
        const auto v=b[p++];if(shift==28&&(v&240))return false;
        n|=static_cast<std::uint32_t>(v&127)<<shift;
        if(!(v&128))return true;
    }
    return false;
}
struct Payload { bool valid=false;std::uint16_t count=0;std::vector<std::uint8_t> bytes; };
struct Cache {
    bool valid=false;
    std::vector<std::uint16_t> which;
    std::vector<std::vector<std::uint16_t>> members;
    std::vector<std::uint8_t> published;
};
inline Payload encode(int w,int h,const std::vector<std::uint8_t>& terrain){
    Payload out;
    if(w<=0||h<=0||static_cast<std::uint64_t>(w)*h>65535)return out;
    const auto n=static_cast<std::size_t>(w)*h;if(terrain.size()!=(n+7)/8)return out;
    std::vector<std::uint16_t> labels(n,absent),stack;stack.reserve(n);
    unsigned count=0;
    for(std::size_t root=0;root<n;++root){
        if(!bit(terrain,root)||labels[root]!=absent)continue;
        if(count>=absent)return out;
        const auto id=static_cast<std::uint16_t>(count++);labels[root]=id;stack.push_back(static_cast<std::uint16_t>(root));
        while(!stack.empty()){
            const int at=stack.back();stack.pop_back();const int x=at%w,y=at/w;
            for(int yy=std::max(0,y-1);yy<std::min(h,y+2);++yy)
                for(int xx=std::max(0,x-1);xx<std::min(w,x+2);++xx){
                    const auto q=static_cast<std::size_t>(yy*w+xx);
                    if(bit(terrain,q)&&labels[q]==absent){labels[q]=id;stack.push_back(static_cast<std::uint16_t>(q));}
                }
        }
    }
    using Run=std::pair<std::uint16_t,std::uint16_t>;
    std::vector<std::vector<Run>> runs(count);
    for(std::size_t at=0;at<n;){
        if(labels[at]==absent){++at;continue;}
        auto end=at+1;while(end<n&&labels[end]==labels[at])++end;
        runs[labels[at]].emplace_back(static_cast<std::uint16_t>(at),static_cast<std::uint16_t>(end-at));at=end;
    }
    for(const auto& group:runs){
        put(out.bytes,static_cast<std::uint32_t>(group.size()));std::uint32_t last=0;
        for(const auto& [start,length]:group){put(out.bytes,start-last);put(out.bytes,length);last=start+length;}
    }
    out.count=static_cast<std::uint16_t>(count);out.valid=true;return out;
}
inline Cache decode(int w,int h,unsigned count,const std::vector<std::uint8_t>& bytes,const std::vector<std::uint8_t>& terrain){
    Cache out;
    if(w<=0||h<=0||static_cast<std::uint64_t>(w)*h>65535)return out;
    const auto n=static_cast<std::size_t>(w)*h;
    if(terrain.size()!=(n+7)/8||count>n||count>=absent)return out;
    out.which.assign(n,absent);out.members.resize(count);std::size_t p=0,total=0;
    for(unsigned cid=0;cid<count;++cid){
        std::uint32_t runs=0;if(!get(bytes,p,runs)||!runs||runs>n)return Cache{};
        std::uint64_t last=0;
        for(std::uint32_t r=0;r<runs;++r){
            std::uint32_t gap=0,length=0;
            if(!get(bytes,p,gap)||!get(bytes,p,length)||!length)return Cache{};
            const std::uint64_t start=last+gap,end=start+length;
            if(end>n)return Cache{};
            for(std::uint64_t at=start;at<end;++at){
                if(out.which[at]!=absent||!bit(terrain,at))return Cache{};
                out.which[at]=static_cast<std::uint16_t>(cid);out.members[cid].push_back(static_cast<std::uint16_t>(at));++total;
            }
            last=end;
        }
    }
    if(p!=bytes.size())return Cache{};
    std::size_t occupied=0;
    for(std::size_t at=0;at<n;++at){const bool bush=bit(terrain,at);occupied+=bush;if(bush!=(out.which[at]!=absent))return Cache{};}
    if(occupied!=total)return Cache{};
    out.published.assign(terrain.size(),0);out.valid=true;return out;
}
template<class Board> inline bool publish(Cache& cache,std::size_t at,std::uint16_t* labels,int& next_id,Board& labelled){
    if(!cache.valid||at>=cache.which.size())return false;
    const unsigned cid=cache.which[at];if(cid>=cache.members.size())return false;
    const auto id=static_cast<std::uint16_t>(next_id++);
    for(const auto tile:cache.members[cid]){labels[tile]=id;mark(cache.published,tile);}
    labelled.import_linear_buffer(cache.published);return true;
}
}
