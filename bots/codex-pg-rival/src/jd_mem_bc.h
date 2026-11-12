// jd_mem_bc.h (JD_MEM): engine glue for jd_mem.h. Draft writers submit through jd_draft_submit, which starts from
// the CURRENT host bytes (sdk_read_draft_memory, not the startup snapshot bc::draft_memory), writes only the
// writer's region and submits the prefix up to that region's end, so no writer can overwrite another's bytes.
#pragma once

#include <algorithm>
#include <array>
#include <span>

#include "common.h"
#include "jd_mem.h"

inline bool jd_draft_submit(jdmem::Region region, const std::uint8_t* bytes, std::size_t n) {
    std::array<std::uint8_t, jdmem::kDraftBytes> cur{};
    const std::size_t cap = std::min<std::size_t>(bc::constants::draft_memory_bytes, jdmem::kDraftBytes);
    if (cap == 0) return false;
    bc::detail::check(bc::detail::sdk_read_draft_memory(0, cur.data(), static_cast<std::uint32_t>(cap)));
    const std::size_t len = jdmem::merge(cur.data(), cap, region, bytes, n);
    if (len == 0) return false;
    bc::draft_memory = std::span<const std::uint8_t>(cur.data(), len);
    return true;
}
