"""Isolated JNP3 collector: retain consumed h0 AND h1 for parity checks."""
from pathlib import Path
import shutil,re
r=Path(__file__).resolve().parents[1]; p=r/'native-upper-actor'
assert not p.exists(); (p/'bots/submission').mkdir(parents=True)
src=p/'bots/submission/src';shutil.copytree(r/'native-query-actor/bots/submission/src',src)
for n in ('sdk','cmake'):(p/n).symlink_to(r/'mac-project'/n,target_is_directory=True)
f=src/'common.h';s=f.read_text();assert '#define JD_NATIVE_LOG 0' in s;s=s.replace('#define JD_NATIVE_LOG 0','#define JD_NATIVE_LOG 1');f.write_text(s)
f=src/'nn_infer.h';s=f.read_text();needle='std::int16_t jd_h1[nnw::kTrunk] = {};';assert s.count(needle)==1;s=s.replace(needle,'std::int16_t jd_h0[nnw::kTrunk] = {}; '+needle)
needle='    std::copy(h1,h1+kTrunk,lv.jd_h1);';assert s.count(needle)==1;s=s.replace(needle,'    std::copy(h0,h0+kTrunk,lv.jd_h0);\n'+needle);f.write_text(s)
f=src/'nnrec.cpp';s=f.read_text();s=s.replace('std::int16_t jd_h1[64];','std::int16_t jd_h0[64], jd_h1[64];');needle='    std::copy(nn_lv.jd_h1,nn_lv.jd_h1+64,clna_snap.jd_h1);';assert s.count(needle)==2;s=s.replace(needle,'    std::copy(nn_lv.jd_h0,nn_lv.jd_h0+64,clna_snap.jd_h0);\n'+needle);s=re.sub(r'#define CLNA_SEED \d+ // JD_CYCLE_SEED','#define CLNA_SEED 110501 // JD_CYCLE_SEED',s);f.write_text(s)
f=src/'jd_native_actor.inc';s=f.read_text().replace('"JNP2 "','"JNP3 "');needle='    *o++=\'\\n\';std::fwrite';assert s.count(needle)==1;s=s.replace(needle,'    *o++=\' \';o+=jd_codec::hex_simd(reinterpret_cast<const std::uint8_t*>(clna_snap.jd_h0),128,o,cap());\n'+needle);f.write_text(s)
print(p)
