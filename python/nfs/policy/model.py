"""Direct masked logits, interpretation2 over the unchanged numeric encoder/kernel arch1 layout.

No teacher score, prior, preferred index or teacher flag is accepted by head_logits. This module reuses the proven
shared encoder implementation and raw candidate MLP math, but never the legacy bounded-residual scorer.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import numpy as np
import torch

from ..models import PolicyNet as _KernelNet, layout, segments
from ..models import init_untrained as _init_kernel
from ..models.config import parse_schema_header, check_limits, canonical_json
from ..models.rt import fnv1a32

ROOT = Path(__file__).resolve().parents[3]
INTERPRETATION_VERSION = 2
POLICY_KIND = "direct_masked_logits"
HEAD_IDS = dict(strategy=1, objective=2, role=3, bank=4, shop=5, move=6, combat=7, engage=8)
HEAD_NAMES = list(HEAD_IDS)


def _hash(v):
    if isinstance(v, bool) or not isinstance(v,(int,np.integer,str)): raise ValueError("schema hash must be an integer")
    n = int(v, 0) if isinstance(v, str) else int(v)
    if not 0 < n <= 0xffffffff: raise ValueError("schema hash must be nonzero uint32")
    return n


def validate_config(cfg):
    if cfg.get("interpretation_version") != 2 or cfg.get("policy_kind") != POLICY_KIND or cfg.get("kernel_arch_version") != 1:
        raise ValueError("requires direct policy interpretation2 and numeric kernel arch1; v1 residual models refused")
    if cfg.get("arch_version") != 1: raise ValueError("numeric kernel arch must remain1")
    check_limits(cfg)
    o=cfg["obs"]; e=cfg["encoder"]
    for key in ("self_global_dim","ally_rows","ally_dim","enemy_rows","enemy_dim","obs_dim"):
        if type(o[key]) is not int or o[key]<0: raise ValueError("invalid observation dimensions")
    if o["obs_dim"] != o["self_global_dim"]+o["ally_rows"]*(o["ally_dim"]+1)+o["enemy_rows"]*(o["enemy_dim"]+1):
        raise ValueError("observation layout sum mismatch")
    if any(type(e[k]) is not int for k in ("global_hidden","entity_hidden","ctx")): raise ValueError("integer encoder dimensions required")
    heads = cfg["heads"]
    if [(h["name"],h["id"]) for h in heads] != list(HEAD_IDS.items()): raise ValueError("exact direct head IDs/order required")
    _hash(cfg["action_schema_hash"]); _hash(cfg["obs"]["obs_schema_hash"])
    for h in heads:
        if (h["kind"], h["uses_ctx"], h["F"],h["n_ctx"],h["n_out"],h["R"]) != ("candidate",True,12,4,1,1.0):
            raise ValueError("direct heads require candidate numeric layout, F12/context4 and unused R tag1")
        _hash(h["action_hash"])
        if type(h["hidden"]) is not int: raise ValueError("integer head dimensions required")
    return cfg


def load_config(name_or_path="policy_v2", *, root=ROOT, action_hashes=None, action_schema_hash=None, obs=None):
    root = Path(root)
    if isinstance(name_or_path, dict): raw = copy.deepcopy(name_or_path)
    else:
        p = Path(name_or_path)
        if not p.suffix: p = root / "configs/model" / (str(name_or_path)+".json")
        raw = json.loads(p.read_text(encoding="utf-8"))
    if raw.get("interpretation_version") != 2 or raw.get("policy_kind") != POLICY_KIND or raw.get("kernel_arch_version") != 1:
        raise ValueError("v1 residual or unversioned model refused by direct policy loader")
    if isinstance(raw.get("heads"),list): return validate_config(raw)
    if raw.get("active_heads") != HEAD_NAMES: raise ValueError("active direct head set/order changed")
    o = copy.deepcopy(obs) if obs is not None else parse_schema_header(root / raw["obs_schema_header"])
    if o is None: raise ValueError("real observation schema is required; no provisional fallback")
    schema_path = root / raw["action_schema"]
    if action_hashes is None:
        if not schema_path.exists(): raise ValueError("policy candidate schema missing; pass explicit action_hashes for synthetic tests")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        # Candidate owner can publish explicit hash fields; otherwise hash the complete head semantics.
        specs = schema.get("heads",[])
        if isinstance(specs,dict): specs = [dict(v,name=k) for k,v in specs.items()]
        action_hashes={}
        for h in specs:
            clean_head=copy.deepcopy(h); stored=clean_head.pop("action_hash",None)
            computed=fnv1a32(canonical_json(clean_head))
            if stored is not None and _hash(stored)!=computed: raise ValueError("stored head schema hash mismatch")
            action_hashes[h["name"]]=computed
        if action_schema_hash is None:
            clean = copy.deepcopy(schema); clean.pop("action_schema_hash",None)
            head_specs = clean.get("heads",[])
            for h in head_specs.values() if isinstance(head_specs,dict) else head_specs: h.pop("action_hash",None)
            computed=fnv1a32(canonical_json(clean))
            stored=schema.get("action_schema_hash")
            if stored is not None and _hash(stored)!=computed: raise ValueError("stored combined schema hash mismatch")
            action_schema_hash = computed
    hashes = {name:_hash(action_hashes[name]) for name in HEAD_NAMES}
    combined = _hash(action_schema_hash) if action_schema_hash is not None else fnv1a32(canonical_json(list(hashes.items())))
    hd = raw["heads"]
    if (hd.get("F"),hd.get("contexts")) != (12,4): raise ValueError("v2 F12/context4 required")
    cfg = dict(name=raw["name"],interpretation_version=2,policy_kind=POLICY_KIND,kernel_arch_version=1,arch_version=1,
               obs=o,encoder=raw["encoder"],action_schema_hash=combined,
               heads=[dict(name=name,id=hid,kind="candidate",uses_ctx=True,F=12,hidden=int(hd["hidden"]),n_ctx=4,
                           n_out=1,R=1.0,action_hash=hashes[name]) for name,hid in HEAD_IDS.items()],provisional=[])
    return validate_config(cfg)


class DirectPolicyNet(_KernelNet):
    """nn.Module with exact legacy raw-kernel parameter layout and new direct score interpretation."""
    def __init__(self,cfg):
        super().__init__(validate_config(copy.deepcopy(cfg)))

    def head_logits(self,head,h,feat,legal,context=None):
        if head not in HEAD_IDS: raise ValueError("not a direct-policy head")
        if feat.ndim!=3 or feat.shape[-1]!=12 or feat.shape[1]>16 or feat.shape[1]==0: raise ValueError("expected [B,1..16,12]")
        if h.ndim!=2 or h.shape!=(feat.shape[0],self.cfg["encoder"]["ctx"]): raise ValueError("context shape mismatch")
        if legal.shape!=feat.shape[:2]: raise ValueError("mask shape mismatch")
        if not bool(torch.isfinite(h).all()) or not bool(torch.isfinite(feat).all()): raise ValueError("nonfinite model inputs")
        if legal.dtype!=torch.bool and not bool(((legal==0)|(legal==1)).all()): raise ValueError("nonbinary mask")
        if context is not None and (context.dtype not in (torch.uint8,torch.int8,torch.int16,torch.int32,torch.int64) or
                                   context.shape!=(feat.shape[0],) or not bool(((context>=0)&(context<4)).all())):
            raise ValueError("context code out of range")
        # Raw score: no teacher prior and no teacher-centred bound. Illegal candidates never gain probability.
        logits = self.head_residual(head,h,feat,context)
        if not bool(torch.isfinite(logits).all()): raise ValueError("nonfinite direct logits")
        return logits.masked_fill(~legal.bool(),float("-inf"))

    def forward(self,obs,head,feat,legal,context=None):
        if not bool(torch.isfinite(obs).all()): raise ValueError("nonfinite observation")
        return self.head_logits(head,self.encode(obs),feat,legal,context)


def build_model(cfg="policy_v2",**kwargs):
    return DirectPolicyNet(load_config(cfg,**kwargs))


def init_untrained(model,seed=20261024,zero_logits=False):
    """Synthetic only, no data: seeded random plumbing model or distinct zero-logit control. Neither is trained."""
    _init_kernel(model,seed,zero_residual=False)
    if zero_logits:
        with torch.no_grad():
            for name in HEAD_NAMES:
                model.heads[name]["w2"].zero_(); model.heads[name]["b2"].zero_()
    return model
