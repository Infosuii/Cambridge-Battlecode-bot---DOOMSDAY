"""Verify the final source bundle and report paired map-level uncertainty."""
import argparse, hashlib, json, struct, tempfile, zipfile
from pathlib import Path
import numpy as np
import train

ROOT = train.ROOT

def sections(path):
    raw = Path(path).read_bytes()
    if raw[:8] != b'\0asm\x01\0\0\0': raise ValueError('Not a Wasm module')
    offset = 8; result = []
    while offset < len(raw):
        kind = raw[offset]; offset += 1; size = 0; shift = 0
        while True:
            byte = raw[offset]; offset += 1; size |= (byte & 127) << shift
            if not byte & 128: break
            shift += 7
        block = raw[offset:offset + size]; offset += size
        if kind: result.append((kind, hashlib.sha256(block).hexdigest()))
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--history',action='store_true');args=parser.parse_args()
    report = json.loads((ROOT / ('historical-training/final.json' if args.history else 'report.json')).read_text())
    stem='bot_neural_history' if args.history else 'bot_neural'
    src = ROOT / f'release/{stem}/src'
    archive = ROOT / f'release/{stem}.zip'
    candidate = ROOT / f'release/{stem}.wasm'
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if any(not n.startswith('src/') or '..' in Path(n).parts for n in names): raise ValueError('Unsafe archive member')
        for n in names:
            if z.read(n) != (ROOT / 'release' / stem / n).read_bytes(): raise ValueError('Source/archive mismatch')
    weights = (src / 'neural_weights.h').read_text()
    assert 'kTraining = false' in weights
    assert '#define A2_CAMPNET 1' in (src / 'common.h').read_text(encoding='utf-8')
    rebuilt = train.compile_bot(src, ROOT / f'release/{stem}-independently-rebuilt.wasm', 20)
    if sections(rebuilt) != sections(candidate): raise ValueError('Source rebuild changed executable Wasm sections')
    evaluation='history-final-'+report['selection']['fingerprint'] if args.history else 'final-holdout'
    neural = json.loads((ROOT / f'evaluation/{evaluation}.json').read_text())['rows']
    baseline = json.loads((ROOT / 'evaluation/original-holdout.json').read_text())['rows']
    def key(r): return (r['map'], Path(r['folder']).name, r['side'])
    original = {key(r): r for r in baseline}
    paired = []
    for r in neural:
        b = original[key(r)]
        paired.append(dict(map=r['map'], delta_win=r['win'] - b['win'],
                           delta_margin=r['gems'] - r['opponent_gems'] - (b['gems'] - b['opponent_gems']),
                           delta_fuel=r['fuel'] - b['fuel']))
    maps = sorted({r['map'] for r in paired})
    # Resample maps as clusters, never treat map/side/opponent cells as independent maps.
    win = np.array([np.mean([r['delta_win'] for r in paired if r['map'] == m]) for m in maps])
    margin = np.array([np.mean([r['delta_margin'] for r in paired if r['map'] == m]) for m in maps])
    rng = np.random.default_rng(20261023); indices = rng.integers(len(maps), size=(20000, len(maps)))
    win_ci = np.quantile(win[indices].mean(1), [0.025, 0.975]).tolist()
    margin_ci = np.quantile(margin[indices].mean(1), [0.025, 0.975]).tolist()
    verification = dict(source_archive_members=len(names), rebuild_executable_sections_equal=True,
                        training_trace_disabled=True, neural_gameplay_enabled=True,
                        source_sha256=train.sha(archive), wasm_sha256=train.sha(candidate),
                        independent_map_clusters=len(maps), paired_cells=len(paired),
                        win_rate_difference=float(win.mean()), win_rate_difference_map_bootstrap_95ci=win_ci,
                        gem_margin_difference=float(margin.mean()), gem_margin_difference_map_bootstrap_95ci=margin_ci,
                        evidence='stronger local performance supported' if win_ci[0] > 0 else 'local improvement not established with confidence',
                        caveat='Eight-map clustered bootstrap is exploratory; no ladder-strength claim.', paired=paired)
    train.write(ROOT / ('verification-history.json' if args.history else 'verification.json'), verification)
    print(json.dumps({k: v for k, v in verification.items() if k != 'paired'}, indent=2))

if __name__ == '__main__': main()
