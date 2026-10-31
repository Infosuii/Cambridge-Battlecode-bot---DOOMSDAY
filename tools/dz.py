"""Portable DZ build, host tests, release matches, and conformance (standard library only).

No credentials or machine-specific config required. All matches are local. Fresh names
are mandatory; exact source, binaries, logs and hashes are frozen before execution.
"""
from __future__ import annotations
import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
def resolve_cli():
    """Prefer an explicit official executable, then the native platform CLI."""
    configured = os.environ.get('DZ_CAMBC')
    if configured:
        return Path(shutil.which(configured) or configured).expanduser().resolve()
    if os.name == 'nt':
        return ROOT / 'tools/vendor/cambc.exe'
    native = shutil.which('cambc')
    return Path(native) if native else Path('cambc')

CLI = resolve_cli()
MAPS = ROOT / 'maps/local-benchmarks'
TMP = ROOT / 'artifacts/tmp/dz'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(command, timeout=900, env=None):
    if command and str(command[0]) == str(CLI) and not shutil.which(str(CLI)):
        raise RuntimeError('Official cambc CLI missing. Install cambc==4.0.0 or set DZ_CAMBC to its executable.')
    p = subprocess.run([str(x) for x in command], cwd=ROOT, capture_output=True,
                       encoding='utf-8', errors='replace', timeout=timeout, env=env)
    output = p.stdout + p.stderr
    if p.returncode:
        raise RuntimeError(f'command failed ({p.returncode}): {command[:3]}\n{output[-6000:]}')
    return output

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')

def build(bot, wasm):
    wasm.parent.mkdir(parents=True, exist_ok=True)
    log = run([CLI, 'build', bot, '--release', '--output', wasm])
    wasm.with_suffix('.build.log').write_text(log, encoding='utf-8')
    if not wasm.is_file():
        raise RuntimeError('build returned success without a Wasm output')
    return wasm

def host_tests():
    cxx = os.environ.get('DZ_CXX') or shutil.which('g++')
    if not cxx and Path('C:/msys64/ucrt64/bin/g++.exe').exists():
        cxx = 'C:/msys64/ucrt64/bin/g++.exe'
    if not cxx:
        raise RuntimeError('Install a C++20 compiler and set DZ_CXX to its executable')
    out = TMP / 'host'; out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ); env['PATH'] = str(Path(cxx).parent) + os.pathsep + env.get('PATH', '')
    for name in ('core_test', 'economy_test', 'strategy_test', 'protocol_v2_test', 'siege_test', 'macro_test', 'gate_plan_test', 'formation_test', 'trip_test', 'objective_cast_test', 'sequence_test', 'team_protocol_test', 'crew_progression_test', 'crew_traffic_test', 'crew_market_test', 'crew_agreement_test'):
        exe = out / (name + ('.exe' if os.name == 'nt' else ''))
        run([cxx, '-std=c++20', '-O2', '-Wall', '-Wextra', '-Werror', '-Wno-misleading-indentation', '-Wno-array-bounds', '-I', ROOT/'bots/dz/src',
             ROOT/'tests/dz/host'/f'{name}.cpp', '-o', exe])
        print(run([exe], env=env).strip(), flush=True)

# Engine payloads extracted for offline readers; not second matches.
EXTRACTED_PAYLOADS=('lifecycle.repl26a','priority.repl26a')

def native_replay(members):
    bundles=[name for name in members if str(name).endswith('.repl26a') and Path(name).name not in EXTRACTED_PAYLOADS]
    if len(bundles)!=1: raise ValueError('expected exactly one native replay bundle per cell')
    return bundles[0]

def verify_evidence(names=None):
    count = 0
    folders = sorted((ROOT/'research/dz/runs').glob('*')) if names is None else [ROOT/'research/dz/runs'/name for name in names]
    if names is not None and any(not re.fullmatch(r'[A-Za-z0-9_-]+',name) or not folder.is_dir() for name,folder in zip(names,folders)):
        raise ValueError('unknown or invalid evidence run name')
    for folder in folders:
        if (folder/'manual-manifest.json').exists():
            manifest = json.loads((folder/'manual-manifest.json').read_text())
            with zipfile.ZipFile(folder/'evidence.zip') as z:
                if z.testzip() is not None: raise ValueError('corrupt initial evidence capsule')
                for row in manifest['files']:
                    raw = z.read(row['path'])
                    if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                        raise ValueError('initial evidence digest mismatch')
            print(f"{folder.name}: verified {len(manifest['files'])} initial evidence files (see limitations)", flush=True)
            count += 1
            continue
        if not (folder/'provenance.json').exists(): continue
        provenance = json.loads((folder/'provenance.json').read_text())
        results = json.loads((folder/'results.json').read_text())
        with zipfile.ZipFile(folder/'evidence.zip') as z:
            if z.testzip() is not None: raise ValueError(f'{folder.name}: corrupt capsule')
            def check(member, expected):
                if hashlib.sha256(z.read(member)).hexdigest() != expected:
                    raise ValueError(f'{folder.name}: digest mismatch: {member}')
            check('candidate.wasm', provenance['candidate_sha256'])
            check('opponent.wasm', provenance['opponent_sha256'])
            for name,digest in provenance.get('analysis_source',{}).items(): check('runner/'+name,digest)
            if 'runner_sha256' in provenance: check('runner/dz.py',provenance['runner_sha256'])
            for name,digest in provenance.get('opponent_source',{}).items(): check('build/opponent/'+name,digest)
            for name, digest in provenance['source'].items(): check('build/candidate/'+name, digest)
            if json.loads(z.read('results.json')) != results: raise ValueError('external results differ from capsule')
            if json.loads(z.read('provenance.json')) != provenance: raise ValueError('external provenance differs from capsule')
            cells = set()
            for game in results['per_game']:
                cell = game['map'], game['side']
                if cell in cells: raise ValueError('duplicate schedule cell')
                cells.add(cell)
                prefix = f"games/{game['map']}-{game['side']}/"
                if 'summary_sha256' in game: check(prefix+'summary.json', game['summary_sha256'])
                bundle=native_replay([name for name in z.namelist() if name.startswith(prefix)])
                check(bundle, game['replay_sha256'])
                for payload in EXTRACTED_PAYLOADS:
                    if prefix+payload not in z.namelist(): continue
                    import io
                    with zipfile.ZipFile(io.BytesIO(z.read(bundle))) as native:
                        if z.read(prefix+payload)!=native.read('replay.repl26a'):
                            raise ValueError(payload+' differs from native replay')
                if game['candidate_sha256'] != provenance['candidate_sha256']: raise ValueError('candidate changed within run')
        print(f'{folder.name}: verified {len(cells)} cells, frozen source, binaries, summaries and replays', flush=True)
        count += 1
    if not count: raise ValueError('no experiment capsules found')

