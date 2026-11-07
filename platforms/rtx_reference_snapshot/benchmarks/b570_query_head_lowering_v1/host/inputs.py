"""Exact delivered fixture algorithm serialized for the real frozen backend."""
import hashlib, math, pathlib, struct, sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import core, oracle, plan

def write_input(path,cell):
    g=core.Geometry(**cell['geometry']);f=oracle.fixture(g,cell['mask'],cell['pattern'])
    header=[g.q,g.n,g.h,g.hk,int(g.storage=='permuted'),
            ('causal','single','holes').index(cell['mask']),int(cell['pattern']=='structured')]
    out=bytearray(struct.pack('<7i',*header))
    for j in range(g.q):
        for h in range(g.h):
            for x in f['q'][j][h]:out.extend(struct.pack('<f',x))
    for h in range(g.hk):
        for p in range(g.n):
            for x in f['k'][h][p]:out.extend(struct.pack('<e',x))
    for h in range(g.hk):
        for d in range(g.dv):
            for x in f['v'][h][d]:out.extend(struct.pack('<e',x))
    for j in range(32):
        for p in range(g.n):out.extend(struct.pack('<f',f['mask'][j][p] if j<g.q else -math.inf))
    pathlib.Path(path).write_bytes(out)
    return hashlib.sha256(out).hexdigest()
