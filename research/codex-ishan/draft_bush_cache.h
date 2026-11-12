#pragma once
#if CODEX_DRAFT_BUSH_CACHE
#include "codex_field_cache.h"
#include "grouped_bush_codec.h"
#include <array>
#include <cstring>
namespace codex_draft_bush {
struct Header {std::uint32_t magic,checksum;std::uint16_t width,height,count,bytes;};
static_assert(sizeof(Header)==16);
constexpr std::uint32_t magic=0x42434831u;
struct Parts {std::size_t first=0,first_size=0,second=0,second_size=0;std::size_t size()const{return first_size+second_size;}};
inline bool parts(const std::byte* memory,std::size_t size,int w,int h,std::size_t groups,Parts& out){
    if(size<codex_field_cache::end||!groups||groups>codex_field_cache::limit)return false;
    codex_field_cache::Header field{};std::memcpy(&field,memory+codex_field_cache::offset,sizeof(field));
    if(field.magic!=codex_field_cache::magic||field.version!=2||field.count!=groups||field.width!=w||field.height!=h)return false;
    std::array<std::uint16_t,codex_field_cache::limit> order{};std::array<std::uint8_t,codex_field_cache::limit> seen{};
    std::memcpy(order.data(),memory+codex_field_cache::offset+sizeof(field),2*groups);
    if(codex_field_cache::checksum(order.data(),groups)!=field.checksum)return false;
    for(std::size_t i=0;i<groups;++i){if(order[i]>=groups||seen[order[i]])return false;seen[order[i]]=1;}
    out.first=codex_field_cache::offset+sizeof(field)+2*groups;out.first_size=codex_field_cache::second-out.first;
    out.second=codex_field_cache::second+sizeof(field)+2*groups;out.second_size=codex_field_cache::end-out.second;
    return out.size()>=sizeof(Header);
}
inline std::uint8_t read_byte(const std::byte* memory,const Parts& p,std::size_t i){return static_cast<std::uint8_t>(memory[i<p.first_size?p.first+i:p.second+i-p.first_size]);}
inline void put_byte(std::uint8_t* memory,const Parts& p,std::size_t i,std::uint8_t value){memory[i<p.first_size?p.first+i:p.second+i-p.first_size]=value;}
inline std::uint32_t checksum(const Header& h,const std::vector<std::uint8_t>& data){
    std::uint32_t hash=2166136261u;
    const std::uint16_t fields[]={h.width,h.height,h.count,h.bytes};
    for(auto v:fields){hash=(hash^(v&255))*16777619u;hash=(hash^(v>>8))*16777619u;}
    for(auto v:data)hash=(hash^v)*16777619u;return hash;
}
inline codex_bush_codec::Cache decode(const std::byte* memory,std::size_t size,int w,int h,std::size_t groups,const std::vector<std::uint8_t>& terrain){
    Parts p;codex_bush_codec::Cache none;if(!parts(memory,size,w,h,groups,p))return none;
    std::array<std::uint8_t,sizeof(Header)> raw{};
    for(std::size_t i=0;i<raw.size();++i)raw[i]=read_byte(memory,p,i);
    Header header{};std::memcpy(&header,raw.data(),sizeof(header));
    if(header.magic!=magic||header.width!=w||header.height!=h||header.bytes>p.size()-sizeof(header))return none;
    std::vector<std::uint8_t> data(header.bytes);
    for(std::size_t i=0;i<data.size();++i)data[i]=read_byte(memory,p,sizeof(header)+i);
    if(checksum(header,data)!=header.checksum)return none;
    return codex_bush_codec::decode(w,h,header.count,data,terrain);
}
inline bool write_payload(std::uint8_t* memory,std::size_t size,int w,int h,std::size_t groups,const codex_bush_codec::Payload& data){
    Parts p;if(!data.valid||data.bytes.size()>65535||!parts(reinterpret_cast<const std::byte*>(memory),size,w,h,groups,p)||sizeof(Header)+data.bytes.size()>p.size())return false;
    Header header{magic,0,static_cast<std::uint16_t>(w),static_cast<std::uint16_t>(h),data.count,static_cast<std::uint16_t>(data.bytes.size())};header.checksum=checksum(header,data.bytes);
    std::array<std::uint8_t,sizeof(Header)> raw{};std::memcpy(raw.data(),&header,sizeof(header));
    for(std::size_t i=0;i<raw.size();++i)put_byte(memory,p,i,raw[i]);
    for(std::size_t i=0;i<data.bytes.size();++i)put_byte(memory,p,raw.size()+i,data.bytes[i]);
    return true;
}
#if CODEX_DRAFT_BUSH_PROBE
inline int store_state=0;
inline std::uint64_t store_before=0,store_after=0;
inline bool store_preserved=false;
#endif
inline void store(){
    static bool done=false;if(done)return;done=true;
    if(!bc::is_draft()||bc::constants::draft_memory_bytes<codex_field_cache::end)return;
    const int w=bc::map::width(),h=bc::map::height();const std::uint64_t area=static_cast<std::uint64_t>(w)*h;
    if(w<=0||h<=0||area>65535)return;
#if CODEX_DRAFT_BUSH_PROBE
    store_before=bc::fuel_remaining();
#endif
    if(bc::fuel_remaining()<65536+1024*area){
#if CODEX_DRAFT_BUSH_PROBE
        store_state=2;store_after=bc::fuel_remaining();
#endif
        return;
    }
    const auto groups=bc::map::camp_groups().size();
    std::array<std::uint8_t,codex_field_cache::end> memory{};
    bc::detail::check(bc::detail::sdk_read_draft_memory(0,memory.data(),memory.size()));
    Parts p;if(!parts(reinterpret_cast<const std::byte*>(memory.data()),memory.size(),w,h,groups,p))return;
#if CODEX_DRAFT_BUSH_PROBE
    const auto before=memory;
    std::array<std::uint8_t,16> tail{};bc::detail::check(bc::detail::sdk_read_draft_memory(codex_field_cache::end,tail.data(),tail.size()));
#endif
    const auto data=codex_bush_codec::encode(w,h,bc::map::bushes().export_linear_buffer());
    if(!write_payload(memory.data(),memory.size(),w,h,groups,data)){
#if CODEX_DRAFT_BUSH_PROBE
        store_state=3;store_after=bc::fuel_remaining();
#endif
        return;
    }
    bc::draft_memory=memory;
#if CODEX_DRAFT_BUSH_PROBE
    store_state=1;store_after=bc::fuel_remaining();
    std::array<std::uint8_t,codex_field_cache::end> after{};bc::detail::check(bc::detail::sdk_read_draft_memory(0,after.data(),after.size()));
    std::array<std::uint8_t,16> after_tail{};bc::detail::check(bc::detail::sdk_read_draft_memory(codex_field_cache::end,after_tail.data(),after_tail.size()));
    store_preserved=tail==after_tail;
    for(std::size_t i=0;i<after.size();++i){const bool padding=(i>=p.first&&i<p.first+p.first_size)||(i>=p.second&&i<p.second+p.second_size);if(!padding&&before[i]!=after[i])store_preserved=false;}
#endif
}
}
#endif
