"""Diagnostic only: phase costs inside the move candidate builder (disposable copy; bot/src untouched).

Adds to fuel_trace.py's patch: fuel spent in blocking(), goal_field(), walk/dash enumeration and feature rows per
move build, averaged and printed every 100 rounds as `NPM ...` after gameplay.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fuel_trace as T  # noqa: E402

base_patch = T.patch


def patch(src):
    base_patch(src)
    q = src / 'nn_policy_tactics.cpp'; u = q.read_text(encoding='utf-8')
    u = T.sub(u, '        auto& x=boards();blocking(b,p,x);goal_field(b,state,p,x);',
              '        const auto mv0=bc::fuel_remaining();auto& x=boards();blocking(b,p,x);const auto mv1=bc::fuel_remaining();'
              'goal_field(b,state,p,x);const auto mv2=bc::fuel_remaining();')
    u = T.sub(u, '        nnpc::Candidate rows[nnpc::kMaxK]{};int n=0;\n        MovePick hold{};',
              '        const auto mv3=bc::fuel_remaining();nnpc::Candidate rows[nnpc::kMaxK]{};int n=0;\n        MovePick hold{};')
    u = T.sub(u, '        return nnpc::build(nncfg::H::move,rows,n,context(state),out)==nnpc::Error::ok;\n    }\n    template<class Fn>static bool targets',
              '        const bool built_ok=nnpc::build(nncfg::H::move,rows,n,context(state),out)==nnpc::Error::ok;\n'
              '        g_mv[0]+=mv0-mv1;g_mv[1]+=mv1-mv2;g_mv[2]+=mv2-mv3;g_mv[3]+=mv3-bc::fuel_remaining();g_mv[4]+=1;g_mv[5]+=total;\n'
              '        if(mv1-mv2>g_mv[6])g_mv[6]=mv1-mv2;\n        return built_ok;\n    }\n    template<class Fn>static bool targets')
    u = T.sub(u, 'struct nn_policy_tactics_access {', 'std::uint64_t g_mv[7]{};\nstruct nn_policy_tactics_access {')
    u = T.sub(u, 'bool build_move(const Bot& b,const OptionsState& s,nnpc::Decision& out) {',
              'void move_profile_report(){if(g_mv[4]&&bc::round_number()%100==0)std::printf("NPM n=%llu blocking=%llu goal=%llu goal_max=%llu enumerate=%llu rows=%llu endpoints=%llu\\n",'
              '(unsigned long long)g_mv[4],(unsigned long long)(g_mv[0]/g_mv[4]),(unsigned long long)(g_mv[1]/g_mv[4]),(unsigned long long)g_mv[6],'
              '(unsigned long long)(g_mv[2]/g_mv[4]),(unsigned long long)(g_mv[3]/g_mv[4]),(unsigned long long)(g_mv[5]/g_mv[4]));}\n'
              'bool build_move(const Bot& b,const OptionsState& s,nnpc::Decision& out) {')
    q.write_text(u, encoding='utf-8', newline='\n')
    r = src / 'nn_policy_runtime.cpp'; v = r.read_text(encoding='utf-8')
    v = T.sub(v, 'namespace nnp {\nvec2 canonical(', 'namespace nnp { void move_profile_report(); }\nnamespace nnp {\nvec2 canonical(')
    v = T.sub(v, '    g_tr.ready=false;\n', '    g_tr.ready=false;if(fuel()>20000)nnp::move_profile_report();\n')
    r.write_text(v, encoding='utf-8', newline='\n')


T.patch = patch
if __name__ == '__main__':
    T.main()
