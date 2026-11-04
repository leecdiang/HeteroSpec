"""Conservative state admission and checkpoint transactions.

This is a single-owner CPU protocol with an explicit native adapter boundary.
Identity/evidence metadata is trusted configuration, not a proof or signature.
No serialization load can manufacture a clean state: snapshots are registered
by the owner after a separate full-state/reference check. Thread safety,
partial checkpoints, sliding windows and multi-stream state are not supported.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Callable, Protocol

class StateError(RuntimeError):
    pass

class Trust(Enum):
    CLEAN='clean'
    UNKNOWN='unknown'
    TAINTED='tainted'

@dataclass(frozen=True)
class Deployment:
    backend: str
    device: str
    build: str
    runtime: str
    model: str
    reference: str
    layout: str
    def __post_init__(self):
        if any(type(x) is not str or not x for x in self.__dict__.values()):
            raise ValueError('complete deployment identity required')

@dataclass(frozen=True)
class Capsule:
    deployment: Deployment
    recipe: str
    tokens: tuple[int,...]
    positions: tuple[int,...]
    pending: tuple[int,...]
    kv: bytes
    initial_logits: bytes
    def __post_init__(self):
        if not self.recipe or type(self.recipe) is not str:
            raise ValueError('recipe required')
        if type(self.tokens) is not tuple or type(self.positions) is not tuple or type(self.pending) is not tuple:
            raise ValueError('immutable token/position tuples required')
        if len(self.tokens)!=len(self.positions): raise ValueError('token/position mismatch')
        for seq in (self.tokens,self.positions,self.pending):
            if any(type(x) is not int or x<0 or x>(1<<63)-1 for x in seq):
                raise ValueError('invalid token/position')
        if self.positions and self.positions!=tuple(range(self.positions[0],self.positions[0]+len(self.positions))):
            raise ValueError('only contiguous single-stream positions supported')
        if type(self.kv) is not bytes or type(self.initial_logits) is not bytes:
            raise ValueError('owned immutable bytes required')
        if not self.initial_logits or len(self.initial_logits)%4:
            raise ValueError('complete binary32 initial logits required')
    def digest(self):
        # Index/integrity aid, never the admission authority. Length-prefix avoids
        # ambiguities; full dataclass equality is checked after every lookup.
        meta=json.dumps((self.deployment.__dict__,self.recipe,self.tokens,self.positions,self.pending),
                        sort_keys=True,separators=(',',':')).encode()
        h=hashlib.sha256()
        for part in (meta,self.kv,self.initial_logits):
            h.update(len(part).to_bytes(8,'big')); h.update(part)
        return h.hexdigest()

@dataclass(frozen=True)
class Verification:
    evidence_id: str
    full_vectors: bool
    committed_state: bool
    token_positions: bool
    # This receipt is supplied by a trusted verifier, not inferred from a hash.
    def valid(self):
        return bool(self.evidence_id and self.full_vectors and self.committed_state and self.token_positions)

class Adapter(Protocol):
    def export(self) -> Capsule: ...
    def import_full(self, capsule: Capsule) -> None: ...
    def synchronize(self) -> None: ...

@dataclass(frozen=True)
class Checkpoint:
    capsule: Capsule
    verification: Verification
    generation: int

class StateOwner:
    """Own one native context and invalidate admission before mutation.

    Import must restore KV, independent initial logits, pending tokens and
    positions. The adapter must export those exact fields for readback. An
    adapter that only wraps llama_state_seq_set_data is insufficient.
    """
    def __init__(self,adapter: Adapter,deployment: Deployment):
        self.adapter=adapter
        self.deployment=deployment
        self.trust=Trust.UNKNOWN
        self.generation=0
        self._current: Capsule|None=None
        self._checkpoint: Checkpoint|None=None
        self._busy=False
    @property
    def current(self): return self._current
    def _export(self):
        self.adapter.synchronize()
        value=self.adapter.export()
        if not isinstance(value,Capsule) or value.deployment!=self.deployment:
            raise StateError('native deployment mismatch')
        return value
    def qualify(self,verify: Callable[[Capsule],Verification]):
        if self._busy: raise StateError('reentrant owner operation')
        self._busy=True
        committed=False
        self.trust=Trust.TAINTED
        self.generation+=1
        try:
            capsule=self._export()
            receipt=verify(capsule)
            if not isinstance(receipt,Verification) or not receipt.valid():
                raise StateError('full state/reference qualification failed')
            self._current=capsule
            self._checkpoint=Checkpoint(capsule,receipt,self.generation)
            self.trust=Trust.CLEAN
            committed=True
            return self._checkpoint
        finally:
            if not committed: self.trust=Trust.TAINTED
            self._busy=False
    def admit(self,*,deployment: Deployment,recipe: str,tokens: tuple[int,...],positions: tuple[int,...]):
        c=self._current
        return (not self._busy and self.trust is Trust.CLEAN and c is not None and
                deployment==self.deployment and c.recipe==recipe and c.tokens==tokens and c.positions==positions)
    def _invalidate(self):
        self.trust=Trust.TAINTED
        self.generation+=1
    def invalidate(self):
        # Policy changes, trimming and graph rebuilds must never clear this bit.
        if self._busy: raise StateError('reentrant owner invalidation')
        self._invalidate()
    def restore_checkpoint(self):
        if self._busy: raise StateError('reentrant owner operation')
        cp=self._checkpoint
        if cp is None or not cp.verification.valid(): raise StateError('no verified checkpoint')
        self._busy=True
        committed=False
        self.trust=Trust.TAINTED
        self.generation+=1
        try:
            self.adapter.import_full(cp.capsule)
            restored=self._export()
            if restored!=cp.capsule: raise StateError('full checkpoint readback mismatch')
            self._current=restored
            self.trust=Trust.CLEAN
            committed=True
            return restored
        finally:
            if not committed: self.trust=Trust.TAINTED
            self._busy=False
    def execute(self,operation: Callable[[],bool],verify: Callable[[Capsule],Verification],*,
                expected_generation: int,restore_on_failure: bool=True):
        if self._busy or self.trust is not Trust.CLEAN or expected_generation!=self.generation:
            raise StateError('stale/untrusted execution admission')
        self._busy=True
        committed=False
        self._invalidate() # Includes export failure, decode failure and late graph rejection.
        error=None
        try:
            if self._export()!=self._current:
                raise StateError('native state changed outside owner')
            if operation() is not True:
                raise StateError('native operation did not report explicit success')
            candidate=self._export()
            receipt=verify(candidate)
            if not isinstance(receipt,Verification) or not receipt.valid():
                raise StateError('candidate failed full-state verification')
            self._current=candidate
            self._checkpoint=Checkpoint(candidate,receipt,self.generation)
            self.trust=Trust.CLEAN
            committed=True
            return candidate
        except BaseException as exc:
            error=exc
        finally:
            if not committed: self.trust=Trust.TAINTED
            self._busy=False
        if restore_on_failure:
            try: self.restore_checkpoint()
            except BaseException as restoration:
                raise StateError('execution and checkpoint restoration failed; context is tainted') from restoration
        raise error
    def restore_cached_checkpoint(self,checkpoint: Checkpoint,identity: 'CacheIdentity'):
        """Import a trusted, already-qualified cache hit with full readback.

        This does not re-prove the receipt or infer cross-recipe compatibility.
        A failed import leaves this owner tainted and preserves its old recovery
        checkpoint; only successful readback publishes the new current state.
        """
        if self._busy: raise StateError('reentrant owner operation')
        if (not isinstance(checkpoint,Checkpoint) or not checkpoint.verification.valid() or
                not isinstance(identity,CacheIdentity) or identity.deployment!=self.deployment or
                CacheIdentity.from_capsule(checkpoint.capsule)!=identity):
            raise StateError('cache admission identity or qualification mismatch')
        self._busy=True
        committed=False
        self._invalidate()
        try:
            self.adapter.import_full(checkpoint.capsule)
            restored=self._export()
            if restored!=checkpoint.capsule: raise StateError('cached checkpoint readback mismatch')
            self._current=restored
            self._checkpoint=Checkpoint(restored,checkpoint.verification,self.generation)
            self.trust=Trust.CLEAN
            committed=True
            return restored
        finally:
            if not committed: self.trust=Trust.TAINTED
            self._busy=False
    def scalar_fallback(self,operation,verify):
        if self.trust is not Trust.CLEAN: self.restore_checkpoint()
        # execute checks full native state under the same reentrancy guard.
        return self.execute(operation,verify,expected_generation=self.generation)

class ExactRecipeCache:
    """Conservative immutable checkpoint cache; not a serving scheduler.

    Cross-recipe compatibility is deliberately NOT inferred. Byte-identical
    serialization and metadata are checked, but only a verifier-issued receipt
    grants the original checkpoint's clean status.
    """
    def __init__(self): self._items: dict[str,list[Checkpoint]]={}
    def put(self,checkpoint: Checkpoint):
        if not isinstance(checkpoint,Checkpoint) or not checkpoint.verification.valid():
            raise StateError('verified checkpoint required')
        key=checkpoint.capsule.digest()
        bucket=self._items.setdefault(key,[])
        if not any(x.capsule==checkpoint.capsule for x in bucket): bucket.append(checkpoint)
        return key
    def get(self,key: str,expected: Capsule):
        for cp in self._items.get(key,()):
            if cp.capsule==expected: return cp
        return None

@dataclass(frozen=True)
class CacheIdentity:
    """Lookup identity known BEFORE producing KV; no state bytes are required.

    This is exact-recipe isolation, not a claim of minimal numerical provenance.
    The deployment/recipe must include every producer dimension the host needs.
    """
    deployment: Deployment
    recipe: str
    tokens: tuple[int,...]
    positions: tuple[int,...]
    pending: tuple[int,...]
    def __post_init__(self):
        if not isinstance(self.deployment,Deployment) or type(self.recipe) is not str or not self.recipe:
            raise ValueError('complete producer identity required')
        for seq in (self.tokens,self.positions,self.pending):
            if type(seq) is not tuple or any(type(x) is not int or x<0 or x>(1<<63)-1 for x in seq):
                raise ValueError('immutable valid token/position tuples required')
        if len(self.tokens)!=len(self.positions): raise ValueError('token/position mismatch')
        if self.positions and self.positions!=tuple(range(self.positions[0],self.positions[0]+len(self.positions))):
            raise ValueError('only contiguous single-stream positions supported')
    @classmethod
    def from_capsule(cls,capsule: Capsule):
        return cls(capsule.deployment,capsule.recipe,capsule.tokens,capsule.positions,capsule.pending)
    def digest(self):
        payload=json.dumps((self.deployment.__dict__,self.recipe,self.tokens,self.positions,self.pending),
                           sort_keys=True,separators=(',',':')).encode()
        return hashlib.sha256(payload).hexdigest()

class PrefixCheckpointCache:
    """Single-owner identity lookup, separate from stored-state integrity.

    Unlike ExactRecipeCache, lookup does not require expected KV/logits bytes.
    Only previously qualified immutable capsules can be stored. A conflicting
    capsule for the exact same identity quarantines that identity: neither old
    nor new value is silently chosen. This is not eviction or a serving scheduler.
    """
    def __init__(self):
        self._items: dict[str,list[tuple[CacheIdentity,Checkpoint,str]]]={}
        self._quarantined: set[CacheIdentity]=set()
    def put(self,checkpoint: Checkpoint):
        if not isinstance(checkpoint,Checkpoint) or not checkpoint.verification.valid():
            raise StateError('verified checkpoint required')
        identity=CacheIdentity.from_capsule(checkpoint.capsule)
        if identity in self._quarantined: raise StateError('producer identity quarantined')
        key=identity.digest()
        bucket=self._items.setdefault(key,[])
        for old_identity,old,integrity in bucket:
            if old_identity==identity:
                if old.capsule!=checkpoint.capsule:
                    self._quarantined.add(identity)
                    raise StateError('same producer identity yielded conflicting state')
                return key
        bucket.append((identity,checkpoint,checkpoint.capsule.digest()))
        return key
    def get(self,identity: CacheIdentity):
        if not isinstance(identity,CacheIdentity): raise StateError('lookup identity required')
        if identity in self._quarantined: return None
        for stored,checkpoint,integrity in self._items.get(identity.digest(),()):
            # Hashes locate candidates only. Full identity is the lookup check;
            # stored state integrity is independent of expected state bytes.
            if stored==identity:
                if not checkpoint.verification.valid() or checkpoint.capsule.digest()!=integrity:
                    self._quarantined.add(identity)
                    raise StateError('stored checkpoint integrity failed')
                return checkpoint
        return None
