"""Independent, constructed state-machine oracle. Never loads/runs a model.

Token-list 'state' below is a logical fixture, not native KV bytes or a CUDA
qualification. The full-vector reader deliberately does not accept argmax-only
evidence. All guards are ordinary exceptions, including under python -O.
"""
from __future__ import annotations
import copy
import hashlib
import math
import struct
from dataclasses import dataclass


class ContractError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ContractError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def vector(winner, vocab=16, salt=0):
    require(0 <= winner < vocab, "winner outside vocabulary")
    values = [float((i + salt) % 7) / 16 for i in range(vocab)]
    values[winner] = 8.0 + salt / 16
    raw = struct.pack("<" + "f" * vocab, *values)
    return {"dtype": "F32_LE", "shape": [vocab], "bytes_hex": raw.hex(),
            "sha256": sha(raw)}


def read_vector(record, vocab):
    require(isinstance(record, dict), "full vector missing")
    require(record.get("dtype") == "F32_LE" and record.get("shape") == [vocab],
            "vector dtype/shape")
    try:
        raw = bytes.fromhex(record["bytes_hex"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("complete vector bytes missing") from exc
    require(len(raw) == vocab * 4, "truncated/extra vector bytes")
    require(record.get("sha256") == sha(raw), "incorrect vector SHA256")
    values = struct.unpack("<" + "f" * vocab, raw)
    require(all(math.isfinite(x) for x in values), "nonfinite vector")
    return raw, max(range(vocab), key=values.__getitem__)


@dataclass
class Owner:
    identity: str
    vocabulary: int
    generation: int = 0
    poisoned: bool = False
    vectors: list | None = None

    def install(self, vectors, expected_rows):
        require(not self.poisoned, "invalid owner reuse")
        try:
            require(len(vectors) == expected_rows, "incomplete requested output mask")
            for item in vectors:
                read_vector(item, self.vocabulary)
            self.generation += 1
            self.vectors = copy.deepcopy(vectors)
        except Exception:
            self.poisoned = True
            raise

    def consume(self, row, generation):
        require(not self.poisoned, "poisoned owner")
        require(generation == self.generation and self.vectors is not None,
                "stale output owner")
        require(0 <= row < len(self.vectors), "unrequested output row")
        raw, token = read_vector(self.vectors[row], self.vocabulary)
        return token, {"owner": self.identity, "generation": generation,
                       "row": row, "vector_sha256": sha(raw)}


def constructed_request(prompt, initial, cycles, cap=12, eog_ids=(), vocab=16):
    """Execute worker semantics with explicitly fabricated proposals/vectors.

    No fixed external continuation is inserted. Every next seed is the actual
    bonus or correction selected from the prior installed complete vector.
    """
    require(prompt and cap > 0, "empty prompt/cap")
    require(all(isinstance(t, int) and 0 <= t < vocab for t in prompt), "prompt token")
    owner = Owner("constructed-oracle", vocab)
    _, pending = read_vector(initial, vocab)
    target, draft = list(prompt), list(prompt)
    emitted, eog, records = [], [], []

    def commit(token):
        require(0 <= token < vocab, "output outside vocabulary")
        emitted.append(token)
        eog.append(token in eog_ids)
        return eog[-1] or len(emitted) == cap

    done = commit(pending)
    terminal_materialized = False
    for index, case in enumerate(cycles):
        if done:
            break
        k = case["k"]
        require(k in (3, 7), "unsupported logical transaction depth")
        proposals = list(case["proposals"])
        require(len(proposals) == k and all(0 <= t < vocab for t in proposals),
                "proposal width/token")
        seed, base = pending, len(target)
        before = {"target": list(target), "draft": list(draft)}
        target.extend([seed] + proposals)
        # Native baseline generates all k proposals before verification. This
        # fixture does not pretend a lazy-tail generator has native coverage.
        draft = draft[:base] + [seed] + proposals
        untrimmed = {"target": list(target), "draft": list(draft)}
        owner.install(case["vectors"], k + 1)
        generation = owner.generation
        consumed = [owner.consume(i, generation) for i in range(k + 1)]
        decisions = [v[0] for v in consumed]
        accepted, rejected, kind, decision_consumer = 0, False, None, None
        for j in range(k):
            if done:
                break
            if decisions[j] == proposals[j]:
                accepted += 1
                done = commit(proposals[j])
                kind = "accepted"
                terminal_materialized = True
            else:
                rejected, pending, kind = True, decisions[j], "correction"
                decision_consumer = consumed[j][1]
                done = commit(pending)
                terminal_materialized = False
                break
        if accepted == k and not done:
            pending, kind = decisions[k], "bonus"
            decision_consumer = consumed[k][1]
            done = commit(pending)
            terminal_materialized = False
        keep = base + 1 + accepted
        target, draft = target[:keep], draft[:keep]
        records.append({"cycle": index, "k": k, "base": base, "seed": seed,
                        "proposals": proposals, "decisions": decisions,
                        "vectors": copy.deepcopy(case["vectors"]),
                        "requested_mask": [True] * (k + 1),
                        "owner": {"identity": owner.identity, "generation": generation,
                                  "valid": not owner.poisoned},
                        "sampled_rows": [v[1] for v in consumed],
                        "decision_consumer": decision_consumer,
                        "state_before": before, "state_untrimmed": untrimmed,
                        "state_after": {"target": list(target), "draft": list(draft)},
                        "geometry": {"base": base, "input_rows": k + 1,
                                     "requested_rows": k + 1, "keep": keep},
                        "accepted": accepted, "rejected": rejected, "keep": keep,
                        "commit_kind": kind, "pending_after": None if done else pending,
                        "pending_materialized": False if not done else None,
                        "terminal_emitted_materialized": terminal_materialized if done else None,
                        "ids": list(emitted), "eog": list(eog), "done": done})
    require(done, "fixture did not reach its declared terminal condition")
    return {"schema": "heterospec.constructed-request.v1", "native_qualification": False,
            "coverage": "CONSTRUCTED_LOGICAL_FIXTURE", "prompt_ids": list(prompt),
            "initial_vector": initial, "vocabulary": vocab, "cap": cap,
            "eog_ids": list(eog_ids), "cycles": records, "ids": emitted, "eog": eog,
            "stop_reason": "EOG" if eog[-1] else "CAP",
            "final_target": target, "final_draft": draft,
            "terminal_emitted_materialized": terminal_materialized,
            "native_KV_bytes": "NOT_CAPTURED", "native_geometry": "NOT_CAPTURED"}


def compare_requests(reference, candidate):
    """Full byte/vector and logical state comparison, never a native KV check."""
    for key in ("schema", "native_qualification", "coverage", "prompt_ids", "vocabulary",
                "cap", "eog_ids", "ids", "eog", "stop_reason", "final_target", "final_draft",
                "terminal_emitted_materialized", "native_KV_bytes", "native_geometry"):
        require(reference.get(key) == candidate.get(key), "request mismatch: " + key)
    require(len(reference["cycles"]) == len(candidate["cycles"]), "cycle count mismatch")
    vocab = reference["vocabulary"]
    a, _ = read_vector(reference["initial_vector"], vocab)
    b, _ = read_vector(candidate["initial_vector"], vocab)
    require(a == b, "initial vector bytes mismatch")
    for ri, ci in zip(reference["cycles"], candidate["cycles"]):
        require(set(ri) == set(ci), "cycle fields missing")
        require(len(ri["vectors"]) == ri["k"] + 1 and len(ci["vectors"]) == ci["k"] + 1,
                "missing full requested vectors")
        for ra, ca in zip(ri["vectors"], ci["vectors"]):
            rb, _ = read_vector(ra, vocab)
            cb, _ = read_vector(ca, vocab)
            require(rb == cb, "full requested vector mismatch")
        for key in ri.keys() - {"vectors"}:
            require(ri[key] == ci[key], "cycle mismatch: " + key)
    return {"equal": True, "scope": "CONSTRUCTED_LOGICAL_FIXTURE_ONLY",
            "full_vector_pairs": 1 + sum(c["k"] + 1 for c in reference["cycles"]),
            "native_KV_or_geometry_qualified": False}


def main_fixture():
    cases = []
    for k, proposals, decisions in (
            (3, [1, 3, 5], [1, 3, 5, 9]),
            (7, [2, 4, 6, 8, 10, 1, 3], [2, 4, 6, 8, 11, 0, 5, 7]),
            (3, [2, 4, 6], [2, 0, 5, 8])):
        cases.append({"k": k, "proposals": proposals,
                      "vectors": [vector(t, salt=i) for i, t in enumerate(decisions)]})
    return constructed_request([2, 4, 6], vector(7), cases, cap=12)
