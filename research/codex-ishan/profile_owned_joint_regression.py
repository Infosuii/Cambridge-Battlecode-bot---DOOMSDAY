"""EXP252: freeze one genuine dev failure and reproduce the same rejected joint."""
import os
import re
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from profile_live109_target import HEADER,main,prepare
from profile_live111_first import exact_build


REFERENCE='live111-owned-factorial-joint-20261106'


def instrument(src,enabled,case):
    prepare(src,enabled,case,reference_name=REFERENCE)
    header=HEADER.replace('inline unsigned count = 0;','''inline unsigned count = 0;
inline bool active=false;
inline void begin(int type,int round){active=type==CODEX_TARGET_TYPE&&round==CODEX_TARGET_ROUND;}''')
    header=header.replace('if (type != CODEX_TARGET_TYPE || round != CODEX_TARGET_ROUND || count >= 96)','if (!active || count >= 96)')
    (src/'codex_trace.h').write_text(f"#define CODEX_TARGET_TYPE {case['type']}\n#define CODEX_TARGET_ROUND {case['round']}\n"+header,encoding='utf8',newline='\n')
    p=src/'main.cpp';data=p.read_text(encoding='utf8');anchor='                bot.play_turn();';assert data.count(anchor)==2
    data=data.replace(anchor,'''#if CODEX_FINE
                codex_trace::begin(static_cast<int>(bc::self().champion_name()),bc::round_number());
                CODEX_FINE_MARK("main_begin",0,0);
#endif
                bot.play_turn();''');p.write_text(data,encoding='utf8',newline='\n')
    p=src/'bot.cpp';data=p.read_text(encoding='utf8')
    data=re.sub(r'CODEX_FINE_MARK\("([a-zA-Z0-9_]+)", static_cast<int>\(type\), round\);',r'CODEX_FINE_MARK("\1",static_cast<int>(type),round,nn_spent,field_calls);',data)
    p.write_text(data,encoding='utf8',newline='\n')
    p=src/'nnrec.cpp';data=p.read_text(encoding='utf8')
    assert data.count('cxowned_hash=cxowned.input_hash();')==1
    data=data.replace('cxowned_hash=cxowned.input_hash();','// No timing-probe verification work in this phase census.')
    data=data.replace('cxowned.input_hash()==cxowned_hash','0')
    anchor='            if(codex_trace::active&&cxowned.captured_at==CODEX_TARGET_ROUND)codex_trace::frame_published=true;'
    assert data.count(anchor)==1;data=data.replace(anchor,'')
    p.write_text(data,encoding='utf8',newline='\n')


if __name__=='__main__':
    result=read(HERE/'LIVE111_OWNED_FACTORIAL_RESULT.json');build=read(HERE/'LIVE111_OWNED_FACTORIAL_BUILDS.json')['joint']
    identity={'source_file_hashes':build['sources'],'wasm_sha256':build['sha256'],
              'platform_submitted':False,'derived_from_platform_source':111,'scope':'Frozen local rejected joint,not an official source archive.'}
    write(HERE/(REFERENCE.upper()+'_SOURCE_VERIFIED.json'),identity)
    by={(r['map'],r['side'],r['opponent'],r['arm']):r for r in result['rows']}
    cells=[]
    for r in result['rows']:
        if r['arm']!='joint':continue
        a=by[r['map'],r['side'],r['opponent'],'stock']
        if r['fuel_outs']>a['fuel_outs'] or r['round1_fuel_outs']>a['round1_fuel_outs']:cells.append((a,r))
    assert len(cells)==1
    old,row=min(cells,key=lambda p:(p[1]['map_hash'],p[1]['side'],p[1]['opponent']))
    docs=[read(bench.ROOT/r['native_path']) for r in (old,row)];team='team'+row['side']
    def events(d):
        return [(x['timestamp']['round'],e['owner']['id'],e['owner']['name']) for e in d['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==team for x in e['entries']]
    old_events={(r,a) for r,a,n in events(docs[0])}
    choices=[e for e in events(docs[1]) if (e[0],e[1]) not in old_events]
    assert choices;round_number,actor,name=min(choices)
    output=bench.CACHE/'live111-owned-joint-regression-20261106';output.mkdir()
    directory=(bench.ROOT/row['native_path']).parent;archive,=directory.glob('*.repl26a');replay=output/'raw.repl26a'
    with ZipFile(archive) as z:
        with replay.open('xb') as f:f.write(z.read('replay.repl26a'))
    turn=output/'turn.json'
    subprocess.run(['node',HERE/'trace_turn.mjs',replay,str(round_number),str(int(row['side']=='B')),str(actor),turn],
                   cwd=bench.ROOT,env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},check=True)
    view=read(turn)
    case={**{k:row[k] for k in ('map','side','opponent','map_hash')},'stage':'ownedjointregression111','round':round_number,
          'actor':actor,'champion':name,'type':view['observation']['actor']['type'],
          'traces':{'base':{'path':turn.relative_to(bench.ROOT).as_posix(),'sha256':bench.digest(turn)}}}
    write(HERE/'LIVE111_OWNED_JOINT_REGRESSION_PLAN.json',{'selection':'Only regressed development cell,stable SHA then earliest unshared joint actor-round tuple; no official failure used.',
          'source_build':build['sha256'],'stock_native':old['native_sha256'],'joint_native':row['native_sha256'],
          'archive_sha256':bench.digest(archive),'case':case})
    print(case,flush=True)
    main(label='ownedjointregression111',cases=[case],prepare_fn=instrument,build_fn=exact_build,
         expected_hash=build['sha256'],project_prefix='live111-owned-joint-target')
