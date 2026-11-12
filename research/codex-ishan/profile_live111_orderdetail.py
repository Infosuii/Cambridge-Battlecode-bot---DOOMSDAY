"""Split charged field-order preparation into allocation/ranking/copy costs."""
from bounded_verdict import apply
from engine3_pool import HERE, read
from profile_live109_fine import scoped
from profile_live109_target import main
from profile_live111_fielddetail import detail
from profile_live111_first import exact_build


def order_detail(src, enabled, case):
    detail(src, enabled, case)
    apply(src / "world.cpp", (('#include "world.h"', '#include "world.h"\n#include "codex_trace.h"'),))
    edits = []
    for statement, name in (("    group_dist.reserve(groups.size());", "distance_reserve"),
                            ("    field_slot.assign(groups.size(), -1);", "slots"),
                            ("    field_ptr.assign(groups.size(), nullptr);", "pointers"),
                            ("    keys.reserve(groups.size());", "keys_reserve"),
                            ("    std::sort(keys.begin(), keys.end());", "keys_sort"),
                            ("    field_order.reserve(keys.size());", "order_reserve"),
                            ("    for (std::uint32_t k : keys) field_order.push_back(static_cast<int>(k & 0xFFF));", "order_copy")):
        edits.append((statement, f'    CODEX_FINE_MARK("prep_{name}_begin", 0, 0);\n' + statement + f'\n    CODEX_FINE_MARK("prep_{name}_end", 0, 0);'))
    scoped(src / "world.cpp", "void World::prepare_field_order() {", "bool World::build_next_group_field", edits)


if __name__ == "__main__":
    main(label="orderdetail111", cases=[read(HERE / "LIVE111_FIRST_TURN_PLAN.json")["case"]], prepare_fn=order_detail,
         build_fn=exact_build, expected_hash=read(HERE / "LIVE111_SOURCE_VERIFIED.json")["wasm_sha256"], project_prefix="live111-target")
