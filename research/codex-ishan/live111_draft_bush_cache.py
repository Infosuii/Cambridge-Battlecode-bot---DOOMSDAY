"""EXP263: cache static connectivity in existing field-cache slot padding."""
from shutil import copytree

import ablate_dev as bench
from engine3_pool import HERE,SDK_ROOT,read

REFERENCE='live111-owned-factorial-joint-20261106'

def patch(src,enabled,probe=False):
    p=src/'common.h';p.write_bytes(f'#define CODEX_DRAFT_BUSH_CACHE {int(enabled)}\n#define CODEX_DRAFT_BUSH_PROBE {int(probe)}\n'.encode()+p.read_bytes())
    for name in ('grouped_bush_codec.h','draft_bush_cache.h'):(src/name).write_bytes((HERE/name).read_bytes())
    p=src/'world.h';data=p.read_text(encoding='utf8');anchor='#include "common.h"';assert data.count(anchor)==1
    data=data.replace(anchor,anchor+'\n#if CODEX_DRAFT_BUSH_CACHE\n#include "grouped_bush_codec.h"\n#endif')
    anchor='    int bush_clusters = 0;';assert data.count(anchor)==1
    data=data.replace(anchor,anchor+'\n#if CODEX_DRAFT_BUSH_CACHE\n    bool codex_bush_checked=false;\n    codex_bush_codec::Cache codex_bush_cache;\n#endif')
    p.write_text(data,encoding='utf8',newline='\n')
    for name in ('main.cpp','world.cpp'):
        p=src/name;data=p.read_text(encoding='utf8');anchor='#include "codex_field_cache.h"';assert data.count(anchor)==1
        p.write_text(data.replace(anchor,anchor+'\n#include "draft_bush_cache.h"'),encoding='utf8',newline='\n')
    p=src/'main.cpp';data=p.read_text(encoding='utf8');anchor='                codex_field_cache::store();';assert data.count(anchor)==1
    data=data.replace(anchor,anchor+'\n#if CODEX_DRAFT_BUSH_CACHE\n                codex_draft_bush::store();\n#endif')
    p.write_text(data,encoding='utf8',newline='\n')
    p=src/'world.cpp';data=p.read_text(encoding='utf8');anchor='    if (!bit(bush_labeled, p)) {';assert data.count(anchor)==1
    data=data.replace(anchor,anchor+'''
#if CODEX_DRAFT_BUSH_CACHE
        if(!codex_bush_checked){
            codex_bush_checked=true;
            if(!bc::is_draft()){
                codex_bush_cache=codex_draft_bush::decode(bc::draft_memory.data(),bc::draft_memory.size(),width,height,groups.size(),bushes.export_linear_buffer());
                if(codex_bush_cache.valid)codex_bush_cache.published=bush_labeled.export_linear_buffer();
            }
        }
        if(codex_bush_codec::publish(codex_bush_cache,static_cast<std::size_t>(p.y*width+p.x),bush_label.get(),bush_clusters,bush_labeled))
            return bush_label[static_cast<std::size_t>(p.y*width+p.x)];
#endif''')
    p.write_text(data,encoding='utf8',newline='\n')

def prepare(src,enabled,probe=False):
    source=SDK_ROOT/'bots'/REFERENCE/'src';identity=read(HERE/(REFERENCE.upper()+'_SOURCE_VERIFIED.json'))
    assert all(bench.digest(source/n)==h for n,h in identity['source_file_hashes'].items())
    copytree(source,src);patch(src,enabled,probe)
