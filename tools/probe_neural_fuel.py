"""Official release/default-fuel probe. No training. Scratch sources only.

Measures real capture/encode and explicitly synthetic dense kernel/record fixtures AFTER teacher decisions.
Never interprets synthetic timing fixtures as gameplay strength. --prepare-only requires no official compiler.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine
from nfs.evaluate import protocol

PROBE = r'''
#include "bot.h"
#include "nn_obs.h"
#include "nn_model.h"
#include "nn_log.h"
#define NN_REGISTRY_WANT_MODELS
#include "nn_registry.h"
#include <cstdio>
namespace nnprobe {
static int index;
static volatile float sink;
static nnobs::RawTurn raw;
static float x[nnobs::kObsDim], h[nnm::kMaxCtx], feat[16*24], prior[16], logits[16];
static std::uint8_t legal[16];
static std::uint32_t ids[16];
static nnm::Scratch scratch;
void run(const Bot& bot) {
    if (index >= 43 || bc::fuel_remaining() < 65000 || nnreg::kNumModels == 0) return;
    const auto& m = *nnreg::kModels[0];
    const int i = index++;
    const char* component = "capture_real";
    int head = -1, K = 0;
    // All preparation is outside the measured kernel interval. Dense features are synthetic worst-shape fixtures.
    for (int j=0;j<nnobs::kObsDim;++j) x[j] = 0.1f + float((j+i)%7)*0.1f;
    for (int j=0;j<m.ally_rows;++j) x[m.self_dim+m.ally_rows*m.ally_dim+j]=1.0f;
    const int em = m.self_dim+m.ally_rows*m.ally_dim+m.ally_rows+m.enemy_rows*m.enemy_dim;
    for (int j=0;j<m.enemy_rows;++j) x[em+j]=1.0f;
    for(int j=0;j<m.ctx;++j) h[j]=0.125f;
    for(int j=0;j<16*24;++j) feat[j]=0.25f+float(j%5)*0.1f;
    for(int j=0;j<16;++j) prior[j]=j ? -0.125f : 0.0f, legal[j]=1,ids[j]=j;
    if (i==1) nnobs::capture(bot,raw);
    if (i>=3 && i<42) head=(i-3)/3,K=(i-3)%3==0 ? 1 : (i-3)%3==1 ? 4 : 16;
    const auto before=bc::fuel_remaining();
    if(i==0) { nnobs::capture(bot,raw); sink=raw.round; }
    else if(i==1) { component="obs_encode_real"; nnobs::encode(raw,x); sink=x[0]; }
    else if(i==2) { component="encoder_synthetic_dense"; nnm::encode(m,x,h,scratch); sink=h[0]; }
    else if(i<42) {
        const auto& hd=m.head[head];
        if(hd.kind==nnm::Kind::candidate) {
            component="candidate_synthetic_dense";
            nnm::candidate_logits(m,hd,hd.uses_ctx?h:nullptr,0,feat,K,legal,prior,logits); sink=logits[K-1];
        } else if(hd.kind==nnm::Kind::leaf) {
            component="leaf_synthetic_dense"; sink=nnm::leaf_out(m,hd,h,0,feat);
        } else {
            component="value_synthetic_dense"; nnm::value_out(m,hd,h,logits);sink=logits[0];
        }
    } else {
        component="record_enqueue_synthetic_max"; K=16;
        nnlog::DecisionRec rec{nnobs::kObsSchemaHash,int(bc::round_number()),0,6,16,24,0,1,1,0,0,0,
                              prior,legal,ids,feat,0,0,0,logits};
        nnlog::enqueue_decision(rec);
    }
    const auto after=bc::fuel_remaining();
    std::printf("NFP1 component=%s head=%d K=%d fuel=%llu\n",component,head,K,
                static_cast<unsigned long long>(before-after));
    if(i==42 && bc::fuel_remaining()>40000) {
        const auto begin=bc::fuel_remaining(); nnlog::flush_one(); const auto end=bc::fuel_remaining();
        std::printf("NFP1 component=record_flush_synthetic_max head=-1 K=16 fuel=%llu\n",
                    static_cast<unsigned long long>(begin-end));
    }
}
}
'''


def prepare(dest):
    bot = engine.make_bot_dir(ROOT / 'bot/src', dest / 'bot')
    subprocess.run([sys.executable, str(ROOT / 'tools/install_models.py'), '--profile', 'dev_untrained',
                    '--src', str(bot / 'src'), '--receipt', str(dest / 'install.json')], check=True, cwd=ROOT)
    main = bot / 'src/main.cpp'
    text = main.read_text(encoding='utf-8')
    text = text.replace('int main() {', 'namespace nnprobe { void run(const Bot&); }\nint main() {')
    text = text.replace('bot.play_turn();', 'bot.play_turn(); nnprobe::run(bot);')
    main.write_text(text, encoding='utf-8', newline='\n')
    (bot / 'src/nn_probe.cpp').write_text(PROBE, encoding='utf-8', newline='\n')
    return bot


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default='artifacts/tmp/fuel_probe')
    ap.add_argument('--prepare-only', action='store_true')
    ap.add_argument('--maps', nargs='+', default=['00rows', '01islands'])
    args = ap.parse_args()
    dest = (ROOT / args.out).resolve()
    dest.relative_to(ROOT)
    training = protocol.load_schedule('map_partitions')['partitions']['training']
    if not set(args.maps) <= set(training):
        raise SystemExit('probe maps must be frozen training-partition reused benchmarks')
    bot = prepare(dest)
    if args.prepare_only:
        print('prepared only; engine measurements NOT RUN:', bot)
        return
    wasm = engine.official_build(bot, dest / 'probe.wasm')
    rows, games = [], []
    for name in args.maps:
        mp = engine.MAPS / (name + '.map26a')
        folder = dest / 'matches' / (engine.sha256(wasm)[:12] + '-' + name)
        result = engine.run_match(wasm, ROOT / 'references/builds/original.wasm', mp, folder)
        games.append(result.row())
        stdout = engine.team_stdout(folder, 'A')
        for component, head, K, fuel in re.findall(r'NFP1 component=(\S+) head=(-?\d+) K=(\d+) fuel=(\d+)', stdout):
            rows.append(dict(map=name, component=component, head=int(head), K=int(K), fuel=int(fuel)))
    groups = {}
    for row in rows:
        key = (row['component'], row['head'], row['K'])
        groups.setdefault(key, []).append(row['fuel'])
    summaries = [dict(component=k[0], head=k[1], K=k[2], count=len(v), min=min(v), max=max(v),
                      mean=sum(v)/len(v)) for k,v in sorted(groups.items())]
    report = dict(label='untrained framework fuel probe; kernels/records synthetic; capture/encode real',
                  release=True, fuel='official default', protocol_sha256=protocol.protocol_sha256(),
                  candidate_sha256=engine.sha256(wasm), source_sha256=engine.tree_sha256(bot/'src'),
                  map_label='reused_benchmark', games=games, measurements=rows, components=summaries)
    out = ROOT / 'evaluation/evidence/neural_fuel_probe.json'
    engine.write_json(out, report)
    print(json.dumps(summaries, indent=2))
    if not rows:
        raise SystemExit('FAIL: no NFP1 measurements; budget remains provisional')
    print('Measured evidence:', out)


if __name__ == '__main__':
    main()
