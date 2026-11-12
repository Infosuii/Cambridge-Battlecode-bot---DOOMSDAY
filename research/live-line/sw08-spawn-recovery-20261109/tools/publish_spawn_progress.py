"""Export the exact spawn repair and compact evidence for the research branch."""
import shutil

from project import ROOT, save, sha
from sw08_followup import load
from sw08_progress import WORK

DEST = ROOT.parent/'research/sw08-spawn-recovery-20261109'


def copy(path, subpath):
    dest = DEST/subpath
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,dest)
    assert sha(path) == sha(dest)


def main():
    selected = load(WORK/'selection.json') if (WORK/'selection.json').exists() else None
    q_path = WORK/'qualification-replicated.json'
    if not q_path.exists():
        q_path = WORK/'qualification.json'
    q = load(q_path) if q_path.exists() else None
    for f in sorted(WORK.glob('*.json')):
        copy(f,'evidence/'+f.name)
    for label in ('sw08-progress-spawn-trace','sw08-progress-spawn-candidates','sw08-progress-candidate-trace',
                  'sw08-progress-development','sw08-progress-development-direct',
                  'sw08-progress-sealed-reference','sw08-progress-sealed-direct',
                  'sw08-progress-direct-replication','sw08-progress-published-direct',
                  'sw08-progress-islands-trace','sw08-progress-islands-release','sw08-progress-islands-development'):
        for f in ('manifest.json','scores.json'):
            src = ROOT/'panels'/label/f
            if src.exists():
                copy(src,f'evidence/panels/{label}/{f}')
    for f in ('sw08_progress.py','stall_replay.mjs','deliver_cycle.py','publish_spawn_progress.py'):
        copy(ROOT/f,'tools/'+f)
    notes = ('# Spawn recovery on v113\n\n'
             'rv11 counterattacked below 85% health. The matched trace showed a 537-round wait '
             'at roughly 95% health. The fix detects a plateau at any incomplete health above '
             'the lower safety threshold and lets the champion fight back from spawn. '
             'The second arm also tracks the best health reached and prefers an adjacent safe spawn tile. '
             'The third arm allows a safe exit at high health. In the measured Homonoliths fixture, '
             'successful counterattacks drove the change and neither movement branch triggered.\n\n')
    m = load(WORK/'mechanism.json')
    for n,s in m['fixture_trace'].items():
        rate = m['fixture_rates'][n]
        notes += (f'- {n} had {s["wait"]:,} corroborated heal-wait rounds and a longest confirmed run '
                  f'of {s["max"]} rounds. The spawn-area stall rate was {rate:.2%} per alive round.\n')
    notes += '\n'
    if selected and selected['winner']:
        notes += f'`{selected["winner"]}` was frozen after development.\n\n'
    if q:
        name = q['candidate']
        rel = ROOT/'release'/name
        for f in ('source.zip','bot-injected.wasm','manifest.json'):
            copy(rel/f,'release/'+f)
        receipt = rel/'ladder-receipt.json'
        delivery = load(receipt) if receipt.exists() else {}
        if delivery:
            identity = {k:delivery[k] for k in ('version','active_version','phase','note') if k in delivery}
            if delivery.get('remote'):
                identity['platform_status'] = delivery['remote']['status']
            save(DEST/'evidence/ladder.json',identity)
            v = delivery.get('active_version')
            report = ROOT/'ladder-cycle'/'challenger'/'report.json'
            if report.exists() and load(report)['version'] == v:
                d = load(report)
                save(DEST/'evidence/unranked-verification.json',
                     {k:d[k] for k in ('version','games','score','own_faults','fuel','stall_audit','active_verified') if k in d})
        c = q['comparisons']['b113']
        notes += (f'The frozen build ran {q["games"]:,} strength games. Its pooled change versus v113 '
                  f'was {c["gain"]*100:+.2f} percentage points and its direct score was {q["head_to_head"]["score"]:.1%}. '
                  f'Ladder delivery phase was {delivery.get("phase", "no upload")}.\n')
        notes += ('\nThe weights header matched v113 byte for byte. In the 400 paired shared-opponent cells, '
                  '12 losses became wins and 11 wins became losses. '
                  'The observed improvement is shorter spawn healing stalls.\n')
    islands = WORK/'islands-trace.json'
    if islands.exists():
        cases = load(islands)
        old = [r for r in cases if r['candidate']=='hp01tr']
        new = [r for r in cases if r['candidate']=='hc01tr']
        before = sum(r['expired_camp_idle_rounds'] for r in old)
        after = sum(r['expired_camp_idle_rounds'] for r in new)
        moves = sum(r['vacates'] for r in new)
        notes += (f'\nA separate Islands candidate moved off expired camp tiles {moves} times in traced games. '
                  f'Idle time on those tiles fell from {before} to {after} rounds in the fixture. '
                  'Its source experiment is in the tools directory.\n')
    (DEST/'README.md').write_text(notes,encoding='utf-8',newline='\n')
    save(DEST/'SHA256.json',{p.relative_to(DEST).as_posix():sha(p) for p in sorted(DEST.rglob('*'))
                             if p.is_file() and p.name!='SHA256.json'})
    print(DEST,flush=True)


if __name__ == '__main__':
    main()
