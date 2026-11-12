"""Exact walking/travel-dash order caching in two explicitly tagged draft slots."""
from live111_draft_cache import HEADER as ORIGINAL_HEADER,prepare as base_prepare

PREFIX=ORIGINAL_HEADER.split("inline void store() {")[0]
PREFIX=PREFIX.replace("constexpr std::size_t offset=512, end=1008;","constexpr std::size_t offset=512, second=760, end=1008, limit=116;")
PREFIX=PREFIX.replace("if(w.bridges_on || size<end || w.groups.empty()) return false;","if(size<end || w.groups.empty()) return false;\n    const std::size_t slot=w.bridges_on?second:offset;")
PREFIX=PREFIX.replace("data+offset","data+slot")
PREFIX=PREFIX.replace("h.version!=1","h.version!=(w.bridges_on?3:2)")
PREFIX=PREFIX.replace("h.count>(end-offset-sizeof(h))/2","h.count>limit")
PREFIX=PREFIX.replace("std::array<std::uint16_t,240>","std::array<std::uint16_t,limit>").replace("std::array<std::uint8_t,240>","std::array<std::uint8_t,limit>")

STORE=r'''inline void store() {
    static bool done=false;
    if(done) return;
    done=true;
    if(!bc::is_draft() || bc::constants::draft_memory_bytes<end) return;
    std::uint32_t count=0;
    if(bc::detail::sdk_map_num_camp_groups(&count)!=0 || !count || count>limit) return;
#if CODEX_DRAFT_CACHE_PROBE
    draft_before=bc::fuel_remaining();
#endif
    std::array<std::uint8_t,end> memory{};
    bc::detail::check(bc::detail::sdk_read_draft_memory(0,memory.data(),memory.size()));
#if CODEX_DRAFT_CACHE_PROBE
    const auto prefix=memory;
    std::array<std::uint8_t,16> tail{};
    bc::detail::check(bc::detail::sdk_read_draft_memory(end,tail.data(),tail.size()));
#endif
    std::fill(memory.begin()+offset,memory.end(),0);
    World w;w.init();w.prepare_field_order();
    const auto put=[&](std::size_t slot,unsigned version) {
        if(w.field_order.size()!=count) return false;
        std::array<std::uint16_t,limit> order{};
        for(unsigned i=0;i<count;++i) order[i]=static_cast<std::uint16_t>(w.field_order[i]);
        Header h{magic,checksum(order.data(),count),static_cast<std::uint16_t>(version),static_cast<std::uint16_t>(count),
                 static_cast<std::uint16_t>(w.width),static_cast<std::uint16_t>(w.height)};
        std::memcpy(memory.data()+slot,&h,sizeof(h));
        std::memcpy(memory.data()+slot+sizeof(h),order.data(),2*count);
        return true;
    };
    if(!put(offset,2)) return;
    w.enable_bridges();
    if(w.bridges_on) {w.field_order.clear();w.prepare_field_order();if(!put(second,3)) return;}
    bc::draft_memory=memory;
#if CODEX_DRAFT_CACHE_PROBE
    draft_after=bc::fuel_remaining();
    std::array<std::uint8_t,end> after{};
    bc::detail::check(bc::detail::sdk_read_draft_memory(0,after.data(),after.size()));
    std::array<std::uint8_t,16> after_tail{};
    bc::detail::check(bc::detail::sdk_read_draft_memory(end,after_tail.data(),after_tail.size()));
    memory_preserved=std::equal(prefix.begin(),prefix.begin()+offset,after.begin())&&tail==after_tail;
#endif
}
}
#endif
'''


def prepare(target,enabled,probe=False):
    base_prepare(target,enabled,probe)
    (target/"codex_field_cache.h").write_text(PREFIX+STORE,encoding="utf8",newline="\n")
