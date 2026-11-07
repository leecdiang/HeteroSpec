"""Re-audit immutable native records with bounded matrix metadata retention."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha
import audit,host
epoch=Path(sys.argv[1]);out=Path(sys.argv[2]);panel=read(epoch/'DEV.json')
r=audit.matrix(host.paths(epoch,'baseline-candidate'),host.paths(epoch,'baseline-oracle'),[x['id'] for x in panel])
need(r==read(epoch/'BASELINE_AUDIT.json'),'compact auditor changed scientific result')
write(out,{'status':'COMPACT_AUDIT_IDENTICAL','baseline_sha256':sha(epoch/'BASELINE_AUDIT.json'),'requests':r['requests'],'result':r,'geometry_fully_validated_before_release':True})
