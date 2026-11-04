#!/usr/bin/env python3
"""Bounded executable design model, not a verifier of HeteroSpec/CUDA code.

Assumes each packed projection is exactly the same function as its scalar
reference. Checks schedule/interleaving, whole-byte rollback and simple guards.
The arithmetic is Python binary64, not a model of CUDA floating-point.
Observers are absent during a transaction; atomic publication and completion
are assumed, not implemented or tested. Whole-array checks are ghost assertions,
not proposed hot-path scanning. The stage manifest is schematic, not native.
"""
from copy import deepcopy
from dataclasses import dataclass
import json
import math
import struct


def bits(values):
    return b''.join(struct.pack('!d', x) for x in values)

@dataclass
class State:
    capacity: int
    k: list
    v: list
    count: int = 0
    history: tuple = ()
    outputs: tuple = ()
    epoch: int = 0
    allocation: int = 1
    taint: bool = False

    @classmethod
    def empty(cls, capacity=8, layers=2):
        return cls(capacity, [[0.] * capacity for _ in range(layers)],
                   [[0.] * capacity for _ in range(layers)])

    def observation(self):
        # Epoch is admission metadata, not the reference numerical state.
        return (self.count, self.history, bits(self.outputs),
                tuple(bits(x) for x in self.k), tuple(bits(x) for x in self.v))

    def free_is_zero(self):
        return all(bits(row[self.count:]) == bytes(8 * (self.capacity-self.count))
                   for group in (self.k, self.v) for row in group)


def project(x, layer):
    return x * (layer + 1) + 0.25, x + (layer + 1) * 0.5


def attend(state, layer, pos, q):
    # Deliberately execute masked terms: dirty/Inf future slots can matter.
    acc = 0.
    for i in range(state.capacity):
        mask = 1. if i <= pos else 0.
        acc = acc + mask * state.v[layer][i]
    return q + acc


def reference_append(state, tokens):
    for token in tokens:
        pos = state.count
        x = float(token)
        for layer in range(len(state.k)):
            k, v = project(x, layer)
            state.k[layer][pos] = k
            state.v[layer][pos] = v
            x = attend(state, layer, pos, k)
        state.count += 1
        state.history += (token,)
        state.outputs += (x,)
    state.epoch += 1


REQUIRED_STAGES = ('projection', 'attention', 'output')


@dataclass(frozen=True)
class Binding:
    epoch: int
    allocation: int
    count: int
    splits: tuple


def candidate_append(state, tokens, binding, fail_after=None):
    initial = state.observation()
    storage = state.k + state.v
    if (state.taint or len({id(row) for row in storage}) != len(storage) or
        binding.epoch != state.epoch or
        binding.allocation != state.allocation or binding.count != state.count or
        tuple(name for name, _ in binding.splits) != REQUIRED_STAGES or
        not all(supported for _, supported in binding.splits) or not state.free_is_zero() or
        not 0 < len(tokens) <= state.capacity-state.count):
        assert state.observation() == initial
        return 'rejected', 0
    first = state.count
    state.taint = True
    state.epoch += 1
    completed_ops = 0
    x = [float(token) for token in tokens]

    def step():
        nonlocal completed_ops
        completed_ops += 1
        if fail_after == completed_ops:
            raise RuntimeError('nonfatal, all submitted work known completed')

    try:
        for layer in range(len(state.k)):
            # Parallel projection equivalence is an explicit imported assumption.
            projected = [project(value, layer) for value in x]
            nxt = []
            for j, (k, v) in enumerate(projected):
                pos = first+j
                state.k[layer][pos] = k
                step()
                state.v[layer][pos] = v
                step()
                nxt.append(attend(state, layer, pos, k))
                step()
            x = nxt
        # One publication point after every operation and output copy is done.
        state.count += len(tokens)
        state.history += tuple(tokens)
        state.outputs += tuple(x)
        state.taint = False
        assert state.free_is_zero()
        return 'committed', completed_ops
    except RuntimeError:
        # Model has no in-flight operations. Real implementation must drain.
        for group in (state.k, state.v):
            for row in group:
                row[first:first+len(tokens)] = [0.] * len(tokens)
        state.taint = False
        assert state.observation() == initial
        assert state.free_is_zero()
        return 'aborted', completed_ops


