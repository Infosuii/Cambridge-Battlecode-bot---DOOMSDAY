"""EXP257: target-only ward clones retain original World cache and all earlier code."""
from engine3_pool import HERE,read
from profile_owned_joint_tail import prepare as tail
from profile_live109_target import main
from profile_live111_first import exact_build

def prepare(src,enabled,case):
    tail(src,enabled,case)
    p=src/'bot.cpp';data=p.read_text(encoding='utf8')
    spans=[('bool Bot::ward_ahead() {','\n#if A2_FOG','ward_ahead_profile'),
           ('bool Bot::ward_reveal() {','\nbool Bot::hidden_here()','ward_reveal_profile')]
    clones=[]
    for start,end,name in spans:
        a=data.index(start);b=data.index(end,a);body=data[a:b]
        body=body.replace(start,f'bool Bot::{name}() {{\n    codex_trace::mark("{name}",0,0);\n'+'''
    auto cx_bush=[&](vec2 p){
        const bool valid=in_bounds(p,w.width,w.height);
        const bool labelled=valid&&bit(w.bush_labeled,p);
        codex_trace::mark("bush_begin",0,0,valid?p.y*w.width+p.x:-1,labelled);
        const int id=w.bush_cluster(p);
        codex_trace::mark("bush_end",0,0,id,w.bush_clusters);
        return id;
    };
''')
        # The helper's one real call must remain original; only body query sites become traced.
        marker='        const int id=w.bush_cluster(p);';assert body.count(marker)==1
        body=body.replace(marker,'        const int id=CODEX_ORIGINAL_BUSH(p);')
        body=body.replace('w.bush_cluster(','cx_bush(').replace('CODEX_ORIGINAL_BUSH(p)','w.bush_cluster(p)')
        if name=='ward_reveal_profile':body=body.replace('ward_ahead()','ward_ahead_profile()')
        clones.append(body)
    anchor='__attribute__((noinline)) void Bot::play_tail_profile(){';a=data.index(anchor)
    before,clone=data[:a],data[a:]
    anchor='    if (ward_reveal()) w.update(round);';assert clone.count(anchor)==1
    clone=clone.replace(anchor,'''    const bool cx_ward=ward_reveal_profile();
    codex_trace::mark("ward_return",0,0,cx_ward,0);
    if(cx_ward){codex_trace::mark("ward_update_begin",0,0);w.update(round);codex_trace::mark("ward_update_end",0,0);}''')
    data=before+clone+'\n#if CODEX_MIN_TRACE\n'+'\n'.join(clones)+'\n#endif\n'
    p.write_text(data,encoding='utf8',newline='\n')
    p=src/'bot.h';data=p.read_text(encoding='utf8');anchor='    void play_tail_profile();';assert data.count(anchor)==1
    p.write_text(data.replace(anchor,anchor+'\n    bool ward_ahead_profile();\n    bool ward_reveal_profile();'),encoding='utf8',newline='\n')

if __name__=='__main__':
    plan=read(HERE/'LIVE111_OWNED_JOINT_REGRESSION_PLAN.json')
    main(label='ownedjointward111',cases=[plan['case']],prepare_fn=prepare,build_fn=exact_build,
         expected_hash=plan['source_build'],project_prefix='live111-owned-joint-ward')
