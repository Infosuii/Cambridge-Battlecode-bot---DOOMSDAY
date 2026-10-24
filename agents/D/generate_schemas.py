"""Regenerate the D action specifications (no models, no training)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMON = [
    ('round', 2000, [-4, 4], 'Current legal round number.'),
    ('hp_fraction', 'max(max_hp,1)', [0, 1], 'Own current health fraction.'),
    ('gems', 100, [-4, 4], 'Own carried gems; not submitted score.'),
    ('gold', 1000, [-4, 4], 'Own current gold.'),
    ('score_margin', 500, [-4, 4], 'Public submitted ally score minus enemy score.'),
    ('slot', 6, [-4, 4], 'Own fixed team slot.'),
    ('team_size', 6, [-4, 4], 'Team bodies in the teacher slot protocol.'),
    ('melee', 1, [0, 1], 'Own champion melee flag.'),
    ('near_allies', 6, [-4, 4], 'Visible allies within six Chebyshev tiles.'),
    ('near_enemies', 8, [-4, 4], 'Visible enemies within six Chebyshev tiles.'),
    ('role', 4, [-4, 4], 'Committed role id, or the teacher-implied role.'),
    ('long_term_signal', 1, [-1, 1], 'Bounded critic signal: .5 act(risk)-.25 act(win)-.25 act(margin), where model margin is submitted gem margin /1000; zero if unavailable.'),
]


def feature(name, scale=1, clip=None, description=None):
    return dict(name=name, scale=scale, clip=[-4, 4] if clip is None else clip,
                description=description or name.replace('_', ' '), visibility='self_or_public_or_visible_or_legally_remembered')


def common():
    return [feature(*row) for row in COMMON]


def write(name, hid, K, features, **kwargs):
    spec = dict(name=name, id=hid, version=1, kind='candidate', F=24, K_max=K, contexts=['default'],
                residual_bound=2.0, teacher_margin=.25, features=features,
                label_sources=['instrumented_original_teacher_NFS1'],
                teacher_index=0, ties='lowest_index', padding='ignored beyond K',
                empty_fallback='execute the already-computed teacher choice',
                status='untrained', **kwargs)
    if len(features) != 24:
        raise ValueError((name, len(features)))
    path = ROOT / 'schemas/heads' / f'{name}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spec, indent=2) + '\n', encoding='utf-8')


def main():
    write('strategy', 1, 6,
          common() + [feature('priority_' + n, clip=[0, 1]) for n in
                      ['teacher_chain', 'farm', 'bank', 'home', 'hunt', 'regroup']] +
          [feature('role_' + n, clip=[0, 1]) for n in ['farmer', 'carrier', 'fighter', 'escort', 'scout']] +
          [feature('teacher', clip=[0, 1])],
          semantics='Candidate 0 executes the unchanged remaining teacher chain. Others attempt the named priority then fall through to that chain if no action succeeds. Emergency combat, win-bank and home guards run first.',
          frequency='Every eligible chain turn; role is committed for 20 rounds.',
          legality='Availability of groups/bag/spawn/visible allies/recent sightings; exact APIs remain deterministic.',
          prior='0 for teacher; -.25 + .05 role_fit + .10 max(signal,0) for bank. Always <= teacher.')
    write('role', 3, 5,
          common() + [feature('candidate_role_' + n, clip=[0, 1]) for n in ['farmer', 'carrier', 'fighter', 'escort', 'scout']] +
          [feature('has_target', clip=[0, 1]), feature('carrier_bag'), feature('fighter_visible_threat'), feature('escort_visible_allies'),
           feature('scout_low_visible_threat'), feature('farmer_small_bag'), feature('teacher', clip=[0, 1])],
          semantics='Teacher-implied role first, other roles in enum order. Role conditions strategy priors and objective features. A role-only active ablation attempts its corresponding deterministic priority.',
          commitment='One decision when an option starts, then no decision records for 20 rounds; reset on dead turns.',
          shared_memory='No new shared-memory bytes or writes. Existing six seven-bit camp claims and sighting word preserved.')
    write('objective', 2, 8,
          common() + [feature('candidate_value', 100), feature('candidate_cost', 100), feature('candidate_score', 5),
                      feature('candidate_finish', 100), feature('candidate_need', 6), feature('candidate_gems', 100),
                      feature('candidate_gold', 1000), feature('candidate_respawn_wait', 200), feature('candidate_distance', 100),
                      feature('candidate_strength', 100), feature('candidate_other_claims', 6), feature('teacher', clip=[0, 1])],
          semantics='Re-rank only the bounded teacher top-K after score_groups route/plan decisions; carry need and score with the selected id.',
          commitment='Only called when score_groups actually recomputes a choice; teacher low-fuel forced target turns emit no decision.',
          legality='Teacher narrowed candidates; invalid group or active avoid_until masks alternative. Deterministic teacher need/safety checks and execution remain.')
    write('draft_pick', 0, 12,
          [feature(f'champion_{i}', clip=[0, 1]) for i in range(12)] +
          [feature('inherited_teacher_logit', 10)] +
          [feature('map_' + n, 1, [-4, 4], 'Already-normalised original draft map feature: ' + desc) for n, desc in
           [('width', 'width / 100'), ('height', 'height / 100'), ('area', 'area / 10000'), ('groups', 'groups / 30'),
            ('gems', 'total gems / 500'), ('gold', 'total gold / 3000')]] +
          [feature('our_melee_picks', 6), feature('their_melee_picks', 6), feature('progress', 1, [0, 1]),
           feature('picking_first', 1, [0, 1]), feature('teacher', 1, [0, 1])],
          semantics='Residual composition/counterpick ranking over the existing trained draft network, which remains a distinct inherited model.',
          uses_shared_context=False, legality='Original deterministic taken mask (both current drafts) plus bounds; teacher first, remaining free ids ascending.',
          label_note='Historical winning drafts are observational/confounded; direct action imitation needs instrumented teacher labels.')
    value = dict(name='value', id=11, version=1, kind='value', F=0, K_max=0, features=[], contexts=[], status='untrained',
                 outputs=[dict(name='win_logit', unit='logit'), dict(name='margin', unit='submitted_gems_per_1000'),
                          dict(name='carry_risk', unit='logit')],
                 consumers=['nns::act: bounded critic contribution to strategy priors/features',
                            'nns::objective: same-turn bounded signal in candidate features', 'offline grouped value regression'],
                 fallback='Zero contribution; no safety or legality changes.',
                 margin_normalization='Final submitted ally-minus-enemy gem margin /1000. Fixed model output unit; independent of reward shaping margin_scale.',
                 label_sources=['engine_1_0_3_public_terminal_outcome', 'engine_1_0_3_submitted_margin', 'instrumented_carried_value_loss'],
                 prohibited_inputs=['future outcomes', 'hidden enemy state', 'opponent private memory'])
    (ROOT / 'schemas/heads/value.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
