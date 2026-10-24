// Synthetic compact-observation encoder harness. No SDK capture, engine match or training.
#include <cstdio>
#include <cstring>
#include "nn_policy_observation.h"
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
int main(int argc, char** argv) {
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY); _setmode(_fileno(stdout), _O_BINARY);
#endif
    if (argc > 1 && std::strcmp(argv[1], "info") == 0) {
        std::printf("%u %d %d %d %d %d %d", nnpobs::kObsSchemaHash, nnpobs::kObsDim,
                    nnpobs::kSelfGlobalDim, nnpobs::kAllyRows, nnpobs::kAllyDim,
                    nnpobs::kEnemyRows, nnpobs::kEnemyDim);
        return 0;
    }
    for (;;) {
        nnpobs::Raw raw{};
        if (std::fread(raw.self, 4, 40, stdin) != 40) return std::feof(stdin) ? 0 : 2;
        if (std::fread(raw.ally, 4, 50, stdin) != 50 || std::fread(raw.enemy, 4, 72, stdin) != 72 ||
            std::fread(raw.ally_mask, 1, 5, stdin) != 5 || std::fread(raw.enemy_mask, 1, 6, stdin) != 6) return 3;
        float encoded[nnpobs::kObsDim];
        const std::uint8_t ok = nnpobs::encode(raw, encoded) ? 1 : 0;
        std::fwrite(&ok, 1, 1, stdout);
        std::fwrite(encoded, 4, nnpobs::kObsDim, stdout);
    }
}
