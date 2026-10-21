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

def write_input(path, f):
    import struct, hashlib
    q,k,h,hk = (f[n] for n in ('q','k','h','hk'))
    exact = f['pattern']==0
    data=bytearray(struct.pack('<7i',q,k,h,hk,f['storage'],f['mask'],f['pattern']))
    for j in range(q):
        for head in range(h):
            for d in range(128):
                x=float(d==(head+3*j)%128) if exact else cancellation(1,j,head,d)
                data.extend(struct.pack('<f',x))
    for head in range(hk):
        for key in range(k):
            for d in range(128):
                x=((key+head)%5-2)/8 if exact else cancellation(2,head,key,d)
                data.extend(struct.pack('<e',x))
    for head in range(hk):
        for d in range(128):
            for key in range(k):
                x=((d+3*head+key)%9-4)/8 if exact else cancellation(3,head,d,key)
                data.extend(struct.pack('<e',x))
    for j in range(32):
        for key in range(k):
            valid=j<q and (f['mask']==0 or f['mask']==1 and key<k-2+j
                           or f['mask']==2 and key==(3+7*j)%k)
            data.extend(struct.pack('<f',0.0 if valid else -float('inf')))
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()

if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser(); p.add_argument('group', choices=['dev', 'holdout'])
    print(json.dumps(list(fixtures(p.parse_args().group)), indent=2))
