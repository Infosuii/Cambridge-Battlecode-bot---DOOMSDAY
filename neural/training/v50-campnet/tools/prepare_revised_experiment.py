"""Materialize the gameplay neural policy without changing the supplied baseline."""
from pathlib import Path
import shutil
import argparse

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--destination', type=Path, default=ROOT / 'candidate/src')
args = parser.parse_args()
src = args.destination.resolve()
shutil.copytree(ROOT / 'baseline/src', src, dirs_exist_ok=True)
common = src / 'common.h'
common.write_text('#define A2_CAMPNET 1\n' + common.read_text(encoding='utf-8'), encoding='utf-8')

p = src / 'bot.cpp'
s = p.read_text(encoding='utf-8').replace('#include "bot.h"', '#include "bot.h"\n#include "neural_policy.h"', 1)
start = s.index('#if A2_LAB\n    const float* W = lab::cn_w;', s.index('int Bot::campnet_pick'))
end = s.index('    // Keep the kCnK best', start)
s = s[:start] + '''    // Keep the original scorer when the turn cannot afford neural inference.
    if (bc::fuel_remaining() < static_cast<std::uint64_t>(tune::kDetSafety) + 18000) return base;
    const int mode = ngp::training() ? 1 : 0;
''' + s[end:]
start = s.index('        float out = W[lab_cn::kW - 1];', s.index('int Bot::campnet_pick'))
end = s.index('        mx = std::max(mx, logit[k]);', start)
s = s[:start] + '''        const float out = ngp::residual(f);
        logit[k] = A2_CN_SHARP * f[0] + (k == 0 ? A2_CN_BASE : 0.0f) + out;
''' + s[end:]
start = s.index('        static std::uint32_t rng = 0;', s.index('int Bot::campnet_pick'))
end = s.index('        while (pick < n - 1', start)
s = s[:start] + '        float u = ngp::uniform(slot) * z;\n' + s[end:]
needle = '    cn_commit_round = round;\n    best_need = cn[pick].need;'
assert needle in s
s = s.replace(needle, '''    if (ngp::training()) {
        float obs[8 * 18] = {};
        for (int k = 0; k < n; ++k)
            for (int i = 0; i < 18; ++i) obs[k * 18 + i] = cn[k].f[i];
        ngp::trace(my_id, round, n, pick, std::log(p[pick] / z), obs);
    }
    cn_commit_round = round;
    best_need = cn[pick].need;''', 1)
# Gather the expensive observations only for the final top-eight candidates,
# after the original ranking and route search have finished. Building inputs
# inside the scoring loop consumes the baseline's search budget prematurely.
feature_start = s.index('            int elks = 0, wolves = 0, big = 0;', s.index('if (score > 0.0f && n_cn < kCnMax)'))
feature_end = s.index('        }\n#endif', feature_start)
feature_code = s[feature_start:feature_end]
s = s[:feature_start] + '            c.f[16] = camp_taken_mult;\n' + s[feature_end:]
needle = '        float* f = cn[k].f;'
populate = '''        {
            CnCand& c = cn[k];
            const auto& g = w.groups[static_cast<std::size_t>(c.gi)];
            const int need = c.need;
            const float camp_taken_mult = c.f[16];
''' + feature_code + '        }\n'
s = s.replace(needle, populate + needle, 1)
p.write_text(s, encoding='utf-8')
p = src / 'draft.cpp'
s = p.read_text(encoding='utf-8')
s = '#include "neural_policy.h"\n' + s
s = s.replace('        have_feat = true;', '        ngp::map_trace(feat);\n        have_feat = true;', 1)
p.write_text(s, encoding='utf-8')

(src / 'neural_policy.h').write_text('''#pragma once
#include <cstdint>
namespace ngp {
bool training();
float residual(const float* features);
float uniform(int slot);
void trace(std::uint32_t champion, int round, int n, int pick, float logp, const float* obs);
void map_trace(const float* features);
}
''')
(src / 'neural_policy.cpp').write_text('''// Small trained policy; only this file is rebuilt when weights change.
#include "neural_policy.h"
#include "neural_weights.h"
#include <cmath>
#include <cstdio>
#include <cstring>
namespace ngp {
bool training() { return kTraining; }
static float fast_tanh(float x) {
    if (x > 4.97f) return 1.0f;
    if (x < -4.97f) return -1.0f;
    const float x2 = x * x;
    return x * (135135.0f + x2 * (17325.0f + x2 * (378.0f + x2))) /
        (135135.0f + x2 * (62370.0f + x2 * (3150.0f + x2 * 28.0f)));
}
float residual(const float* f) {
    float out = kWeights[320];
    float hidden[16];
    for (int j = 0; j < 16; ++j) hidden[j] = kWeights[288 + j];
    for (int i = 0; i < 18; ++i) {
        const float x = f[i] < -8.0f ? -8.0f : f[i] > 8.0f ? 8.0f : f[i];
        for (int j = 0; j < 16; ++j) hidden[j] += kWeights[i * 16 + j] * x;
    }
    for (int j = 0; j < 16; ++j) out += kWeights[304 + j] * fast_tanh(hidden[j]);
    return 4.0f * fast_tanh(out / 4.0f);
}
float uniform(int slot) {
    static std::uint32_t rng = 0;
    if (!rng) rng = kSeed ^ (2654435761u * static_cast<std::uint32_t>(slot + 1));
    rng = rng * 1664525u + 1013904223u;
    return static_cast<float>(rng >> 8) / 16777216.0f;
}
static void hex_record(const char* tag, const void* bytes, int count) {
    const unsigned char* b = static_cast<const unsigned char*>(bytes);
    const char* digits = "0123456789abcdef";
    char output[1400]; int at = 0;
    while (*tag) output[at++] = *tag++;
    for (int i = 0; i < count; ++i) {
        output[at++] = digits[b[i] >> 4]; output[at++] = digits[b[i] & 15];
    }
    output[at++] = '\\n'; std::fwrite(output, 1, at, stdout);
}
void trace(std::uint32_t champion, int round, int n, int pick, float logp, const float* obs) {
    if (!kTraining) return;
    // Fixed little-endian Wasm record: five u32s, old log probability, 8x18 features.
    unsigned char record[600];
    const std::uint32_t header[5] = {1u, champion, static_cast<std::uint32_t>(round),
        static_cast<std::uint32_t>(n), static_cast<std::uint32_t>(pick)};
    std::memcpy(record, header, 20); std::memcpy(record + 20, &logp, 4);
    std::memcpy(record + 24, obs, 576); hex_record("NGP1 ", record, 600);
}
void map_trace(const float* f) {
    if (kTraining) hex_record("NGPMAP ", f, 64);
}
}
''')
print(src)