def fuel_values(bundle, side):
    with zipfile.ZipFile(bundle) as z:
        raw = z.read(f'team-{side.lower()}.fuel')
    if raw[:7] != b'a62leuf' or (len(raw)-13) % 8:
        raise ValueError('unknown engine fuel trace format')
    values = struct.unpack('<%dQ' % ((len(raw)-13)//8), raw[13:])
    return values[:8], values[8:]

def sample_at(runs, sample):
    """Native RLE sample value. Never extrapolate past the recorded match."""
    if sample < 0: raise ValueError('negative sample')
    start = 0
    for segment in runs:
        duration = int(segment['duration'])
        if duration <= 0: raise ValueError('invalid RLE duration')
        if sample < start + duration: return float(segment['value'])
        start += duration
    return None

def checkpoints(summary, side):
    me = 'team'+side
    result = {}
    for requested in (100,250,500):
        actual = min(requested, int(summary['match']['roundsStarted']))
        values = dict(collected=0., gold=0., deaths=0., banked=0.)
        available = set()
        for row in summary.get('championTimelines', []):
            key = {'collectedGems':'collected','earnedGold':'gold','deaths':'deaths'}.get(row['metric'])
            if not key or row['owner']['team'] != me: continue
            value = sample_at(row['runs'], actual)
            if value is not None: values[key] += value; available.add(key)
        for row in summary.get('teamTimelines', []):
            if row['owner'] == me and row['metric'] == 'submittedGems':
                value = sample_at(row['runs'], actual)
                if value is not None: values['banked'] = value; available.add('banked')
        result[str(requested)] = dict(round=actual, ended_before_checkpoint=actual < requested,
            **{k:(v if k in available else None) for k,v in values.items()})
    return result

def caught_errors(stdout):
    # Formatting caps may drop individual error lines. Later cumulative body
    # counters still expose the failure; never accept a false zero from prints.
    bodies={}
    for slot,actions,modules in re.findall(r'DZ_COUNTS round=\d+ slot=(\d+) actions=(\d+) modules=(\d+) stale=\d+',stdout):
        previous=bodies.setdefault(slot,[0,0])
        previous[0]=max(previous[0],int(actions));previous[1]=max(previous[1],int(modules))
    return (max(len(re.findall(r'DZ_ACTION_ERROR ',stdout)),sum(v[0] for v in bodies.values())),
            max(len(re.findall(r'DZ_MODULE_ERROR ',stdout)),sum(v[1] for v in bodies.values())))


def transcript_assertions(stdout):
    checks={}
    for name,value in re.findall(r'CT_CHECK name=(\w+) pass=(\d+)\b',stdout):
        checks[name]=bool(checks.get(name,True) and value=='1')
    return checks

def diagnostic_checks(stdout, fixture, opponent_stdout=''):
    model_fixtures={'objective-reward':'prospector','objective-capture':'capture-time','objective-tribute':'tribute-passive'}
    if fixture in model_fixtures:
        base=diagnostic_checks(stdout,model_fixtures[fixture],opponent_stdout)
        checks=transcript_assertions(stdout)
        labels={'baseline_gold','gem_7_floor','gem_14_floor','gold_cluster_bonus','wolf_reward_unchanged'}
        required={'math_tribute_delay'} if fixture=='objective-tribute' else {prefix+label for prefix in ('math_reward_','math_unknown_') for label in labels}
        if fixture=='objective-capture': required|={prefix+label for prefix in ('math_capture_step_','math_capture_receipt_') for label in labels}
        return dict(passed=base['passed'] and stdout.count('CT_MATH enabled=1')==1 and not(required-checks.keys()) and all(checks.values()),
                    underlying=base,checks=checks,missing=sorted(required-checks.keys()),scope='exact production objective_math.h; restricted solo inputs, no strategy activation')
    if fixture=='priority':
        # SDK-side receipts only; native order is gated separately by the
        # pinned replay reader in match().
        checks=transcript_assertions(stdout);opponent_checks=transcript_assertions(opponent_stdout)
        required={'priority_roster','priority_once_per_round','priority_deferred_current','priority_next_visible'}
        missing=sorted((required-checks.keys())|{'opponent_'+n for n in required-opponent_checks.keys()})
        return dict(passed=not missing and all(checks.values()) and all(opponent_checks.values()) and
                    'ERROR' not in stdout and 'ERROR' not in opponent_stdout,
                    checks=checks,opponent_checks=opponent_checks,missing=missing)
    if fixture in ('group-visibility','group-visibility-first'):
        checks=transcript_assertions(stdout);opponent_checks=transcript_assertions(opponent_stdout)
        required={'single_spawn_setup','single_spawn_position','visible_camp_full_health'}
        rows=[tuple(map(int,r)) for r in re.findall(r'CT10_SAMPLE round=(\d+) spawns=(\d+) live=(\d+) group=(\d+) capture=(\d+) timer=(-?\d+) actor_visible=([01])',stdout)]
        alive=sum(spawns==1 and live==1 and state==1 for _,spawns,live,state,_,_,_ in rows)
        dead_alive=sum(spawns==1 and live==0 and state==1 for _,spawns,live,state,_,_,_ in rows)
        reward=sum(spawns==1 and live==0 and state==2 for _,spawns,live,state,_,_,_ in rows)
        hidden_capture=sum(spawns==1 and live==0 and state==2 and capture==3 and actor==0 for _,spawns,live,state,capture,_,actor in rows)
        cooldown=sum(spawns==1 and live==0 and state==3 for _,spawns,live,state,_,_,_ in rows)
        hidden=re.findall(r'CT10_QUERY name=hidden_camp_health accepted=(\d) value=([0-9.eE+-]+) code=(\d+)',stdout)
        visible=re.findall(r'CT10_QUERY name=visible_camp_health accepted=(\d) value=([0-9.eE+-]+) code=(\d+)',stdout)
        query_ok=hidden==[('0','0','97')] and len(visible)==1 and visible[0][0]=='1' and float(visible[0][1])>0 and visible[0][2]=='0'
        first=fixture=='group-visibility-first'
        order_ok=not first or 'CT10_ORDER seen_member_first=1' in opponent_stdout and dead_alive>=5
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and opponent_checks.get('single_spawn_actor_receipt') is True and order_ok and alive>=5 and reward>0 and hidden_capture>0 and cooldown>0 and query_ok and 'ERROR' not in stdout and 'ERROR' not in opponent_stdout,
                    checks=checks,opponent_checks=opponent_checks,missing=sorted(required-checks.keys()),single_visible_alive=alive,dead_visible_member_group_alive=dead_alive,single_visible_reward=reward,hidden_capturer_samples=hidden_capture,single_visible_cooldown=cooldown,queries=dict(hidden=hidden,visible=visible),samples=len(rows))
    if fixture=='draft-stale':
        choices=[tuple(map(int,r)) for r in re.findall(r'CT_DRAFT_CHOICE prefix=(\d+) pick=(\d+)',stdout)]
        bodies=[tuple(map(int,r)) for r in re.findall(r'CT_DRAFT_PLAY body=(\d+) type=(\d+) picks=(\d+)',stdout)]
        burns=[tuple(map(int,r)) for r in re.findall(r'CT_DRAFT_BURN prefix=(\d+) round=(\d+)',stdout)]
        resumes=re.findall(r'CT_DRAFT_RESUME prefix=(\d+) round=(\d+) original_round=(\d+)',stdout)
        size=bodies[0][2] if bodies else 0
        desired={3:[11,2,6],4:[1,11,2,6],5:[1,11,2,6,0]}.get(size,[])
        physical=[c if c<3 else c+1 for c in desired]
        clock_ok=bool(len(burns)==len(resumes)==1 and burns[0][0] in (0,1) and int(resumes[0][0])==burns[0][0]+1 and int(resumes[0][2])==burns[0][1] and int(resumes[0][1])==int(resumes[0][2])+1)
        valid=bool(desired and clock_ok and choices==list(enumerate(desired)) and
            len(bodies)==size and len({r[0] for r in bodies})==size and sorted(r[1] for r in bodies)==sorted(physical) and all(r[2]==size for r in bodies))
        return dict(passed=valid and 'DZ_ACTION_ERROR' not in stdout and 'DZ_MODULE_ERROR' not in stdout,
                    choices=choices,body_types=bodies,burns=burns,resumes=resumes,
                    draft_round_number_changed=bool(resumes and resumes[0][1]!=resumes[0][2]),
                    scope='one deliberate fuel suspension after first/second successful pick request; intended complete roster must survive')
    if fixture=='tribute-passive':
        checks=transcript_assertions(stdout)
        required={'tribute_passive_setup','tribute_financed','tribute_bag_prepared','tribute_baseline_timer',
                  'tribute_cancel_retains_bag','tribute_item_created','tribute_same_bag','tribute_completed','tribute_live_duration'}
        results=re.findall(r'CT12_RESULT bag=(\d+) base_timer=(\d+) initial_timer=(\d+) elapsed=(\d+) banked_delta=(\d+) gold_delta=(-?\d+) active=([01]) magnitude=([0-9.eE+-]+)',stdout)
        observed='CT12_OBSERVATION_ONLY effect_not_asserted=1' in stdout
        structural=not(required-checks.keys()) and all(checks.values()) and len(results)==1 and 'ERROR' not in stdout
        effect=False
        bases=re.findall(r'CT12_BASE bag=(\d+) timer=(\d+)',stdout)
        items=re.findall(r'CT12_ITEM active=([01]) magnitude=([0-9.eE+-]+)',stdout)
        if len(results)==len(bases)==len(items)==1:
            bag,base,live,elapsed,banked,gold,active=map(int,results[0][:7]);mag=float(results[0][7])
            effect=math.isfinite(mag) and bag>0 and base==max(1,(bag+9)//10) and live==elapsed==max(1,math.ceil(base*(1-mag))) and banked==bag and gold==0 and abs(mag-(.33 if active else 0))<.000001 and tuple(map(int,bases[0]))==(bag,base) and int(items[0][0])==active and float(items[0][1])==mag
        return dict(passed=bool(structural and effect and not observed and checks.get('tribute_passive_effect') is True),mechanical_setup_passed=structural,observation_only=observed,
                    checks=checks,results=results,missing=sorted(required-checks.keys()),scope='uncontested banking: ceil(base rounded timer * (1 - tribute magnitude)); rewards unchanged')
    if fixture=='capture-time':
        base=diagnostic_checks(stdout,'prospector')
        items=re.findall(r'CT_CAP_ITEM active=([01]) timer=(\d+)',stdout)
        entries=re.findall(r'CT_CAP_ENTER label=(\w+) round=(\d+) all_dead=1 onsite=1',stdout)
        results=re.findall(r'CT_CAP_RESULT label=(\w+) entered=(\d+) captured=(\d+) elapsed=(\d+) configured=(\d+)',stdout)
        steps=re.findall(r'CT_CAP_STEP label=(\w+) round=(\d+) timer=(-?\d+) state=(\d+)',stdout)
        labels={'baseline_gold','gem_7_floor','gem_14_floor','gold_cluster_bonus','wolf_reward_unchanged'}
        valid=bool(len(items)==1 and int(items[0][1])==(3 if items[0][0]=='1' else 5) and len(entries)==len(results)==5 and {r[0] for r in entries}==labels and {r[0] for r in results}==labels)
        for label,entered,captured,elapsed,configured in results:
            entered,captured,elapsed,configured=map(int,(entered,captured,elapsed,configured))
            timer=3 if items and items[0][0]=='1' and label!='baseline_gold' else 5
            progress=[tuple(map(int,r[1:])) for r in steps if r[0]==label]
            valid &= configured==timer and elapsed==captured-entered==timer+1 and (label,str(entered)) in entries and len(progress)==elapsed and [r[0] for r in progress]==list(range(entered,captured)) and [r[1] for r in progress[1:]]==list(range(timer,0,-1)) and all(r[2]==1 for r in progress[1:])
        return dict(passed=base['passed'] and valid,underlying_rewards=base,capture_item=items,entries=entries,results=results,steps=steps,
                    scope='solo physical on-site entry after all members defeated; configured timer plus first initialization phase')
    if fixture=='camp-mods':
        checks=transcript_assertions(stdout)
        required={'modifier_setup','modifier_gold_captured','modifier_items_created','modifier_feasible','modifier_hit_damage',
                  'modifier_phase_damage','modifier_attack_count','modifier_elapsed','modifier_total_damage','modifier_isolated_fixed_stats'}
        setup=re.findall(r'CT_MOD_SETUP monster=([01]) jungle=([01]) durability=([01]) strength=([0-9.eE+-]+) camp_hp=([0-9.eE+-]+) camp_strength=([0-9.eE+-]+) hit=([0-9.eE+-]+) incoming=([0-9.eE+-]+) predicted=(\d+)',stdout)
        result=re.findall(r'CT_MOD_RESULT attacks=(\d+) elapsed=(\d+) hp_lost=([0-9.eE+-]+) expected_damage=([0-9.eE+-]+)',stdout)
        phases=[(int(r),float(d)) for r,d in re.findall(r'CT_MOD_PHASE round=(\d+) delta=([0-9.eE+-]+)',stdout)]
        valid=False
        if len(setup)==len(result)==1:
            m,j,d=map(int,setup[0][:3]);strength,hp,camp_strength,hit,incoming=map(float,setup[0][3:8]);predicted=int(setup[0][8])
            attacks,elapsed=map(int,result[0][:2]);loss,expected_loss=map(float,result[0][2:])
            finite=all(math.isfinite(x) for x in (strength,hp,camp_strength,hit,incoming,loss,expected_loss))
            if finite and hit>0 and hp>0:
                n=math.ceil(hp/hit); damage=incoming*(n-1)
                valid=abs(hit-strength*(1+.15*m))<.01 and abs(incoming-camp_strength*(1-.3*j)*(1-.1*d))<.01 and n==attacks==predicted and elapsed==n-1 and abs(loss-damage)<.1 and abs(expected_loss-damage)<.01 and len(phases)==n-1 and len(phases)>=5 and all(abs(delta-incoming)<.01 for _,delta in phases) and all(phases[i][0]==phases[0][0]+i for i in range(len(phases)))
        return dict(passed=valid and not(required-checks.keys()) and all(checks.values()) and 'ERROR' not in stdout,
                    checks=checks,setup=setup,result=result,phase_samples=len(phases),missing=sorted(required-checks.keys()),scope='constant-stat stationary wolf duel; no spells or other combatants')
    if fixture=='prospector':
        checks=transcript_assertions(stdout)
        rewards=re.findall(r'CT13_REWARD label=(\w+) base_gems=(\d+) actual_gems=(\d+) expected_gems=(\d+) base_gold=(\d+) actual_gold=(\d+) expected_gold=(\d+)',stdout)
        labels={'baseline_gold','gem_7_floor','gem_14_floor','gold_cluster_bonus','wolf_reward_unchanged'}
        required=labels|{'item_created','prospector_setup'}
        items=re.findall(r'CT13_ITEM prospector=([01])',stdout)
        actors=re.findall(r'CT13_ACTOR vesper=([01]) bonus_gold_percent=(\d+)',stdout)
        vesper=bool(actors and actors[0][0]=='1')
        arithmetic_ok=True
        cumulative_gold_units=0
        for label,bg,ag,eg,bo,ao,eo in rewards:
            bg,ag,eg,bo,ao,eo=map(int,(bg,ag,eg,bo,ao,eo))
            boosted=items==['1'] and label in ('gem_7_floor','gem_14_floor','gold_cluster_bonus')
            expected_gems=bg*5//4 if boosted else bg
            units=bo*(5 if boosted else 4)*(133 if vesper else 100)
            expected_gold=(cumulative_gold_units+units)//400-cumulative_gold_units//400
            cumulative_gold_units+=units
            arithmetic_ok &= ag==eg==expected_gems and ao==eo==expected_gold
            if label=='gem_7_floor': arithmetic_ok &= bg==7 and bo==0
            if label=='gem_14_floor': arithmetic_ok &= bg==14 and bo==0
            if label=='baseline_gold': arithmetic_ok &= bg==0 and bo>=150
            if label=='gold_cluster_bonus': arithmetic_ok &= bg==0 and bo>0
            if label=='wolf_reward_unchanged': arithmetic_ok &= bg>0 and bo>0
        actor_ok=len(actors)==1 and int(actors[0][1])==(33 if vesper else 0)
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and arithmetic_ok and actor_ok and len(items)==1 and len(rewards)==5 and {r[0] for r in rewards}==labels and 'ERROR' not in stdout,
                    checks=checks,rewards=rewards,prospector=bool(items and items[0]=='1'),vesper=vesper,missing=sorted(required-checks.keys()),scope='cluster rounding, gold and wolf only; golem/monolith remain open')
    if fixture=='draft-miss':
        skips=[tuple(map(int,r)) for r in re.findall(r'CT20_SKIP turn=(\d+) picks=(\d+) before=(\d+)',stdout)]
        picks=[tuple(map(int,r)) for r in re.findall(r'CT20_PICK turn=(\d+) before=(\d+) after=(\d+) choice=(\d+)',stdout)]
        bodies=re.findall(r'CT20_PLAY body=(\d+) type=(\d+) picks=(\d+) word=([0-9a-f]{16})',stdout)
        skip,size,before=skips[0] if len(skips)==1 else (-1,0,-1)
        word=int(bodies[0][3],16) if bodies else 0
        recorded=(word>>32)&15
        selected=[(word>>(4*i))&15 for i in range(recorded)]
        expected=[]
        for c in selected: expected.extend([3,4] if c==3 else [c if c<3 else c+1])
        physical=[int(b[1]) for b in bodies]; linked=3 in physical or 4 in physical
        valid=bool(3<=size<=5 and skip in (0,1) and recorded==before==skip and ((word>>48)&15)==skip and
            len(set(selected))==recorded and all(c<12 for c in selected) and word>>62==3 and len(picks)==skip and
            all((turn,prior,after)==(i,i,i) and value==selected[i] for i,(turn,prior,after,value) in enumerate(picks)) and
            len(bodies)==size+int(linked) and len({b[0] for b in bodies})==len(bodies) and
            len(set(physical))==len(physical) and all(0<=t<=12 for t in physical) and
            (not linked or 3 in physical and 4 in physical) and all(t in physical for t in expected) and
            all(int(b[2])==size and int(b[3],16)==word for b in bodies) and 'CT20_AFTER_SKIP' not in stdout)
        return dict(passed=valid and 'ERROR' not in stdout,team_picks=size,missed_turn=skip,recorded_prefix=selected,
                    champion_bodies=len(bodies),physical_types=physical,
                    own_post_pick_list_delayed=bool(picks and all(prior==after for _,prior,after,_ in picks)),
                    scope='missed first/second pick; guest not resumed for remaining draft; completed roster observed, autofill choices not assumed')
    if fixture=='linked':
        checks=transcript_assertions(stdout)
        required={'linked_roster','linked_both_dead','linked_both_return','linked_partner_parked'}
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and 'ERROR' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()))
    if fixture=='low-fuel':
        forced=[tuple(map(int,r)) for r in re.findall(r'CT_LOW_FUEL_FORCE round=(\d+) slot=(\d+) target=(\d+)',stdout)]
        rows=[tuple(map(int,r)) for r in re.findall(r'DZ_LOW_FUEL round=(\d+) slot=(\d+) entry=(\d+) remaining=(\d+) moved=(\d) cleared=(\d) before=(-?\d+) after=(-?\d+)',stdout)]
        selected=[r for r in rows if (r[0],r[1]) in {(f[0],f[1]) for f in forced}]
        good=bool(forced and len(selected)==len(forced) and len({f[1] for f in forced})==len(forced) and
            all(0<end<entry<=5000 and moved and cleared and 0<=after<before for _,_,entry,end,moved,cleared,before,after in selected))
        continued=bool(re.search(r'DZ_COUNTS round=300 slot=0 actions=0 modules=0 stale=0',stdout))
        return dict(passed=good and continued and 'DZ_ACTION_ERROR' not in stdout and 'DZ_MODULE_ERROR' not in stdout,
                    forced=forced,measured=selected,bodies=len(forced),continued_at_round_300=continued,
                    scope='bounded cached-home movement and claim clearing; not full planned SafeMode')
    if fixture=='duel':
        checks=transcript_assertions(stdout)
        required={'duel_outcome','duel_elapsed','duel_hp','duel_basics','duel_casts','duel_isolated'}
        quotes=re.findall(r'CT_DUEL_QUOTE sample=(\d+) heart=([01]) other=([01]) round=(\d+) status=([01]) ',stdout)
        results=re.findall(r'CT_DUEL_RESULT sample=(\d+) won=([01]) ',stdout)
        matching=(1<=len(quotes)<=3 and [int(q[0]) for q in quotes]==list(range(len(quotes)))
                  and [q[0] for q in quotes]==[r[0] for r in results]
                  and all(int(q[4])+int(r[1])==1 for q,r in zip(quotes,results)))
        return dict(passed=matching and not(required-checks.keys()) and all(checks.values()) and 'ERROR' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()),quotes=quotes,results=results,
                    scope='Controlled stationary two-actor primitive, not live EE/strategy validation')
    if fixture=='shield':
        checks=transcript_assertions(stdout)
        required={'shield_outcome','shield_elapsed','shield_hp','shield_basics','shield_casts','shield_isolated'}
        quotes=re.findall(r'CT_SHIELD_QUOTE sample=(\d+) heart=([01]) existing=([01]) round=(\d+) status=([01]) ',stdout)
        results=re.findall(r'CT_SHIELD_RESULT sample=(\d+) cleared=([01]) ',stdout)
        matching=(1<=len(quotes)<=2 and [int(q[0]) for q in quotes]==list(range(len(quotes)))
                  and [q[0] for q in quotes]==[r[0] for r in results] and quotes[0][2]=='0'
                  and all(int(q[4])+int(r[1])==1 for q,r in zip(quotes,results))
                  and (len(quotes)==1 or quotes[1][2]=='1'))
        return dict(passed=matching and not(required-checks.keys()) and all(checks.values()) and 'ERROR' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()),quotes=quotes,results=results,
                    scope='Controlled stationary isolated target; primitive conformance, not field-model or strength validation')
    if fixture=='clear':
        checks=transcript_assertions(stdout)
        required={'clear_outcome','clear_attack_count','clear_elapsed','clear_damage','clear_hit_damage','clear_isolated'}
        starts=re.findall(r'CT_CLEAR_START ranged=(\d) round=(\d+) members=(\d+) hp=([\d.]+) camp_hp=([\d.]+) hit=([\d.]+) incoming=([\d.]+) predicted=(\d+) survives=(\d)',stdout)
        results=re.findall(r'CT_CLEAR_RESULT outcome=(kill|dead) attacks=(\d+) predicted=(\d+) elapsed=(\d+) moves=(\d+)',stdout)
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and len(starts)==len(results)==1 and 'ERROR' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()),start=starts,result=results)
    if fixture=='restart':
        forced=re.findall(r'CT_RESTART_FORCE round=50 slot=0 body=(\d+) wrote=1 objective=55 onsite=1',stdout)
        cleared=bool(re.search(r'DZ_BOOT_CLAIM round=51 slot=0 objective=127 onsite=0',stdout))
        continued=bool(re.search(r'DZ_COUNTS round=100 slot=0 actions=0 modules=0 stale=0',stdout))
        return dict(passed=len(forced)==1 and cleared and continued and 'DZ_ACTION_ERROR' not in stdout and 'DZ_MODULE_ERROR' not in stdout,
                    subject_body=int(forced[0]) if forced else -1,old_claim_cleared_on_restart=cleared,continued_at_round_100=continued)
    if fixture=='uncaught':
        thrown=re.findall(r'CT4_THROW round=(\d+) body=(\d+)',stdout)
        beats=re.findall(r'CT4_HEARTBEAT round=(\d+) body=(\d+)',stdout)
        boots=re.findall(r'CT4_BOOT round=(\d+) body=(\d+) local=(\d+) shared=(\d+) flag=(\d+)',stdout)
        subject=int(boots[0][1]) if boots else -1
        reset=bool(len(boots)==2 and tuple(map(int,boots[0]))==(1,subject,1,1,0) and
            tuple(map(int,boots[1]))==(51,subject,1,2,1))
        marker_valid=len(thrown)<=1 and all(int(r)==50 and int(b)==subject for r,b in thrown)
        others={body for round_no,body in beats if int(round_no)==100}
        resumed=str(subject) in others
        return dict(passed=reset and resumed and marker_valid and len(others)>=3,subject_body=subject,throw_logs=len(thrown),
                    main_restarted_next_round=reset,local_static_reset=reset,shared_memory_persisted=reset,
                    healthy_bodies_at_round_100=len(others),faulted_body_resumed=resumed,
                    faulted_actor_alive_observations=[int(x) for x in re.findall(r'CT4_STATUS actor_alive=(\d)',stdout)])
    if fixture=='kernel':
        drafts=re.findall(r'CT20 draft_turn=(\d+) fuel=(\d+) team_size=(\d+) ours=(\d+) theirs=(\d+)',stdout)
        bodies=re.findall(r'CT3 round=(\d+) slot=(\d+) play_turn=(\d+) fuel=(\d+) bodies=(\d+) type=(\d+)',stdout)
        samples=re.findall(r'CT1 ([\w.]+) round=(\d+) stable=(\d) fuel=(\d+) samples=1',stdout)
        stale=re.findall(r'CT2 before=(\d+) resumed=(\d+) stale_refused=(\d)',stdout)
        writes=re.findall(r'CT5 round=(\d+) slot=(\d+) observed_round=(\d+) observed_mask=(\d+)',stdout)
        count=int(bodies[0][4]) if bodies else 0
        first_round=min((int(row[0]) for row in bodies),default=-1)
        first=[tuple(map(int,row)) for row in writes if int(row[0])==first_round]
        shared_ok=len(first)==count and count>0 and all(slot==0 or (seen==round_no and mask==(1<<slot)-1) for round_no,slot,seen,mask in first)
        draft_ok=bool(drafts and len(drafts)==int(drafts[0][2]) and all(int(row[0])==i and int(row[3])==i for i,row in enumerate(drafts)))
        suspension_ok=len(stale)==1 and int(stale[0][1])==int(stale[0][0])+1 and stale[0][2]=='1'
        primitives={'field.compute','champions','visible.camps','camp_groups','champion.state','shared.read','bitboard.union'}
        samples_ok={row[0] for row in samples}==primitives and all(row[2]=='1' for row in samples)
        bodies_ok=bool(drafts and count==int(drafts[0][2])+1 and {int(row[1]) for row in bodies if row[2]=='0'}==set(range(count)))
        fingerprint=bool(re.search(r'CT27 partial_fingerprint=[0-9a-f]{8}',stdout))
        return dict(passed=all((shared_ok,draft_ok,suspension_ok,samples_ok,bodies_ok,fingerprint)) and 'ERROR' not in stdout,
                    same_round_shared_writes=shared_ok,draft_pick_count=draft_ok,suspension_guard=suspension_ok,
                    bounded_primitive_samples=samples_ok,linked_body_count=bodies_ok,partial_fingerprint_present=fingerprint)
    if fixture=='contest':
        checks=transcript_assertions(stdout)
        required={'contest_resets_capture_timer','contest_preserves_unclaimed_gems','full_reward_after_enemy_leaves','capture_progress_resumed'}
        progress=re.findall(r'CT_CONTEST_PROGRESS round=(\d+) timer=(\d+) max=(\d+) enemy_capturing=1',opponent_stdout)
        prior=any(0<int(timer)<int(maximum) for _,timer,maximum in progress)
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and prior and 'ERROR' not in stdout and 'ERROR' not in opponent_stdout,
                    checks=checks,missing=sorted(required-checks.keys()),prior_progress_confirmed_by_opponent=prior)
    if fixture=='death':
        checks=transcript_assertions(stdout)
        required={'enemy_hidden_before_death','enemy_hidden_during_death','enemy_respawn_observation_bound','ally_respawn_observation_bound'}
        queries={name:(int(ok),int(value),int(code)) for name,ok,value,code in re.findall(r'CT_QUERY name=(\w+) accepted=(\d) value=(-?\d+) code=(\d+)',stdout)}
        expected={'hidden_alive_before':1,'hidden_enemy_dead_alive':0,'hidden_enemy_respawn_alive':1,'ally_dead_alive':0,'ally_respawn_alive':1}
        live_ok=all(queries.get(name)==(1,value,0) for name,value in expected.items())
        denied=all(queries.get(name)==(0,0,97) for name in ('hidden_health_before','hidden_health_dead'))
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and live_ok and denied and 'ERROR' not in stdout,
                    checks=checks,queries=queries,missing=sorted(required-checks.keys()))
    if fixture=='recovery':
        checks=transcript_assertions(stdout)
        required={'injury_established','base_recall_five_ticks','arrival_before_healing','health_purchase_heals_gain',
                  'home_emblem_created','next_spawn_turn_full_heal','home_recall_three_ticks'}
        spawn=re.search(r'CT_HOME_SPAWN accepted=(\d) active=(\d) timer=(-?\d+) code=(\d+)',stdout)
        spawn_ok=bool(spawn and tuple(map(int,spawn.groups()))==(1,1,3,0))
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and spawn_ok and 'ERROR' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()),
                    recall_on_spawn={key:int(value) for key,value in zip(('accepted','active','timer','code'),spawn.groups())} if spawn else None)
    if fixture=='targeting':
        handles=re.search(r'CT11_HANDLES a=(\d+) b=(\d+)',stdout)
        rows=re.findall(r'CT11_TARGET phase=(\d+) round=(\d+) da=([\d.-]+) db=([\d.-]+) ia=([\d.-]+) ib=([\d.-]+) dista=(\d+) distb=(\d+)',stdout)
        best={2:0,4:0,6:0}; streak=0; previous=None
        for phase,round_no,da,db,ia,ib,dist_a,dist_b in rows:
            phase,round_no,dist_a,dist_b=map(int,(phase,round_no,dist_a,dist_b)); da,db,ia,ib=map(float,(da,db,ia,ib))
            a_hit=phase==2 or (phase==6 and handles and int(handles[1])<int(handles[2]))
            good=ia>0 and ia==ib and (da,db)==((ia,0) if a_hit else (0,ib)) and (
                (dist_a,dist_b)=={2:(1,2),4:(2,1),6:(1,1)}[phase])
            streak=(streak+1 if previous==(phase,round_no-1) else 1) if good else 0
            best[phase]=max(best[phase],streak); previous=(phase,round_no)
        second_attacker=re.search(r'CT11_SECOND_ATTACKER body=(\d+) round=(\d+)',stdout)
        return dict(passed=bool(handles and second_attacker and int(second_attacker[1])==int(handles[2]) and
                    all(n>=4 for n in best.values()) and 'ERROR' not in stdout),
                    consecutive_valid_rounds=best,tie_rule='lower champion handle',samples=len(rows))
    if fixture=='module-stale':
        counts=re.findall(r'DZ_COUNTS round=100 slot=(\d+) actions=(\d+) modules=(\d+) stale=(\d+)',stdout)
        return dict(passed=bool(counts and all(int(a)==0 and int(m)==0 and int(s)==1 for _,a,m,s in counts)
                    and 'DZ_MODULE_ERROR' not in stdout and 'DZ_ACTION_ERROR' not in stdout),
                    bodies=len(counts),all_resumed_without_module_failure=bool(counts and all(int(m)==0 and int(s)==1 for _,_,m,s in counts)))
    if fixture == 'module-failure':
        errors=re.findall(r'DZ_MODULE_ERROR round=(\d+) body=(\d+) module=(\w+) failures=(\d+) disabled=(\d+)',stdout)
        by_body={}
        for round_no,body,module,failures,disabled in errors:
            by_body.setdefault(body,[]).append((module,int(failures),int(disabled)))
        expected=[('memory',1,0),('memory',2,0),('memory',3,1)]
        counts=re.findall(r'DZ_COUNTS round=100 slot=(\d+) actions=(\d+) modules=(\d+) stale=(\d+)',stdout)
        return dict(passed=bool(by_body and counts and len(by_body)==len(counts) and
                    all(rows==expected for rows in by_body.values()) and
                    all(int(actions)==0 and int(modules)==3 and int(stale)==0 for _,actions,modules,stale in counts)
                    and 'DZ_ACTION_ERROR' not in stdout and stdout.count('DZ_MODULE_ERROR')==len(errors)),bodies=len(by_body),errors=len(errors),
                    all_quarantined_after_three=bool(by_body and all(rows==expected for rows in by_body.values())))
    if fixture == 'fingerprint':
        records=re.findall(r'CT27_FIELD ([\w.]+) (u32|f32|f64) ([0-9a-f]+)',stdout)
        fields={key:kind+':'+value for key,kind,value in records}
        canonical=json.dumps(fields,sort_keys=True,separators=(',',':')).encode()
        digest=hashlib.sha256(canonical).hexdigest()
        reference=ROOT/'research/dz/ENGINE_FINGERPRINT.json'
        expected=json.loads(reference.read_text()) if reference.exists() else None
        return dict(passed=bool(expected and fields==expected['fields'] and digest==expected['sha256'] and
                    len(fields)==expected['field_count'] and expected['schema']==1 and len(records)==len(fields)
                    and 'CT27_COMPLETE schema=1' in stdout and 'ERROR' not in stdout),
                    schema=1,field_count=len(fields),sha256=digest,reference_present=bool(expected))
    if fixture == 'tribute':
        checks=transcript_assertions(stdout)
        required={'lock_interrupts_channel','lock_keeps_carried_gems','both_team_locks_visible',
                  'submit_into_lock_hits_once','enemy_lock_removed_five_hits','tribute_completes','tribute_duration','lock_range_three_rejected'}
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and 'ERROR' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()))
    if fixture == 'reset':
        match=re.search(r'CT_CHECK name=camp_kill_resets_both_cooldowns pass=(\d)',stdout)
        after=re.search(r'CT26 second_cast_after_kill=(\d) code=(\d+)',stdout)
        return dict(passed=bool(match and int(match[1]) and after and 'ERROR' not in stdout),
                    camp_reset_observed=bool(match and int(match[1])),
                    second_cast_after_kill_accepted=bool(after and int(after[1])),second_cast_code=int(after[2]) if after else None)
    if fixture == 'capture':
        checks=transcript_assertions(stdout)
        required={'split_primary_low_handle_remainder','split_partner_share','occupied_spawn_delays_respawn','vacated_spawn_respawns'}
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and 'ERROR' not in stdout and 'CT_SETUP_FAILURE' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()))
    if fixture == 'visibility':
        records={name:dict(accepted=int(ok),value=int(value),code=int(code)) for name,ok,value,code in
                 re.findall(r'CT_QUERY name=(\w+) accepted=(\d) value=(\d+) code=(\d+)',stdout)}
        required={'hidden_alive','hidden_gems','hidden_items','hidden_cooldown','visible_alive','visible_gems',
                  'visible_items','visible_cooldown0','visible_cooldown1'}
        visible_ok=all(records.get(name,{}).get('accepted')==1 for name in required if name.startswith('visible_'))
        hidden_ok=all(records.get(name,{}).get('accepted')==0 and records.get(name,{}).get('code')==97 for name in ('hidden_gems','hidden_items','hidden_cooldown'))
        alive_ok=records.get('hidden_alive',{}).get('accepted')==1 and records.get('hidden_alive',{}).get('value')==1
        return dict(passed=not(required-records.keys()) and visible_ok and hidden_ok and alive_ok and 'ERROR' not in stdout,
                    queries=records,missing=sorted(required-records.keys()))
    if fixture == 'channels':
        checks=transcript_assertions(stdout)
        required={'recall_starts_in_camp_range','camp_damage_interrupts_recall','base_recall_duration_five',
                  'spawn_arrival_precedes_heal','one_spawn_turn_full_heal'}
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and 'ERROR' not in stdout and 'CT_SETUP_FAILURE' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()))
    if fixture == 'actions':
        checks = transcript_assertions(stdout)
        required = {'ranged_move_blocks_attack','ranged_attack_blocks_move','reset_restores_attack','one_cast_per_turn',
                    'move_blocks_exclusive_cast','exclusive_cast_blocks_move','melee_move_then_attack','melee_attack_then_move'}
        if 'CT7_ACTOR type=12' in stdout: required.add('shield_then_move')
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and 'ERROR' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()))
    if fixture != 'camps': return {'automated_fixture_checks': 'not yet implemented'}
    rows = re.findall(r'CT11 round=(\d+) hp=([\d.]+) delta=([-\d.]+) active=(\d+) incoming=([\d.]+)[^\n]*target_awake=(\d) target_strength=([\d.]+) target_in_range=(\d)', stdout)
    consecutive = best = 0; previous = None; hits = []
    for raw in rows:
        round, hp, delta, active, incoming, target_awake, target_strength, target_in_range = map(float, raw)
        matches = incoming > 0 and delta > 0 and abs(delta-incoming) < .01 and target_awake==1 and target_in_range==1 and 0<target_strength<=incoming
        consecutive = consecutive+1 if matches and previous is not None and round == previous+1 else int(matches)
        best = max(best, consecutive); previous = round
        if matches: hits.append(dict(round=int(round), delta=delta, in_range_strength=incoming))
    return dict(passed=best>=5 and 'ERROR' not in stdout, consecutive_full_strength_damage_rounds=best,
                matching_hits=len(hits), first_hits=hits[:10], setup_reached_damage=bool(hits),
                conclusion='full in-range camp strength lost every round in this fixture; targeting not isolated')

