"""Native synthetic paused-flood scenario; never competitive evidence."""
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('screen',Path(__file__).with_name('screen.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
for label,safe in [('probe-cover-old',0),('probe-cover-fixed',1)]:
    # Freeze once, then inject only the diagnostic scenario before normal play.
    folder=s.OUT/'builds'/label
    if not folder.exists():
        import shutil
        shutil.copytree(s.ROOT/'bots/botx3/src',folder/'src')
        cfg=folder/'src/x1_config.h'
        text=cfg.read_text(encoding='utf-8')
        import re
        for key,value in [('X1_BUSHPRE',15),('X1_BUSHPRE_LAZY',60),('X3_COVER_SAFE',safe)]:
            text,n=re.subn(r'^#define '+key+r'\s+[^\n]+','#define '+key+' '+str(value),text,flags=re.M)
            if not n:text+='\n#define '+key+' '+str(value)+'\n'
        cfg.write_text(text,encoding='utf-8')
        p=folder/'src/main.cpp';text=p.read_text(encoding='utf-8')
        needle='            if (bc::is_draft()) {'
        injection='''            static bool probed = false;
            if (!bc::is_draft() && !probed) {
                probed = true;
                World probe;
                probe.width = bc::map::width(); probe.height = bc::map::height();
                probe.bush_label.reset(new std::uint16_t[probe.width * probe.height]);
                probe.bushes.clear(); probe.bush_labeled.clear(); probe.pre_seen.clear();
                vec2 root{1,1}, next{2,1};
                set_bit(probe.bushes, root); set_bit(probe.bushes, next);
                probe.pre_init = true; probe.pre_push(root);
                // Valid paused-flood state: root labelled, frontier not complete.
                set_bit(probe.bush_labeled, root);
                probe.bush_label[root.y * probe.width + root.x] = probe.pre_id;
                const int partial = probe.bush_cluster(root);
                probe.pre_step(0);
                const int complete = probe.bush_cluster(root);
                std::printf("COVER_PROBE partial%d complete%d expected%d pass%d\\n", partial, complete,
                    X3_COVER_SAFE ? -1 : 0, partial == (X3_COVER_SAFE ? -1 : 0) && complete == 0);
            }
'''
        assert text.count(needle)==1
        p.write_text(text.replace(needle,injection+needle),encoding='utf-8')
    wasm=folder/'bot.wasm'
    if not wasm.exists():s.dz.build(folder,wasm)
    target=s.OUT/'diagnostics'/label
    if not (target/'receipt.json').exists():s.dz.match(wasm,s.OUT/'opponents/v92.wasm',s.ROOT/'maps/local-benchmarks/01gold-rush.map26a','A',target,True,5)
    lines=[x for x in (target/'candidate.stdout').read_text().splitlines() if x.startswith('COVER_PROBE')]
    assert lines and all(x.endswith('pass1') for x in lines),lines
    print(label,lines,flush=True)
off=s.build('final-off',[])
assert s.dz.sha(off)=='1746f2bb7fa341530f41bd8c8c4896b35172783f35eacee8e4a4b6ac0ceea183'
