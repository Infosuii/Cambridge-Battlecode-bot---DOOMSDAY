"""Check EXP-009 components on all frozen development maps with the official engine."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
import json
import re
import subprocess
import zipfile
import ablate_dev as h

OUT = h.CACHE / 'bushlinear-check'

def one(mp):
    dst = OUT / 'games-complete' / mp.stem
    dst.mkdir(parents=True)
    with (dst / 'run.log').open('wb') as log:
        subprocess.run([h.CLI, 'run', OUT / 'bot.wasm', h.CACHE / 'v92.wasm', '--map', mp,
                        '--release', '--json', '--statistics', dst / 'native.json',
                        '--out-dir', dst], cwd=h.ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
    with zipfile.ZipFile(next(dst.glob('*.repl26a'))) as archive:
        text = archive.read('team-a.stdout').decode('utf8', 'replace')
    lines = re.findall(r'BUSH_EQ[^\n]+', text)
    assert len(lines) == 1, (mp.name, lines)
    values = {k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', lines[0])}
    assert values['mismatches'] == values['packing_mismatches'] == 0, mp.name
    assert values['mask_equal'] == 1 and values['components'] == values['reference_components'], mp.name
    native = json.loads((dst / 'native.json').read_bytes())
    assert native['match']['engineBuildHash'] == h.ENGINE
    assert native['diagnostics']['botFaults']['teamA'] == 0
    exhausted = sum(len(e['entries']) for e in native['events']
                    if e['kind'] == 'fuelExhausted' and e['owner']['team'] == 'teamA')
    draft_exhausted = sum(1 for e in native['events']
                          if e['kind'] == 'fuelExhausted' and e['owner']['team'] == 'teamA'
                          for x in e['entries'] if x['timestamp']['round'] == 0)
    assert draft_exhausted == 0, mp.name
    return {'map': mp.name, 'map_sha256': h.digest(mp), 'diagnostic_game_fuel_outs': exhausted, **values}

def main():
    maps = sorted((h.CACHE / 'jd-sets/dev').glob('*.map26a')) + sorted((h.CACHE / 'jd-sets/conf').glob('*.map26a'))
    assert len(maps) == 106
    unique = {}
    for mp in maps:
        if mp.name in unique:
            assert h.digest(mp) == h.digest(unique[mp.name])
        unique[mp.name] = mp
    maps = list(unique.values())
    assert len(maps) == 90  # The 16-map stress subset belongs to the development set.
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(one, maps):
            rows.append(row)
            if len(rows) % 20 == 0:
                print(f'{len(rows)}/{len(maps)}', flush=True)
    result = {'engine': h.ENGINE, 'fixture_sha256': h.digest(OUT / 'bot.wasm'),
              'maps': len(rows), 'tiles': sum(r['tiles'] for r in rows),
              'components': sum(r['components'] for r in rows),
              'mismatches': sum(r['mismatches'] for r in rows),
              'packing_mismatches': sum(r['packing_mismatches'] for r in rows),
              'optimized_fuel': sum(r['optimized_fuel'] for r in rows),
              'reference_fuel': sum(r['reference_fuel'] for r in rows), 'rows': rows}
    with (Path(__file__).parent / 'BUSH_EQUIVALENCE.json').open('x', encoding='utf8', newline='\n') as file:
        json.dump(result, file, indent=2)
        file.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2), flush=True)

if __name__ == '__main__':
    main()