def match(candidate, opponent, map_path, side, folder, diagnostic=False, diagnostic_rounds=12, fixture='kernel', existing=False):
    if not existing:
        folder.mkdir(parents=True, exist_ok=False)
        a, b = (candidate, opponent) if side == 'A' else (opponent, candidate)
        command = [CLI, 'run', a, b, '--map', map_path, '--out-dir', folder,
                   '--statistics', folder/'summary.json', '--json', '--release']
        if diagnostic: command += ['--rounds', str(diagnostic_rounds)]
        log = run(command, timeout=300)
        (folder/'runner.log').write_text(log, encoding='utf-8')
    bundle = native_replay(list(folder.glob('*.repl26a')))
    if diagnostic:
        budgets, fuel = fuel_values(bundle, side)
        with zipfile.ZipFile(bundle) as z:
            stdout = z.read(f'team-{side.lower()}.stdout').replace(b'\0', b'').decode('utf-8', 'replace')
        (folder/'candidate.stdout').write_text(stdout, encoding='utf-8')
        result = dict(map=map_path.stem, map_sha256=sha(map_path), side=side, diagnostic=True,
            rounds=diagnostic_rounds, outcome='unfinished-diagnostic', banked=0, opponent_banked=0, collected=0, gold=0,
            deaths=0, faults=0, faults_measured=False, opponent_faults=0, fuel_outs=sum(x>=100000 for x in fuel[20:]),
            fuel_budgets=budgets, candidate_sha256=sha(candidate), opponent_sha256=sha(opponent), replay_sha256=sha(bundle))
        opponent_stdout=''
        if fixture in ('contest','group-visibility','group-visibility-first','priority'):
            with zipfile.ZipFile(bundle) as z:
                opponent_stdout=z.read('team-'+('b' if side=='A' else 'a')+'.stdout').replace(b'\0',b'').decode('utf-8','replace')
            (folder/'opponent.stdout').write_text(opponent_stdout,encoding='utf-8')
        result['diagnostic_checks'] = diagnostic_checks(stdout, fixture, opponent_stdout)
        if fixture in ('death','linked'):
            inner=folder/'lifecycle.repl26a'
            with zipfile.ZipFile(bundle) as z: inner.write_bytes(z.read('replay.repl26a'))
            env=dict(os.environ); env['NFS_REPLAY_ENGINE']='2.0.0'
            script=folder.parents[1]/'runner/dz_lifecycle_audit.mjs'
            if not script.exists(): script=ROOT/'tools/dz_lifecycle_audit.mjs'
            audit=json.loads(run(['node','--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',script,inner,folder/'candidate.stdout'],env=env))
            write(folder/'lifecycle_audit.json',audit)
            result['diagnostic_checks']['native_lifecycle']=audit
            result['diagnostic_checks']['passed'] &= audit['passed']
        if fixture=='priority':
            inner=folder/'priority.repl26a'
            with zipfile.ZipFile(bundle) as z: inner.write_bytes(z.read('replay.repl26a'))
            env=dict(os.environ); env['NFS_REPLAY_ENGINE']='2.0.0'
            script=folder.parents[1]/'runner/dz_priority_audit.mjs'
            if not script.exists(): script=ROOT/'tools/dz_priority_audit.mjs'
            audit=json.loads(run(['node','--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',script,inner,
                folder/'candidate.stdout',folder/'opponent.stdout'],env=env))
            write(folder/'priority_audit.json',audit)
            result['diagnostic_checks']['native_priority']=audit
            result['diagnostic_checks']['passed'] &= audit['passed']
        if (folder/'summary.json').exists():
            native=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
            owner='team'+side
            result.update(outcome='completed-diagnostic',faults=int(native['diagnostics']['botFaults'][owner]),
                faults_measured=True,opponent_faults=int(native['diagnostics']['botFaults']['team'+('B' if side=='A' else 'A')]),
                fuel_outs=sum(len(e['entries']) for e in native['events'] if e['kind']=='fuelExhausted' and e['owner']['team']==owner),
                summary_sha256=sha(folder/'summary.json'))
            other='team'+('B' if side=='A' else 'A')
            result['opponent_fuel_outs']=sum(len(e['entries']) for e in native['events'] if e['kind']=='fuelExhausted' and e['owner']['team']==other)
            result['diagnostic_checks']['passed'] &= result['opponent_faults']==result['opponent_fuel_outs']==0
            if fixture in ('module-failure','module-stale'):
                bodies=sum(c['team']==owner for c in native['champions'])
                expected_outs=bodies if fixture=='module-stale' else 0
                checks=result['diagnostic_checks']
                checks.update(expected_bodies=bodies,expected_deliberate_fuel_outs=expected_outs)
                checks['passed'] &= checks['bodies']==bodies and result['fuel_outs']==expected_outs
            if fixture=='low-fuel':
                bodies=sum(c['team']==owner for c in native['champions'])
                result['diagnostic_checks']['expected_bodies']=bodies
                result['diagnostic_checks']['passed'] &= result['diagnostic_checks']['bodies']==bodies
            if fixture=='draft-stale':
                result['diagnostic_checks']['passed'] &= result['fuel_outs']==1
                result['diagnostic_checks']['expected_deliberate_fuel_outs']=1
            if fixture=='kernel':
                result['diagnostic_checks']['passed'] &= result['fuel_outs']==1
                result['diagnostic_checks']['expected_deliberate_fuel_outs']=1
            if fixture in ('uncaught','restart'):
                faults=[(e['owner']['id'],entry['timestamp']['round']) for e in native['events'] if e['kind']=='botFault' and e['owner']['team']==owner for entry in e['entries']]
                checks=result['diagnostic_checks']
                checks['passed'] &= result['faults']==1 and result['fuel_outs']==0 and faults==[(checks['subject_body'],50)]
                checks['expected_deliberate_faults']=1
                checks['native_faults']=faults
        if fixture in ('uncaught','restart','draft-stale') and not result['faults_measured']:
            result['diagnostic_checks']['passed']=False
        if fixture=='kernel':
            result['diagnostic_checks']['passed'] &= budgets==tuple([10000000,100000,200000,100000]*2)
        if fixture not in ('kernel','module-stale','draft-stale') and result['fuel_outs']:
            result['diagnostic_checks']['passed']=False
        write(folder/'receipt.json', result)
        return result, fuel[20:]
    d = json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    me, other = 'team'+side, 'team'+('B' if side == 'A' else 'A')
    def number(value): return int(value)
    teams = {row['team']: row for row in d['teams']}
    champs = [row for row in d['champions'] if row['team'] == me]
    budgets, fuel = fuel_values(bundle, side)
    # The trace starts with draft and boosted first turns. Exclude only this
    # bounded prefix from ordinary-turn quantiles; exact exhaustions use events.
    draft_turns = sum(row['team'] == me for row in d['roster']['draft'])
    boosted_turns = len(champs)
    prefix = draft_turns + boosted_turns
    ordinary = fuel[prefix:]
    exhaustions = sum(len(e['entries']) for e in d['events'] if e['kind'] == 'fuelExhausted' and e['owner']['team'] == me)
    result = dict(map=map_path.stem, map_sha256=sha(map_path), side=side,
        rounds=d['match']['roundsStarted'], outcome=d['match']['outcome'],
        banked=number(teams[me]['submittedGems']), opponent_banked=number(teams[other]['submittedGems']),
        collected=sum(number(c['metrics']['collectedGems']) for c in champs),
        gold=sum(number(c['metrics']['earnedGold']) for c in champs),
        deaths=sum(number(c['metrics']['deaths']) for c in champs),
        faults=number(d['diagnostics']['botFaults'][me]), opponent_faults=number(d['diagnostics']['botFaults'][other]),
        fuel_outs=exhaustions, engine=d['match']['engineVersion'], engine_hash=d['match']['engineBuildHash'],
        fuel_budgets=budgets, candidate_sha256=sha(candidate), opponent_sha256=sha(opponent),
        summary_sha256=sha(folder/'summary.json'), replay_sha256=sha(bundle))
    result.update(fuel_prefix_excluded=prefix, checkpoints=checkpoints(d, side))
    with zipfile.ZipFile(bundle) as z:
        stdout = z.read(f'team-{side.lower()}.stdout').replace(b'\0', b'').decode('utf-8', 'replace')
    (folder/'candidate.stdout').write_text(stdout, encoding='utf-8')
    if 'DZ_COUNTS' in stdout:
        result['caught_action_errors'],result['caught_module_errors']=caught_errors(stdout)
    write(folder/'receipt.json', result)
    return result, ordinary

