"""Fresh combined candidate and separate same-binary factor ablations."""
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need
import host
from audit_committed_vectors import audit as committed

root=Path(sys.argv[1]);version=sys.argv[2] if len(sys.argv)>2 else '02';build=sys.argv[3] if len(sys.argv)>3 else 'candidate-combined-01';deadline=time.monotonic()+3600
while not(root/build/'BUILD.json').exists() or Path('C:/hs/b570-llama-exclusive.lock').exists():
    need(time.monotonic()<deadline,'bounded prerequisite wait expired; no model work launched');time.sleep(2)
for label,q8,prefix in [('combined',True,True),('combined-no-prefix',True,False),('combined-no-q8',False,True)]:
    c=read(root/'host-reference-q8-00.json');c['candidate_build']=str(root/build/'BUILD.json');c['reference_q8']=q8;c['prefix_extent']=prefix
    c['policy']['purpose']=label+'; same combined numerical binary, independent Q8 activation and scalar-prefix physical extent switches'
    config=root/('host-'+label+'-'+version+'.json');epoch=root/(label+'-epoch-'+version);write(config,c);host.prepare(config,epoch)
    host.execute(epoch,'capacity',[],admit=True);host.execute(epoch,'capacity-oracle',[],oracle=True,admit=True)
    result=host.baseline(epoch);print(label,result['status'],flush=True)
    if result['all_reference_equal']:
        out=root/(label.upper().replace('-','_')+'_COMMITTED_AUDIT-'+version+'.json');committed(epoch,out)
        if label=='combined':need(read(out)['status']=='COMMITTED_REFERENCE_VECTORS_PASS','combined full-vector repair incomplete; retain development and continue mechanism work')
    elif label=='combined':raise ValueError('combined endpoint repair incomplete')
