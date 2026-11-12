// Entry point: the draft, or one champion's turn; errors are logged and the turn still ends.
#include <cstdio>
#include <exception>

#include "bot.h"
#include "draft.h"

namespace {
Mimic bot; // ~100 KB of map, memory and observation: static storage, not the (small) wasm stack
} // namespace

int main() {
    while (true) {
        try {
            if (cambc::is_draft()) play_draft();
            else bot.turn();
        } catch (const std::exception& e) {
            std::printf("bot error: %s\n", e.what());
        } catch (...) {
            std::printf("bot error: unknown exception\n");
        }
        cambc::end_turn();
    }
}
