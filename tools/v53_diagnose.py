"""Reproducible v52 logging/profile builds; never edits a submitted source tree."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import re
import zipfile
from nfs import engine

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', action='store_true')
    p.add_argument('--rounds', type=int, default=1200)
    p.add_argument('--maps', nargs='+', default=['01boss-battle', '01concentrated-wealth', '00elkring', '00swirl', '01yellow-brick-road'])
    a = p.parse_args()
    label = 'profile' if a.profile else 'log'
    root = ROOT / 'artifacts/local-only/v53-review' / label
    root.mkdir(parents=True, exist_ok=True)
    common = (ROOT/'bots/v52/src/common.h').read_text()
    world = (ROOT/'bots/v52/src/world.cpp').read_text()
    assert world.count('if (APEX_LOG)') == 1
    overrides = {'common.h': ('#define APEX_PROFILE 1\n' if a.profile else '#define APEX_LOG 1\n') + common,
                 'world.cpp': world.replace('if (APEX_LOG)', 'if (0)')}
    bot = engine.make_bot_dir(ROOT/'bots/v52/src', root/'bot', overrides)
    wasm = engine.official_build(bot, root/'bot.wasm')
    def run(m):
        out = root/m
        out.mkdir(exist_ok=True)
        text = engine._run([engine.CLI, 'run', wasm, ROOT/'artifacts/tmp/v52.wasm', '--map', engine.MAPS/f'{m}.map26a',
                            '--rounds', a.rounds, '--release', '--log-limit', '16000000', '--out-dir', out], timeout=1800)
        (out/'run.log').write_text(text, encoding='utf8')
        for replay in out.glob('*.repl26a'):
            with zipfile.ZipFile(replay) as z:
                raw = z.read('team-a.stdout')
                (out/'team-a.txt').write_text('\n'.join(x.decode('utf8', errors='replace') for x in re.findall(rb'[\x20-\x7e]{5,}', raw)), encoding='utf8')
        print(m, 'done', flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(run, a.maps))

if __name__ == '__main__':
    main()
