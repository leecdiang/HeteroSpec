#!/usr/bin/env python3
"""Synthetic tests for the preregistered generated-token comparison contract."""

def normalize_generated(tokens, eos_ids, cap=128):
    out = []
    for token in tokens:
        if len(out) == cap:
            break
        out.append(token)
        if token in eos_ids:
            break
    return out

def main():
    eos = {2}
    assert normalize_generated([10, 11, 12], eos) == [10, 11, 12]
    assert normalize_generated([10, 2, 99], eos) == [10, 2]
    assert normalize_generated(list(range(200)), eos_ids=set()) == list(range(128))
    baseline = normalize_generated([41, 42, 43], eos)
    speculative = normalize_generated([41, 42, 43], eos)
    assert baseline == speculative
    mismatch = normalize_generated([41, 99, 43], eos)
    first = next(i for i, pair in enumerate(zip(baseline, mismatch)) if pair[0] != pair[1])
    assert (first, baseline[first], mismatch[first]) == (1, 42, 99)
    print("normalization_mock_tests=PASS")

if __name__ == "__main__":
    main()
