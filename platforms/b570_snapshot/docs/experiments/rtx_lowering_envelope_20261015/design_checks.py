"""CPU-only index/planning helpers. No backend support or native result certificate."""
import math

FAMILIES = ('Qwen', 'SmolLM2', 'Llama')
LAYERS = {'Qwen': (0, 18, 35), 'SmolLM2': (0, 12, 23), 'Llama': (0, 16, 31)}
PHASES = ('prefill', 'continuation')
ARMS = ('R', 'M_QB', 'M_QH', 'C_PQ', 'C_QB', 'C_QH')


def integer(x, lo=0, hi=(1 << 63)-1):
    if type(x) is not int or not lo <= x <= hi:
        raise ValueError('bounded integer required; booleans/floats are not descriptors')
    return x


def logical_head(q, h, j, heads, kv_heads):
    for x in (q, heads, kv_heads): integer(x, 1)
    integer(q, 1, 4); integer(h, 0, heads-1); integer(j, 0, q-1)
    if heads % kv_heads: raise ValueError('integral GQA required')
    r = h*q+j
    return {'packed_head': r, 'query': r % q, 'original_head': r // q,
            'kv_head': r // (q*(heads//kv_heads))}


def q_address(d, h, j, dims, strides, offset, owner_bytes):
    if len(dims) != 3 or len(strides) != 3: raise ValueError('three logical dimensions/strides required')
    for x in dims: integer(x, 1)
    for x in strides: integer(x, 1)
    integer(offset); integer(owner_bytes, 1)
    for x, n in zip((d, j, h), dims): integer(x, 0, n-1)
    if strides[0] != 4 or any(x % 4 for x in strides) or offset % 4:
        raise ValueError('F32 aligned element addresses required')
    extent = offset + sum((n-1)*s for n,s in zip(dims,strides)) + 4
    if extent > owner_bytes: raise ValueError('view exceeds owner')
    return offset + d*strides[0] + j*strides[1] + h*strides[2]


def profile_coordinates():
    """24 full E1 contexts; deterministic rotation includes first/middle/last layers."""
    return [(f, p, q, LAYERS[f][(pi*4+q-1) % 3])
            for f in FAMILIES for pi,p in enumerate(PHASES) for q in range(1,5)]


def choose_mask(census, descriptor_ids):
    """Pure decision rule on a COMPLETE caller-supplied full-support census.
    It authenticates neither a GPU query nor source semantics; host audit required.
    """
    ids = tuple(descriptor_ids)
    if not ids or len(set(ids)) != len(ids): raise ValueError('nonempty unique descriptors required')
    if set(census) != {'QH_C', 'QH_D'}: raise ValueError('both predetermined mask variants required')
    for variant in census.values():
        if set(variant) != set(ids): raise ValueError('incomplete or surplus census')
        if any(v is not None and type(v) is not bool for v in variant.values()):
            raise ValueError('support must be actual boolean or unknown')
    for name in ('QH_C', 'QH_D'):
        if all(census[name][i] is True for i in ids): return name
    return 'NO_ADMITTED_QH'


def budgets():
    numerical = 72*5*2
    timing_hosts = 24*3*3
    trace_hosts = 24*3
    return {'S1_support_host_attempts': 1, 'S1_numerical_host_attempts': numerical,
            'S1_timing_host_attempts': timing_hosts, 'S1_trace_host_attempts': trace_hosts,
            'S1_total_operator_host_attempts': 1+numerical+timing_hosts+trace_hosts,
            'S1_graph_computes': numerical+timing_hosts*9+trace_hosts*2,
            'S1_warmup_graphs': timing_hosts+trace_hosts,
            'S2_model_requests': 3*2*7*2, 'S2_model_processes': 3*2*7*2,
            'S3_measured_requests': 3*18*len(ARMS)*3,
            'S3_model_requests_including_warmups': 3*18*len(ARMS)*3*2,
            'S3_model_processes': 3*18*len(ARMS)*3}


def qualified_ratio(records, expected):
    """Only a minimal arithmetic guard, NOT the host full-panel/raw auditor.
    Endpoint-match flags must come from a separate complete raw endpoint comparison.
    """
    integer(expected, 1)
    if len(records) != expected: return None
    if any(r.get('endpoint_match') is not True for r in records): return None
    logs=[]
    for r in records:
        x,y=r['left_ms'],r['right_ms']
        if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in (x,y)):
            raise ValueError('finite positive completed latency required')
        logs.append(math.log(x)-math.log(y))
    return math.exp(sum(logs)/len(logs))
