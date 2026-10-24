#include "nn_policy_candidates.h"
#include "nn_rt.h"

namespace nnpc {
Error build(nncfg::H head, const Candidate* rows, int count, std::uint8_t context, Decision& out) {
    // Do not clear padding: it is never an input and zeroing 192 floats would spend fuel unnecessarily.
    out.head = head; out.K = 0; out.F = kF; out.context = context;
    if (!supported(head)) return Error::unsupported_head;
    if (count < 0 || count > kMaxK || (count && !rows)) return Error::bad_count;
    if (context > 3) return Error::bad_context;
    if (!count) return Error::empty;
    int order[kMaxK], legal_count = 0;
    for (int i = 0; i < count; ++i) {
        if (rows[i].legal > 1) return Error::bad_mask;
        if (!nnrt::all_finite(rows[i].raw, kF)) return Error::non_finite;
        legal_count += rows[i].legal != 0;
        int j = i;
        while (j > 0 && rows[order[j - 1]].id > rows[i].id) { order[j] = order[j - 1]; --j; }
        order[j] = i;
    }
    for (int i = 1; i < count; ++i) if (rows[order[i - 1]].id == rows[order[i]].id) return Error::duplicate_id;
    if (!legal_count) return Error::no_legal;
    const FeatureSpec* spec = kFeatureSpec[static_cast<int>(head)];
    for (int k = 0; k < count; ++k) {
        const auto& a = rows[order[k]]; out.id[k] = a.id; out.legal[k] = a.legal;
        for (int j = 0; j < kF; ++j) {
            const float v = a.raw[j] * spec[j].inv_scale;
            out.feat[k * kF + j] = v < spec[j].lo ? spec[j].lo : v > spec[j].hi ? spec[j].hi : v;
        }
    }
    out.K = count;
    return Error::ok;
}
int teacher_index(const Decision& d, std::int64_t id) {
    if (id < 0 || id > 0xFFFFFFFFll || d.K <= 0 || d.K > kMaxK) return -1;
    for (int k = 0; k < d.K; ++k) if (d.id[k] == static_cast<std::uint32_t>(id)) return d.legal[k] ? k : -1;
    return -1;
}
bool move_id(unsigned kind, int x, int y, std::uint32_t& out) {
    if (kind > 3 || x < 0 || y < 0 || x > 32767 || y > 32767) return false;
    out = (static_cast<std::uint32_t>(kind) << 30) | (static_cast<std::uint32_t>(y) << 15) | static_cast<std::uint32_t>(x);
    return true;
}
bool combat_id(unsigned kind, std::uint32_t target, std::uint32_t& out) {
    if (kind > 3 || target > 0x3FFFFFFFu) return false;
    out = (target << 2) | kind; return true;
}
} // namespace nnpc
