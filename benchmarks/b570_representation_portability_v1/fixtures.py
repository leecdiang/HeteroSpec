"""Preregistered finite CPU matrix. No numerical execution on import."""
import itertools

SEED = 0x570108
HEADS = ((8, 8), (8, 1), (32, 8))

def mix(x):
    x &= 0xffffffff
    x ^= x >> 16
    x = x * 0x7feb352d & 0xffffffff
    x ^= x >> 15
    x = x * 0x846ca68b & 0xffffffff
    return (x ^ (x >> 16)) & 0xffffffff

def cancellation(tag, a, b, c):
    return (int(mix(SEED ^ (tag * 0x9e3779b9) ^ (a * 73856093)
                    ^ (b * 19349663) ^ (c * 83492791)) % 511) - 255) / 256

def fixtures(group):
    ks = {'dev': (128, 256), 'holdout': (127, 129, 255, 257)}[group]
    for q, k, (h, hk), storage, mask, pattern in itertools.product(
            (1, 2), ks, HEADS, (0, 1), range(3), range(2)):
        yield dict(q=q, k=k, h=h, hk=hk, storage=storage, mask=mask,
                   pattern=pattern, id=f'q{q}_k{k}_h{h}v{hk}_s{storage}_m{mask}_p{pattern}')

if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser(); p.add_argument('group', choices=['dev', 'holdout'])
    print(json.dumps(list(fixtures(p.parse_args().group)), indent=2))
