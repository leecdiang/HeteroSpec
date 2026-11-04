"""Replay the supplied F32 RN XOR sum tree on the retained actual inputs.

This NumPy probe validates intermediate numerical domains and final half sum
fields only. It makes no assertion about GPU approximate division, quantizer
byte identity, or projection outputs. Original input files are read-only.
"""
import argparse
import base64
import gzip
import json
from pathlib import Path

import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-dir', type=Path, default=Path(__file__).parents[1],
                    help='Directory containing authorized operand-sample.json.gz')
parser.add_argument('--output', type=Path, default=Path(__file__).with_name('xor-sum-domain.json'),
                    help='Destination JSON; defaults beside this script')
args = parser.parse_args()
P = args.input_dir
results = {}
with gzip.open(P / 'operand-sample.json.gz', 'rt') as source:
    samples = json.load(source)
for name, blobs in samples.items():
    raw = base64.b64decode(blobs['input'], validate=True)
    x = np.frombuffer(raw, dtype='<f4').reshape(-1, 32).copy()
    stages = []
    for offset in (16, 8, 4, 2, 1):
        # A simultaneous shuffle/add stage, rounded to F32 after every add.
        x = np.add(x, x[:, np.arange(32) ^ offset], dtype=np.float32)
        bits = x.view(np.uint32)
        zero = (bits & 0x7fffffff) == 0
        subnormal = ((bits & 0x7f800000) == 0) & ~zero
        stages.append({
            'xor': offset,
            'nonfinite': int((~np.isfinite(x)).sum()),
            'subnormal': int(subnormal.sum()),
            'zero_count': int(zero.sum()),
            'min_abs_nonzero': float(np.abs(x[~zero]).min()),
        })
    sums = x[:, 0]
    half_sums = sums.astype(np.float16)
    half_bits = half_sums.view(np.uint16)
    half_zero = (half_bits & 0x7fff) == 0
    half_subnormal = ((half_bits & 0x7c00) == 0) & ~half_zero
    results[name] = {
        'fp32_xor_sum_stages': stages,
        'sum_lanes_identical': bool((x == sums[:, None]).all()),
        'half_sum_nonfinite': int((~np.isfinite(half_sums)).sum()),
        'half_sum_zero': int(half_zero.sum()),
        'half_sum_subnormal': int(half_subnormal.sum()),
        'min_abs_nonzero_half_sum': float(np.abs(half_sums[~half_zero]).min()),
        'max_abs_half_sum': float(np.abs(half_sums).max()),
    }
output = args.output
serialized = json.dumps(results, indent=2) + '\n'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(serialized)
print(serialized, end='')
