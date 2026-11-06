"""EXP222 exact current-source feature cache, dynamic ranking and row attribution."""
from bounded_verdict import apply
from engine3_pool import HERE,read
from profile_live109_target import main
from profile_live111_first import exact_build
from profile_live111_late import instrument


def prepare(src,enabled,case):
    instrument(src,enabled,case)
    apply(src/'nnrec.cpp',(
        ('    if (gst.size() != w.groups.size() || gst_bridges != w.bridges_on) {',
         '''    CODEX_FINE_MARK("gstat_cache",static_cast<int>(type),round,gst.size(),w.groups.size());
    CODEX_FINE_MARK("gstat_mode",static_cast<int>(type),round,gst_bridges,w.bridges_on);
    if (gst.size() != w.groups.size() || gst_bridges != w.bridges_on) {'''),
        ('    struct GC { int gi; vec2 c; int d, wd, key; };','    CODEX_FINE_MARK("gstat_done",static_cast<int>(type),round);\n    struct GC { int gi; vec2 c; int d, wd, key; };'),
        ('    if (gc.empty())','    CODEX_FINE_MARK("gc_cache",static_cast<int>(type),round,gc.size(),0);\n    if (gc.empty())'),
        ('    const std::size_t here_idx = field_index(pos);','    CODEX_FINE_MARK("gc_dynamic",static_cast<int>(type),round,gc.size(),0);\n    const std::size_t here_idx = field_index(pos);'),
        ('    for (std::size_t i = 1; i < gc.size(); ++i) {','    CODEX_FINE_MARK("gc_sort",static_cast<int>(type),round,gc.size(),0);\n    for (std::size_t i = 1; i < gc.size(); ++i) {'),
        ('    for (int i = 0; i < NC; ++i, k += kCF) {','    CODEX_FINE_MARK("camp_rows",static_cast<int>(type),round,NC,AF);\n    for (int i = 0; i < NC; ++i, k += kCF) {'),))


if __name__=='__main__':
    main(label='featuredetail111',cases=[read(HERE/'LIVE111_LATE_TURN_PLAN.json')['case']],prepare_fn=prepare,
         build_fn=exact_build,expected_hash=read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256'],project_prefix='live111-target')
