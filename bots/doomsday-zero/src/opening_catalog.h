#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <optional>
#include <span>
#include <vector>
namespace dz::opening_catalog {
// Immutable public map metadata, never observations or a learned policy.
struct Design {float hp=0,strength=0;std::int32_t range=0;std::uint32_t kind=0;};
struct Member {std::uint32_t id=0;std::int16_t x=0,y=0;std::uint32_t kind=0;};
struct Header {std::uint32_t magic=0x445a5032u,width=0,height=0,designs=0,members=0;};
template<class T> void append(std::vector<std::byte>& bytes,const T& value) {
    const auto old=bytes.size();bytes.resize(old+sizeof(T));std::memcpy(bytes.data()+old,&value,sizeof(T));
}
inline std::vector<std::byte> encode(unsigned width,unsigned height,std::span<const Design> designs,
                                     std::span<const Member> members,std::size_t capacity) {
    const auto prefix=sizeof(Header)+designs.size()*sizeof(Design);
    if(prefix>capacity)return {};
    std::vector<Member> ordered(members.begin(),members.end());
    std::sort(ordered.begin(),ordered.end(),[](auto a,auto b){return a.id<b.id;});
    const unsigned count=std::min<std::size_t>(ordered.size(),(capacity-prefix)/sizeof(Member));
    Header header;header.width=width;header.height=height;header.designs=designs.size();header.members=count;
    std::vector<std::byte> result;result.reserve(prefix+count*sizeof(Member));append(result,header);
    for(auto d:designs)append(result,d);
    for(unsigned i=0;i<count;++i)append(result,ordered[i]);
    return result;
}
struct Catalog {
    std::vector<Design> designs;std::vector<Member> members;bool valid=false;
    bool load(std::span<const std::byte> bytes,unsigned width,unsigned height) {
        valid=false;designs.clear();members.clear();if(bytes.size()<sizeof(Header))return false;
        Header h;std::memcpy(&h,bytes.data(),sizeof h);
        if(h.magic!=Header{}.magic||h.width!=width||h.height!=height||h.designs>16||h.members>100000)return false;
        const auto needed=sizeof(Header)+h.designs*sizeof(Design)+h.members*sizeof(Member);
        if(needed>bytes.size())return false;
        designs.resize(h.designs);members.resize(h.members);
        if(h.designs)std::memcpy(designs.data(),bytes.data()+sizeof(Header),h.designs*sizeof(Design));
        if(h.members)std::memcpy(members.data(),bytes.data()+sizeof(Header)+h.designs*sizeof(Design),h.members*sizeof(Member));
        unsigned kinds=0;
        for(auto d:designs) {
            if(d.kind>=16||(kinds&(1u<<d.kind))||!std::isfinite(d.hp)||d.hp<=0||!std::isfinite(d.strength)||d.strength<0||d.range<0)return false;
            kinds|=1u<<d.kind;
        }
        for(unsigned i=0;i<members.size();++i) {
            const auto m=members[i];
            if(m.x<0||m.y<0||static_cast<unsigned>(m.x)>=width||static_cast<unsigned>(m.y)>=height||m.kind>=16||
               !(kinds&(1u<<m.kind))||(i&&members[i-1].id>=m.id))return false;
        }
        return valid=true;
    }
    std::optional<Member> member(unsigned id) const {
        if(!valid)return {};
        const auto it=std::lower_bound(members.begin(),members.end(),id,[](auto m,unsigned key){return m.id<key;});
        return it!=members.end()&&it->id==id?std::optional<Member>{*it}:std::nullopt;
    }
    std::optional<Design> design(unsigned kind) const {
        if(valid)for(auto d:designs)if(d.kind==kind)return d;
        return {};
    }
};
}
