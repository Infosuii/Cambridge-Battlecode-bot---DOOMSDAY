// Entry point: dispatch draft and gameplay turns; errors are logged and the turn still ends.
#include <iostream>

#include "bot.h"
#include "draft.h"

#if A2_LAB
#include "learner.h"
// Engine lab: the host finds the learner weights through this export.
extern "C" __attribute__((export_name("lab_learner_w"))) float* lab_learner_w() { return learner::w_lab; }
#include "lab.h"
#include "fbstyle.h"

// ---- E162 A2_POOL: recycle 16-byte-aligned blocks (SDK bitboards) instead of dlmalloc memalign / free each time ----
#include <cstdlib>
#include <new>
namespace a2pool {
struct FreeList {
    std::size_t size = 0;
    void* head = nullptr;
};
inline FreeList lists[6];
inline void* alloc(std::size_t n, std::size_t al) {
    if (al < 16) al = 16;
    if (al == 16)
        for (auto& fl : lists)
            if (fl.size == n && fl.head) {
                char* p = static_cast<char*>(fl.head);
                fl.head = *reinterpret_cast<void**>(p);
                return p;
            }
    const std::size_t hdr = al; // keeps the user pointer aligned; size and header size sit just below it
    const std::size_t total = (n + hdr + al - 1) / al * al;
    char* blk = static_cast<char*>(std::aligned_alloc(al, total));
    if (!blk) return nullptr;
    char* p = blk + hdr;
    reinterpret_cast<std::size_t*>(p)[-2] = n;
    reinterpret_cast<std::size_t*>(p)[-1] = hdr;
    return p;
}
inline void release(void* ptr) noexcept {
    if (!ptr) return;
    char* p = static_cast<char*>(ptr);
    const std::size_t n = reinterpret_cast<std::size_t*>(p)[-2], hdr = reinterpret_cast<std::size_t*>(p)[-1];
    if (hdr == 16) {
        FreeList* empty = nullptr;
        for (auto& fl : lists) {
            if (fl.size == n) {
                *reinterpret_cast<void**>(p) = fl.head;
                fl.head = p;
                return;
            }
            if (!empty && fl.size == 0) empty = &fl;
        }
        if (empty) {
            empty->size = n;
            *reinterpret_cast<void**>(p) = nullptr;
            empty->head = p;
            return;
        }
    }
    std::free(p - hdr);
}
} // namespace a2pool
void* operator new(std::size_t n, std::align_val_t al) {
    void* p = a2pool::alloc(n, static_cast<std::size_t>(al));
    if (!p) throw std::bad_alloc();
    return p;
}
void* operator new[](std::size_t n, std::align_val_t al) {
    void* p = a2pool::alloc(n, static_cast<std::size_t>(al));
    if (!p) throw std::bad_alloc();
    return p;
}
void* operator new(std::size_t n, std::align_val_t al, const std::nothrow_t&) noexcept { return a2pool::alloc(n, static_cast<std::size_t>(al)); }
void* operator new[](std::size_t n, std::align_val_t al, const std::nothrow_t&) noexcept { return a2pool::alloc(n, static_cast<std::size_t>(al)); }
void operator delete(void* p, std::align_val_t) noexcept { a2pool::release(p); }
void operator delete[](void* p, std::align_val_t) noexcept { a2pool::release(p); }
void operator delete(void* p, std::size_t, std::align_val_t) noexcept { a2pool::release(p); }
void operator delete[](void* p, std::size_t, std::align_val_t) noexcept { a2pool::release(p); }
void operator delete(void* p, std::align_val_t, const std::nothrow_t&) noexcept { a2pool::release(p); }
void operator delete[](void* p, std::align_val_t, const std::nothrow_t&) noexcept { a2pool::release(p); }
// ---- end A2_POOL ----
extern "C" __attribute__((export_name("lab_ctl"))) lab::Ctl* lab_ctl() { return &lab::ctl; }
extern "C" __attribute__((export_name("lab_fb_draft"))) std::int32_t* lab_fb_draft() { return lab::fb_draft; }
extern "C" __attribute__((export_name("lab_fb_cfg"))) std::int32_t* lab_fb_cfg() { return &lab::fb_cfg; }
extern "C" __attribute__((export_name("lab_fb_flags"))) std::int32_t* lab_fb_flags() { return &lab::fb_flags; }
extern "C" __attribute__((export_name("lab_fb_style"))) std::int32_t* lab_fb_style() { return &lab::fb_style; }
extern "C" __attribute__((export_name("lab_fb_feat"))) float* lab_fb_feat() { return fbstyle::feat; }
extern "C" __attribute__((export_name("lab_fb_chosen"))) std::int32_t* lab_fb_chosen() { return &fbstyle::chosen; }
extern "C" __attribute__((export_name("lab_knobs"))) float* lab_knobs() { return lab::knobs; }
extern "C" __attribute__((export_name("lab_pol_w"))) float* lab_pol_w() { return lab::pol_w; }
extern "C" __attribute__((export_name("lab_pol_cfg"))) std::int32_t* lab_pol_cfg() { return lab::pol_cfg; }
extern "C" __attribute__((export_name("lab_pol_log"))) float* lab_pol_log() { return lab::pol_log; }
extern "C" __attribute__((export_name("lab_macro_feat"))) float* lab_macro_feat() { return lab::macro_feat; }
extern "C" __attribute__((export_name("lab_cn_w"))) float* lab_cn_w() { return lab::cn_w; }
extern "C" __attribute__((export_name("lab_cn_cfg"))) std::int32_t* lab_cn_cfg() { return lab::cn_cfg; }
extern "C" __attribute__((export_name("lab_cn_force"))) std::int32_t* lab_cn_force() { return lab::cn_force; }
extern "C" __attribute__((export_name("lab_cn_log"))) float* lab_cn_log() { return lab::cn_log; }
extern "C" __attribute__((export_name("lab_builds"))) std::int32_t* lab_builds() { return lab::builds; }
#endif

int main() {
    Bot bot;
#if A2_FUELLOG
    // Diagnostics only: a turn that is still running when the round advances ran out of fuel and lost the next turn.
    std::uint32_t turns = 0, overruns = 0;
#endif
    while (true) {
        try {
            if (bc::is_draft()) {
                play_draft();
#if V58_DIRECTOR
                economy_record_roster();
#endif
            }
#if A2_FUELLOG
            else {
                const std::uint32_t r0 = bc::round_number();
                bot.play_turn();
#if defined(A2_NN_PIPE) && A2_NN_PIPE
                bot.nn_pipe_step();
#endif
#if defined(A2_NN_LIVE) && A2_NN_LIVE
                bot.nn_turn_end();
#endif
                ++turns;
                if (bc::round_number() != r0) {
                    ++overruns;
                    std::printf("fuellog overrun round %u type %d\n", r0, static_cast<int>(bc::self().champion_name()));
                }
                if (r0 % 250 == 0) std::printf("fuellog round %u turns %u overruns %u\n", r0, turns, overruns);
            }
#else
            else {
                bot.fb_turn_start();
                bot.play_turn();
#if A2_NN_MACRO && defined(A2_NN_RL)
                bot.nn_rl_end();
#endif
#if defined(A2_NN_PIPE) && A2_NN_PIPE
                bot.nn_pipe_step();
#endif
#if defined(A2_NN_LIVE) && A2_NN_LIVE
                bot.nn_turn_end();
#endif
                bot.fb_turn_end();
            }
#endif
        } catch (const std::exception& error) {
            std::printf("bot error: %s\n", error.what());
        } catch (...) {
            std::printf("bot error: unknown exception\n");
        }
        bc::end_turn();
    }
}
