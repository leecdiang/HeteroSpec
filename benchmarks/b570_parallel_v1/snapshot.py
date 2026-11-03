"""Publish compact, losslessly encoded evidence alongside the full external archive."""
from paths import *
import gzip
def snapshot():
    dest=HERE/'evidence';dest.mkdir(exist_ok=True)
    patterns=('CONTROL-*.json','SCALAR-*.json','REUSE.json','TINY_RESULT.json','D_P1_ANCHOR.json','D_P1_WIDE.json','K1_REGRESSION.json','SMOL_INTACT-*.json','POLL_RESULT.json','NATURAL_PANEL.json','NATURAL_QUAL.json','NATURAL_COST.json','FAST_COST.json','FREEZE.json','SOURCE_BINDING-candidate-D.json')
    for pattern in patterns:
        for p in ROOT.glob(pattern):
            z=dest/(p.name+'.gz');packed=gzip.compress(p.read_bytes(),compresslevel=9,mtime=0)
            if z.exists():assert gzip.decompress(z.read_bytes())==p.read_bytes()
            else:z.write_bytes(packed)
if __name__=='__main__':snapshot()