def experiment(args):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.name): raise ValueError('name must use letters, digits, dash or underscore')
    if args.map_dir and args.command not in ('conformance','scenario'): raise ValueError('custom fixture maps are for conformance/scenario only')
    if args.command=='scenario' and not args.map_dir: raise ValueError('production scenarios require a separate --map-dir')
    out = TMP / args.name
    out.mkdir(parents=True, exist_ok=False)
    (out/'runner').mkdir(); shutil.copyfile(Path(__file__),out/'runner/dz.py')
    if args.command=='conformance' and args.fixture in ('death','linked','priority'):
        (out/'runner/replay').mkdir()
        reader='dz_priority_audit.mjs' if args.fixture=='priority' else 'dz_lifecycle_audit.mjs'
        shutil.copyfile(ROOT/'tools'/reader,out/'runner'/reader)
        shutil.copyfile(ROOT/'tools/replay/engine.mjs',out/'runner/replay/engine.mjs')
    fixtures = {'objective-reward':'prospector_probe','objective-capture':'prospector_probe','objective-tribute':'tribute_passive_probe','kernel':'conformance','group-visibility-first':'group_visibility_probe','group-visibility':'group_visibility_probe','tribute-passive':'tribute_passive_probe','capture-time':'prospector_probe','camp-mods':'camp_modifiers_probe','prospector':'prospector_probe','draft-miss':'draft_miss_probe','linked':'linked_probe','duel':'duel_probe','shield':'shield_probe','clear':'clear_probe','uncaught':'uncaught_probe','camps':'camp_probe','targeting':'target_probe','actions':'actions_probe','channels':'channel_probe','recovery':'recovery_probe','death':'death_probe','contest':'contest_probe','visibility':'visibility_probe','capture':'capture_probe','reset':'reset_probe','fingerprint':'fingerprint_probe','tribute':'tribute_probe','priority':'priority_probe'}
    injected=args.command=='conformance' and args.fixture in ('module-failure','module-stale','restart','low-fuel','draft-stale')
    source = ROOT / (f'tests/dz/{fixtures[args.fixture]}' if args.command == 'conformance' and not injected else 'bots/dz')
    if args.candidate_bot:
        # Benchmark another existing bot as the candidate (e.g. v65 against
        # idle). Evaluation only: its code is never copied into bots/dz.
        if args.command!='smoke' or args.trace or args.set: raise ValueError('--candidate-bot is for plain smoke benchmarks')
        source = ROOT/'bots'/args.candidate_bot
    frozen = out / 'build/candidate'
    if args.command=='smoke' and args.source:
        # A long screen builds every run from one frozen snapshot, so edits to bots/dz during it never mix in.
        if args.candidate_bot: raise ValueError('--source replaces bots/dz; not with --candidate-bot')
        source = Path(args.source)
    shutil.copytree(source/'src', frozen/'src')
    if args.command=='smoke' and args.plan_rows:
        # Z14 screens: a whole-pool table (tools/dz_plan_select.py --uniform) in the frozen copy only, so a screened
        # config runs the same code as the final table build; only table data differs.
        shutil.copyfile(Path(args.plan_rows), frozen/'src/map_plans.inc')
    if args.command=='conformance' and args.fixture in ('capture-time','objective-capture'):
        config=frozen/'src/config.h'; source_text=config.read_text()
        for flag,value in [('DZ_CAPTURE_TEST',1),('DZ_CAPTURE_ITEM',1),('DZ_PROSPECTOR',0)]:
            source_text,n=re.subn(r'^#define '+flag+r'\s+[01]$',f'#define {flag} {value}',source_text,flags=re.MULTILINE)
            if n!=1: raise ValueError('capture fixture flag changed: '+flag)
        config.write_text(source_text,encoding='utf-8',newline='\n')
    if args.command=='conformance' and args.fixture=='duel':
        for header in ('duel.h','fight.h'):shutil.copyfile(ROOT/'bots/dz/src'/header,frozen/'src'/header)
    if args.command=='conformance' and args.fixture=='shield':
        shutil.copyfile(ROOT/'bots/dz/src/shield_clear.h',frozen/'src/shield_clear.h')
    if args.command=='conformance' and args.fixture in ('clear','camp-mods'):
        shutil.copyfile(ROOT/'bots/dz/src/basic_clear.h',frozen/'src/basic_clear.h')
    if args.command=='conformance' and args.fixture in ('prospector','capture-time','tribute-passive','objective-reward','objective-capture','objective-tribute'):
        shutil.copyfile(ROOT/'bots/dz/src/objective_math.h',frozen/'src/objective_math.h')
        if args.fixture.startswith('objective-'):
            config=frozen/'src/config.h'
            config.write_text(config.read_text().replace('#define DZ_OBJECTIVE_MATH 0','#define DZ_OBJECTIVE_MATH 1'),encoding='utf-8',newline='\n')
    if args.trace or injected:
        config = frozen/'src/config.h'
        config.write_text(config.read_text().replace('#define DZ_TRACE 0', '#define DZ_TRACE 1'))
    if args.command=='conformance' and args.fixture=='draft-stale':
        config=frozen/'src/config.h'
        config.write_text(config.read_text()+'\n#define DZ_DRAFT_BURN_SECOND 0\n',encoding='utf-8',newline='\n')
        draft=frozen/'src/draft.cpp'; source_text=draft.read_text()
        needle='            if (!initialized) initialized = act.publish(protocol::empty_word());'
        if source_text.count(needle)!=1: raise ValueError('draft suspension injection boundary changed')
        injection=r'''            std::printf("CT_DRAFT_CHOICE prefix=%zu pick=%d\n",picks.size(),static_cast<int>(next));
            static bool forced=false;
            if (!forced&&picks.size()==(DZ_DRAFT_BURN_SECOND?1u:0u)) {
                forced=true;
                std::printf("CT_DRAFT_BURN prefix=%zu round=%u\n",picks.size(),tc.round); std::fflush(stdout);
                while (cambc::draft::current_draft(cambc::team::ally).size()==picks.size()) { }
                std::printf("CT_DRAFT_RESUME prefix=%zu round=%u original_round=%u\n",cambc::draft::current_draft(cambc::team::ally).size(),cambc::round_number(),tc.round);
            }
'''
        draft.write_text(source_text.replace(needle,injection+needle),encoding='utf-8',newline='\n')
        main=frozen/'src/main.cpp'; source_text=main.read_text(); needle='    if (cambc::is_draft()) dz::draft_loop(counts);'
        if source_text.count(needle)!=1: raise ValueError('draft roster diagnostic boundary changed')
        source_text=source_text.replace(needle,needle+r'''
    std::printf("CT_DRAFT_PLAY body=%u type=%d picks=%u\n",static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),static_cast<int>(cambc::self().champion_name()),cambc::draft::team_size());
''')
        main.write_text(source_text,encoding='utf-8',newline='\n')
    if args.command=='conformance' and args.fixture=='low-fuel':
        main=frozen/'src/main.cpp'; source_text=main.read_text()
        needle='            if (world->ready&&dz::tier_for(cambc::fuel_remaining())==dz::Tier::Fallback) {'
        if source_text.count(needle)!=1: raise ValueError('low-fuel fixture injection boundary changed')
        injection=r'''            static bool forced_low=false;
            if (!forced_low&&world->ready&&tc.round>=50&&tc.round<250) {
                auto& me=cambc::self(); auto state=me.state();
                if (!state.is_dead()&&!me.is_recalling()&&!me.is_submitting_gems()&&!me.is_teleporting()&&me.can_move()) {
                    auto p=me.position(); bool available=false;
                    if (world->home.get(p)>0&&world->home.get(p)<cambc::distance_field::unreachable)
                        for (auto delta:world->home.next_moves_from(p)) {
                            auto q=p+delta;
                            if (world->walkable(q)&&!cambc::vision::has_champion(q)&&!cambc::vision::has_camp(q)&&!cambc::vision::has_teleport(q)) available=true;
                        }
                    if (available) {
                        forced_low=true;
                        std::printf("CT_LOW_FUEL_FORCE round=%u slot=%u target=5000\n",tc.round,world->slot);
                        while (cambc::fuel_remaining()>5000) { }
                    }
                }
            }
'''
        main.write_text(source_text.replace(needle,injection+needle),encoding='utf-8',newline='\n')
    if injected and args.fixture in ('module-failure','module-stale'):
        main=frozen/'src/main.cpp'; text=main.read_text(); needle='mem->update(*world,tc);'
        if text.count(needle)!=1: raise ValueError('memory fault injection site changed')
        injection='throw std::runtime_error("controlled memory failure");'
        if args.fixture=='module-stale':
            injection='''static bool injected=false;
                if (!injected) {
                    injected=true; volatile unsigned sink=1;
                    while (cambc::round_number()==tc.round) for (unsigned n=0;n<100;++n) sink=sink*1664525u+1013904223u;
                    throw std::runtime_error("controlled stale SDK error after suspension");
                }
                mem->update(*world,tc);'''
        main.write_text(text.replace(needle,injection),encoding='utf-8',newline='\n')
    if injected and args.fixture=='restart':
        main=frozen/'src/main.cpp'; text=main.read_text(); needle='        try {\n            if (!world)'
        if text.count(needle)!=1: raise ValueError('uncaught restart injection site changed')
        injection=r'''        if (tc.round==50 && world && world->ready && world->slot==0) {
            bool wrote=act.publish(dz::protocol::with_slot(dz::shared_word(),world->slot,{55,true}));
            std::printf("CT_RESTART_FORCE round=50 slot=0 body=%u wrote=%d objective=55 onsite=1\n",
                static_cast<unsigned>(static_cast<cambc::handle_champion_t>(cambc::self())),wrote);
            std::fflush(stdout);
            throw std::runtime_error("controlled production restart diagnostic");
        }
'''
        main.write_text(text.replace(needle,injection+needle),encoding='utf-8',newline='\n')
    for definition in args.set:
        name,separator,value=definition.partition('=')
        if not separator or not re.fullmatch(r'DZ_[A-Z0-9_]+',name) or not (re.fullmatch(r'[01]',value) or (name.startswith(('DZ_TRACE_','DZ_DRAFT_','DZ_SWITCH_')) and value.isdigit())): raise ValueError('expected DZ_FLAG=0 or 1 (DZ_TRACE_*/DZ_DRAFT_*/DZ_SWITCH_* may be any integer)')
        config=frozen/'src/config.h'; source=config.read_text()
        source,count=re.subn(r'^#define '+name+r'\s+[^\n]+', '#define '+name+' '+value,source,flags=re.MULTILINE)
        if count!=1: raise ValueError('unknown or ambiguous define: '+name)
        config.write_text(source,encoding='utf-8',newline='\n')
    if args.command=='conformance' and args.fixture in ('priority','duel') and not args.fixture_opponent:
        raise ValueError(f'{args.fixture} audit needs a scripted opponent (--fixture-opponent)')
    candidate = build(frozen, out/'candidate.wasm')
    if args.opponent_wasm:
        opponent = out/'opponent.wasm'; shutil.copyfile(Path(args.opponent_wasm), opponent)
    else:
        source_opp = ROOT/'tests/dz'/fixtures[args.fixture] if args.fixture_opponent else ROOT/'bots'/args.opponent
        if args.fixture_opponent and (args.command!='conformance' or args.fixture not in ('tribute','death','contest','group-visibility','group-visibility-first','priority','duel')):
            raise ValueError('scripted opponent is unavailable for this fixture')
        frozen_opp = out/'build/opponent'
        shutil.copytree(source_opp/'src', frozen_opp/'src')
        if args.fixture_opponent:
            if args.fixture=='duel':
                shutil.copyfile(frozen/'src/config.h',frozen_opp/'src/config.h')
                for header in ('duel.h','fight.h'):shutil.copyfile(ROOT/'bots/dz/src'/header,frozen_opp/'src'/header)
            config=frozen_opp/'src/config.h'
            text=config.read_text()
            if text.count('#define CT_OPPONENT 0')!=1: raise ValueError('scripted opponent configuration changed')
            config.write_text(text.replace('#define CT_OPPONENT 0','#define CT_OPPONENT 1'),encoding='utf-8',newline='\n')
            if args.fixture=='group-visibility-first':
                text=config.read_text()
                if text.count('#define DZ_SEEN_MEMBER_FIRST 0')!=1: raise ValueError('visible-member-first configuration changed')
                config.write_text(text.replace('#define DZ_SEEN_MEMBER_FIRST 0','#define DZ_SEEN_MEMBER_FIRST 1'),encoding='utf-8',newline='\n')
        opponent = build(frozen_opp, out/'opponent.wasm')
    map_directory=Path(args.map_dir) if args.map_dir else MAPS
    if not map_directory.is_absolute(): map_directory=ROOT/map_directory
    names = sorted(p.stem for p in map_directory.glob('*.map26a')) if args.pool else args.maps
    diagnostic = args.command == 'conformance'
    jobs = [(map_directory/(name+'.map26a'), side) for name in names for side in ('A','B')]
    provenance = dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(), command=sys.argv,
        git_head=run(['git','rev-parse','HEAD']).strip(), release=True,
        trace=bool(args.trace or injected), diagnostic=diagnostic,
        runner_sha256=sha(out/'runner/dz.py'),
        cli_sha256=sha(CLI), source={p.relative_to(frozen).as_posix():sha(p) for p in (frozen/'src').rglob('*') if p.is_file()},
        sdk={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'sdk/cpp').rglob('*') if p.is_file()},
        maps={p.stem:sha(p) for p,_ in jobs}, candidate_sha256=sha(candidate), opponent_sha256=sha(opponent),
        seed='deterministic; no seed parameter; duplicate identities are not independent samples')
    provenance['map_directory']=os.path.relpath(map_directory,ROOT)
    provenance['fixture']=args.fixture if diagnostic else None
    if args.command=='scenario': provenance['scope']='Production bot on correctness fixture; not strength or promotion evidence'
    provenance['candidate_bot']=args.candidate_bot or 'dz'
    if args.command=='conformance' and args.fixture in ('death','linked','priority'):
        provenance['analysis_source']={p.relative_to(out/'runner').as_posix():sha(p) for p in (out/'runner').rglob('*') if p.is_file() and p.name!='dz.py'}
    if not args.opponent_wasm:
        provenance['opponent_source']={p.relative_to(frozen_opp).as_posix():sha(p) for p in (frozen_opp/'src').rglob('*') if p.is_file()}
    write(out/'provenance.json', provenance)
    ledger = ROOT/'research/dz/SEED_LEDGER.md'
    with ledger.open('a', encoding='utf-8', newline='\n') as f:
        opponent_label='scripted '+args.fixture+' opponent' if args.fixture_opponent else args.opponent
        f.write(f'| {args.name} | {dt.datetime.now(dt.timezone.utc).date()} | deterministic; Wasm {sha(candidate)[:12]} | {len(jobs)} cells; {opponent_label} | {args.command}; trace={args.trace} |\n')
    rows, fuel, errors = [], [], []
    with cf.ThreadPoolExecutor(max_workers=min(4, args.workers)) as executor:
        futures = [executor.submit(match, candidate, opponent, p, side, out/'games'/f'{p.stem}-{side}', diagnostic, args.diagnostic_rounds, args.fixture) for p,side in jobs]
        for future in cf.as_completed(futures):
            try: row, used = future.result()
            except Exception as error: errors.append(str(error)); continue
            rows.append(row); fuel.extend(used)
            print(f"{len(rows)}/{len(jobs)} {row['map']} {row['side']} banked={row['banked']} faults={row['faults']} fuel_outs={row['fuel_outs']}", flush=True)
    if errors:
        write(out/'runner_failures.json', errors)
        raise RuntimeError(f'{len(errors)} cells could not be analyzed; raw evidence retained for recover: '+errors[0])
    finish_report(args.name, out, rows, fuel, diagnostic)

