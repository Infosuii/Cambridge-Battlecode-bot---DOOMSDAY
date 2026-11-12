"""Resolve current111 first-turn field preparation versus search cost."""
from bounded_verdict import apply
from engine3_pool import HERE, read
from profile_live109_fine import scoped
from profile_live109_target import main
from profile_live111_first import exact_build, instrument


def detail(src, enabled, case):
    instrument(src, enabled, case)
    scoped(src / "bot.cpp", "void Bot::build_fields() {", "void Bot::play_turn() {", (
        ("    if (tune::kDet) {", '    CODEX_FINE_MARK("field_entry", static_cast<int>(type), round, nn_spent, field_calls);\n    if (tune::kDet) {'),
        ("        if (!w.fields_ready() && quota > 0) w.prepare_field_order();", '''        CODEX_FINE_MARK("field_prepare_begin", static_cast<int>(type), round, full, quota);
        if (!w.fields_ready() && quota > 0) w.prepare_field_order();
        CODEX_FINE_MARK("field_prepare_end", static_cast<int>(type), round, full, quota);'''),
        ("            if (!w.build_next_group_field(full)) return;", '''            CODEX_FINE_MARK("field_search_begin", static_cast<int>(type), round, full, nn_spent);
            if (!w.build_next_group_field(full)) return;
            CODEX_FINE_MARK("field_search_end", static_cast<int>(type), round, full, nn_spent);'''),
    ))


if __name__ == "__main__":
    case = read(HERE / "LIVE111_FIRST_TURN_PLAN.json")["case"]
    main(label="fielddetail111", cases=[case], prepare_fn=detail, build_fn=exact_build,
         expected_hash=read(HERE / "LIVE111_SOURCE_VERIFIED.json")["wasm_sha256"], project_prefix="live111-target")
