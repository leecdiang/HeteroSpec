"""CPU provenance mapping repair: restore previously omitted PR64 canonical label."""
import json,hashlib,shutil
from prepare import R,load,save,sha
old=R/'HISTORICAL_OWN_PATH.json';before=sha(old);shutil.copyfile(old,R/'HISTORICAL_OWN_PATH.initial.json');history=load(old);dest=R/'dependencies/pr64'
sources=[]
for p in sorted((dest/'raw').glob('*/RESULT.json')):
 x=load(p)
 if x['warm'] or x['config'].get('label')!='CANONICAL_PREFILL_INPLACE_PHASE_BINDING' or x['config'].get('cap',128)!=128:continue
 caps=[dest/f for f in x['files'] if f.endswith('/capture.json')];assert len(caps)==1;raw=load(caps[0]);key=x['task']+'/C'
 row=dict(ids=raw['ids'],eog=raw['eog'],endpoint=x['endpoint'],source_unit=x['unit_id'],capture_sha256=sha(caps[0]))
 if key in history:assert history[key]['ids']==row['ids'] and history[key]['eog']==row['eog'],key
 else:history[key]=row
 sources.append(dict(key=key,source_unit=x['unit_id'],sha256=sha(caps[0])))
save('HISTORICAL_OWN_PATH.json',history)
save('A_HISTORY_BINDING_AMENDMENT.json',dict(before_sha256=before,after_sha256=sha(old),reason='CPU historical label map omitted CANONICAL_PREFILL_INPLACE_PHASE_BINDING. Add all retained cap128 canonical own-path records, without inspecting new bridge outputs for selection.',frozen_generation_code_or_assets_changed=False,model_reruns=0,new_smol_forwards=0,source_records=sources))
