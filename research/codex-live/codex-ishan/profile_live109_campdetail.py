"""Resolve cache initialization, ranking and row costs within the matched warm feature call."""
from bounded_verdict import apply
from engine3_pool import HERE, read
from profile_live109_target import main, prepare


def detail(src, enabled, case):
    prepare(src, enabled, case)
    apply(src / "nnrec.cpp", (
        ("    if (gst.size() != w.groups.size() || gst_bridges != w.bridges_on) {", '    CODEX_FINE_MARK("gstat_begin", static_cast<int>(type), round, w.groups.size());\n    if (gst.size() != w.groups.size() || gst_bridges != w.bridges_on) {'),
        ("    struct GC { int gi; vec2 c; int d, wd, key; };", '    CODEX_FINE_MARK("gstat_end", static_cast<int>(type), round);\n    struct GC { int gi; vec2 c; int d, wd, key; };'),
        ("    for (std::size_t i = 1; i < gc.size(); ++i) {", '    CODEX_FINE_MARK("sort_begin", static_cast<int>(type), round, gc.size());\n    for (std::size_t i = 1; i < gc.size(); ++i) {'),
        ("    for (int i = 0; i < NC; ++i, k += kCF) {", '    CODEX_FINE_MARK("rows_begin", static_cast<int>(type), round);\n    for (int i = 0; i < NC; ++i, k += kCF) {'),
    ))


if __name__ == "__main__":
    case = next(r for r in read(HERE / "LIVE109_RUNTIME_MATCHED_TURNS.json")["rows"] if r["stage"] == "61->62")
    main(label="campdetail", cases=[case], prepare_fn=detail)
