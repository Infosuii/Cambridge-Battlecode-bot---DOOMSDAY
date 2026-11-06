"""Capture and profile the entire new frozen cohort with the established backoff."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import subprocess
import sys

import ablate_dev as bench
from engine3_pool import CLI,ENGINE,HERE,read
from freeze_live111c_discovery import OUT,PREFIX


if __name__=='__main__':
    sample=read(HERE/f'{PREFIX}_DISCOVERY_SPLIT.json')
    spec=importlib.util.spec_from_file_location('losses_recent',bench.ROOT/'tools/ladder/losses_recent.py')
    collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector);collector.CLI=str(CLI)
    for mode in ('summaries','replays'):
        directory=OUT/mode;directory.mkdir(exist_ok=True)
        def fetch(row):
            mid=row['matchId'];target=directory/(mid+('.json' if mode=='summaries' else '.zip'))
            args=['matches','summary','--json',mid] if mode=='summaries' else ['matches','download',mid]
            assert collector.fetch(args,target),mid
            if mode=='summaries':
                d=read(target)
                assert (d['match']['engineVersion'],d['match']['engineBuildHash'])==('3.0.0',ENGINE) and d['diagnostics']['detailedCaptureComplete']
            return mid
        with ThreadPoolExecutor(max_workers=2) as pool:
            for i,_ in enumerate(pool.map(fetch,sample['matches']),1):
                if i%20==0 or i==len(sample['matches']):print(f'{mode} {i}/{len(sample["matches"])}',flush=True)
        tool='profile_engine3_discovery.py' if mode=='summaries' else 'profile_engine3_replays.py'
        for part in ('discovery','control','confirm'):
            if not any(r['partition']==part for r in sample['matches']):continue
            with (OUT/f'{part}-{mode}.log').open('xb') as log:
                subprocess.run([sys.executable,HERE/tool,part,'--prefix',PREFIX,'--data-dir',OUT],cwd=bench.ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
            print(f'{mode} {part} profile verified',flush=True)
