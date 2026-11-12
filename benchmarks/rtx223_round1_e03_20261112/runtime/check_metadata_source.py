from pathlib import Path
import ast,json,re

HERE=Path(__file__).resolve().parent
source=HERE/'stage-v4/hs_e03_runtime.cpp'
s=source.read_text(encoding='utf8')
start=s.index('    return ');end=s.index(';',start)
tokens=re.findall(r'"(?:[^"\\]|\\.)*"',s[start:end])
actual=json.loads(''.join(ast.literal_eval(x) for x in tokens))
expected=json.loads((HERE/'RUNTIME_METADATA_EXPECTED.json').read_bytes())
if actual!=expected:raise RuntimeError('metadata source and frozen expected mapping differ')
print(json.dumps({'metadata_exact':True,'source':str(source),'schema':actual['schema']}))
