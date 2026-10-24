"""Frozen evaluation protocol: map partitions, schedules, gate constants, protocol lock.

`build()` uses the official map list, reference manifest and (for fuel-scenario map choice) the read-only diagnosis
evidence of an original-equivalent control. A development clone without the original laptop's diagnosis restores
the already locked historical scenario choices; the selected-map properties are insufficient to rerank the full
original cohort. `tools/eval_protocol.py freeze` writes the result
once and records its sha256 in evaluation/protocol.lock.json. Later code calls `load(verify=True)`, which refuses a
protocol whose bytes no longer match the lock.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from .. import engine

EVAL = engine.ROOT / 'evaluation'
PROTOCOL = EVAL / 'protocol.json'
LOCK = EVAL / 'protocol.lock.json'
SCHEDULES = EVAL / 'schedules'
LEDGER = EVAL / 'ledger.jsonl'
RESULTS = EVAL / 'results'

VERSION = 'nfs-eval-v1'
PARTITION_SALT = 'nfs-eval-v1|partition'      # fixed once, never tuned (see EVALUATION_PROTOCOL.md 2)
FRAMEWORK_SALT = 'nfs-eval-v1|framework'
MAP_LABEL = 'reused_benchmark'
REFERENCE_NAMES = ('original', 'v47', 'first-hour', 'v50')
EVIDENCE = Path(engine.PATHS['previous_experiment']) / 'diagnosis-phase2'
# per (series, partition) counts: 25 '00' maps and 15 '01' maps, stratified proportionally
PARTITION_COUNTS = {'00': {'final': 8, 'selection': 6}, '01': {'final': 4, 'selection': 4}}

GATE = {
    'alpha_one_sided': 0.05,
    'n_boot': 20000,
    'seed': 20261024,
    'primary_reference': 'original',
    'required_opponents': list(REFERENCE_NAMES),
    'original': {'d_win_point_min': 0.0, 'd_win_lower_min': -0.10, 'd_margin_lower_min': -100.0},
    'other_references': {'d_win_point_min': -0.05, 'd_win_lower_min': -0.20, 'd_margin_lower_min': -150.0},
    'benefit': {'pooled_d_win_lower_gt': 0.0},
    'incumbent': {'original': {'d_win_point_min': 0.0, 'd_win_lower_min': -0.10},
                  'other_references': {'d_win_point_min': -0.05, 'd_win_lower_min': -0.20}},
    'fuel': {'entries_ratio_max': 1.25, 'entries_slack': 4, 'games_ratio_max': 1.25, 'games_slack': 2},
    'faults_max': 0,
    'invalid_actions_max': 0,
    'engine_version': engine.PATHS['expected']['engine_version'],
    'override_reason_min_chars': 20,
}


def _rank(salt: str, name: str) -> str:
    return hashlib.sha256(f'{salt}|{name}'.encode()).hexdigest()


def map_names() -> list[str]:
    return [p.stem for p in engine.maps()]


def partitions(names: list[str] | None = None) -> dict[str, list[str]]:
    names = sorted(names or map_names())
    out = {'final': [], 'selection': [], 'training': []}
    for series in sorted({n[:2] for n in names}):
        ranked = sorted((n for n in names if n[:2] == series), key=lambda n: _rank(PARTITION_SALT, n))
        c = PARTITION_COUNTS.get(series, {'final': 0, 'selection': 0})
        out['final'] += ranked[:c['final']]
        out['selection'] += ranked[c['final']:c['final'] + c['selection']]
        out['training'] += ranked[c['final'] + c['selection']:]
    return {k: sorted(v) for k, v in out.items()}


def framework_order(training: list[str]) -> list[str]:
    return sorted(training, key=lambda n: _rank(FRAMEWORK_SALT, n))


def evidence_map_properties() -> dict[str, dict]:
    """Per-map properties of an original-equivalent control (campnet-off vs original, side A) from the previous
    diagnosis (read-only). campnet-off scored exactly 40/80 and 0.0 mean margin against the original."""
    proto = json.loads((EVIDENCE / 'protocol.json').read_text(encoding='utf-8'))
    names = [Path(m).stem for m in proto['maps']]
    props = {}
    for i, m in enumerate(names):
        p = EVIDENCE / 'runs' / 'campnet-off' / f'm{i:02d}-o0-A' / 'summary.json'
        if not p.exists():
            continue
        s = json.loads(p.read_text(encoding='utf-8'))
        ev: dict[str, int] = {}
        for e in s['events']:
            ev[e['kind']] = ev.get(e['kind'], 0) + len(e['entries'])
        rounds = int(s['match']['roundsStarted'])
        props[m] = dict(champions=len(s['roster']['champions']), width=int(s['match']['width']),
                        height=int(s['match']['height']), rounds=rounds, deaths=ev.get('death', 0),
                        deaths_per_100_rounds=round(100.0 * ev.get('death', 0) / max(1, rounds), 3),
                        camp_clears=ev.get('campClear', 0), fuel_exhausted_entries=ev.get('fuelExhausted', 0))
    return props


def fuel_scenarios(training: list[str], props: dict[str, dict]) -> dict[str, dict]:
    """Deterministic scenario -> top-2 maps of the training partition under each rule (a map may serve several
    scenarios; ties broken by the frozen framework hash order)."""
    order = framework_order(training)
    pool = [m for m in order if m in props]
    rules = [
        ('low_fuel', 'most fuelExhausted entries of the original-equivalent control (tail turns at the fuel cap)',
         lambda m: (-props[m]['fuel_exhausted_entries'],)),
        ('many_entities', 'most champions on the map (12 > 10 > 8), then most camp clears',
         lambda m: (-props[m]['champions'], -props[m]['camp_clears'])),
        ('crowded_combat', 'highest deaths per 100 rounds', lambda m: (-props[m]['deaths_per_100_rounds'],)),
        ('late_game', 'longest games (2000-round maps first)', lambda m: (-props[m]['rounds'],)),
        ('typical', 'closest to the median rounds and deaths among 10-champion maps with zero exhaustion',
         None),
    ]
    out = {}
    rounds_med = sorted(props[m]['rounds'] for m in pool)[len(pool) // 2]
    deaths_med = sorted(props[m]['deaths'] for m in pool)[len(pool) // 2]
    for name, why, key in rules:
        cands = list(pool)
        if key is None:
            cands = [m for m in cands if props[m]['champions'] == 10 and props[m]['fuel_exhausted_entries'] == 0]
            key = (lambda m: (abs(props[m]['rounds'] - rounds_med) / 400 + abs(props[m]['deaths'] - deaths_med) / 20,))
        chosen = sorted(cands, key=lambda m: key(m) + (pool.index(m),))[:2]
        out[name] = dict(maps=chosen, rule=why, properties={m: props[m] for m in chosen})
    out['late_game']['note'] = 'per-turn analysis also reports the last 25% of rounds of every scenario game'
    out['low_fuel']['note'] = ('the official fuel limit is never changed; low-fuel behaviour is observed on the '
                               'tail turns of these maps and in native budget-refusal tests (Agent B)')
    return out


def frozen_fuel_scenarios(training: list[str]) -> dict[str, dict]:
    """Restore historical choices from verified repository evidence, without inventing missing run summaries.

    The portable schedule preserves the chosen maps' exact measured properties, but not the full cohort used
    for the original median/ranking. Consequently this path reuses the locked choices rather than reranking
    that incomplete subset. A changed partition requires original evidence or an explicit protocol amendment.
    """
    proto = load(verify=True)
    if proto['protocol_version'] != VERSION or proto['map_label'] != MAP_LABEL:
        raise RuntimeError('frozen fuel evidence belongs to a different evaluation protocol')
    parts = json.loads((SCHEDULES / 'map_partitions.json').read_text(encoding='utf-8'))['partitions']
    if sorted(training) != sorted(parts['training']):
        raise RuntimeError('frozen fuel evidence cannot be reused with a changed training partition')
    schedule = json.loads((SCHEDULES / 'fuel_profile.json').read_text(encoding='utf-8'))
    scenarios = schedule['scenarios']
    if set(scenarios) != {'low_fuel', 'many_entities', 'crowded_combat', 'late_game', 'typical'}:
        raise RuntimeError('frozen fuel scenario inventory is incomplete')
    observed = {}
    for name, scenario in scenarios.items():
        maps = scenario['maps']
        if len(maps) != 2 or len(set(maps)) != 2 or not set(maps) <= set(training) or \
                set(scenario['properties']) != set(maps):
            raise RuntimeError(f'invalid frozen fuel scenario: {name}')
        for map_name, props in scenario['properties'].items():
            if map_name in observed and props != observed[map_name]:
                raise RuntimeError(f'inconsistent frozen map properties: {map_name}')
            observed[map_name] = props
    return scenarios


def _cells(maps, opponents, sides=('A', 'B')) -> list[dict]:
    return [dict(map=m, side=s, opponent=o) for o in opponents for m in maps for s in sides]


def build() -> tuple[dict, dict[str, dict]]:
    names = map_names()
    parts = partitions(names)
    refs = json.loads((engine.ROOT / 'references/builds/manifest.json').read_text(encoding='utf-8'))['opponents']
    fw = framework_order(parts['training'])
    if (EVIDENCE / 'protocol.json').is_file():
        scen = fuel_scenarios(parts['training'], evidence_map_properties())
    else:
        scen = frozen_fuel_scenarios(parts['training'])
    label = {m: MAP_LABEL for m in names}
    common = dict(protocol_version=VERSION, map_label=MAP_LABEL, release=True, fuel='official default (no fuel override flag)')
    schedules = {
        'map_partitions': dict(common, kind='partition', salt=PARTITION_SALT, counts=PARTITION_COUNTS,
                               partitions=parts, labels=label,
                               note='All 40 local maps were used by previous experiments; every map is a reused '
                                    'benchmark. Training uses only `training`; checkpoint selection only '
                                    '`selection`; `final` is evaluated once per candidate (ledger).'),
        'repro': dict(common, kind='framework', purpose='reproducibility: identical match run twice',
                      maps=fw[:4], opponents=['original'], sides=['A'], repeats=2, cells=_cells(fw[:4], ['original'], ('A',))),
        'equivalence': dict(common, kind='framework',
                            purpose='teacher/neutral equivalence fixtures (replay + summary bytes vs reference cells)',
                            maps=fw[:6], opponents=['original', 'v47'], sides=['A', 'B'],
                            cells=_cells(fw[:6], ['original', 'v47'])),
        'smoke': dict(common, kind='framework', label='untrained framework check',
                      purpose='bounded smoke vs original/v47/first-hour, both sides; NOT strength evidence',
                      maps=fw[:8], opponents=['original', 'v47', 'first-hour'], sides=['A', 'B'],
                      cells=_cells(fw[:8], ['original', 'v47', 'first-hour'])),
        'fuel_profile': dict(common, kind='framework',
                             purpose='fuel profiling scenarios (per-turn fuel from the replay .fuel member, '
                                     'fuelExhausted events, NFT1 telemetry in dev builds)',
                             scenarios=scen, opponents=['original'], sides=['A', 'B'],
                             evidence='neural-gameplay/diagnosis-phase2/runs/campnet-off (original-equivalent '
                                      'control; read-only; used only to choose maps by property)',
                             cells=_cells(sorted({m for s in scen.values() for m in s['maps']}), ['original'])),
        'selection': dict(common, kind='selection',
                          purpose='checkpoint selection for training runs (repeated use allowed; per-opponent gate)',
                          maps=parts['selection'], opponents=list(REFERENCE_NAMES), sides=['A', 'B'],
                          cells=_cells(parts['selection'], REFERENCE_NAMES)),
        'final': dict(common, kind='final',
                      purpose='promotion benchmark; once per candidate and candidate family (ledger.jsonl)',
                      maps=parts['final'], opponents=list(REFERENCE_NAMES), sides=['A', 'B'],
                      cells=_cells(parts['final'], REFERENCE_NAMES)),
    }
    for name in ('smoke', 'fuel_profile', 'equivalence'):
        schedules[name]['control_arms'] = ['original', 'neutral_real']
        schedules[name]['control_note'] = (
            'Amendment 2026-10-24: pair dev_untrained with neutral_real on identical cells. '
            'neutral_real runs the same encoder, feature builders and scorer architecture in shadow mode; '
            'it is an overhead control, not proof of identical fuel or teacher decisions. '
            'All results are untrained framework checks, not strength evidence.')
    sched_hash = {k: hashlib.sha256(_dump(v).encode()).hexdigest() for k, v in schedules.items()}
    protocol = dict(
        protocol_version=VERSION,
        written_before_candidate_results=False,
        base_protocol_written_before_candidate_results=True,
        amendments=[dict(id='2026-10-24-overhead-control',
                         reason='Pre-decision fuel sensitivity invalidates zero-residual equivalence claims.',
                         known_evidence='evaluation/evidence/neutral_equivalence_bisect.json',
                         scope='Add neutral_real control arm; measure credit/shadow divergence, keep teacher_exact exact.',
                         original_protocol_sha256='af278d4f088e4bd391c44729fa713c474c2a99dc51a3b2b7401bd91daaff4bd3',
                         after_initial_framework_results=True, before_wave2_results=True)],
        engine=dict(cli=engine.PATHS['expected']['cli_version'], engine_version=GATE['engine_version'],
                    release=True, fuel='official default; the CLI fuel override flag is forbidden', max_concurrent_matches=4),
        determinism='Matches are deterministic for (wasm A, wasm B, map); re-running a cell or changing a seed does '
                    'not create an independent sample. Uncertainty uses maps as clusters.',
        map_label=MAP_LABEL,
        references={k: dict(wasm=f'references/builds/{k}.wasm', wasm_sha256=v['wasm_sha256'],
                            code_section_sha256=v['code_section_sha256'], source_tree_sha256=v['source_tree_sha256'])
                    for k, v in refs.items()},
        schedules={k: dict(file=f'evaluation/schedules/{k}.json', sha256=h) for k, h in sched_hash.items()},
        framework_checks=FRAMEWORK_CHECKS,
        gate=GATE,
        ledger=dict(file='evaluation/ledger.jsonl', append_only=True, hash_chained=True,
                    rule='one final evaluation per candidate sha256 and per candidate family; a second requires a '
                         f'recorded reason (>= {GATE["override_reason_min_chars"]} chars) and is reported'),
    )
    return protocol, schedules


FRAMEWORK_CHECKS = [
    dict(id='reference_preservation', what='sha256 of references/builds/*.wasm equal manifest.json and protocol',
         pass_rule='all equal', schedule=None),
    dict(id='reproducibility', schedule='repro',
         what='same (wasm A, wasm B, map) run twice in separate folders', pass_rule='replay member, both .fuel '
         'members, stdout members and summary.json byte-identical for every repeat'),
    dict(id='teacher_equivalence', schedule='equivalence', profile='teacher_exact',
         what='all heads off vs the original reference cells',
         pass_rule='replay.repl26a and summary.json byte-identical on every cell; .fuel members reported '
                   '(expected identical when the code section equals the original)'),
    dict(id='neutral_credit_equivalence', schedule='equivalence', profile='neutral_credit',
         what='all heads shadow, zero residual, experimental kFuelCredit', pass_rule='MEASUREMENT: report '
         'divergent replay/summary cells and overhead; credit is not proof of action equivalence. '
         'Amended after neutral_equivalence_bisect; teacher_exact remains the exact-equivalence requirement.'),
    dict(id='neutral_real_divergence', schedule='equivalence', profile='neutral_real',
         what='all heads shadow, no credit', pass_rule='MEASUREMENT, not pass/fail: cells with divergent replays, '
         'first divergent round, outcome flips, margin deltas and fuel overhead are reported, never hidden'),
    dict(id='dev_untrained_plumbing', schedule='smoke', profile='dev_untrained',
         what='every head active with seeded untrained weights (plumbing only)',
         pass_rule='0 bot faults, 0 diagnostics codes, 0 invalid actions and per-head call/fallback/budget '
                   'counters present in NFT1 telemetry; win rates are NOT evaluated'),
    dict(id='per_head_shadow', schedule='equivalence', profile='per-head shadow builds (one head shadow, rest off)',
         what='each head in isolation', pass_rule='0 faults; divergence and fuel measured as in neutral_real; '
         'no shadow or credit equivalence claim (recorded amendment)'),
    dict(id='release_config_audit', schedule=None, what='tools/verify_release.py on the packaged release ZIP',
         pass_rule='every verify_release check passes'),
    dict(id='fuel_profile', schedule='fuel_profile', profile='release and dev telemetry builds',
         what='typical, many entities, crowded combat, late game, low fuel', pass_rule='release: fuelExhausted '
         'entries <= 1.25x original + 4 on the scenario cells; per-turn p99/p99.9/max reported; dev: per-head '
         'fuel and budget refusals reported; low-fuel fallback additionally covered by native budget tests (B)'),
    dict(id='smoke', schedule='smoke', profile='release (untrained heads off) and dev_untrained',
         label='untrained framework check',
         what='vs original, v47, first-hour, both sides', pass_rule='all cells complete, 0 faults; results '
         'reported as untrained-framework checks, never as learning or strength evidence'),
]


def _dump(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n'


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def freeze(force_reason: str | None = None) -> dict:
    protocol, schedules = build()
    text = _dump(protocol)
    if LOCK.exists():
        lock = json.loads(LOCK.read_text(encoding='utf-8'))
        if lock['protocol_sha256'] == sha256_text(text) and PROTOCOL.exists() and \
                sha256_text(PROTOCOL.read_text(encoding='utf-8')) == lock['protocol_sha256']:
            return lock
        if not force_reason:
            raise SystemExit('protocol is frozen and the rebuilt protocol differs; pass a supersede reason')
        history = lock.get('history', []) + [dict(protocol_sha256=lock['protocol_sha256'],
                                                  frozen_utc=lock['frozen_utc'])]
    else:
        history = []
    SCHEDULES.mkdir(parents=True, exist_ok=True)
    for k, v in schedules.items():
        (SCHEDULES / f'{k}.json').write_text(_dump(v), encoding='utf-8', newline='\n')
    PROTOCOL.write_text(text, encoding='utf-8', newline='\n')
    lock = dict(protocol_sha256=sha256_text(text), protocol_file='evaluation/protocol.json',
                frozen_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                schedules={k: hashlib.sha256((SCHEDULES / f'{k}.json').read_bytes()).hexdigest() for k in schedules},
                frozen_before_any_candidate_result=not bool(history), supersede_reason=force_reason, history=history)
    LOCK.write_text(_dump(lock), encoding='utf-8', newline='\n')
    return lock


def load(verify: bool = True) -> dict:
    text = PROTOCOL.read_text(encoding='utf-8')
    if verify:
        lock = json.loads(LOCK.read_text(encoding='utf-8'))
        if sha256_text(text) != lock['protocol_sha256']:
            raise RuntimeError('evaluation/protocol.json does not match protocol.lock.json (protocol was modified)')
        for k, h in lock['schedules'].items():
            if hashlib.sha256((SCHEDULES / f'{k}.json').read_bytes()).hexdigest() != h:
                raise RuntimeError(f'schedule {k} does not match the lock')
    return json.loads(text)


def load_schedule(name: str, verify: bool = True) -> dict:
    if verify:
        load(verify=True)
    return json.loads((SCHEDULES / f'{name}.json').read_text(encoding='utf-8'))


def protocol_sha256() -> str:
    return sha256_text(PROTOCOL.read_text(encoding='utf-8'))
