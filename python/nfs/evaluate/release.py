"""Release verification logic (used by tools/verify_release.py and tools/package_release.py; unit-tested).

Official ZIP layout (learned from `cambc bundle` 3.0.5 on references/builds/original, agents/H/REPORT.md):
flat `src/<file>` members, sorted, DEFLATE, timestamp 1980-01-01, no directory entries, no comment. `cambc bundle`
packs EVERYTHING under src/ (also nested dirs and non-source files), so this verifier enforces the stricter project
rule: only flat src/*.cpp and src/*.h, byte-equal to the source tree, nothing else.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path, PurePosixPath

from . import wasm as wasm_mod

MEMBER_RE = re.compile(r'^src/[A-Za-z0-9_][A-Za-z0-9_.\-]*\.(cpp|h)$')
FORBIDDEN_STRINGS = (b'NFS1', b'NFT1')
UNSAFE_STATUSES = ('untrained', 'teacher_initialized')


def _chk(name, ok, detail=None):
    return dict(name=name, passed=bool(ok), detail=detail)


def check_zip(zip_path, src_dir) -> list[dict]:
    zip_path, src_dir = Path(zip_path), Path(src_dir)
    out = []
    with zipfile.ZipFile(zip_path) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        bad = [n for n in names if not MEMBER_RE.match(n)]
        out.append(_chk('zip_members_flat_src_cpp_h', not bad, bad[:10]))
        unsafe = [n for n in names if n.startswith('/') or '\\' in n or ':' in n or
                  '..' in PurePosixPath(n).parts or n.endswith('/')]
        out.append(_chk('zip_no_path_traversal', not unsafe, unsafe[:10]))
        out.append(_chk('zip_no_duplicates', len(names) == len(set(names)), len(names) - len(set(names))))
        links = [i.filename for i in infos if (i.external_attr >> 16) & 0o170000 == 0o120000]
        out.append(_chk('zip_no_symlinks', not links, links))
        tree = sorted(p for p in src_dir.rglob('*') if p.is_file())
        extra = [p.relative_to(src_dir).as_posix() for p in tree
                 if p.parent != src_dir or p.suffix not in ('.cpp', '.h')]
        out.append(_chk('source_tree_flat_cpp_h_only', not extra, extra[:10]))
        tree_names = {f'src/{p.name}' for p in tree if p.parent == src_dir}
        out.append(_chk('zip_members_equal_source_files', set(names) == tree_names,
                        dict(missing_in_zip=sorted(tree_names - set(names))[:10],
                             not_in_tree=sorted(set(names) - tree_names)[:10])))
        diff = []
        for n in names:
            if MEMBER_RE.match(n) and n in tree_names:
                if z.read(n) != (src_dir / n[4:]).read_bytes():
                    diff.append(n)
        out.append(_chk('zip_bytes_equal_source_tree', not diff and set(names) == tree_names, diff[:10]))
        out.append(_chk('zip_crc_ok', z.testzip() is None, None))
    return out


def safe_extract(zip_path, dest) -> Path:
    """Extract after validating every member name (never trusts the archive)."""
    dest = Path(dest)
    with zipfile.ZipFile(zip_path) as z:
        for i in z.infolist():
            if not MEMBER_RE.match(i.filename):
                raise ValueError(f'refusing to extract member {i.filename!r}')
            target = (dest / i.filename).resolve()
            if dest.resolve() not in target.parents:
                raise ValueError(f'path traversal: {i.filename!r}')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(i.filename))
    return dest


def _strip_comments(text: str) -> str:
    text = re.sub(r'/\*.*?\*/', ' ', text, flags=re.S)
    return re.sub(r'//[^\n]*', '', text)


def parse_nn_config(text: str) -> dict:
    """Extract profile, flags, macros and per-head modes from a generated nn_config.h (comments ignored; the
    per-head model names that tools/gen_config.py writes as comments are returned separately)."""
    head_models = {m.group(1): m.group(2) for m in
                   re.finditer(r'Mode::\w+\s*,\s*//\s*(\w+)\s*\(([\w.\-]+)\)', text)}
    raw = text
    text = _strip_comments(text)

    def flag(name):
        m = re.search(r'\b' + name + r'\s*=\s*(true|false)\s*;', text)
        return None if m is None else m.group(1) == 'true'

    def macro(name):
        m = re.search(r'#\s*define\s+' + name + r'\s+(\d+)', text)
        return None if m is None else int(m.group(1))

    prof = re.search(r'kProfile\s*=\s*"([^"]*)"', text)
    heads_m = re.search(r'enum\s+class\s+H\s*:\s*int\s*\{([^}]*)\}', text)
    heads = [h.strip() for h in heads_m.group(1).split(',')] if heads_m else []
    heads = [h for h in heads if h and h != 'count']
    modes_m = re.search(r'kMode\s*\[[^\]]*\]\s*=\s*\{([^}]*)\}', text)
    modes = {}
    if modes_m is not None:
        toks = [t.strip() for t in modes_m.group(1).split(',') if t.strip()]
        for i, h in enumerate(heads):
            t = toks[i] if i < len(toks) else 'off'
            t = t.split('::')[-1]
            modes[h] = {'0': 'off', '1': 'shadow', '2': 'active'}.get(t, t)
    return dict(profile=prof.group(1) if prof else None,
                flags={k: flag(k) for k in ('kAnyHead', 'kTraining', 'kTelemetry', 'kFuelCredit', 'kSelfTest', 'kStripLab')},
                macros={k: macro(k) for k in ('NN_ANY_HEAD', 'NN_STRIP_LAB', 'NN_TRAINING', 'NN_TELEMETRY')},
                head_modes=modes, heads=heads, modes_parsed=modes_m is not None, head_models=head_models,
                generated='GENERATED by tools/gen_config.py' in raw)


def check_config(cfg: dict) -> list[dict]:
    f, m = cfg['flags'], cfg['macros']
    out = [_chk('config_profile_release', cfg['profile'] == 'release', cfg['profile'])]
    for k in ('kTraining', 'kTelemetry', 'kSelfTest', 'kFuelCredit'):
        out.append(_chk(f'config_{k}_false', f.get(k) is False, f.get(k)))
    for k in ('NN_TRAINING', 'NN_TELEMETRY'):
        out.append(_chk(f'config_{k}_0', m.get(k) == 0, m.get(k)))
    out.append(_chk('config_head_modes_parsed', cfg['modes_parsed'] and len(cfg['heads']) > 0, len(cfg['heads'])))
    active_any = any(v != 'off' for v in cfg['head_modes'].values())
    out.append(_chk('config_kAnyHead_consistent', f.get('kAnyHead') in (None, active_any), [f.get('kAnyHead'), active_any]))
    shadow = [h for h, v in cfg['head_modes'].items() if v == 'shadow']
    out.append(_chk('config_no_shadow_heads_in_release', not shadow, shadow))
    return out


def check_wasm(path, strip_lab: bool) -> tuple[list[dict], dict]:
    mod = wasm_mod.WasmModule.load(path)
    exports = mod.exports()
    lab = [n for n, _ in exports if n.startswith('lab_')]
    forb = wasm_mod.find_forbidden(mod, FORBIDDEN_STRINGS)
    out = [_chk(f'wasm_no_{k}_string', v['data'] == 0 and v['executable_sections'] == 0, v) for k, v in forb.items()]
    if strip_lab:
        out.append(_chk('wasm_no_lab_exports', not lab, lab))
    info = dict(exports=[n for n, _ in exports], lab_exports=lab, strip_lab_selected=strip_lab,
                custom_sections=mod.custom_sections(), data_bytes=len(mod.data_bytes()),
                lab_exports_note=None if strip_lab else 'lab strip not selected: inherited lab exports are expected '
                                                       '(as in the original); reported, not failed')
    return out, info


def _load_registry(models_dir: Path):
    reg = models_dir / 'registry.json'
    if not reg.exists():
        return None, {}
    data = json.loads(reg.read_text(encoding='utf-8'))
    items = data.get('models', data) if isinstance(data, dict) else data
    if isinstance(items, dict):  # Agent B layout: {"models": {name: {path, status, exportable}}, "release_selection"}
        items = [dict(v, name=v.get('name', k)) for k, v in items.items()]
    selection = data.get('release_selection', {}) if isinstance(data, dict) else {}
    return items, selection or {}


FNV64_OFFSET, FNV64_PRIME = 0xCBF29CE484222325, 0x100000001B3


def fnv1a64(data: bytes) -> int:
    """Independent FNV-1a 64 (CONTRACTS 5: checksum over little-endian float32 parameter bytes)."""
    h = FNV64_OFFSET
    for b in data:
        h = ((h ^ b) * FNV64_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


def check_registry(models_dir, head_modes: dict[str, str], head_models: dict[str, str] | None = None) \
        -> tuple[list[dict], dict]:
    """Lifecycle audit: no untrained/teacher_initialized model active or release-selected, every active head
    backed by a validated model, registry status == manifest status, weights checksum re-computed independently."""
    import hashlib
    models_dir = Path(models_dir)
    root = models_dir.parent
    items, selection = _load_registry(models_dir)
    active_heads = sorted(h for h, v in head_modes.items() if v == 'active')
    head_models = head_models or {}
    if items is None:
        return [_chk('registry_present_or_no_active_heads', not active_heads, dict(active_heads=active_heads))], \
            dict(registry=None)
    out, info = [], dict(models=[], release_selection=selection)
    by_name = {}
    for it in items:
        name = it.get('name')
        mdir = (root / it['path']) if it.get('path') else models_dir / str(name)
        man_p = mdir / 'manifest.json'
        man = json.loads(man_p.read_text(encoding='utf-8')) if man_p.exists() else {}
        status = man.get('status', it.get('status'))
        head = man.get('head', it.get('head'))
        active = bool(it.get('active') or it.get('selected') or it.get('enabled'))
        files = {}
        if mdir.is_dir():
            for p in sorted(mdir.rglob('*')):
                if p.is_file():
                    files[p.relative_to(root).as_posix() if p.is_relative_to(root) else str(p)] = \
                        hashlib.sha256(p.read_bytes()).hexdigest()
        rec = dict(name=name, head=head, status=status, registry_status=it.get('status'), active_flag=active,
                   checksum=man.get('checksum', it.get('checksum')), files_sha256=files, manifest_present=man_p.exists())
        wf = mdir / (man.get('files', {}) or {}).get('weights', 'weights.f32')
        if man.get('checksum') and wf.exists() and man.get('exportable', it.get('exportable', True)):
            got = f'0x{fnv1a64(wf.read_bytes()):016x}'
            rec['checksum_recomputed'] = got
            out.append(_chk(f'registry_{name}_weights_checksum', got == man['checksum'], [got, man['checksum']]))
        if it.get('status') and man.get('status') and it['status'] != man['status']:
            out.append(_chk(f'registry_{name}_status_matches_manifest', False, [it['status'], man['status']]))
        info['models'].append(rec)
        by_name[name] = rec
        if status in UNSAFE_STATUSES and active:
            out.append(_chk(f'registry_{name}_not_active_while_{status}', False, it))
        if status in UNSAFE_STATUSES and head in active_heads:
            out.append(_chk(f'registry_{name}_head_{head}_active_with_{status}_model', False, head))
    for h, name in sorted(selection.items()):
        st = by_name.get(name, {}).get('status')
        out.append(_chk(f'release_selection_{h}_{name}_validated', st == 'validated', st))
    for h in active_heads:
        name = head_models.get(h) or selection.get(h)
        st = by_name.get(name, {}).get('status') if name else None
        ok = st == 'validated' if name else any(m['head'] == h and m['status'] == 'validated' for m in info['models'])
        out.append(_chk(f'registry_active_head_{h}_has_validated_model', ok, dict(model=name, status=st)))
    out.append(_chk('registry_statuses_consistent', all(c['passed'] for c in out), len(info['models'])))
    return out, info


def scan_for_fuel_flag(paths) -> list[dict]:
    """Fail on any USE of the engine's fuel-override flag in scripts: the flag as a quoted token, an assignment
    (flag=value) or the flag followed by a numeric/variable value. Plain-prose mentions (comments/docstrings such as
    'never pass the flag') are reported separately and do not fail."""
    needle = '--' + 'fuel'  # split so this file does not match itself
    use_re = re.compile(r"""(['"])""" + re.escape(needle) + r"""\1|""" + re.escape(needle) + r"""(=|\s+[\d{$(])""")
    mention_re = re.compile(re.escape(needle) + r'(?![\w-])')
    uses, mentions = [], []
    for base in paths:
        base = Path(base)
        if not base.exists():
            continue
        files = [base] if base.is_file() else [p for p in base.rglob('*') if p.is_file() and
                                                p.suffix in ('.py', '.ps1', '.sh', '.bat', '.cmd', '.json', '.toml')]
        for p in files:
            if '__pycache__' in p.parts or '.cambc' in p.parts:
                continue
            try:
                text = p.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if use_re.search(line):
                    uses.append(f'{p}:{i}')
                elif mention_re.search(line):
                    mentions.append(f'{p}:{i}')
    return [_chk('no_fuel_override_in_scripts', not uses, dict(uses=uses[:20], prose_mentions=mentions[:20]))]
