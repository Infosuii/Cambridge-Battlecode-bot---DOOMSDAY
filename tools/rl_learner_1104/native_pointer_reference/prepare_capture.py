from pathlib import Path
import shutil
r=Path(__file__).resolve().parent;p=r/'native-pointer-audit';assert not p.exists()
(p/'bots/submission').mkdir(parents=True);src=p/'bots/submission/src'
shutil.copytree(r/'head-cached-review/bots/submission/src',src)
for n in ('sdk','cmake'):(p/n).symlink_to(r/'mac-project'/n,target_is_directory=True)
f=src/'common.h';s=f.read_text()
for line in ['#define CLNA_HEAD 1\n','#define CLNA_HEAD_MIN 35000\n','#define CLNA_RLOG 1\n','#define CLNA_EPS 0.02\n']:s=s.replace(line,'',1)
f.write_text(s)
f=src/'nn_infer.h';s=f.read_text()
# Only the fixed-point Live branch. Original inference math stays unchanged.
s=s.replace('std::int16_t x[nnw::kTrunkIn], acc0[nnw::kTrunk], r[kE];','std::int16_t x[nnw::kTrunkIn], acc0[nnw::kTrunk], r[kE];\n    std::int16_t jd_h1[nnw::kTrunk] = {}, jd_q[kE] = {};',1)
needle='    dense16<kE>(kP_target_qW_TQ, kP_target_qbQ, h1, kTrunk, q, false);'
assert s.count(needle)==1
s=s.replace(needle,needle+'\n    std::copy(h1,h1+kTrunk,lv.jd_h1); std::copy(q,q+kE,lv.jd_q);',1)
needle='    o.target[kNC] = static_cast<float>(dot16(nnw::kP_target_EQ, lv.r) + lv.c0) * sc;'
assert s.count(needle)==1
trace='''
    // Bounded diagnostic output only; never a strength or unmodified-fuel claim.
    static int jd_rows = 0;
    if (jd_rows < 12 && bc::fuel_remaining() > 20000u) {
        ++jd_rows;
        std::printf("JDNATIVE %u %u %d %d",bc::round_number(),static_cast<unsigned>(static_cast<bc::handle_champion_t>(bc::self())),jd_rows,lv.c0);
        for (int i=0;i<nnw::kTrunk;++i) std::printf(" %d",lv.jd_h1[i]);
        for (int i=0;i<kE;++i) std::printf(" %d",lv.jd_q[i]);
        for (int i=0;i<kE;++i) std::printf(" %d",lv.r[i]);
        for (int i=0;i<kNC;++i) {
            std::printf(" %d",lv.pc[i]?1:0);
            for(int j=0;j<kE;++j) std::printf(" %d",lv.ec[i][j]);
        }
        for (int i=0;i<=kNC;++i) std::printf(" %.9g",static_cast<double>(o.target[i]));
        std::printf("\\n");
    }
'''
s=s.replace(needle,needle+trace,1);f.write_text(s)
print(p)
