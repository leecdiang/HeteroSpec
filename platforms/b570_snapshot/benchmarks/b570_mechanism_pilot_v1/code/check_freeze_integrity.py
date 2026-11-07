from pathlib import Path
import json,hashlib
R=Path(__file__).parent
def load(n):return json.loads((R/n).read_text(encoding='utf8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for name in ['B_FREEZE.json','C_FREEZE.json','D_FREEZE.json']:
 f=load(name);paths=dict(f.get('sources',{}),**f.get('binaries',{}),**f.get('files',{}));wrong=[p for p,h in paths.items() if sha(R/p)!=h];print(name,len(paths),'checked','mismatches',wrong);assert not wrong
print('All loaded frozen source/binary/data identities remain unchanged')
