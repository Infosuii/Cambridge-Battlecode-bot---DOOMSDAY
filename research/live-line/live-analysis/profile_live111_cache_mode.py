"""Verify whether travel-mode coherence is the matched cache miss."""
from engine3_pool import HERE,read
from profile_live109_fine import scoped
from profile_live109_target import main
from profile_live111_cache_first import prepare
from profile_live111_first import exact_build


def mode(src,enabled,case):
    prepare(src,enabled,case)
    scoped(src/"bot.cpp","void Bot::build_fields() {","void Bot::play_turn() {",(
        ("    if (tune::kDet) {",'    CODEX_FINE_MARK("field_mode",0,0,w.bridges_on,w.groups.size());\n    if (tune::kDet) {'),
        ("        if (!w.fields_ready() && quota > 0) w.prepare_field_order();",'''        CODEX_FINE_MARK("prepare_begin",0,0,w.bridges_on,w.groups.size());
        if (!w.fields_ready() && quota > 0) w.prepare_field_order();
        CODEX_FINE_MARK("prepare_end",0,0,w.bridges_on,w.groups.size());'''),))


if __name__ == "__main__":
    plan=read(HERE/"LIVE111_CACHE_REMAINING_R1_PLAN.json")
    main(label="cachemode111",cases=[plan["case"]],prepare_fn=mode,build_fn=exact_build,expected_hash=plan["derived_release"],project_prefix="live111-target")
