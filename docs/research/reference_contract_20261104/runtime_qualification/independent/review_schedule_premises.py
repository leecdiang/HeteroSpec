#!/usr/bin/env python3
"""Independent finite schedule tests with a stronger Python toy attention.

The 200 schedule cases use bounded integer inputs with Python binary64 padded
QK, softmax, and PV, not native HeteroSpec attention. Scalar and batched schedules
share the same toy functions. A separate unsafe alias fixture deliberately omits
admission; the reviewed model itself must reject aliases without mutation.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import sys

EXPECTED_MODEL_SHA256 = 'bf70caf1f72c6e1fd16ee504d3e6dc1f776d9dfbc0cbe66fd82c304980508ecb'


def load_model(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_MODEL_SHA256:
        raise SystemExit('Model differs from reviewed version: ' + digest)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('independent_schedule_model', path)
    model = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = model
    spec.loader.exec_module(model)
    return model, digest


def check(m):
    def binding(state):
        return m.Binding(state.epoch, state.allocation, state.count,
                         tuple((name, True) for name in m.REQUIRED_STAGES))

    state = m.State.empty()
    state.k[1] = state.k[0]
    state.v[1] = state.v[0]
    before = state.observation()
    assert m.candidate_append(state, (1, 2), binding(state))[0] == 'rejected'
    assert state.observation() == before

    # This deliberately unsafe fixture is NOT the reviewed candidate function.
    reference = deepcopy(state)
    unsafe = deepcopy(state)
    tokens = (1, 2)
    m.reference_append(reference, tokens)
    x = [float(token) for token in tokens]
    for layer in range(len(unsafe.k)):
        projected = [m.project(value, layer) for value in x]
        next_x = []
        for pos, (k, v) in enumerate(projected):
            unsafe.k[layer][pos] = k
            unsafe.v[layer][pos] = v
            next_x.append(m.attend(unsafe, layer, pos, k))
        x = next_x
    unsafe.count = len(tokens)
    unsafe.history = tokens
    unsafe.outputs = tuple(x)
    assert unsafe.observation() != reference.observation()

    def padded_attention(state, layer, pos, query):
        scores = [query*state.k[layer][i] + (0. if i <= pos else -math.inf)
                  for i in range(state.capacity)]
        maximum = max(scores)
        probabilities = [math.exp(value-maximum) for value in scores]
        denominator = sum(probabilities)
        return sum((probabilities[i]/denominator)*state.v[layer][i]
                   for i in range(state.capacity))

    original_attention = m.attend
    m.attend = padded_attention
    try:
        rng = random.Random(2)
        for _ in range(200):
            capacity = rng.randint(2, 25)
            width = rng.randint(1, min(capacity, 8))
            layers = rng.randint(1, 4)
            tokens = tuple(rng.randint(-4, 4) for _ in range(width))
            reference = m.State.empty(capacity, layers)
            candidate = deepcopy(reference)
            m.reference_append(reference, tokens)
            assert m.candidate_append(candidate, tokens, binding(candidate))[0] == 'committed'
            assert reference.observation() == candidate.observation()

        # Independent nonfinite counterexample, not part of bounded-input suite.
        state = m.State.empty(2, 1)
        state.k[0][0] = state.v[0][0] = 1.
        assert padded_attention(state, 0, 0, 1.) == 1.
        state.k[0][1] = float('inf')
        assert math.isnan(padded_attention(state, 0, 0, 1.))
    finally:
        m.attend = original_attention

    return {
        'current_shared_layer_alias_rejected_without_mutation': True,
        'explicit_unsafe_shared_alias_fixture_diverges': True,
        'bounded_integer_padded_qk_softmax_pv_schedule_cases': 200,
        'separate_future_K_inf_mask_counterexample': True,
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
