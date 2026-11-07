"""Read-only paired diagnostics: explicit row ownership, never guess an axis."""
from __future__ import annotations
import argparse
import json
from array import array
from pathlib import Path
import struct
from common import need, read, sha, write


def logical_row(payload, meta, row, axis):
    need(meta['type'] in ('f32', 'f16'), 'unimplemented trace dtype')
    n, strides = meta['ne'], meta['nb'];size = 4 if meta['type'] == 'f32' else 2
    need(len(n) == len(strides) == 4 and 0 <= axis < 4 and 0 <= row < n[axis], 'explicit row mapping required')
    need(all(type(v) is int and v > 0 for v in n) and all(type(v) is int and v >= 0 for v in strides), 'tensor metadata')
    data = Path(payload).read_bytes();need(len(data) == meta['bytes'], 'trace payload size')
    import itertools
    result = bytearray()
    for indices in itertools.product(*[range(d) if a != axis else [row] for a, d in enumerate(n)]):
        offset = sum(i * s for i, s in zip(indices, strides))
        need(offset >= 0 and offset + size <= len(data), 'stride outside payload')
        result += data[offset:offset + size]
    return bytes(result)


def compare(a_path, b_path, a_meta, b_meta, a_row, b_row, axis):
    a, b = read(a_meta), read(b_meta)
    need(a['type'] == b['type'], 'dtype mismatch')
    need([n for i, n in enumerate(a['ne']) if i != axis] == [n for i, n in enumerate(b['ne']) if i != axis], 'non-query axes differ')
    av = logical_row(a_path, a, a_row, axis);bv = logical_row(b_path, b, b_row, axis)
    size = 4 if a['type'] == 'f32' else 2;fmt = '<f' if size == 4 else '<e'
    import math
    aa = [x[0] for x in struct.iter_unpack(fmt, av)];bb = [x[0] for x in struct.iter_unpack(fmt, bv)]
    need(all(math.isfinite(x) for x in aa + bb), 'nonfinite operand; no arithmetic distance claim')
    return {'bitwise_equal': av == bv, 'elements': len(aa),
            'different_elements': sum(av[i:i+size] != bv[i:i+size] for i in range(0, len(av), size)),
            'max_abs': max((abs(x-y) for x, y in zip(aa, bb)), default=0),
            'a_backend': a.get('scheduler_backend'), 'b_backend': b.get('scheduler_backend'),
            'scope': 'specified logical row only; trace/control and same-state gates remain mandatory'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('a', 'b', 'a-meta', 'b-meta', 'out'): p.add_argument('--'+key, required=True)
    for key in ('a-row', 'b-row', 'axis'): p.add_argument('--'+key, type=int, required=True)
    x = p.parse_args();write(x.out, compare(x.a, x.b, x.a_meta, x.b_meta, x.a_row, x.b_row, x.axis))
