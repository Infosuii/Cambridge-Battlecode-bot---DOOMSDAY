// Synthetic-only binary harness for all D candidate builders. No SDK, model, or engine dependency.
#include <cstdio>
#include "nn_strategy.h"
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
int main() {
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY); _setmode(_fileno(stdout), _O_BINARY);
#endif
    float in[129];
    while (std::fread(in, sizeof(float), 129, stdin) == 129) {
        const int mode = static_cast<int>(in[0]); const float* p = in + 1;
        const nns::Common c{p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11], p[12]};
        nnh::Decision d{};
        if (mode == 0) {
            bool legal[6]; for (int j = 0; j < 6; ++j) legal[j] = p[13 + j] != 0;
            nns::build_strategy(c, legal, d);
        } else if (mode == 1) nns::build_role(c, static_cast<int>(p[13]), p[14] != 0, d);
        else if (mode == 2) {
            const int n = static_cast<int>(p[13]); nns::ObjectiveCandidate rows[8]{};
            for (int j = 0; j < n && j < 8; ++j) {
                const float* q = p + 14 + 13 * j;
                rows[j] = {static_cast<int>(q[0]), static_cast<int>(q[1]), q[2], q[3], q[4], q[5], q[6], q[7], q[8], q[9], q[10], q[11], q[12] != 0};
            }
            nns::build_objective(c, rows, n, d);
        } else if (mode == 3) {
            nns::DraftInput a{}; for (int j = 0; j < 6; ++j) a.map[j] = p[1 + j];
            for (int j = 0; j < 12; ++j) a.score[j] = p[7 + j];
            a.taken = static_cast<unsigned>(p[19]); a.our_melee = p[20]; a.their_melee = p[21]; a.progress = p[22]; a.first = p[23];
            nns::build_draft(a, static_cast<int>(p[0]), d);
        } else if (mode == 4) {
            d.K = 1; d.F = 1; d.legal[0] = 1; d.id[0] = 0; d.prior[0] = 0;
            d.feat[0] = nns::bounded_value_signal(p[0], p[1], p[2]);
        } else return 2;
        const unsigned header[2] = {static_cast<unsigned>(d.K), static_cast<unsigned>(d.F)};
        std::fwrite(header, sizeof(unsigned), 2, stdout);
        std::fwrite(d.legal, 1, d.K, stdout); std::fwrite(d.id, 4, d.K, stdout);
        std::fwrite(d.prior, 4, d.K, stdout); std::fwrite(d.feat, 4, d.K * d.F, stdout);
    }
}