def finish_report(name, out, rows, fuel, diagnostic):
    rows.sort(key=lambda r:(r['map'],r['side'])); fuel.sort()
    result = dict(games=len(rows), wins=sum(r['outcome']=='team'+r['side'] for r in rows),
        faults=sum(r['faults'] for r in rows), opponent_faults=sum(r['opponent_faults'] for r in rows),
        fuel_outs=sum(r['fuel_outs'] for r in rows),
        mean_collected=sum(r['collected'] for r in rows)/len(rows),
        mean_banked=sum(r['banked'] for r in rows)/len(rows),
        fuel_mean=sum(fuel)/max(1,len(fuel)), fuel_p99=fuel[min(len(fuel)-1,int(.99*len(fuel)))] if fuel else None,
        fuel_quantile_policy='diagnostics: omit 20 entries; full matches: omit exactly own draft picks + first boosted turn per body', per_game=rows)
    write(out/'results.json', result)
    dest = ROOT/'research/dz/runs'/name; dest.mkdir(parents=True, exist_ok=False)
    for name in ('results.json','provenance.json'): shutil.copyfile(out/name, dest/name)
    # Complete fresh-system evidence, compressed below normal Git file limits on
    # starter runs. Large campaigns should split capsules before committing.
    with zipfile.ZipFile(dest/'evidence.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in out.rglob('*'):
            if p.is_file() and '.cambc' not in p.parts and not p.name.endswith('.obj'):
                z.write(p, p.relative_to(out))
    print(json.dumps({k:v for k,v in result.items() if k!='per_game'}, indent=2), flush=True)
    provenance=json.loads((out/'provenance.json').read_text())
    missing_trace=provenance.get('trace',False) and not diagnostic and any('caught_action_errors' not in r for r in rows)
    expected_faults=len(rows) if diagnostic and provenance.get('fixture') in ('uncaught','restart') else 0
    if result['faults']!=expected_faults or missing_trace or (not diagnostic and (result['fuel_outs'] or any(
            r.get('caught_action_errors',0) or r.get('caught_module_errors',0) for r in rows))):
        raise SystemExit('runtime gate failed; evidence preserved')
    if diagnostic and any(row.get('diagnostic_checks',{}).get('passed') is False for row in rows):
        raise SystemExit('diagnostic assertions failed; complete evidence preserved')

def recover(args):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.name): raise ValueError('invalid run name')
    out = TMP/args.name
    if (out/'results.json').exists() or (ROOT/'research/dz/runs'/args.name).exists():
        raise ValueError('finished experiments are immutable; recover only incomplete analysis')
    provenance = json.loads((out/'provenance.json').read_text())
    candidate, opponent = out/'candidate.wasm', out/'opponent.wasm'
    if sha(candidate) != provenance['candidate_sha256'] or sha(opponent) != provenance['opponent_sha256']:
        raise ValueError('frozen binaries changed')
    rows, fuel = [], []
    for name,digest in sorted(provenance['maps'].items()):
        directory=Path(provenance.get('map_directory',str(MAPS)))
        if not directory.is_absolute(): directory=ROOT/directory
        path = directory/(name+'.map26a')
        if sha(path) != digest: raise ValueError('map changed')
        for side in ('A','B'):
            row, used = match(candidate,opponent,path,side,out/'games'/f'{name}-{side}',existing=True)
            rows.append(row); fuel.extend(used)
    write(out/'analysis_recovery.json',dict(parser_sha256=sha(Path(__file__)),
        note='Completed raw matches reanalyzed after parser correction; no engine rerun, source or binary change'))
    finish_report(args.name,out,rows,fuel,False)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('host')
    sub.add_parser('build')
    verification = sub.add_parser('verify')
    verification.add_argument('--names',nargs='+',help='verify only these immutable run capsules')
    p = sub.add_parser('recover'); p.add_argument('--name',required=True)
    for name in ('smoke','conformance','scenario'):
        p = sub.add_parser(name); p.add_argument('--name', required=True)
        p.add_argument('--maps', nargs='+', default=['00collision'])
        p.add_argument('--map-dir', help='separate conformance fixture directory; never used for strength tests')
        p.add_argument('--pool', action='store_true'); p.add_argument('--workers', type=int, default=4)
        p.add_argument('--opponent', default='idle81'); p.add_argument('--opponent-wasm')
        p.add_argument('--candidate-bot', help='benchmark bots/<name> instead of DZ (smoke only)')
        p.add_argument('--trace', action='store_true')
        p.add_argument('--fixture', choices=['objective-reward','objective-capture','objective-tribute','kernel','group-visibility-first','group-visibility','draft-stale','tribute-passive','capture-time','camp-mods','prospector','draft-miss','linked','duel','shield','clear','low-fuel','uncaught','restart','camps','targeting','actions','channels','recovery','death','contest','visibility','capture','reset','fingerprint','tribute','module-failure','module-stale','priority'], default='kernel')
        p.add_argument('--fixture-opponent', action='store_true', help='use a scripted tribute/death/contest diagnostic opponent')
        p.add_argument('--diagnostic-rounds', type=int, default=12)
        p.add_argument('--set', action='append', default=[], help='override one DZ boolean flag in the frozen copy only')
        p.add_argument('--plan-rows', help='replace map_plans.inc in the frozen copy (DZ_PLAN_TABLE screens)')
        p.add_argument('--source', help='build DZ from DIR/src (a frozen snapshot) instead of bots/dz')
    args = parser.parse_args()
    if args.command in ('smoke','conformance','scenario'):
        if args.workers<1: parser.error('--workers must be positive')
        if args.diagnostic_rounds<1: parser.error('--diagnostic-rounds must be positive; zero runs no turns')
    if args.command == 'host': host_tests()
    elif args.command == 'verify': verify_evidence(args.names)
    elif args.command == 'recover': recover(args)
    elif args.command == 'build': print(build(ROOT/'bots/dz', TMP/'dz.wasm'))
    else: experiment(args)

if __name__ == '__main__': main()
