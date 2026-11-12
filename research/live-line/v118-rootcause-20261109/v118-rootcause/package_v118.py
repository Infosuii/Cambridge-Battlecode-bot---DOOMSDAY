"""Package the v118 candidate (release/v18HDR) and the portable handoff folder DOOMSDAY-v118-handoff/."""
from pathlib import Path
import sys, json, shutil, subprocess, zipfile, os, datetime, hashlib
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from project import ROOT, ARENA, CLI, ENGINE, ENGINE_HASH, save, sha, digest

NAME = 'v18HDR'


def package():
    dest = ROOT / 'release' / NAME; dest.mkdir(parents=True, exist_ok=True); bundle = dest / 'source.zip'
    if not bundle.exists():
        r = subprocess.run([str(CLI), 'bundle', 'bots/' + NAME, '--output', str(bundle)], cwd=ARENA, capture_output=True, text=True,
                           encoding='utf-8', timeout=120, env={**os.environ, 'CAMBC_NO_UPDATE_CHECK': '1'})
        assert r.returncode == 0, (r.stdout + r.stderr)[-1000:]
    src = ARENA / 'bots' / NAME
    with zipfile.ZipFile(bundle) as z:
        assert z.testzip() is None
        expected = {p.relative_to(src).as_posix(): p for p in (src / 'src').rglob('*') if p.is_file()}
        assert {n for n in z.namelist() if not n.endswith('/')} == set(expected)
        for n, f in expected.items(): assert z.read(n) == f.read_bytes()
    shutil.copy2(src / '.cambc/build-release/bot-injected.wasm', dest / 'bot-injected.wasm')
    hold = HERE / 'holdout-result.json'; result = json.loads(hold.read_text())
    approved = all(result['gates'].values())
    manifest = {'candidate': NAME, 'version_label': 'v118 candidate (v117 + home siege H + relaxed bridge dash D + route veto R)',
                'parent': {'name': 'hp01', 'ladder_version': 117, 'source_digest': digest(ARENA / 'bots/hp01/src'),
                           'wasm_sha256': sha(ARENA / 'bots/hp01/.cambc/build-release/bot-injected.wasm')},
                'source_digest': digest(src / 'src'), 'source_zip': {'file': 'source.zip', 'sha256': sha(bundle)},
                'wasm': {'file': 'bot-injected.wasm', 'sha256': sha(dest / 'bot-injected.wasm')},
                'nn_weights_sha256': sha(src / 'src/nn_weights.h'), 'weights_note': 'frozen v113/v117 network (identical to hp01 nn_weights.h)',
                'sdk_digest': digest(ARENA / 'sdk/cpp'), 'cli_sha256': sha(CLI), 'engine': ENGINE, 'engine_build': ENGINE_HASH,
                'holdout_result_sha256': sha(hold), 'protocol_sha256': sha(HERE / 'release-protocol.json'),
                'gates': result['gates'], 'approved_for_upload': approved,
                'reason': 'Sealed holdout G4 strength gate failed (-4/720 paired, bootstrap p10 -3.6pp); targeted incidents fixed; not for ladder submission without a new decision.' if not approved else 'All pre-registered gates passed.',
                'rollback': 'Re-activate ladder version 117 (hp01): cambc submissions activate 117 --json; verify active/selected == 117.'}
    save(dest / 'manifest.json', manifest)
    (dest / 'README.md').write_text('# v118 candidate package (v18HDR)\n\nExact source, release Wasm and identities in manifest.json. '
                                   f'Upload approved: {approved}. See ../../v118-rootcause/FINDINGS.md.\n', encoding='utf-8')
    return dest, manifest


def handoff():
    out = ROOT / 'DOOMSDAY-v118-handoff'
    if out.exists(): shutil.rmtree(out)
    out.mkdir()
    keep_ext = {'.py', '.json', '.md', '.inc', '.log'}
    for p in HERE.iterdir():
        if p.is_file() and p.suffix in keep_ext and p.stat().st_size < 2_000_000: shutil.copy2(p, out / 'v118-rootcause' / p.name) if (out / 'v118-rootcause').exists() else ((out / 'v118-rootcause').mkdir(), shutil.copy2(p, out / 'v118-rootcause' / p.name))
    for b in ('hp01', 'v18HDR', 'v18H', 'v18DR', 'v18L'):
        shutil.copytree(ARENA / 'bots' / b / 'src', out / 'bots' / b / 'src')
    shutil.copytree(ROOT / 'release' / NAME, out / 'release' / NAME)
    shutil.copytree(ROOT / 'release' / 'hp01', out / 'release' / 'hp01-v117-rollback')
    t = out / 'training/v118-hdr'; t.mkdir(parents=True)
    tw = ROOT / 'training/v118-hdr'
    for f in tw.iterdir():
        if f.suffix in ('.json', '.h', '.log') or f.name in ('best.pt', 'resume_6.pt', 'student_4.pt', 'blend_050.pt'):
            shutil.copy2(f, t / f.name)
    shutil.copy2(ROOT / 'training/initial-v113.pt', t / 'initial-v113.pt')
    for s in ('project.py', 'local_panel.py', 'policy_rows.py', 'sw08_followup.py', 'sw08_v113_minimal.py', 'stall_campaign.py', 'merge.py',
              'setup_training.py', 'prepare_campaign.py', 'published-maps.json', 'references.json', 'campaign.json', 'stall_replay.mjs'):
        if (ROOT / s).exists(): shutil.copy2(ROOT / s, out / 'tools' / s) if (out / 'tools').exists() else ((out / 'tools').mkdir(), shutil.copy2(ROOT / s, out / 'tools' / s))
    ev = out / 'evidence'; ev.mkdir()
    for panel in ('v118-incident-homonoliths', 'v118-incident-islands', 'v118-dev-a', 'v118-dev-b-styles', 'v118-dev-c-generated', 'v118-dev-d-hdrl',
                  'v118-dev-L', 'v118-arms-select', 'v118-dev-c-generated-arms', 'v118-holdout-reference', 'v118-holdout-direct', 'v118-confirm-fresh'):
        for f in ('results.json', 'manifest.json', 'scores.json'):
            p = ROOT / 'panels' / panel / f
            if p.exists(): (ev / panel).mkdir(exist_ok=True); shutil.copy2(p, ev / panel / f)
    files = []
    for p in sorted(out.rglob('*')):
        if p.is_file(): files.append({'path': p.relative_to(out).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    save(out / 'MANIFEST.json', {'created': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'files': files,
                                 'total_bytes': sum(f['bytes'] for f in files),
                                 'not_included': 'raw replays and native summaries (panels/*/<cell>/), rollout data_*.npz (~220 MB), arena SDK/CLI; regenerate with the scripts'})
    return out, len(files), sum(f['bytes'] for f in files)


if __name__ == '__main__':
    d, m = package(); print(d, m['approved_for_upload'])
    print(handoff())
