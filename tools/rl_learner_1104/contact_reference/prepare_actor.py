"""Create an isolated, initially zero-weight stochastic contact actor, not a deployment."""
from pathlib import Path
import shutil
import argparse

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--project', default='native-contact-actor')
args = parser.parse_args()
assert Path(args.project).name == args.project, 'Project must be a single directory name'
project = root / args.project
assert not project.exists(), 'Refusing to overwrite an existing actor'
src = project / 'bots/submission/src'
src.parent.mkdir(parents=True)
shutil.copytree(root / 'native-contact-probe/bots/submission/src', src)
for name in ('sdk', 'cmake'):
    (project / name).symlink_to(root / 'mac-project' / name, target_is_directory=True)
shutil.copyfile(root / 'mac-project/cambc.toml', project / 'cambc.toml')
header = (src / 'jd_contact_probe.h').read_text()
start = header.index('// NONTRAINED diagnostic coefficients.')
end = header.index('inline void score(', start)
header = header[:start] + '''// Initial trainable head: all zero; keep receives a fixed +2 logit prior.
inline constexpr std::array<std::int16_t,48*8> W{};
inline constexpr std::int16_t bias[8]={};
#ifndef JD_CONTACT_SEED
#define JD_CONTACT_SEED 110701ULL
#endif
inline std::uint64_t rng=JD_CONTACT_SEED;
inline bool rng_initialized=false;
inline void initialize_rng(int body){
    if(!rng_initialized){rng^=static_cast<std::uint64_t>(body)*0xd1342543de82ef95ULL;rng_initialized=true;}
}
inline double uniform(){
    rng+=0x9e3779b97f4a7c15ULL;auto z=rng;
    z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;
    z=(z^(z>>27))*0x94d049bb133111ebULL;
    z^=z>>31;
    return static_cast<double>(z>>11)*0x1.0p-53;
}
inline int choose(const bool* valid,const std::int16_t* z,double* prob){
    double logits[3], maximum=-1e100,total=0;
    for(int j=0;j<3;++j){logits[j]=z[j]/1024.0+(j==0?2.0:0.0);if(valid[j])maximum=std::max(maximum,logits[j]);}
    for(int j=0;j<3;++j){prob[j]=valid[j]?std::exp(logits[j]-maximum):0;total+=prob[j];}
    for(int j=0;j<3;++j)prob[j]/=total;
    const double u=uniform();double c=0;int last=0;
    for(int j=0;j<3;++j)if(valid[j]){last=j;c+=prob[j];if(u<c)return j;}
    return last;
}
''' + header[end:]
start = header.index('inline void record(')
header = header[:start] + '''inline void record(int logical,int body,int seq,int ref_win,int ref_danger,const bool* valid,const std::int16_t* x,const std::int16_t* z,int action,const double* prob){
    char row[1024];int n=std::snprintf(row,sizeof row,"JCA1 %d %u %d %d %d %d %d %.17g %.17g %.17g ",logical,bc::round_number(),body,seq,ref_win,ref_danger,action,prob[0],prob[1],prob[2]);
    for(int j=0;j<3;++j)row[n++]=valid[j]?'1':'0';row[n++]=' ';
    n+=jd_codec::hex_simd(reinterpret_cast<const std::uint8_t*>(x),96,row+n,sizeof row-n);row[n++]=' ';
    n+=jd_codec::hex_simd(reinterpret_cast<const std::uint8_t*>(z),16,row+n,sizeof row-n);row[n++]='\\n';
    std::fwrite(row,1,n,stdout);std::fflush(stdout);
}
}
'''
(src / 'jd_contact_probe.h').write_text(header)
features = (src / 'jd_contact_features.inc').read_text()
features = features.replace('// Shadow only.', '// Stochastic training actor, complete uncapped admitted-command logging.')
features = features.replace('jd_contact::records<8 && ', '')
old = '++jd_contact::records;jd_contact::record(round,static_cast<int>(my_id),jd_contact::records,winning,in_danger,valid,q,z,f0,f1,f2);'
assert features.count(old) == 1
features = features.replace(old, '''jd_contact::initialize_rng(static_cast<int>(my_id));
                double prob[3];const int action=jd_contact::choose(valid,z,prob);
                ++jd_contact::records;
                jd_contact::record(round,static_cast<int>(my_id),jd_contact::records,winning,in_danger,valid,q,z,action,prob);
                const bool fresh=bc::round_number()==static_cast<unsigned>(round);
                if(fresh && action==1){winning=true;in_danger=false;}
                if(fresh && action==2){winning=false;in_danger=true;if(threat_on_me<=0)threat_on_me=1;}
                std::printf("JCE1 %d %d %u %d %llu\\n",static_cast<int>(my_id),jd_contact::records,bc::round_number(),fresh,static_cast<unsigned long long>(bc::fuel_remaining()));std::fflush(stdout);''')
(src / 'jd_contact_features.inc').write_text(features)
print(project)
