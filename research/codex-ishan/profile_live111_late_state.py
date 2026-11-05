"""Expose whether the exact matched scorer cost forecast has a real measurement."""
from profile_live109_fine import scoped
from engine3_pool import HERE,read
from profile_live109_target import main
from profile_live111_first import exact_build
from profile_live111_late import instrument


def state(src,enabled,case):
    instrument(src,enabled,case)
    scoped(src/"nnrec.cpp","void Bot::nn_lazy_score() {","#ifdef A2_NN_FCMP",(("    static bool first_camps = true;",'''    static bool first_camps = true;
    CODEX_FINE_MARK("lazy_history",static_cast<int>(type),round,first_camps,nn_c_camps);
    CODEX_FINE_MARK("lazy_holds",static_cast<int>(type),round,nn_c_hold,nn_est_camps);'''),))


if __name__ == "__main__":
    main(label="latehistory111r2",cases=[read(HERE/"LIVE111_LATE_TURN_PLAN.json")["case"]],prepare_fn=state,
         build_fn=exact_build,expected_hash=read(HERE/"LIVE111_SOURCE_VERIFIED.json")["wasm_sha256"],project_prefix="live111-target")
