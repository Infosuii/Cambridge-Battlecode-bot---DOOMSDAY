// Synthetic-only native harness. Wire input is explicit little-endian scalar fields, no C++ struct padding.
#include <cstdio>
#include <cstring>
#include "nn_policy_candidates.h"
#include "nn_rt.h"
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
int main(int argc, char** argv) {
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY); _setmode(_fileno(stdout), _O_BINARY);
#endif
    if (argc > 1 && std::strcmp(argv[1], "info") == 0) {
        std::printf("%u", nnpc::kActionSchemaHash);
        for (int h = 0; h < 13; ++h) std::printf(" %u", nnpc::action_hash(static_cast<nncfg::H>(h)));
        return 0;
    }
    if (argc > 1 && std::strcmp(argv[1], "ids") == 0) {
        const int coord[4] = {0, 1, 100, 32767}; const std::uint32_t handle[4] = {0, 1, 100, 0x3FFFFFFFu};
        std::uint32_t id = 0;
        for (unsigned kind = 0; kind < 4; ++kind) for (int x : coord) for (int y : coord) {
            if (!nnpc::move_id(kind, x, y, id)) return 4; std::fwrite(&id, 4, 1, stdout);
        }
        for (unsigned kind = 0; kind < 4; ++kind) for (auto h : handle) {
            if (!nnpc::combat_id(kind, h, id)) return 5; std::fwrite(&id, 4, 1, stdout);
        }
        if (nnpc::move_id(4, 0, 0, id) || nnpc::move_id(0, -1, 0, id) || nnpc::move_id(0, 0, 32768, id) ||
            nnpc::combat_id(4, 0, id) || nnpc::combat_id(0, 0x40000000u, id)) return 6;
        nnpc::Decision d{};
        if (nnpc::build(nncfg::H::strategy, nullptr, 1, 0, d) != nnpc::Error::bad_count || d.K != 0) return 7;
        if (nnpc::build(nncfg::H::strategy, nullptr, -1, 0, d) != nnpc::Error::bad_count || d.K != 0) return 8;
        return 0;
    }
    for (;;) {
        std::int32_t head, count, ctx; std::int64_t teacher;
        if (std::fread(&head, 4, 1, stdin) != 1) return 0;
        if (std::fread(&count, 4, 1, stdin) != 1 || std::fread(&ctx, 4, 1, stdin) != 1 || std::fread(&teacher, 8, 1, stdin) != 1) return 2;
        nnpc::Candidate rows[17]{};
        for (int i = 0; i < count && i <= 16; ++i) {
            if (std::fread(&rows[i].id, 4, 1, stdin) != 1 || std::fread(&rows[i].legal, 1, 1, stdin) != 1 ||
                std::fread(rows[i].raw, 4, 12, stdin) != 12) return 3;
        }
        nnpc::Decision d{};
        const auto err = nnpc::build(static_cast<nncfg::H>(head), rows, count, static_cast<std::uint8_t>(ctx), d);
        float zero_logits[16]{};
        const int tie = d.K ? nnrt::masked_argmax(zero_logits, d.legal, d.K) : -1;
        const int label = nnpc::teacher_index(d, teacher);
        const std::int32_t result[5] = {static_cast<int>(err), d.K, d.F, label, tie};
        std::fwrite(result, 4, 5, stdout);
        std::fwrite(d.id, 4, d.K, stdout); std::fwrite(d.legal, 1, d.K, stdout);
        std::fwrite(d.feat, 4, d.K * d.F, stdout);
    }
}