def main():
    checks = {'successful_schedule_equivalence': 0, 'abort_points': 0,
              'guard_rejections': 0, 'counterexamples': 0}
    for prefix in range(6):
        for width in range(1, min(3, 8-prefix)+1):
            for suffix in ((1, -2, 3)[:width], (0, 0, 0)[:width], (-7, 4, 2)[:width]):
                old = State.empty()
                if prefix:
                    reference_append(old, tuple(range(1, prefix+1)))
                expected = deepcopy(old)
                reference_append(expected, suffix)
                current = deepcopy(old)
                binding = Binding(old.epoch, old.allocation, old.count, tuple((name, True) for name in REQUIRED_STAGES))
                status, nops = candidate_append(current, suffix, binding)
                assert status == 'committed'
                assert current.observation() == expected.observation()
                checks['successful_schedule_equivalence'] += 1
                for cut in range(1, nops+1):
                    current = deepcopy(old)
                    assert candidate_append(current, suffix, binding, cut)[0] == 'aborted'
                    checks['abort_points'] += 1
                valid = binding.splits
                for bad in (Binding(old.epoch+1, old.allocation, old.count, valid),
                            Binding(old.epoch, old.allocation+1, old.count, valid),
                            Binding(old.epoch, old.allocation, old.count+1, valid),
                            Binding(old.epoch, old.allocation, old.count,
                                    ((REQUIRED_STAGES[0], True), (REQUIRED_STAGES[1], False), (REQUIRED_STAGES[2], True))),
                            Binding(old.epoch, old.allocation, old.count, ()),
                            Binding(old.epoch, old.allocation, old.count, valid[:-1]),
                            Binding(old.epoch, old.allocation, old.count, valid[::-1])):
                    current = deepcopy(old)
                    assert candidate_append(current, suffix, bad)[0] == 'rejected'
                    checks['guard_rejections'] += 1
                for mutation in range(5):
                    current = deepcopy(old)
                    if mutation == 0:
                        current.k[1] = current.k[0]
                    elif mutation == 1:
                        current.v[1] = current.v[0]
                    elif mutation == 2:
                        current.v[0] = current.k[0]
                    elif mutation == 3:
                        current.taint = True
                    else:
                        current.k[0][-1] = 1.
                    before_reject = current.observation()
                    assert candidate_append(current, suffix, binding)[0] == 'rejected'
                    assert current.observation() == before_reject
                    checks['guard_rejections'] += 1
    # Masking does not make future bytes observationally irrelevant.
    clean = State.empty(capacity=2, layers=1)
    clean.v[0][0] = 1.
    r = attend(clean, 0, 0, 0.)
    clean.v[0][1] = float('inf')
    a = attend(clean, 0, 0, 0.)
    assert r == 1. and math.isnan(a)
    checks['counterexamples'] += 1
    # Future K also matters if QK is formed before adding a -Inf mask.
    ref_score = 1. * 0. + float('-inf')
    dirty_score = 1. * float('inf') + float('-inf')
    assert ref_score == float('-inf') and math.isnan(dirty_score)
    checks['counterexamples'] += 1
    # A late device store after rollback breaks the zero-free invariant.
    late = State.empty(capacity=2, layers=1)
    late.v[0][1] = 0.  # premature rollback
    late.v[0][1] = 7.  # simulated delayed store
    assert not late.free_is_zero()
    checks['counterexamples'] += 1
    # SET_ROWS casts its flattened logical index to uint32_t.
    i = 2**32
    assert i & 0xffffffff == 0 and i != 0
    checks['counterexamples'] += 1
    # A per-split guard can reject after an earlier split's write.
    dirty = State.empty(capacity=2, layers=1)
    old = dirty.observation()
    dirty.k[0][0] = 4.
    later_split_supported = False
    assert not later_split_supported and dirty.observation() != old
    checks['counterexamples'] += 1
    print(json.dumps({'scope': __doc__, 'passed': checks,
                      'native_runtime_tested': False, 'gpu_tested': False,
                      'formal_proof': False}, indent=2))

if __name__ == '__main__':
    main()
