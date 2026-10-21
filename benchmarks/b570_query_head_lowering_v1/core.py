"""Pure descriptors, provenance helpers and structural costs. No backend is loaded."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path

STUDY = 'b570-query-head-lowering-v1'
MODES = ('MQ', 'PQ', 'QB4', 'QH_C', 'QH_D', 'REPEAT4')
PIN = '9fafc4ba49119f1c52e1606d295bd0b9a55a06d1'
VK = 'a9bcbe815d0fc1b9a7914fceb55b7275750169ec58dc8c4a09691ea0ea12f92c'

def need(ok, message):
    if not ok:
        raise ValueError(message)

def encode(x):
    return (json.dumps(x, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(',', ':'))+'\n').encode()

def sha(x):
    return hashlib.sha256(encode(x)).hexdigest()

def read(path):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            need(k not in out, 'duplicate JSON key')
            out[k] = v
        return out
    def bad(x):
        raise ValueError('nonfinite JSON')
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),
                      object_pairs_hook=unique, parse_constant=bad)

def write_new(path, x):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(encode(x))

def hash_ok(x):
    return type(x) is str and len(x)==64 and all(c in '0123456789abcdef' for c in x)

@dataclass(frozen=True)
class Geometry:
    d: int
    dv: int
    q: int
    n: int
    h: int
    hk: int
    storage: str = 'permuted'

    def check(self):
        for name in ('d','dv','q','n','h','hk'):
            need(type(getattr(self,name)) is int, 'integer descriptor required')
        need(1 <= self.q <= 4 and 1 <= self.d <= 256 and 1 <= self.dv <= 256, 'feature/query domain')
        need(self.q <= self.n <= 4096 and 1 <= self.hk <= self.h <= 128 and self.h % self.hk == 0, 'extent/GQA domain')
        need(self.storage in ('compact','permuted'), 'unsupported storage')
        return self

    def dict(self):
        return asdict(self.check())

    def q_strides(self):
        self.check()
        return (4,4*self.d,4*self.d*self.q,4*self.d*self.q*self.h) if self.storage=='compact' else (
            4,4*self.d*self.h,4*self.d,4*self.d*self.h*self.q)


def lower(g: Geometry, mode: str, backend=VK):
    g.check(); need(mode in MODES, 'unknown representation')
    common = g.q==1
    actual = 'MQ' if common else mode
    if actual in ('QH_C','QH_D'):
        qshape=[g.d,1,g.h*g.q,1]
        mshape=[g.n,1,g.q if actual=='QH_C' else g.h*g.q,1]
        source_batch3=(1,1)
    elif actual in ('QB4','REPEAT4'):
        qshape=[g.d,1,g.h,g.q]; mshape=[g.n,1,1,g.q]
        source_batch3=(g.q if actual=='REPEAT4' else 1,g.q)
    else:
        qshape=[g.d,g.q if actual=='MQ' else 1,g.h,1]
        mshape=[g.n,g.q if actual=='MQ' else 1,1,1]
        source_batch3=(1,1)
    condition = source_batch3[0]==source_batch3[1] if backend==VK else None
    return dict(geometry=g.dict(),requested_mode=mode,effective_mode=actual,
        q_shape=qshape,mask_shape=mshape,source_batch3=list(source_batch3),
        common_original_path=common,kv_copy=actual=='REPEAT4',
        q_pack_required=actual in ('QH_C','QH_D') and g.storage!='compact',
        batch3_necessary_condition=condition,
        full_backend_support=False if condition is False else None,
        actual_placement='UNKNOWN',numerical_qualification='NOT_TESTED',
        scope='symbolic descriptor only; satisfying one predicate is not admission')


def allocation_model(g: Geometry, mode: str):
    """Logical extra destinations, not peak allocator use or measured DRAM traffic."""
    x=lower(g,mode); a=x['effective_mode']
    qpack=4*g.d*g.q*g.h if x['q_pack_required'] else 0
    mask=4*g.n*g.h*g.q if a=='QH_D' else 0
    kv=2*g.n*g.hk*(g.d+g.dv)*g.q if a=='REPEAT4' else 0
    return dict(q_pack_destination_bytes=qpack,expanded_mask_destination_bytes=mask,
        repeated_kv_destination_bytes=kv,extra_destination_bytes=qpack+mask+kv,
        attention_chains=g.q if a=='PQ' else 1,
        assumed_copy_read_plus_write_bytes=2*(qpack+mask+kv),
        scope='STRUCTURAL_ESTIMATE_NOT_PEAK_MEMORY_DRAM_OR_LATENCY',
        shared_kv_can_also_be_reused_by_PQ=True,
        unmodeled=['output_contiguous_recovery','graph_metadata','allocator_liveness',
                   'backend_workspace','broadcast_ports','caches','launches'])
