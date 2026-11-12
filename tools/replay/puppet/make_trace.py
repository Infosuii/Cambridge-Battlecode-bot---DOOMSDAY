"""Make a narrow-window trace copy; never edit the frozen source or assume trace fidelity."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deep_preflight import ROOT


def make(case, destination):
    study = ROOT / 'research/deep-2026-10-28'
    cid = case['card_id']
    predictions = json.loads((study / 'CARD_PREDICTIONS.json').read_text(encoding='utf-8'))['rows']
    start, end = case['window'][0] - 20, case['window'][1] + 20
    if cid == 'matched-C034-control':
        native = json.loads((ROOT / 'artifacts/local-only/deep-2026-10-28/replays/examined' / (case['match_id'] + '.summary.json')).read_text(encoding='utf-8'))
        bank = max((dict(e, owner=s['owner']) for s in native['events'] if s['kind'] == 'gemSubmission' and s['owner']['team'] == ('teamA' if case['side'] == 'a' else 'teamB') for e in s['entries'] if 150 <= e['timestamp']['round'] <= 160), key=lambda e: int(e['value']))
        actor = bank['owner']['id']
    elif cid == 'C082':
        det = json.loads((ROOT / 'artifacts/local-only/deep-2026-10-28/detector-examined-v3' / (case['match_id'] + '.json')).read_text(encoding='utf-8'))
        actor = next(a['id'] for a in det['actors'] if a['team'] == (0 if case['side'] == 'a' else 1) and any(case['window'][0] < e['start'] <= case['window'][1] for e in a['detectors']['D3']['events']))
    else:
        actor = next(r['actor_id'] for r in predictions if r['card_id'] == cid)
    destination = Path(destination).resolve()
    assert destination.is_relative_to(ROOT / 'artifacts')
    source = ROOT / 'bots/live-69/src'
    contents = {p.relative_to(source).as_posix(): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    changes = []
    def insert(filename, needle, addition, before=True):
        n = needle.encode()
        b = contents[filename]
        assert b.count(n) == 1, (filename, needle[:60], b.count(n))
        eol = '\r\n' if b.count(b'\r\n') else '\n'
        extra = (addition.rstrip('\n').replace('\n', eol) + eol).encode()
        contents[filename] = b.replace(n, extra + n if before else n + extra, 1)
        changes.append({'file': filename, 'anchor': needle[:100]})
    macros = f'''// Local diagnostic, case {cid}; enabled only for the selected actor/window.
#define DT_FROM {start}
#define DT_UNTIL {end}
#define DT_ACTOR {actor}u
#define DT_LOG(fmt, ...) do {{ if(round>=DT_FROM && round<=DT_UNTIL && my_id==DT_ACTOR) std::printf("DT %d %u " fmt "\\n",round,my_id __VA_OPT__(,) __VA_ARGS__); }} while(0)
'''.replace('\n', '\r\n').encode()
    contents['common.h'] = macros + contents['common.h']
    insert('bot.cpp', '    cast_done = false;\r\n    keep_channel = false;', '''    DT_LOG("TUNE carry=%d shop=%d goldw=%.5f aggression=%.5f retreat=%.5f danger=%.5f stand2=%d tsearch=%d ranged_flee=%d lone=%.3f bag=%d race=%.3f gate=%d mapknobs=%d lab=%d act=%d survive=%d group=%d", tune::kTributeCarry,tune::kShopGold,tune::kGoldWeight,tune::kAggression,tune::kRetreatHp,tune::kDangerHp,tune::kStand2,tune::kTSearch,tune::kRangedFlee,double(V75_LONE),V75_BAG,double(V75_RACE),V75_GATE,V71_MAP_KNOBS,A2_LAB,V58_ACT,V58_SURVIVE,target_group);
    if(round==DT_FROM && my_id==DT_ACTOR){std::printf("DT %d %u KNOBS",round,my_id);for(int dt_i=0;dt_i<48;++dt_i)std::printf(" %.5f",double(lab::knobs[dt_i]));std::printf("\\n");}
''')
    insert('bot.cpp', '    if (state.is_dead()) {\r\n        episode_tick(true);', '    DT_LOG("TURN dead=%d group=%d",state.is_dead(),target_group);')
    insert('bot.cpp', '    // A recall started before a capture landed:', '    DT_LOG("SELF x=%d y=%d hp=%.3f maxhp=%.3f bag=%d gold=%d range=%d melee=%d home=%d group=%d",pos.x,pos.y,hp,max_hp,gems,gold,range,melee,heading_home,target_group);')
    insert('bot.cpp', 'bool Bot::handle_enemies() {\r\n', '    DT_LOG("ENTER handle_enemies enemies=%d",int(w.enemies.size()));', before=False)
    insert('bot.cpp', '    // V75_LONE = r (0 = off):', '''    DT_LOG("GUARD_IN win=%d danger=%d nearest=%d nd=%d erange=%d target=%d ttk=%.5f ttd=%.5f risk=%.5f",winning,in_danger,nearest?int(nearest->id):-1,nearest_d,nearest?nearest->range:-1,target?int(target->id):-1,target_ttk,ttd,risk);
''')
    insert('bot.cpp', '        if (friends == 0 && theirs >= V75_LONE * hp) {', '        DT_LOG("GUARD_COUNT friends4=%d enemy_hp6=%.3f self_hp=%.3f",friends,theirs,hp);')
    insert('bot.cpp', '    if (tune::kTribDeny & 2) {', '    DT_LOG("GUARD_OUT win=%d danger=%d target=%d ttk=%.5f",winning,in_danger,target?int(target->id):-1,target_ttk);')
    insert('bot.cpp', 'bool Bot::tribute_if_needed() {\r\n', '    DT_LOG("BANK_CHECK bag=%d no_bank=%d gated=%d off_until=%d force=%d carry=%d",gems,w.no_bank,w.altar_gated,tribute_off_until,force_tribute,tune::kTributeCarry);', before=False)
    insert('bot.cpp', '    if (dist == kUnreach) return false;\r\n    const bool wins = ally_score + gems', '    DT_LOG("BANK_ROUTE dist=%d safe=%d",dist,use_safe);')
    insert('bot.cpp', '    PROF_CHECK("tail");\r\n    build_fields();', '    DT_LOG("END mode=%s x=%d y=%d hp=%.3f bag=%d walked=%d cast=%d home=%d group=%d force=%d",mode,pos.x,pos.y,hp,gems,walked,cast_done,heading_home,target_group,force_tribute);')
    insert('tactics.cpp', 'bool Bot::act_enemy_before_walk() {\r\n', '    DT_LOG("ENTER act_before enemies=%d walked=%d cast=%d",int(w.enemies.size()),walked,cast_done);', before=False)
    insert('tactics.cpp', 'bool Bot::survive_contact() {\r\n', '    DT_LOG("ENTER survive enemies=%d",int(w.enemies.size()));', before=False)
    insert('tactics.cpp', '    if (!bag_panic && (immediate_finish || hostile < 1.65f * friendly)) return false;', '    DT_LOG("SURVIVE_EVAL nd=%d nearest=%d bag_panic=%d immediate=%d hostile=%.5f friendly=%.5f",distance,int(nearest->id),bag_panic,immediate_finish,hostile,friendly);')
    insert('tactics.cpp', '    if (!moved) return false;\r\n    if (bag_panic || hp < 0.45f * max_hp)', '    DT_LOG("SURVIVE_MOVE dashed=%d moved=%d",dashed,moved);')
    for name, data in contents.items():
        target = destination / 'src' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == data, 'Trace configuration changed; use a fresh output directory'
        target.write_bytes(data)
    result = case | {'trace_actor': actor, 'trace_from': start, 'trace_until': end, 'changes': changes,
                     'source_hashes': {n: hashlib.sha256(b).hexdigest() for n, b in contents.items()},
                     'interpretation': 'trust observations only before first trajectory divergence from exact source run; no frozen source edits'}
    (destination / 'trace-identity.json').write_bytes((json.dumps(result, indent=2) + '\n').encode())
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--card',required=True);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
    case=next(r for r in json.loads((ROOT/'research/deep-2026-10-28/REPRO_PLAN.json').read_text(encoding='utf-8'))['rows'] if r['card_id']==a.card)
    r=make(case,a.out);print(json.dumps({k:r[k] for k in ('card_id','trace_actor','trace_from','trace_until')}))


if __name__=='__main__':main()
