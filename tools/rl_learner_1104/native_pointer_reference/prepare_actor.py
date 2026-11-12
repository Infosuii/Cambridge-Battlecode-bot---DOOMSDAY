from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent;p=r/'native-query-actor';assert not p.exists();(p/'bots/submission').mkdir(parents=True)
src=p/'bots/submission/src';shutil.copytree(r/'conditional-runtime-review/bots/submission/src',src)
for n in ('sdk','cmake'):(p/n).symlink_to(r/'mac-project'/n,target_is_directory=True)
# Frozen native82d weights; remove diagnostic cheap gate relevance by native early return.
shutil.copyfile(r/'native_pointer_reference/original_native_header.h',src/'nn_weights.h')
f=src/'common.h';f.write_text('#define JD_NATIVE_ACTOR 1\n#define JD_NATIVE_MIN 18000\n#define JD_NATIVE_TEMP 0.5\n#define JD_NATIVE_BONUS 2.0\n#define JD_NATIVE_LOG 1\n#define JD_NATIVE_DET 1\n#define CLNA_SEED 110401\n'+f.read_text())
f=src/'nn_infer.h';s=f.read_text();needle='std::int16_t x[nnw::kTrunkIn], acc0[nnw::kTrunk], r[kE];';assert s.count(needle)==1
s=s.replace(needle,needle+'\n    std::int16_t jd_h1[nnw::kTrunk] = {}; int jd_h1_at = -1;',1)
needle='    dense16<kE>(kP_target_qW_TQ, kP_target_qbQ, h1, kTrunk, q, false);';assert s.count(needle)==1
s=s.replace(needle,needle+'\n    std::copy(h1,h1+kTrunk,lv.jd_h1);lv.jd_h1_at=static_cast<int>(bc::round_number());',1);f.write_text(s)
f=src/'nnrec.cpp';s=f.read_text();needle='    std::int16_t ec[10][16], ft[10][4];';assert s.count(needle)==1
s=s.replace(needle,needle+'\n    std::int16_t jd_h1[64]; int jd_h1_at=-1, jd_state[10];',1)
needle='    std::copy(nn_lv.x, nn_lv.x + 160, clna_snap.x);';assert s.count(needle)==1
s=s.replace(needle,needle+'\n    std::copy(nn_lv.jd_h1,nn_lv.jd_h1+64,clna_snap.jd_h1);clna_snap.jd_h1_at=nn_lv.jd_h1_at;',1)
# Capture camp state at the same packing point as each camp embedding.
needle='        const std::int16_t* r = f + coff + i * kCF;';pos=s.index('static void clna_take_snap');tail=s[pos:];assert needle in tail
# state assignment must follow presence check, before n increments. Inspect and insert at ec-copy.
needle2='        std::copy(nn_lv.ec[i], nn_lv.ec[i] + 16, clna_snap.ec[n]);';assert needle2 in tail
s=s.replace(needle2,'        clna_snap.jd_state[n]=r[7];\n'+needle2,1)
needle='    const int ref = nn_ens_keep(v92g, ng) ? v92g : ng;';assert s.count(needle)==1
s=s.replace(needle,needle+'\n#include "jd_native_actor.inc"',1);f.write_text(s)
shutil.copyfile(r/'native_pointer_reference/jd_native_actor.inc',src/'jd_native_actor.inc')
print(p)
