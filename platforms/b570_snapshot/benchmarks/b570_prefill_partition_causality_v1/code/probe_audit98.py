import verify98
from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
for p in (r/"payloads").glob("*.seqkv.bin"):
 b=p.read_bytes();n=int.from_bytes(b[12:16],"little");v=verify98.parse_kv(b,n);print(p.name,n,len(v["tensors"]),len(b))
