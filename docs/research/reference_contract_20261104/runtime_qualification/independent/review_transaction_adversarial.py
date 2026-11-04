#!/usr/bin/env python3
"""Independent finite tests of the supplied Python transaction design model.

Not native attention, CUDA, IEEE instruction semantics, or a formal proof.
Projection equality, deterministic scalar arithmetic, and immediate completion
are imported from the toy model. Observer tests intentionally violate the
model's no-observer premise to demonstrate why native reader exclusion is needed.
"""
import argparse
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random
import sys

EXPECTED_MODEL_SHA256 = 'bf70caf1f72c6e1fd16ee504d3e6dc1f776d9dfbc0cbe66fd82c304980508ecb'


def load_model(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_MODEL_SHA256:
        raise SystemExit('Model differs from reviewed version: ' + digest)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('independent_transaction_model', path)
    model = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = model
    spec.loader.exec_module(model)
    return model, digest


def check(model):
    m = model
    valid = tuple((name, True) for name in m.REQUIRED_STAGES)

    def binding(state, stages=valid):
        return m.Binding(state.epoch, state.allocation, state.count, stages)

    baseline_output = io.StringIO()
    with redirect_stdout(baseline_output):
        m.main()
    baseline = json.loads(baseline_output.getvalue())
    expected_baseline = {'successful_schedule_equivalence': 54, 'abort_points': 648,
                         'guard_rejections': 648, 'counterexamples': 5}
    assert baseline['passed'] == expected_baseline

    for stages in ((), valid[:1], valid[::-1], valid + valid[:1]):
        state = m.State.empty()
        before = state.observation()
        assert m.candidate_append(state, (3,), binding(state, stages))[0] == 'rejected'
        assert state.observation() == before

    # Deterministic, premise-violating observer between publication assignments.
    state = m.State.empty()
    before = state.observation()
    expected = deepcopy(state)
    m.reference_append(expected, (3,))
    after = expected.observation()
    observed = []

    def trace(frame, event, arg):
        if event == 'line' and frame.f_code is m.candidate_append.__code__:
            if state.count == 1 and state.history == ():
                observed.append(state.observation())
        return trace

    previous_trace = sys.gettrace()
    sys.settrace(trace)
    try:
        assert m.candidate_append(state, (3,), binding(state))[0] == 'committed'
    finally:
        sys.settrace(previous_trace)
    assert any(value != before and value != after for value in observed)

    # Old immutable metadata still points to mutable physical KV storage.
    state = m.State.empty(capacity=2, layers=1)
    state.count = 1
    state.k[0][0] = state.v[0][0] = 1.
    old_descriptor = (state.count, state.k, state.v)
    assert m.attend(state, 0, 0, 0.) == 1.
    state.v[0][1] = float('inf')
    assert old_descriptor[2][0][1] == float('inf')
    import math
    assert math.isnan(m.attend(state, 0, 0, 0.))

    # Abstract element-address layout, not native F16 memset execution.
    capacity, dimensions, prefix, width = 7, 3, 2, 2
    original = [100+d*capacity+i if i < prefix else 0
                for d in range(dimensions) for i in range(capacity)]
    written = original[:]
    for d in range(dimensions):
        for i in range(prefix, prefix+width):
            written[d*capacity+i] = 77
    exact = written[:]
    for d in range(dimensions):
        exact[d*capacity+prefix:d*capacity+prefix+width] = [0]*width
    broad = written[:]
    end = (dimensions-1)*capacity+prefix+width
    broad[prefix:end] = [0]*(end-prefix)
    assert exact == original
    assert broad != original

    # Special-value inputs are abstract Python scalars, not native token IDs.
    values = [0., -0., 1., -1., float('inf'), float('-inf'), float('nan'),
              5e-324, 1e308, -1e308]
    rng = random.Random(6)
    for _ in range(500):
        capacity = rng.randint(1, 20)
        width = rng.randint(1, capacity)
        layers = rng.randint(1, 5)
        tokens = tuple(rng.choice(values) for _ in range(width))
        reference = m.State.empty(capacity, layers)
        candidate = deepcopy(reference)
        m.reference_append(reference, tokens)
        assert m.candidate_append(candidate, tokens, binding(candidate))[0] == 'committed'
        assert reference.count == candidate.count
        assert m.bits(reference.history) == m.bits(candidate.history)
        assert m.bits(reference.outputs) == m.bits(candidate.outputs)
        assert [m.bits(row) for row in reference.k] == [m.bits(row) for row in candidate.k]
        assert [m.bits(row) for row in reference.v] == [m.bits(row) for row in candidate.v]

    for cut in range(1, 19):
        old = m.State.empty()
        m.reference_append(old, (4, -5))
        state = deepcopy(old)
        assert m.candidate_append(state, (1, 2, 3), binding(state), cut)[0] == 'aborted'
        expected = deepcopy(old)
        m.reference_append(expected, (7, -2))
        assert m.candidate_append(state, (7, -2), binding(state))[0] == 'committed'
        assert state.observation() == expected.observation()

    return {
        'baseline_model': baseline['passed'],
        'manifest_rejection_regressions': 4,
        'scalar_toy_special_value_schedule_cases': 500,
        'abort_then_next_append_cases': 18,
        'premise_violating_partial_publication_observed': True,
        'old_descriptor_observes_tentative_free_bytes': True,
        'abstract_exact_transposed_clear_restores': True,
        'abstract_bounding_clear_corrupts_prefix': True,
        'native_runtime_tested': False,
        'gpu_tested': False,
        'formal_proof': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path,
                        default=Path(__file__).resolve().parent.parent/'check_transaction_model.py')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    model, digest = load_model(args.model)
    result = {'model_sha256': digest, 'scope': __doc__, 'results': check(model)}
    rendered = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered, encoding='utf-8')
    print(rendered, end='')


if __name__ == '__main__':
    main()
