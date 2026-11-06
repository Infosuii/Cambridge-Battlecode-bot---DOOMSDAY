"""EXP241: enumerate actual compiled graph references without changing source/builds."""
import re
import subprocess

import ablate_dev as bench
from engine3_pool import HERE,SDK_ROOT,read
from freeze_engine3_discovery import write


if __name__=='__main__':
    source=SDK_ROOT/'bots/live111/src';identity=read(HERE/'LIVE111_SOURCE_VERIFIED.json')
    assert all(bench.digest(source/n)==sha for n,sha in identity['source_file_hashes'].items())
    commands=SDK_ROOT/'bots/live111/.cambc/build-release/compile_commands.json'
    row,=[r for r in read(commands) if r['file'].endswith('nnrec.cpp')]
    prefix=row['command'].split(' -o ',1)[0]
    assert '"' not in prefix and "'" not in prefix
    args=prefix.split()+['-E','-dD',str(source/'nnrec.cpp')]
    output=bench.CACHE/'live111-graph-ownership-20261106';output.mkdir()
    target=output/'nnrec.preprocessed.cpp'
    with target.open('xb') as out,(output/'preprocess.log').open('xb') as log:
        subprocess.run(args,cwd=output,stdout=out,stderr=log,check=True)
    current_file='';current_line=0;references=[];macros={}
    for text in target.read_text(encoding='utf8').splitlines():
        location=re.match(r'# (\d+) "([^"]+)"',text)
        if location:
            current_line=int(location[1]);current_file=location[2];continue
        define=re.match(r'#define ((?:A2_NN|CLFS|V58_ACT)\w*)\s*(.*)',text)
        if define:macros[define[1]]=define[2]
        undef=re.match(r'#undef ((?:A2_NN|CLFS|V58_ACT)\w*)',text)
        if undef:macros.pop(undef[1],None)
        if re.search(r'\bnn_lv\b',text):
            references.append({'file':current_file,'line':current_line,'code':text.strip()})
        current_line+=1
    report={'platform_source':111,'exact_release':identity['wasm_sha256'],'source_archive':identity['archive_sha256'],
            'compile_commands_sha256':bench.digest(commands),'preprocessor_args':args,'preprocessed_sha256':bench.digest(target),
            'artifact':target.relative_to(bench.ROOT).as_posix(),'macros':macros,'references':references,
            'limits':'Compiled-reference inventory only; no exclusive-owner implementation, correctness or safety proof. Original source/build objects unchanged.'}
    write(HERE/'LIVE111_GRAPH_OWNERSHIP_INVENTORY.json',report)
    print({'references':len(references),'macros':macros,'active_lines':references},flush=True)
