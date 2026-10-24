// Agent A scratch-only self-test of the teacher captures (never part of the bot). Built with every head `shadow` so
// all captures compile in; main.cpp calls a_teacher_check(bot) after each play_turn and a_teacher_check_draft() after
// each draft turn. Prints one compact "TCHK" line every 250 rounds (printf is ~65 fuel per character).
#include <cstdio>

#include "nn_teacher.h"

namespace {
struct Counts {
    unsigned obj_ok = 0, obj_bad = 0, obj_commit = 0, obj_commit_other = 0;
    unsigned fight_ok = 0, fight_bad = 0;
    unsigned bank_ok = 0, bank_bad = 0;
    unsigned move_ok = 0, move_bad = 0;
    unsigned draft_ok = 0, draft_bad = 0;
    unsigned chain[16] = {};
    int first_bad_code = 0, first_bad_round = -1;
};
Counts g;
int last_print = 0;
} // namespace

void a_teacher_check_draft() {
    const int c = nn_teacher_access::check_draft();
    if (c == 1) return;
    (c == 0 ? g.draft_ok : g.draft_bad)++;
    const nnt::Draft& d = nn_teacher_access::draft();
    int legal = 0;
    for (int i = 0; i < nnt::kMaxDraft; ++i) legal += d.legal[i];
    std::printf("TCHKD picks %d check %d teacher %d legal %d z %.3f\n", d.picks_made, c, d.teacher, legal, d.teacher >= 0 ? d.z[d.teacher] : 0.0f);
}

void a_teacher_check(const Bot& b) {
    const int r = nn_teacher_access::round(b);
    if (const nnt::Turn* t = nn_teacher_access::turn(b)) ++g.chain[static_cast<int>(t->chain) & 15];
    if (const nnt::Objective* o = nn_teacher_access::objective(b)) {
        const int c = nn_teacher_access::check_objective(b);
        if (c == 0) ++g.obj_ok;
        else {
            ++g.obj_bad;
            if (g.first_bad_round < 0) g.first_bad_code = 100 + c, g.first_bad_round = r;
        }
        // On a farm turn the committed target is the last score_groups result unless farm() overrode it afterwards.
        const nnt::Turn* t = nn_teacher_access::turn(b);
        if (t && (t->chain == nnt::Chain::farm || t->chain == nnt::Chain::nofarm) && o->teacher >= 0)
            (nn_teacher_access::target_group(b) == o->teacher ? g.obj_commit : g.obj_commit_other)++;
    }
    if (const nnt::Fight* f = nn_teacher_access::fight(b)) {
        // The formula target is the first strict minimum of key over the scored enemies (handle_enemies loop).
        bool ok = f->n <= nnt::kMaxEnemies;
        if (f->n > 0 && f->n < nnt::kMaxEnemies) {
            int bi = 0;
            for (int i = 1; i < f->n; ++i)
                if (f->cand[i].key < f->cand[bi].key) bi = i;
            ok = ok && f->formula_target_id == f->cand[bi].id; // candidate 0 for a target head = this enemy
        }
        if (f->n == 0) ok = ok && f->formula_target_id == 0;
        if (!ok && g.first_bad_round < 0) g.first_bad_code = 200, g.first_bad_round = r;
        (ok ? g.fight_ok : g.fight_bad)++;
    }
    if (const nnt::Bank* k = nn_teacher_access::bank(b)) {
        const nnt::Turn* t = nn_teacher_access::turn(b);
        // A tribute branch means tribute_if_needed returned true, which requires go (or the lock/submit path after go).
        bool ok = !(t && (t->chain == nnt::Chain::tribute || t->chain == nnt::Chain::tribute_win) && !k->go);
        ok = ok && k->gems > 0;
        if (ok) ++g.bank_ok;
        else {
            ++g.bank_bad;
            if (g.first_bad_round < 0) g.first_bad_code = 300, g.first_bad_round = r;
        }
    }
    if (const nnt::Move* m = nn_teacher_access::move(b)) {
        bool ok = m->n >= 0 && m->n <= nnt::kMaxSteps;
        for (int i = 1; i < m->n; ++i) ok = ok && m->score[i - 1] <= m->score[i];
        (ok ? g.move_ok : g.move_bad)++;
    }
    if (r - last_print >= 250) {
        last_print = r;
        std::printf("TCHK r%d s%d obj %u/%u commit %u/%u fight %u/%u bank %u/%u move %u/%u draft %u/%u bad %d@%d chain", r,
            nn_teacher_access::slot(b), g.obj_ok, g.obj_bad, g.obj_commit, g.obj_commit_other, g.fight_ok, g.fight_bad, g.bank_ok,
            g.bank_bad, g.move_ok, g.move_bad, g.draft_ok, g.draft_bad, g.first_bad_code, g.first_bad_round);
        for (int i = 0; i < 10; ++i) std::printf(" %u", g.chain[i]);
        std::printf("\n");
    }
}
