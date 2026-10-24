// rt_parity.cpp (agent B) - native driver for the Torch/numpy <-> C++ parity tests (tests/python/test_rt_parity.py).
// Reads a binary fixture (synthetic model + cases, written by the Python test), runs the C++ kernels of
// bot/src/nn_model.h / nn_rt.h, writes the outputs. Format: see write_fixture() in tests/python/test_rt_parity.py.
#include <cstdio>
#include <cstring>
#include <vector>

#include "nn_model.h"
#include "nn_rt.h"

static std::vector<unsigned char> g_in;
static size_t g_pos = 0;
template <class T> static T get() {
    T v;
    std::memcpy(&v, g_in.data() + g_pos, sizeof(T));
    g_pos += sizeof(T);
    return v;
}
template <class T> static void put(std::FILE* f, const T* p, size_t n) { std::fwrite(p, sizeof(T), n, f); }

int main(int argc, char** argv) {
    if (argc < 3) return 2;
    std::FILE* fi = std::fopen(argv[1], "rb");
    if (!fi) return 3;
    unsigned char buf[65536];
    size_t n;
    while ((n = std::fread(buf, 1, sizeof buf, fi)) > 0) g_in.insert(g_in.end(), buf, buf + n);
    std::fclose(fi);
    if (get<std::uint32_t>() != 0x58504E46u) return 4;
    nnm::ModelDesc m{};
    m.name = "parity";
    m.arch_version = nnm::kArchVersion;
    m.n_params = get<std::uint32_t>();
    m.self_dim = static_cast<std::uint16_t>(get<std::uint32_t>());
    m.ally_rows = static_cast<std::uint16_t>(get<std::uint32_t>());
    m.ally_dim = static_cast<std::uint16_t>(get<std::uint32_t>());
    m.enemy_rows = static_cast<std::uint16_t>(get<std::uint32_t>());
    m.enemy_dim = static_cast<std::uint16_t>(get<std::uint32_t>());
    m.g_hidden = static_cast<std::uint16_t>(get<std::uint32_t>());
    m.e_hidden = static_cast<std::uint16_t>(get<std::uint32_t>());
    m.ctx = static_cast<std::uint16_t>(get<std::uint32_t>());
    for (int h = 0; h < nnm::kHeads; ++h) {
        nnm::HeadDesc& d = m.head[h];
        d.kind = static_cast<nnm::Kind>(get<std::uint32_t>());
        d.uses_ctx = static_cast<std::uint8_t>(get<std::uint32_t>());
        d.F = static_cast<std::uint16_t>(get<std::uint32_t>());
        d.hidden = static_cast<std::uint16_t>(get<std::uint32_t>());
        d.n_ctx = static_cast<std::uint16_t>(get<std::uint32_t>());
        d.n_out = static_cast<std::uint16_t>(get<std::uint32_t>());
        d.R = get<float>();
        d.wh = get<std::uint32_t>(), d.wf = get<std::uint32_t>(), d.emb = get<std::uint32_t>();
        d.b1 = get<std::uint32_t>(), d.w2 = get<std::uint32_t>(), d.b2 = get<std::uint32_t>();
        d.seg = {0, 0, 0};
    }
    std::uint32_t off[8];
    for (auto& o : off) o = get<std::uint32_t>();
    m.g1 = {off[0], off[1], m.self_dim, m.g_hidden};
    m.a1 = {off[2], off[3], m.ally_dim, m.e_hidden};
    m.e1 = {off[4], off[5], m.enemy_dim, m.e_hidden};
    m.c1 = {off[6], off[7], static_cast<std::uint16_t>(m.g_hidden + 4 * m.e_hidden), m.ctx};
    m.enc = {0, 0, 0};
    std::vector<float> blob(m.n_params);
    std::memcpy(blob.data(), g_in.data() + g_pos, 4 * blob.size());
    g_pos += 4 * blob.size();
    m.blob = blob.data();
    if (!nnm::desc_ok(m)) {
        std::fprintf(stderr, "descriptor invalid\n");
        return 5;
    }
    const int D = nnm::obs_dim(m);
    const std::uint32_t cases = get<std::uint32_t>();
    std::FILE* fo = std::fopen(argv[2], "wb");
    nnm::Scratch s;
    std::vector<float> obs(D), feat(16 * 24);
    for (std::uint32_t c = 0; c < cases; ++c) {
        const std::uint32_t head = get<std::uint32_t>(), K = get<std::uint32_t>(), ctxc = get<std::uint32_t>();
        const float u = get<float>();
        const nnm::HeadDesc& hd = m.head[head];
        for (int i = 0; i < D; ++i) obs[i] = get<float>();
        const int F = hd.F;
        for (std::uint32_t i = 0; i < K * F; ++i) feat[i] = get<float>();
        std::uint8_t legal[16];
        float prior[16];
        for (std::uint32_t k = 0; k < K; ++k) legal[k] = get<std::uint8_t>();
        for (std::uint32_t k = 0; k < K; ++k) prior[k] = get<float>();
        float h[nnm::kMaxCtx];
        nnm::encode(m, obs.data(), h, s);
        put(fo, h, m.ctx);
        const float* hh = hd.uses_ctx ? h : nullptr;
        if (hd.kind == nnm::Kind::candidate) {
            float logit[16], lp[16];
            nnm::candidate_logits(m, hd, hh, static_cast<int>(ctxc), feat.data(), static_cast<int>(K), legal, prior,
                                  logit);
            const std::int32_t am = nnrt::masked_argmax(logit, legal, static_cast<int>(K));
            if (!nnrt::masked_log_softmax(logit, legal, static_cast<int>(K), lp))
                for (std::uint32_t k = 0; k < K; ++k) lp[k] = nnrt::kNegInf;
            float slp = 0.0f;
            const std::int32_t smp = nnrt::masked_sample(logit, legal, static_cast<int>(K), u, &slp);
            put(fo, logit, K);
            put(fo, &am, 1);
            put(fo, lp, K);
            put(fo, &smp, 1);
            put(fo, &slp, 1);
        } else if (hd.kind == nnm::Kind::value) {
            float y[nnm::kMaxOut];
            nnm::value_out(m, hd, hh, y);
            put(fo, y, hd.n_out);
        } else {
            const float y = nnm::leaf_out(m, hd, hh, static_cast<int>(ctxc), feat.data());
            put(fo, &y, 1);
        }
    }
    std::fclose(fo);
    return 0;
}
