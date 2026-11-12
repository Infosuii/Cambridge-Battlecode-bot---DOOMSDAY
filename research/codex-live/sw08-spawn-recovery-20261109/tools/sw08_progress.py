"""Trace real healing loops separately from other stationary time."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

from local_panel import read_native, run
from policy_rows import stdout
from project import ARENA, ROOT, save
from sw08_followup import build_from, load, replace

WORK = ROOT / 'sw08-progress'
OPPONENTS = ['b111','nnm4','ref_x1','teammate_john_nnfinal','ref_hold_rush100']
ARMS = {'hp01':'widen','hp02':'sidestep','hp03':'release'}


def map_path(name):
    maps = load(ROOT/'campaign.json')['maps']['dev']
    return next(Path(p) for p in maps if Path(p).stem == name)


def instrument(files):
    c = files['bot.cpp'].decode().replace('\r\n','\n')
    marker = '        return hp < max_hp; // stay put this turn so the spawn heals us'
    c = replace(c, marker, '''        debug_block({
            if (hp < max_hp) std::printf("HWAIT %d %u %d %d %.1f %.1f %.1f %d %d %llu\\n",
                round, my_id, pos.x, pos.y, hp, max_hp, prev_hp, bit(w.hot_zone,pos),
                static_cast<int>(w.enemies.size()), static_cast<unsigned long long>(bc::fuel_remaining()));
        });
''' + marker)
    marker = '    PROF_CHECK("decide");'
    c = replace(c, marker, '''    debug_block({
        if (!walked && !cast_done && me.can_move()) {
            const int g = w.group_at_spawn(pos);
            const bool tile = g >= 0 && static_cast<std::size_t>(g) < w.groups.size();
            std::printf("HIDLE %d %u %d %d %s %d %d %d %d\\n", round, my_id, pos.x, pos.y, mode,
                target_group, tile ? g : -1, tile ? static_cast<int>(w.groups[g].state) : -1,
                tile ? w.groups[g].respawn_round - round : -1);
        }
    });
''' + marker)
    # The original v113 World lacks group_at_spawn. Use the existing tile lookup.
    c = c.replace('const int g = w.group_at_spawn(pos);',
                  'const int g = bit(w.camp_tiles_all,pos) ? w.group_of_camp_tile(pos) : -1;')
    files['bot.cpp'] = c.encode()


def series(native, field):
    result = {}
    for t in native['championTimelines']:
        if t['metric'] == field:
            values = [float(r['value']) for r in t['runs'] for _ in range(r['duration'])]
            result[t['owner']['id']] = [v - (values[i-1] if i else 0.0) for i,v in enumerate(values)]
    return result


def inspect(row):
    n = read_native(row['summary'])
    hits = series(n, 'monsterDamageTaken')
    heals = series(n, 'healingReceived')
    text = stdout(row['replay_bundle'], row['side'])
    idle, waits, attacks, escapes = {}, {}, [], []
    for line in text.splitlines():
        p = line.split()
        if p and p[0] == 'HWAIT':
            waits[int(p[2]),int(p[1])] = p[3:]
        elif p and p[0] == 'HIDLE':
            idle[int(p[2]),int(p[1])] = p[3:]
        elif p and p[0] == 'STALL_CLEAR':
            attacks.append(list(map(int,p[1:])))
        elif p and p[0] in ('SAFE_SPAWN','SAFE_EXIT'):
            escapes.append([p[0],*map(int,p[1:])])
    longest, open_streak = [], None
    confirmed, camp_occupied = 0, 0
    for (body,t), v in sorted(waits.items()):
        # Native summary changes can be adjacent to the logged turn, depending
        # on champion order. Require corroborating damage and actual healing.
        xy, hp, mh, prev, hot = v[:2], float(v[2]), float(v[3]), float(v[4]), int(v[5])
        near = range(max(0,t-1), min(t+2,len(hits[body]),len(heals[body])))
        stalled = hot and hp <= prev+1 and any(hits[body][i]>0 and heals[body][i]>0 for i in near)
        if not stalled:
            open_streak = None
            continue
        confirmed += 1
        if open_streak and (open_streak['body'],open_streak['end']+1,open_streak['xy']) == (body,t,xy):
            open_streak['end'] = t
        else:
            open_streak = {'body':body,'start':t,'end':t,'xy':xy,'hp':hp,'max_hp':mh}
            longest.append(open_streak)
    occupied = Counter((v[2],v[4]) for v in idle.values() if int(v[4]) >= 0 and v[5]=='2' and int(v[6])<=0)
    camp_occupied = sum(occupied.values())
    return {'candidate':row['candidate'],'map':row['map'],'opponent':row['opponent'],'side':row['side'],
            'score':row['score'],'fuel':row['fuel'],'faults':row['faults'],'spawn_waits':len(waits),
            'confirmed_wait_rounds':confirmed,'expired_camp_idle_rounds':camp_occupied,
            'expired_modes':{f'{k[0]}:{k[1]}':v for k,v in occupied.most_common(8)},
            'counterattacks':len(attacks),'first_counterattacks':attacks[:8],
            'safe_steps':len(escapes),'first_safe_steps':escapes[:8],
            'longest':sorted(longest,key=lambda s:s['end']-s['start'],reverse=True)[:6]}


def trace():
    bots = {'hpdbg0':'b113','hpdbg1':'rv11'}
    with ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda n:build_from(n,bots[n],instrument,True),bots))
    rows = run('sw08-progress-spawn-trace', list(bots), [map_path('03homonoliths')], OPPONENTS, 8, True)
    data = [inspect(r) for r in rows]
    save(WORK/'trace.json',data)
    for n in bots:
        report = [r for r in data if r['candidate']==n]
        print(n,{k:sum(r[k] for r in report) for k in
                 ('confirmed_wait_rounds','expired_camp_idle_rounds','counterattacks','score','faults')},flush=True)


def fix(files, kind):
    c = files['bot.cpp'].decode().replace('\r\n','\n')
    c = replace(c, 'hp >= max_hp * 0.40f && hp < max_hp * 0.85f)',
                'hp >= max_hp * 0.40f && hp < max_hp)')
    if kind != 'widen':
        old = '''            static vec2 plateau_pos{-1, -1};
            if (round != plateau_round) {
                plateau_turns = round == plateau_round + 1 && pos == plateau_pos && hp <= prev_hp + 1.0f
                    ? plateau_turns + 1 : 0;
                plateau_round = round;
                plateau_pos = pos;
            }'''
        new = '''            static vec2 plateau_pos{-1, -1};
            static float best_heal = 0.0f;
            if (round != plateau_round) {
                const bool continuing = round == plateau_round + 1 && pos == plateau_pos;
                if (!continuing || hp > best_heal + 1.0f) {
                    plateau_turns = 0;
                    best_heal = hp;
                } else {
                    ++plateau_turns;
                }
                plateau_round = round;
                plateau_pos = pos;
            }'''
        c = replace(c, old, new)
        c = replace(c, '''                    // No adjacent safe tile: use the spawn heal while clearing''',
                    '''                    bc::bitboard safe_step;
                    safe_step.clear();
                    safe_step.draw_chebyshev(pos, 1.0f);
                    safe_step &= ~w.hot_zone & ~w.static_blocked & ~w.unit_tiles & ~w.camp_tiles_all;
                    const bc::bitboard safe_spawn = safe_step & w.ally_spawn;
                    if (!safe_spawn.is_empty() && walk_toward(safe_spawn)) {
                        plateau_turns = 0;
                        mode = "home-safe-heal";
                        debug_block({ std::printf("SAFE_SPAWN %d %u\\n", round, my_id); });
                        return true;
                    }
                    // No adjacent safe spawn tile: use the spawn heal while clearing''')
        if kind == 'release':
            key = '''                    // No adjacent safe spawn tile: use the spawn heal while clearing'''
            c = replace(c, key, '''                    if (hp >= max_hp * 0.85f && !safe_step.is_empty() && walk_toward(safe_step)) {
                        plateau_turns = 0;
                        mode = "home-safe-exit";
                        debug_block({ std::printf("SAFE_EXIT %d %u\\n", round, my_id); });
                        return true;
                    }
''' + key)
    files['bot.cpp'] = c.encode()


def screen():
    with ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda n: build_from(n,'rv11',lambda f:fix(f,ARMS[n])),ARMS))
    probe = run('sw08-progress-spawn-candidates', [*ARMS,'b113'], [map_path('03homonoliths')],
                OPPONENTS, 8)
    from stall_campaign import analyze
    analyze('sw08-progress-spawn-candidates', probe)


def validation_plan():
    plan = load(ROOT/'sw08-followup/v113-anchor/plan.json')
    generated = dict(list(plan['reserve'].items())[:24])
    assert not (ROOT/'panels/sw08-v113-minimal-final-reference/manifest.json').exists()
    assert not (ROOT/'panels/sw08-v113-anchor-final-reference/manifest.json').exists()
    assert set(generated.values()).isdisjoint(plan['final'].values())
    from project import sha
    for p,h in {**generated,**plan['final']}.items():
        assert sha(p) == h
    out = {'development':generated, 'final':plan['final'], 'styles':OPPONENTS,
           'expected_ladder':plan['expected_ladder'],
           'gates':{'maximum_pooled_drop':.01, 'minimum_cluster_lower':-.05,
                    'minimum_direct':.475, 'maximum_style_drop':.10, 'max_fuel_ratio':1.15,
                    'fixture_proximity_stall_ratio':.75, 'fixture_confirmed_wait_ratio':.65,
                    'fixture_max_wait_ratio':.80}}
    path = WORK/'plan.json'
    if path.exists():
        assert load(path) == out
    else:
        save(path,out)
    return out


def trace_candidates(names):
    labels = {f'{n}tr':n for n in names}
    with ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda n:build_from(n,labels[n],instrument,True),labels))
    rows = run('sw08-progress-candidate-trace', list(labels), [map_path('03homonoliths')], OPPONENTS, 8, True)
    data = [inspect(r) for r in rows]
    for r in data:
        r['candidate'] = labels[r['candidate']]
    save(WORK/'candidate-trace.json',data)
    return data


def development():
    from local_panel import artifact
    from project import digest, sha
    from retune_campaign import aggregate
    plan = validation_plan()
    probe = load(ROOT/'stall-audit/sw08-progress-spawn-candidates.json')
    rate = {n:v['counts']['spawn_near_camp_stall_pairs']/v['counts']['alive_pairs'] for n,v in probe.items()}
    viable = [n for n in ARMS if rate[n] <= rate['b113']*plan['gates']['fixture_proximity_stall_ratio']]
    evidence = trace_candidates(viable) if viable else []
    base_trace = [r for r in load(WORK/'trace.json') if r['candidate']=='hpdbg0']
    def stats(data):
        return {'wait':sum(r['confirmed_wait_rounds'] for r in data),
                'max':max((s['end']-s['start']+1 for r in data for s in r['longest']),default=0),
                'safe_steps':sum(r.get('safe_steps',0) for r in data),
                'counterattacks':sum(r['counterattacks'] for r in data)}
    stats_by = {'b113':stats(base_trace), **{n:stats([r for r in evidence if r['candidate']==n]) for n in viable}}
    viable = [n for n in viable if stats_by[n]['wait'] <= stats_by['b113']['wait']*plan['gates']['fixture_confirmed_wait_ratio']
              and stats_by[n]['max'] <= stats_by['b113']['max']*plan['gates']['fixture_max_wait_ratio']]
    receipt = {'fixture_rates':rate,'fixture_trace':stats_by,'viable':viable}
    save(WORK/'mechanism.json',receipt)
    if not viable:
        print(receipt,flush=True)
        return
    maps = list(map(Path,plan['development']))
    pooled = aggregate(run('sw08-progress-development',[*viable,'b113'],maps,OPPONENTS,12))
    direct = aggregate(run('sw08-progress-development-direct',viable,maps,['b113'],12))
    valid = [n for n in viable if not pooled[n]['faults'] and not direct[n]['faults']
             and pooled[n]['score'] >= pooled['b113']['score']-.025 and direct[n]['score']>=.45]
    winner = max(valid,key=lambda n:(pooled[n]['score']+.35*direct[n]['score'],-stats_by[n]['wait'])) if valid else None
    result = {**receipt,'winner':winner,'pooled':pooled,'direct':direct}
    if winner:
        result.update(wasm_sha256=sha(artifact(winner)),source_sha256=digest(ARENA/'bots'/winner/'src'))
    save(WORK/'selection.json',result)
    print({'winner':winner,'pooled':{n:s['score'] for n,s in pooled.items()},
           'direct':{n:s['score'] for n,s in direct.items()}},flush=True)


def qualify():
    from local_panel import artifact
    from project import digest, sha
    from qualify_campaign import comparison, fuel_rate, package
    from retune_campaign import aggregate
    selected = load(WORK/'selection.json')
    name = selected['winner']
    if not name:
        return
    assert sha(artifact(name)) == selected['wasm_sha256']
    assert digest(ARENA/'bots'/name/'src') == selected['source_sha256']
    plan = validation_plan()
    protocol = {**plan,'selection_sha256':sha(WORK/'selection.json'),'candidate':name,
                'controls':{n:sha(artifact(n)) for n in (name,'b113')}}
    p = WORK/'protocol.json'
    if p.exists():
        assert load(p) == protocol
    else:
        save(p,protocol)
    maps = list(map(Path,plan['final']))
    rows = run('sw08-progress-sealed-reference',[name,'b113'],maps,OPPONENTS,12)
    direct = run('sw08-progress-sealed-direct',[name],maps,['b113'],12)
    c, a = comparison(rows,name,'b113'), aggregate(direct)[name]
    fuel = {n:fuel_rate(rows,n) for n in (name,'b113')}
    g = plan['gates']
    gates = {'no_faults_or_codes':not any(r['faults'] or r['opponent_faults'] or r['diagnostic_codes'] for r in rows+direct),
             'pooled_strength_preserved':c['gain']>=-g['maximum_pooled_drop'],
             'cluster_lower_bounded':c['map_cluster_bootstrap_95'][0]>=g['minimum_cluster_lower'],
             'direct_strength_preserved':a['score']>=g['minimum_direct'],
             'no_large_style_drop':min(c['style_deltas'].values())>=-g['maximum_style_drop'],
             'fuel_bounded':fuel[name]['per_1000_scheduled_champion_rounds'] <=
                            fuel['b113']['per_1000_scheduled_champion_rounds']*g['max_fuel_ratio'],
             'stall_guard_pass':name in selected['viable']}
    report = {'candidate':name,'gates':gates,'approved_for_upload':all(gates.values()),
              'expected_ladder':plan['expected_ladder'],'comparisons':{'b113':c},'head_to_head':a,
              'fuel_rates':fuel,'fixture':{k:selected[k] for k in ('fixture_rates','fixture_trace')},
              'games':len(rows)+len(direct),'protocol_sha256':sha(p),'source_sha256':selected['source_sha256'],
              'wasm_sha256':selected['wasm_sha256']}
    dest = WORK/'qualification.json'
    save(dest,report)
    package(name,report,dest)
    print({'candidate':name,'gates':gates,'pooled_gain':c['gain'],'direct':a['score']},flush=True)


def confirm_direct():
    from local_panel import artifact
    from project import digest, sha
    from qualify_campaign import package
    from retune_campaign import aggregate
    initial_path = WORK/'qualification.json'
    initial = load(initial_path)
    failed = {k for k,v in initial['gates'].items() if not v}
    assert failed == {'direct_strength_preserved'}, 'Only a marginal direct-only miss warrants a fixed-build replication'
    name = initial['candidate']
    assert initial['head_to_head']['score'] >= .475 - 1/initial['head_to_head']['games']
    assert sha(artifact(name)) == initial['wasm_sha256']
    assert digest(ARENA/'bots'/name/'src') == initial['source_sha256']
    plan = validation_plan()
    anchor = load(ROOT/'sw08-followup/v113-anchor/plan.json')
    confirm = {p:h for p,h in anchor['reserve'].items() if p not in plan['development']}
    pub = {p:h for p,h in load(ROOT/'campaign.json')['maps']['final'].items()
           if Path(p).parent.name != 'maps_generated_v113'}
    assert len(confirm)==len(pub)==24
    assert not set(confirm.values()) & (set(plan['development'].values()) | set(plan['final'].values()))
    assert all(sha(p)==h for p,h in {**confirm,**pub}.items())
    old_panel = ROOT/'panels/sw08-progress-sealed-direct/results.json'
    protocol = {'candidate':name,'artifact_sha256':initial['wasm_sha256'],
                'initial_qualification_sha256':sha(initial_path),'initial_direct_sha256':sha(old_panel),
                'unseen_maps':confirm,'published_maps':pub,
                'gates':{'new_direct_minimum':.50,'combined_direct_minimum':.475,'published_direct_minimum':.45,
                         'zero_faults_and_codes':True},
                'purpose':'One fixed-build replication of a one-game miss. Keep the initial result. Use no new fit or selection.'}
    p = WORK/'direct-replication-protocol.json'
    if p.exists():
        assert load(p)==protocol
    else:
        save(p,protocol)
    new = run('sw08-progress-direct-replication',[name],list(map(Path,confirm)),['b113'],10)
    published = run('sw08-progress-published-direct',[name],list(map(Path,pub)),['b113'],10)
    together = load(old_panel)+new
    n, a, b = (aggregate(rows)[name] for rows in (new,together,published))
    g = protocol['gates']
    gates = {k:v for k,v in initial['gates'].items() if k!='direct_strength_preserved'}
    gates.update(new_direct_minimum=n['score']>=g['new_direct_minimum'],
                 combined_direct_minimum=a['score']>=g['combined_direct_minimum'],
                 published_direct_minimum=b['score']>=g['published_direct_minimum'],
                 replication_no_faults_or_codes=not any(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']
                                                       for r in new+published))
    out = {**initial,'initial_direct':initial['head_to_head'],'new_direct':n,
           'head_to_head':a,'published_direct':b,'gates':gates,'approved_for_upload':all(gates.values()),
           'games':initial['games']+len(new)+len(published),'replication_protocol_sha256':sha(p)}
    dst = WORK/'qualification-replicated.json'
    save(dst,out)
    manifest = ROOT/'release'/name/'manifest.json'
    if not (WORK/'initial-package-manifest.json').exists():
        save(WORK/'initial-package-manifest.json',load(manifest))
    package(name,out,dst)
    print({'candidate':name,'new':n['score'],'combined':a['score'],'published':b['score'],'gates':gates},flush=True)


def vacate_expired(files):
    h = files['bot.h'].decode()
    h = replace(h,'    bool go_home_if_needed();',
                '    bool vacate_expired_camp_tile();\n    bool go_home_if_needed();')
    files['bot.h'] = h.encode()
    c = files['bot.cpp'].decode()
    mark = 'bool Bot::go_home_if_needed() {'
    c = replace(c,mark,'''bool Bot::vacate_expired_camp_tile() {
    if (walked || !bit(w.camp_tiles_all, pos) || !bc::self().can_move()) return false;
    const int group = w.group_of_camp_tile(pos);
    if (group < 0 || static_cast<std::size_t>(group) >= w.groups.size()) return false;
    const auto& camp = w.groups[group];
    if (camp.state != GroupState::respawning || round < camp.respawn_round) return false;
#if V54_HOLD
    if (group == sole_gem_group && round >= A2_SOLE_FROM && ally_score-enemy_score >= V54_HOLD_LEAD &&
        gems < 10 && hp >= max_hp*0.5f) return false;
#endif
    if (bc::fuel_remaining() < 18000) return false;
    for (const auto& e : w.enemies)
        if (cheb(e.pos,pos) <= e.range + 2) return false;
    bc::bitboard exits;
    exits.clear();
    exits.draw_chebyshev(pos, 1.0f);
    exits &= ~w.camp_tiles_all & ~w.static_blocked & ~w.unit_tiles & ~w.hot_zone;
    if (exits.is_empty() || !walk_toward(exits)) return false;
    mode = "vacate-expired-camp";
    debug_block({ std::printf("VACATED %d %u %d\\n", round, my_id, group); });
    return true;
}

''' + mark)
    c = replace(c,'    } else if (go_home_if_needed()) {',
                '    } else if (vacate_expired_camp_tile()) {\n    } else if (go_home_if_needed()) {')
    files['bot.cpp'] = c.encode()


def islands():
    from stall_campaign import analyze
    build_from('hc01','hp01',vacate_expired)
    build_from('hc01tr','hc01',instrument,True)
    maps = [map_path('01islands')]
    candidates = ['hp01tr','hc01tr']
    rows = run('sw08-progress-islands-trace',candidates,maps,OPPONENTS,8,True)
    cases = []
    for r in rows:
        stat = inspect(r)
        stat['vacates'] = sum(line.startswith('VACATED ') for line in
                              stdout(r['replay_bundle'],r['side']).splitlines())
        cases.append(stat)
    save(WORK/'islands-trace.json',cases)
    released = run('sw08-progress-islands-release',['hp01','hc01'],maps,OPPONENTS,8)
    analyze('sw08-progress-islands-release',released)
    print({n:{k:sum(s[k] for s in cases if s['candidate']==n) for k in ('vacates','expired_camp_idle_rounds','score')}
           for n in candidates},flush=True)


if __name__ == '__main__':
    {'trace':trace,'screen':screen,'development':development,'qualify':qualify,
     'confirm':confirm_direct,'islands':islands}[sys.argv[1]]()
