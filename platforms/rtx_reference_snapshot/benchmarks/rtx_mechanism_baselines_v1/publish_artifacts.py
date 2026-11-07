"""Byte-copy consumed JSON artifacts; Git newline conversion explicitly disabled."""
import shutil
from common import V,load,save,sha
from prepare_rtx import root
r=root();out=V/'execution';out.mkdir();names=['FREEZE.json','FREEZE_REPAIR1.json','EXECUTION_POLICY.json','MODE_EVIDENCE.json','FORMAL_ADMISSION.json','CAPABILITY_ADMISSION.json','TOOL_REPAIR1.json','P0_FREEZE.json','P0_PLAN.json','GPU_EXECUTION_CLOSED.json','RUNTIME_MANIFEST.json']
index={}
for name in names:
    shutil.copyfile(r/name,out/name);assert sha(out/name)==sha(r/name);index['execution/'+name]=dict(sha256=sha(r/name),bytes=(r/name).stat().st_size,source=str(r/name),exact_bytes=True)
save(V/'EXACT_ARTIFACTS.json',index)
p=V/'.gitattributes'
with p.open('a',encoding='utf8') as file:file.write('\nexecution/*.json -text\n')
print('exact artifacts',len(index))
