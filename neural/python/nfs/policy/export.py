"""Versioned direct-policy exports; v1 manifests are rejected even if tensors have identical shapes.

Produces f32 weights, an SDK-free constexpr header and an explicit interpretation2 manifest. Numeric arch stays1;
the wrapper descriptor changes meaning. No model is registered, promoted, trained or installed by this module.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import numpy as np

from .. import export as _legacy
from ..models import layout, segments
from ..models.config import canonical_json
from ..models.rt import fnv1a32,fnv1a64_f32
from .model import DirectPolicyNet,validate_config,INTERPRETATION_VERSION,POLICY_KIND

ExportError = _legacy.ExportError
STATUSES = ("untrained","trained","validated")


def checksum(blob):
    return _legacy.checksum(np.asarray(blob,dtype="<f4"))


def state_to_blob(state,cfg):
    validate_config(cfg)
    return _legacy.state_to_blob(state,cfg)


def blob_to_state(blob,cfg):
    validate_config(cfg)
    if not np.isfinite(np.asarray(blob)).all(): raise ExportError("NaN/Inf in weights")
    return _legacy.blob_to_state(blob,cfg)


def render_header(name,cfg,blob,status,segment_checksums,total):
    # The legacy renderer is used for mechanical kernel offsets/literals only; its scorer is never invoked.
    text = _legacy.render_header(name,cfg,blob,status,segment_checksums,total,
                                "Interpretation2 DIRECT logits; kernel arch1; synthetic/untrained unless manifest says trained.")
    text = text.replace("python/nfs/export.py","python/nfs/policy/export.py")
    text = text.replace('#include "nn_model.h"','#include "nn_policy_model.h"')
    text = text.replace(f"nnw_{name}",f"nnpw_{name}").replace("kDesc","kKernel")
    # Kernel action hash must be the complete v2 candidate schema identity, not the legacy head-list digest.
    text = text.replace(f'0x{_legacy.action_schema_hash(cfg):08x}u,',f'0x{cfg["action_schema_hash"]:08x}u,',1)
    closing = f'}} // namespace nnpw_{name}'
    wrapper = (f'inline constexpr nnpm::PolicyDesc kDesc = {{2u, &kKernel}};\n'
               f'static_assert(nnpm::desc_ok(kDesc), "{name}: invalid direct policy interpretation2 descriptor");\n')
    return text.replace(closing,wrapper+closing)


def export_model(model,name,out_dir,status,provenance,validation=None):
    if not isinstance(model,DirectPolicyNet): raise ExportError("export requires DirectPolicyNet; v1 model refused")
    cfg = validate_config(model.cfg)
    if not _legacy.NAME_RE.fullmatch(name): raise ExportError("invalid C++ model name")
    if status not in STATUSES: raise ExportError("direct policy status must be untrained/trained/validated")
    if status != "untrained" and provenance.get("synthetic"):
        raise ExportError("synthetic model cannot be labelled trained or validated")
    blob = state_to_blob(model.state_dict(),cfg)
    segs = _legacy.segment_checksums(cfg,blob); total = checksum(blob)
    header_name = f"nn_policy_weights_{name}.h"
    header = render_header(name,cfg,blob,status,segs,total)
    out = Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"weights.f32").write_bytes(blob.tobytes())
    (out/header_name).write_text(header,encoding="utf-8",newline="\n")
    man = dict(name=name,format="nfs.direct_policy.v2",interpretation_version=2,policy_kind=POLICY_KIND,
               kernel_arch_version=1,arch_version=1,obs_schema_hash=f'0x{cfg["obs"]["obs_schema_hash"]:08x}',
               action_schema_hash=f'0x{cfg["action_schema_hash"]:08x}',
               head_action_hashes={h["name"]:f'0x{h["action_hash"]:08x}' for h in cfg["heads"]},
               architecture=_legacy.architecture(cfg),n_params=int(blob.size),checksum=total,
               segment_checksums=segs,export_precision="f32",engine_version="1.0.3",status=status,
               provenance=copy.deepcopy(provenance),validation=validation or {},config=cfg,
               files=dict(weights="weights.f32",header=header_name),submitted=False)
    (out/"manifest.json").write_text(json.dumps(man,indent=2)+"\n",encoding="utf-8",newline="\n")
    return man


def load_blob(model_dir,*,expected_obs=None,expected_action=None,expected_head_hashes=None):
    d = Path(model_dir); man = json.loads((d/"manifest.json").read_text(encoding="utf-8"))
    if (man.get("format"),man.get("interpretation_version"),man.get("policy_kind"),man.get("kernel_arch_version")) != \
       ("nfs.direct_policy.v2",2,POLICY_KIND,1): raise ExportError("v1 residual/unversioned model refused by direct-policy loader")
    if man.get("export_precision")!="f32" or man.get("engine_version")!="1.0.3" or man.get("status") not in STATUSES:
        raise ExportError("unsupported precision/engine/status")
    cfg = validate_config(man["config"])
    if man.get("architecture")!=_legacy.architecture(cfg): raise ExportError("manifest architecture/config mismatch")
    obs_hash = cfg["obs"]["obs_schema_hash"]; action_hash=cfg["action_schema_hash"]
    read_hash = lambda v:int(v,0) if isinstance(v,str) else int(v)
    if read_hash(man["obs_schema_hash"])!=obs_hash or read_hash(man["action_schema_hash"])!=action_hash:
        raise ExportError("manifest/config schema mismatch")
    if expected_obs is not None and read_hash(expected_obs)!=obs_hash: raise ExportError("observation schema mismatch")
    if expected_action is not None and read_hash(expected_action)!=action_hash: raise ExportError("action schema mismatch")
    for h in cfg["heads"]:
        if read_hash(man["head_action_hashes"][h["name"]])!=h["action_hash"]: raise ExportError("per-head schema mismatch")
        if expected_head_hashes is not None and read_hash(expected_head_hashes[h["name"]])!=h["action_hash"]:
            raise ExportError("expected per-head schema mismatch")
    weights_path = (d/man["files"]["weights"]).resolve()
    if not weights_path.is_relative_to(d.resolve()): raise ExportError("weights path escapes model directory")
    raw = weights_path.read_bytes()
    if len(raw)%4: raise ExportError("partial f32 weight")
    blob=np.frombuffer(raw,dtype="<f4").copy()
    expected_n=sum(int(np.prod(s)) for _,s in layout(cfg))
    if blob.size!=expected_n or blob.size!=man["n_params"]: raise ExportError("parameter count mismatch")
    if not np.isfinite(blob).all(): raise ExportError("NaN/Inf in weights")
    if checksum(blob)!=man["checksum"]: raise ExportError("weights checksum mismatch")
    if _legacy.segment_checksums(cfg,blob)!=man["segment_checksums"]: raise ExportError("segment checksum mismatch")
    # Header is deterministic derived data: reject manually altered descriptors or weights there too.
    wanted = render_header(man["name"],cfg,blob,man["status"],man["segment_checksums"],man["checksum"])
    header_path=(d/man["files"]["header"]).resolve()
    if not header_path.is_relative_to(d.resolve()) or header_path.read_text(encoding="utf-8")!=wanted:
        raise ExportError("header content mismatch")
    return man,blob


def load_model(model_dir,**kwargs):
    man,blob=load_blob(model_dir,**kwargs)
    model=DirectPolicyNet(man["config"])
    model.load_state_dict(blob_to_state(blob,man["config"]))
    return model
