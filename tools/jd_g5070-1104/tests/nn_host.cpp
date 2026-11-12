// Host runner for nn_golden.py: reads N x 500 int16 feature rows (stdin-named file), writes N x 24 float32 logits
// (target 11, behaviour 8, option 5) of nn::forward (the candidate's nn_infer.h + jd_nn_weights.h, host float path).
#include <cstdint>
#include <cstdio>
#include <vector>

#include "nn_infer.h"

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    std::FILE* in = std::fopen(argv[1], "rb");
    std::FILE* out = std::fopen(argv[2], "wb");
    if (!in || !out) return 3;
    std::int16_t f[500];
    while (std::fread(f, sizeof f, 1, in) == 1) {
        nn::Out o{};
        nn::forward(f, o, nn::kHBeh | nn::kHTarget | nn::kHOption);
        std::fwrite(o.target, sizeof(float), 11, out);
        std::fwrite(o.behaviour, sizeof(float), 8, out);
        std::fwrite(o.option, sizeof(float), 5, out);
    }
    std::fclose(in);
    std::fclose(out);
    return 0;
}
