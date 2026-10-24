// Direct masked policy interpretation v2. Pure SDK-free wrapper over the unchanged arch1 numeric kernels.
// R in the kernel descriptor is a structural compatibility tag only: direct logits never read priors or R.
#pragma once
#include "nn_model.h"

namespace nnpm {
inline constexpr std::uint32_t kInterpretationVersion = 2;
inline constexpr int kFeatureDim = 12, kContexts = 4, kMaxCandidates = 16;
struct PolicyDesc {
    std::uint32_t interpretation_version;
    const nnm::ModelDesc* kernel;
};
inline constexpr bool policy_head(int h) { return h >= 1 && h <= 8; }
inline constexpr bool desc_ok(const PolicyDesc& p, std::uint32_t expected_obs = 0,
                              std::uint32_t expected_action = 0,
                              const std::uint32_t* expected_head_hashes = nullptr) {
    if (p.interpretation_version != kInterpretationVersion || !p.kernel || !nnm::desc_ok(*p.kernel)) return false;
    const auto& m = *p.kernel;
    if (m.arch_version != 1 || static_cast<unsigned>(m.status) > static_cast<unsigned>(nnm::Status::validated) ||
        !m.obs_schema_hash || !m.action_schema_hash || (expected_obs && expected_obs != m.obs_schema_hash) ||
        (expected_action && expected_action != m.action_schema_hash)) return false;
    for (int i = 0; i < nnm::kHeads; ++i) {
        const auto& h = m.head[i];
        if (!policy_head(i)) { if (h.kind != nnm::Kind::none) return false; continue; }
        if (h.kind != nnm::Kind::candidate || !h.uses_ctx || h.F != kFeatureDim || h.n_ctx != kContexts ||
            h.n_out != 1 || !h.action_hash || h.R != 1.0f ||
            (expected_head_hashes && expected_head_hashes[i] != h.action_hash)) return false;
    }
    // Canonical offsets prevent pointer-range overlap/overflow and keep descriptors inside their checked segments.
    std::uint32_t end = 0;
    auto linear = [&](const nnm::Lin& l) {
        if (l.w != end) return false;
        end += std::uint32_t(l.in)*l.out;
        if (l.b != end) return false;
        end += l.out; return true;
    };
    if (m.enc.begin != 0 || !linear(m.g1) || !linear(m.a1) || !linear(m.e1) || !linear(m.c1) || m.enc.end != end)
        return false;
    for (int i = 0; i < nnm::kHeads; ++i) if (policy_head(i)) {
        const auto& h=m.head[i];
        if (h.seg.begin != end || h.wh != end) return false;
        end += std::uint32_t(m.ctx)*h.hidden;
        if (h.wf != end) return false; end += std::uint32_t(h.F)*h.hidden;
        if (h.emb != end) return false; end += std::uint32_t(h.n_ctx)*h.hidden;
        if (h.b1 != end) return false; end += h.hidden;
        if (h.w2 != end) return false; end += std::uint32_t(h.hidden)*h.n_out;
        if (h.b2 != end) return false; end += h.n_out;
        if (h.seg.end != end) return false;
    }
    return end == m.n_params;
}

// Full independent finite/checksum verification. Call once at install/warmup, not for every decision.
// Runtime can use nnm::verify_step for resumable segment verification after desc_ok if draft fuel is limited.
inline bool verify(const PolicyDesc& p) {
    if (!desc_ok(p)) return false;
    const auto& m = *p.kernel;
    bool finite = true;
    if (nnrt::fnv1a64_f32(nnrt::kFnvOffset, m.blob, static_cast<int>(m.n_params), &finite) != m.checksum || !finite)
        return false;
    auto seg_ok = [&](const nnm::Seg& s) {
        bool good = true;
        return nnrt::fnv1a64_f32(nnrt::kFnvOffset, m.blob+s.begin, static_cast<int>(s.end-s.begin), &good) ==
               s.checksum && good;
    };
    if (!seg_ok(m.enc)) return false;
    for (int i=1; i<=8; ++i) if (!seg_ok(m.head[i].seg)) return false;
    return true;
}

// Already-validated fast kernel, used by the runtime after descriptor/model verification.
inline void direct_logits(const PolicyDesc& p, int head, int context, const float* h, const float* feat,
                          int K, const std::uint8_t* legal, float* out) {
    const auto& m = *p.kernel; const auto& hd = m.head[head];
    float u[nnm::kMaxHidden]; nnm::head_pre(m,hd,h,context,u);
    for (int k=0;k<K;++k) out[k] = legal[k] ? nnm::head_residual(m,hd,u,feat+k*kFeatureDim) : nnrt::kNegInf;
}

// Checked forward: failure has no implicit teacher index. Caller must explicitly enter its fallback path.
inline bool logits(const PolicyDesc& p, int head, int context, const float* h, const float* feat,
                   int K, const std::uint8_t* legal, float* out) {
    if (!desc_ok(p) || !policy_head(head) || context < 0 || context >= kContexts || K <= 0 ||
        K > kMaxCandidates || !h || !feat || !legal || !out ||
        !nnrt::all_finite(h,p.kernel->ctx) || !nnrt::all_finite(feat,K*kFeatureDim)) return false;
    bool any = false; for (int k=0;k<K;++k) { if (legal[k]>1) return false; any |= legal[k]!=0; }
    if (!any) return false;
    direct_logits(p,head,context,h,feat,K,legal,out);
    for (int k=0;k<K;++k) if (legal[k] && !nnrt::is_finite(out[k])) return false;
    return true;
}
} // namespace nnpm
