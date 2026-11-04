// Host / WASM parity driver for clrl_actor.h: runs every fixture and prints one JSON line per fixture with the
// preprocessed globals and entities, logits (null = illegal) and hidden output. Compared by test_actor_parity.py.
#include <cmath>
#include <cstdio>

#include "clrl_actor.h"
#include "clrl_parity_fixtures.h"

static void arr(const float* v, int n) {
    std::printf("[");
    for (int i = 0; i < n; ++i) {
        if (std::isinf(v[i])) std::printf("%snull", i ? "," : "");
        else std::printf("%s%.9g", i ? "," : "", static_cast<double>(v[i]));
    }
    std::printf("]");
}

int main() {
    for (int f = 0; f < clrl_fx::kN; ++f) {
        clrl_actor::Out o;
        clrl_actor::Pre p;
        clrl_actor::preprocess(clrl_fx::raw[f], p);
        clrl_actor::forward(clrl_fx::raw[f], clrl_fx::hidden_in + f * clrl_actor::kH, clrl_fx::reset[f], o);
        std::printf("{\"i\":%d,\"globals\":", f);
        arr(p.glob, clrl_actor::kG);
        std::printf(",\"camp\":[");
        for (int r = 0; r < 12; ++r) {
            if (r) std::printf(",");
            arr(p.camp[r], clrl_actor::kWCamp);
        }
        std::printf("],\"enemy\":[");
        for (int r = 0; r < 6; ++r) {
            if (r) std::printf(",");
            arr(p.enemy[r], clrl_actor::kWEnemy);
        }
        std::printf("],\"ally\":[");
        for (int r = 0; r < 5; ++r) {
            if (r) std::printf(",");
            arr(p.ally[r], clrl_actor::kWAlly);
        }
        std::printf("],\"altar\":[");
        for (int r = 0; r < 4; ++r) {
            if (r) std::printf(",");
            arr(p.altar[r], clrl_actor::kWAltar);
        }
        std::printf("],\"logits\":");
        arr(o.logits, clrl_actor::kNA);
        std::printf(",\"hidden\":");
        arr(o.h, clrl_actor::kH);
        std::printf("}\n");
    }
    return 0;
}
