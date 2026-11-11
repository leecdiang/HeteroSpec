"""Pure CPU endpoint-name correction, preserve source arrays and completed model receipt."""
from pathlib import Path
import json,hashlib,shutil,datetime
R=Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
u='D/1/HumanEval/58';receipt=R/'raw'/hashlib.sha256(u.encode()).hexdigest()[:20]/'RESULT.json';r=load(receipt);refs=load(R/'D_REFERENCES.json');ep=r['endpoint'];ref=refs['HumanEval/58']
assert ep['ids']==ref['ids'] and ep['eog']==ref['eog'] and ep['reason']=='CAP' and ref['reason']=='CAP128' and len(ep['ids'])==128 and not any(ep['eog'])
for n in ['D_REFERENCES.json','D_FREEZE.json','D_QUALIFICATION.json']:
 shutil.copyfile(R/n,R/(n[:-5]+'_PRE_NAMESPACE_CORRECTION.json'))
for ref in refs.values():
 ref['source_endpoint_literal']=ref['reason']
 if ref['reason']=='CAP128':assert len(ref['ids'])==128 and not any(ref['eog']);ref['reason']='CAP'
 assert ref['reason'] in ['CAP','EOG']
(R/'D_REFERENCES.json').write_text(json.dumps(refs,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
amend=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind='CPU_ONLY_ENDPOINT_NAMESPACE_CORRECTION',old_literal='CAP128',canonical_literal='CAP',semantic_rule='CAP128 denotes exactly128 IDs with no runtime EOG, identical to cap128 request reason CAP; preserved original literal for every reference.',all_reference_ID_and_EOG_arrays_unchanged=True,first_completed_unit=u,first_complete_raw_ids_identical=True,first_complete_raw_eog_identical=True,reused_model_receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),old_source_epoch=r['source_commit'],completed_request_regenerations=0,scientific_candidate_changes=0,scientific_retry=False,one_explicit_resume='Existing complete unit reused; next session has a newly charged warmup. No whole-generation attempt is repeated.',old_freeze='D_FREEZE_PRE_NAMESPACE_CORRECTION.json')
(R/'D_ENDPOINT_NAMESPACE_AMENDMENT.json').write_text(json.dumps(amend,indent=2)+'\n',encoding='utf8')
print('Pure CPU label correction; all full arrays unchanged, zero model reruns.')
