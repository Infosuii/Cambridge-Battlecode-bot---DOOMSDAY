"""Own isolated static field-order cache, with a byte-identical erased control."""
from shutil import copytree

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import HERE,SDK_ROOT,read

HEADER=r'''#pragma once
#if CODEX_DRAFT_FIELD_CACHE
#include "world.h"
#include <array>
#include <cstring>
#include <span>
namespace codex_field_cache {
constexpr std::size_t offset=512, end=1008;
struct Header { std::uint32_t magic, checksum; std::uint16_t version,count,width,height; };
static_assert(sizeof(Header)==16);
constexpr std::uint32_t magic=0x43464f31u;
#if CODEX_DRAFT_CACHE_PROBE
inline bool bypass=false;
inline std::uint64_t draft_before=0,draft_after=0;
#endif
inline std::uint32_t checksum(const std::uint16_t* values,std::size_t n) {
    std::uint32_t h=2166136261u;
    for(std::size_t i=0;i<n;++i) h=(h^values[i])*16777619u;
    return h;
}
inline bool load(World& w) {
    if(bc::is_draft() || w.bridges_on || bc::draft_memory.size()<end || w.groups.empty()) return false;
#if CODEX_DRAFT_CACHE_PROBE
    if(bypass) return false;
#endif
    Header h{};
    std::memcpy(&h,bc::draft_memory.data()+offset,sizeof(h));
    if(h.magic!=magic || h.version!=1 || h.count!=w.groups.size() || h.count>(end-offset-sizeof(h))/2 ||
       h.width!=w.width || h.height!=w.height) return false;
    std::array<std::uint16_t,240> order{};
    std::memcpy(order.data(),bc::draft_memory.data()+offset+sizeof(h),2*h.count);
    if(checksum(order.data(),h.count)!=h.checksum) return false;
    std::array<std::uint8_t,240> seen{};
    for(unsigned i=0;i<h.count;++i) {
        const auto gi=order[i];
        if(gi>=h.count || seen[gi]) return false;
        seen[gi]=1;
    }
    w.field_order.resize(h.count);
    for(unsigned i=0;i<h.count;++i) w.field_order[i]=order[i];
    return true;
}
inline void store() {
    static bool done=false;
    if(done) return;
    done=true;
    if(!bc::is_draft() || bc::constants::draft_memory_bytes<end) return;
    std::uint32_t count=0;
    if(bc::detail::sdk_map_num_camp_groups(&count)!=0 || !count || count>240) return;
#if CODEX_DRAFT_CACHE_PROBE
    draft_before=bc::fuel_remaining();
#endif
    World w;
    w.init();
    w.prepare_field_order();
    if(w.field_order.size()!=count) return;
    std::array<std::uint16_t,240> order{};
    for(unsigned i=0;i<count;++i) order[i]=static_cast<std::uint16_t>(w.field_order[i]);
    Header h{magic,checksum(order.data(),count),1,static_cast<std::uint16_t>(count),
             static_cast<std::uint16_t>(w.width),static_cast<std::uint16_t>(w.height)};
    std::array<std::uint8_t,end> memory{};
    bc::detail::check(bc::detail::sdk_read_draft_memory(0,memory.data(),memory.size()));
    std::memcpy(memory.data()+offset,&h,sizeof(h));
    std::memcpy(memory.data()+offset+sizeof(h),order.data(),2*count);
    bc::draft_memory=memory;
#if CODEX_DRAFT_CACHE_PROBE
    draft_after=bc::fuel_remaining();
#endif
}
}
#endif
'''


def prepare(target,enabled,probe=False):
    identity=read(HERE/"LIVE111_SOURCE_VERIFIED.json")
    source=SDK_ROOT/"bots/live111/src"
    assert all(bench.digest(source/n)==h for n,h in identity["source_file_hashes"].items())
    copytree(source,target)
    header=target/"common.h"
    header.write_bytes(f"#define CODEX_DRAFT_FIELD_CACHE {int(enabled)}\n#define CODEX_DRAFT_CACHE_PROBE {int(probe)}\n".encode()+header.read_bytes())
    (target/"codex_field_cache.h").write_text(HEADER,encoding="utf8",newline="\n")
    for name,anchor in (("main.cpp",'#include "draft.h"'),("world.cpp",'#include "world.h"')):
        apply(target/name,((anchor,anchor+'\n#include "codex_field_cache.h"'),))
    apply(target/"main.cpp",(("                play_draft();",'''#if CODEX_DRAFT_FIELD_CACHE
                codex_field_cache::store();
#endif
                play_draft();'''),))
    apply(target/"world.cpp",(("    field_ptr.assign(groups.size(), nullptr);",'''    field_ptr.assign(groups.size(), nullptr);
#if CODEX_DRAFT_FIELD_CACHE
    if(codex_field_cache::load(*this)) return;
#endif'''),))
