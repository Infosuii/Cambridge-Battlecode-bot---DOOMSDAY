"""Native C++ test runner for the neural runtime (agent B).

    python tools/run_cpp_tests.py [--only rt_head] [--keep] [--json evaluation/results/cpp_tests.json]

Compiles every tests/cpp/rt_* target with g++ -std=c++20 -O2 -ffp-contract=off (config/paths.json native_cxx),
runs it, and cross-checks outputs against the Python twins where the program emits data:
  rt_kernels            self-checking kernel tests (nn_rt.h, nn_log.h)
  rt_records            NFS1 writer -> python/nfs/records.py decoder round trip
  rt_head:<variant>     nn_head.cpp in a scratch tree installed by tools/install_models.py for a profile
                        (-DNN_HOST_TEST, stub nn_schema.h/nn_obs.h); training records and selftest lines are
                        re-derived bit-for-bit by python/nfs/models/reference.py
  rt_off_empty          nn_head.cpp under teacher_exact compiles to an object without any symbol
Scratch trees: artifacts/tmp/B/cpp/. Results JSON: evaluation/results/cpp_tests.json. Synthetic data only.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
sys.path.insert(0, str(ROOT / 'tools'))

from nfs import export, records  # noqa: E402
from nfs.models import reference  # noqa: E402
from nfs.models.rt import decision_stream, fnv1a64_f32  # noqa: E402
import install_models  # noqa: E402

PATHS = json.loads((ROOT / 'config/paths.json').read_text(encoding='utf-8'))
CXX = PATHS.get('native_cxx', 'g++')
TMP = ROOT / 'artifacts/tmp/B/cpp'
FLAGS = ['-std=c++20', '-O2', '-ffp-contract=off', '-Wall', '-Wextra', '-Wno-unused-parameter']
OWN = ['nn_rt.h', 'nn_model.h', 'nn_budget.h', 'nn_head.h', 'nn_head.cpp', 'nn_log.h']
VARIANTS = {  # variant -> (profile, model override, tamper)
    'zero_active': ('dev_untrained', 'fs_v1_untrained', None),
    'dev_active': ('dev_untrained', None, None),
    'shadow': ('neutral_real', None, None),
    'training': ('training', None, None),
    'selftest': ('selftest', None, None),
    'badsum': ('dev_untrained', None, 'badsum'),
    'nanw': ('dev_untrained', None, 'nanw'),
    'schema': ('dev_untrained', None, 'schema'),
}


def compile_exe(sources, out, includes, defines=(), extra=()):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [CXX, *FLAGS, *[f'-D{d}' for d in defines], *[f'-I{i}' for i in includes], *map(str, sources), '-o',
           str(out), *extra]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f'compile failed: {" ".join(cmd)}\n{r.stdout}{r.stderr}')
    return out


def run_exe(exe, *args, timeout=600):
    r = subprocess.run([str(exe), *map(str, args)], capture_output=True, timeout=timeout)
    return r.returncode, r.stdout.decode('utf-8', 'replace'), r.stderr.decode('utf-8', 'replace')


_STUB_REG = None


def stub_registry() -> Path:
    """Synthetic test models exported against tests/cpp/rt_stub_nn_schema.h (built once per run)."""
    global _STUB_REG
    if _STUB_REG is None:
        from nfs.models import untrained
        base = TMP / 'stub_models'
        stub = ROOT / 'tests/cpp/rt_stub_nn_schema.h'
        models = {}
        for name, zr in (('fs_v1_untrained', True), ('fs_v1_dev', False)):
            untrained.make(name, zr, out_dir=base / name, schema_header=stub)
            models[name] = dict(path=(base / name).relative_to(ROOT).as_posix(), status='untrained', exportable=True,
                                label='synthetic test model (stub schema)')
        _STUB_REG = base / 'registry.json'
        _STUB_REG.write_text(json.dumps(dict(version=1, models=models, release_selection={}), indent=2),
                             encoding='utf-8')
    return _STUB_REG


def prepare_tree(name: str, profile: str, model: str | None = None, tamper: str | None = None) -> Path:
    """Scratch source tree: B's runtime files + stub C headers + generated config/registry/weights."""
    d = TMP / name
    src = d / 'src'
    if d.exists():
        shutil.rmtree(d)
    src.mkdir(parents=True)
    for f in OWN:
        shutil.copy2(ROOT / 'bot/src' / f, src / f)
    # Runtime unit tests use the stub observation layout (RawTurn.x = encoded obs) and test-only synthetic models
    # exported against that stub schema; the real models in models/ follow agent C's schema (lead, wave-1 fix).
    shutil.copy2(ROOT / 'tests/cpp/rt_stub_nn_schema.h', src / 'nn_schema.h')
    shutil.copy2(ROOT / 'tests/cpp/rt_stub_nn_obs.h', src / 'nn_obs.h')
    summary = install_models.install(profile, src, ROOT, quiet=True, model=model, registry_path=stub_registry())
    (d / 'install.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    if tamper in ('badsum', 'nanw'):
        m = summary['models'][0]
        man, blob = export.load_blob(TMP / 'stub_models' / m)
        cfg = man['config']
        segs = export.segment_checksums(cfg, blob)
        total = man['checksum']
        if tamper == 'badsum':
            segs['enc'] = f'0x{(int(segs["enc"], 16) ^ 1):016x}'  # one-bit checksum mismatch
            text = export.render_header(m, cfg, blob, man['status'], segs, total)
        else:
            bad = blob.copy()
            bad[3] = np.float32(1.0)  # placeholder, replaced by a NaN literal below
            nan_blob = blob.copy()
            nan_blob.view('<u4')[3] = 0x7FC00000
            segs = export.segment_checksums(cfg, nan_blob)  # checksums MATCH: only the NaN check can reject it
            total = export.checksum(nan_blob)
            text = export.render_header(m, cfg, bad, man['status'], segs, total)
            lits = re.search(r'kBlob\[\d+\] = \{\n([^\n]*)', text)
            first = lits.group(1).split(',')
            first[3] = '__builtin_nanf("")'
            text = text[:lits.start(1)] + ','.join(first) + text[lits.end(1):]
        (src / f'nn_weights_{m}.h').write_text(text, encoding='utf-8', newline='\n')
    elif tamper == 'schema':
        t = (src / 'nn_schema.h').read_text(encoding='utf-8').replace('kObsSchemaHash = 0x00000000u',
                                                                      'kObsSchemaHash = 0x12345678u')
        (src / 'nn_schema.h').write_text(t, encoding='utf-8', newline='\n')
    return src


def parse_checks(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        if line.startswith('PASS '):
            out.append(dict(name=line[5:].strip(), passed=True))
        elif line.startswith('FAIL '):
            parts = line[5:].split(' ', 1)
            out.append(dict(name=parts[0], passed=False, detail=parts[1] if len(parts) > 1 else ''))
    return out


# ---------------------------------------------------------------------- cross checks against the Python twins
def check_training_records(stdout: str, src: Path) -> list[dict]:
    """Every decision record: logits re-derived bit-exactly by the numpy reference from the logged context; the
    sampled choice re-derived from the PRNG twin; logp within 1e-6."""
    summary = json.loads((src.parent / 'install.json').read_text(encoding='utf-8'))
    m = summary['models'][0]
    man, blob = export.load_blob(TMP / 'stub_models' / m)
    cfg = man['config']
    B = reference.Blob(cfg, blob)
    seed = int(re.search(r'kSeed = (\d+)u', (src / 'nn_config.h').read_text()).group(1))
    recs = records.parse_text(stdout)
    ctx = {}
    n_dec = bad_logit = bad_choice = bad_logp = 0
    max_lp = 0.0
    hcache = {}
    for r in recs:
        key = (r['round'], r['champion'])
        if r['kind'] == 'turn':
            ctx[key] = np.frombuffer(r['raw'], '<f4')
            continue
        if r['kind'] != 'decision':
            continue
        n_dec += 1
        hc = cfg['heads'][r['head']]
        if hc['uses_ctx']:
            if key not in ctx:  # a context head's decision must be preceded by its turn-context record
                bad_logit += 1
                continue
            if key not in hcache:
                hcache[key] = reference.encode(B, ctx[key])
        h = hcache.get(key)
        lg = reference.candidate_logits(B, hc['name'], h if hc['uses_ctx'] else None, r['feat'], r['legal'],
                                        r['prior'], r['context'])
        if lg.tobytes() != r['logit'].tobytes():
            bad_logit += 1
        if r['sampled']:
            u = decision_stream(seed, r['round'], r['champion'], r['head'], r['call']).uniform()
            pick, lp = reference.masked_sample(lg, r['legal'], u)
            if pick != r['chosen']:
                bad_choice += 1
            max_lp = max(max_lp, abs(float(lp) - r['logp']))
            if abs(float(lp) - r['logp']) > 1e-6:
                bad_logp += 1
    return [dict(name='records_decode', passed=n_dec > 0, detail=f'{len(recs)} records, {n_dec} decisions'),
            dict(name='records_logits_bit_exact_vs_reference', passed=n_dec > 0 and bad_logit == 0,
                 detail=f'{bad_logit}/{n_dec} differ'),
            dict(name='records_sampled_choice_prng_twin', passed=n_dec > 0 and bad_choice == 0,
                 detail=f'{bad_choice}/{n_dec} differ'),
            dict(name='records_logp_within_1e-6', passed=bad_logp == 0, detail=f'max |dlogp| {max_lp:.3g}')]


def check_selftest(stdout: str, src: Path) -> list[dict]:
    summary = json.loads((src.parent / 'install.json').read_text(encoding='utf-8'))
    out = []
    got = [l.strip() for l in stdout.splitlines() if l.startswith('NNST ') and (' enc ' in l or ' head ' in l
                                                                               or ' value ' in l or ' leaf ' in l)]
    for m in summary['models']:
        man, blob = export.load_blob(TMP / 'stub_models' / m)
        want = reference.selftest_lines(man['config'], blob, m)
        mine = [l for l in got if l.split()[1] == m]
        out.append(dict(name=f'selftest_lines_match_reference_{m}', passed=mine == want,
                        detail=f'{sum(a == b for a, b in zip(mine, want))}/{len(want)} lines equal'))
    out.append(dict(name='selftest_verify_ok', passed='verify 1' in stdout, detail='segment verification state'))
    return out


def check_records_roundtrip(stdout: str) -> list[dict]:
    from nfs.models.rt import SplitMix64
    recs = records.parse_text(stdout)
    r = SplitMix64(424242)
    ok = len(recs) == 18 and recs[0]['kind'] == 'episode' and recs[0]['seed'] == 2026102401 and \
        recs[0]['model_checksum'] == 0x0123456789ABCDEF and recs[1]['raw'] == bytes((i * 7 + 3) & 255 for i in range(37))
    bad = 0
    for K, rec in zip(range(1, 17), recs[2:]):
        F = 1 + (K * 5) % 24
        legal = [k == 0 or (k % 3) != 1 for k in range(K)]
        logit = [r.uniform() if legal[k] else np.float32(-np.inf) for k in range(K)]
        feat = r.uniform_pm1(K * F)
        chosen = max(k for k in range(K) if legal[k])
        good = (rec['K'] == K and rec['F'] == F and rec['head'] == K % 13 and rec['round'] == -5 + K
                and rec['chosen'] == chosen and rec['champion'] == 7 and rec['schema_hash'] == 0xA1B2C3D4
                and rec['context'] == K % 4 and rec['action_hash'] == 0xBEEF0000 + K and rec['call'] == K * 3
                and rec['net'] == K // 2 and rec['mode'] == 'active' and rec['sampled'] and rec['reason'] == 'ok'
                and rec['logp'] == np.float32(-0.5 * K)
                and np.array_equal(rec['prior'], np.array([-0.25 * k for k in range(K)], np.float32))
                and list(rec['legal']) == legal and list(rec['id']) == [1000 * K + k for k in range(K)]
                and rec['feat'].tobytes() == feat.tobytes()
                and np.array_equal(rec['logit'], np.array(logit, np.float32)))
        bad += not good
    # Python writer -> decoder identity on the C++ records.
    ident = all(records.decode_payload(records.encode_payload(x)).keys() == x.keys() for x in recs)
    return [dict(name='records_cpp_to_python_fields', passed=ok and bad == 0, detail=f'{bad} decision mismatches'),
            dict(name='records_oversize_dropped', passed='dropped=1 written=18 oversize_ok=0' in stdout,
                 detail=stdout.strip().splitlines()[-1] if stdout.strip() else ''),
            dict(name='records_python_reencode', passed=ident, detail='')]


# ---------------------------------------------------------------------- targets
def t_kernels():
    exe = compile_exe([ROOT / 'tests/cpp/rt_kernels.cpp'], TMP / 'rt_kernels/rt_kernels.exe', [ROOT / 'bot/src'])
    rc, out, err = run_exe(exe)
    return parse_checks(out + err), rc


def t_records():
    exe = compile_exe([ROOT / 'tests/cpp/rt_records.cpp'], TMP / 'rt_records/rt_records.exe', [ROOT / 'bot/src'])
    rc, out, err = run_exe(exe)
    return check_records_roundtrip_safe(out), rc


def check_records_roundtrip_safe(out):
    try:
        return check_records_roundtrip(out)
    except records.RecordError as e:
        return [dict(name='records_cpp_to_python_fields', passed=False, detail=str(e))]


def t_head(variant: str):
    profile, model, tamper = VARIANTS[variant]
    src = prepare_tree(f'rt_head_{variant}', profile, model, tamper)
    exe = compile_exe([ROOT / 'tests/cpp/rt_head.cpp', src / 'nn_head.cpp'], src.parent / 'rt_head.exe', [src],
                      defines=['NN_HOST_TEST'])
    rc, out, err = run_exe(exe, variant)
    (src.parent / 'stdout.txt').write_text(out, encoding='utf-8')
    checks = [dict(c, name=f'{variant}:{c["name"]}') for c in parse_checks(err)]
    if variant == 'training':
        checks += [dict(c, name=f'{variant}:{c["name"]}') for c in check_training_records(out, src)]
    if variant == 'selftest':
        checks += [dict(c, name=f'{variant}:{c["name"]}') for c in check_selftest(out, src)]
    return checks, rc


def t_off_empty():
    """teacher_exact: nn_head.cpp must compile to an object with no symbols and no code (natively)."""
    src = prepare_tree('rt_off', 'teacher_exact')
    obj = src.parent / 'nn_head.o'
    r = subprocess.run([CXX, *FLAGS, '-c', str(src / 'nn_head.cpp'), '-o', str(obj)], capture_output=True, text=True)
    if r.returncode:
        return [dict(name='off_compiles', passed=False, detail=r.stderr[-2000:])], 1
    nm = Path(CXX).with_name('nm.exe') if Path(CXX).with_name('nm.exe').exists() else 'nm'
    syms = subprocess.run([str(nm), str(obj)], capture_output=True, text=True).stdout
    real = [l for l in syms.splitlines() if l.strip() and not re.search(r'\s[btdrN]\s\.', l)]
    return [dict(name='off_nn_head_object_has_no_symbols', passed=not real, detail='; '.join(real[:5]))], 0


TARGETS = {'rt_kernels': t_kernels, 'rt_records': t_records, 'rt_off_empty': t_off_empty,
           **{f'rt_head:{v}': (lambda v=v: t_head(v)) for v in VARIANTS}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', default=None, help='substring filter on target names')
    ap.add_argument('--json', default=str(ROOT / 'evaluation/results/cpp_tests.json'))
    a = ap.parse_args(argv)
    results, t0 = [], time.time()
    for name, fn in TARGETS.items():
        if a.only and a.only not in name:
            continue
        t = time.time()
        try:
            checks, rc = fn()
            err = None
        except Exception as e:  # compile errors etc. are reported, not hidden
            checks, rc, err = [], -1, str(e)[-4000:]
        ok = rc == 0 and err is None and checks and all(c['passed'] for c in checks)
        results.append(dict(target=name, passed=bool(ok), returncode=rc, error=err, seconds=round(time.time() - t, 2),
                            n_checks=len(checks), failed=[c for c in checks if not c['passed']], checks=checks))
        print(f'{"PASS" if ok else "FAIL"} {name}: {sum(c["passed"] for c in checks)}/{len(checks)} checks'
              + (f' ERROR {err[:3000]}' if err else '') + ''.join(f'\n    FAIL {c["name"]} {c.get("detail", "")}'
                                                               for c in checks if not c['passed']), flush=True)
    rep = dict(tool='tools/run_cpp_tests.py', compiler=CXX, flags=FLAGS, synthetic_data_only=True,
               generated=time.strftime('%Y-%m-%dT%H:%M:%S'), seconds=round(time.time() - t0, 1),
               passed=all(r['passed'] for r in results), n_targets=len(results),
               n_checks=sum(r['n_checks'] for r in results), results=results)
    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps(rep, indent=2) + '\n', encoding='utf-8')
    print(f'{"ALL PASS" if rep["passed"] else "FAILURES"}: {rep["n_targets"]} targets, {rep["n_checks"]} checks -> {a.json}')
    return 0 if rep['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
