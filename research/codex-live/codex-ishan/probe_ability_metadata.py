"""EXP217 standalone normal-budget immutable ability metadata reader."""
import json
from shutil import copyfile
import subprocess

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, read
from freeze_engine3_discovery import write
from qualify_local import partition

if __name__=='__main__':
    out=bench.CACHE/'ability-metadata-20261106'
    out.mkdir()
    project=SDK_ROOT/'bots/codex-ability-metadata-20261106'
    src=project/'src';src.mkdir(parents=True)
    copyfile(HERE/'ability_metadata_probe.cpp',src/'main.cpp')
    wasm=project/'bot.wasm'
    assert bench.digest(CLI)==CLI_HASH
    mp=min(partition('dev'),key=lambda p:bench.digest(p))
    ref=bench.CACHE/bench.OPPS['v92'][0]
    assert bench.digest(ref)==bench.OPPS['v92'][1]
    with (project/'build.log').open('xb') as log:
        subprocess.run([CLI,'build',project,'--release','--output',wasm],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    with (out/'run.log').open('xb') as log:
        subprocess.run([CLI,'run',wasm,ref,'--map',mp,'--release','--fuel','100000','--json','--log-limit','50000',
                        '--statistics',out/'native.json','--out-dir',out],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    doc=read(out/'native.json')
    assert (doc['match']['engineVersion'],doc['match']['engineBuildHash'])==('3.0.0',ENGINE)
    assert doc['diagnostics']['detailedCaptureComplete']
    result={'engine':ENGINE,'cli_sha256':CLI_HASH,'sdk_header_sha256':bench.digest(SDK_ROOT/'sdk/cpp/cambc.h'),
            'source_sha256':bench.digest(src/'main.cpp'),'wasm_sha256':bench.digest(wasm),'map_sha256':bench.digest(mp),
            'reference_sha256':bench.digest(ref),'native_sha256':bench.digest(out/'native.json'),
            'run_log_sha256':bench.digest(out/'run.log'),'artifact_dir':str(out),
            'limits':'Metadata prerequisite only; stdout retained in replay/archive or run output, no action-reach/strength claim'}
    write(HERE/'ABILITY_METADATA_20261106_PINS.json',result)
    print(json.dumps(result,indent=2),flush=True)
