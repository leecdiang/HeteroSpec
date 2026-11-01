"""Read-only comparison to authenticated PR151 native Llama records, not a new oracle."""
import pathlib,sys,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from common import *
bundle=Path(sys.argv[1]);repo=Path(sys.argv[2]);out=Path(sys.argv[3]);cfg=read(bundle/'CONFIG.json');need(cfg['regression_family']=='Llama','pinned Llama history only')
historical=git_read(repo,BASE,'benchmarks/rtx_scope_transfer_v1/sidecar_execution/diagnostic/REQUESTS.jsonl');oldroot=Path(cfg['parent_root'])
history=[json.loads(l) for l in historical.decode().splitlines() if l];index={(r['input_id'],r['arm'],r['observer']):r for r in history if r['stage']=='diagnostic_A1'};need(len(index)==18,'complete original A1 history')
unit=bundle/'units/regression01';receipt=read(unit/'RECEIPT.json');need(receipt['success'] and receipt['active_processes_after_wait']==0,'regression incomplete');result=[]
for slot in read(unit/'SLOTS.json'):
    old=index[slot['input_id'],slot['arm'],slot['observer']];pin=old['raw_native_record'];source=oldroot/pin['path'];need(source.stat().st_size==pin['bytes'] and file_hash(source)==pin['sha256'],'historical native record changed')
    a=read(source);path=unit/'native'/(slot['slot_id']+'.json');b=read(path);same=endpoint(a)==endpoint(b);native=slot['repair']['prefill']=='native';work=all(a[k]==b[k] for k in ('cycles','target_final_kv','draft_final_kv')) if native else None
    vectors=True;count=0
    if slot['observer']=='heavy':
        oldfolder=source.with_suffix('');newfolder=unit/'native'/slot['slot_id'];names=set()
        for v in old['raw_vectors']:
            oldfile=oldroot/v['path'];rel=oldfile.relative_to(oldfolder);need(file_hash(oldfile)==v['sha256'],'historical vector changed');candidate=newfolder/rel;names.add(rel.as_posix());vectors=vectors and candidate.exists() and file_hash(candidate)==v['sha256'];count+=1
        current={p.relative_to(newfolder).as_posix() for role in ('target','draft') for p in (newfolder/role).glob('*.f32')};vectors=vectors and names==current
    result.append({'slot':slot['slot_id'],'original_native_sha256':pin['sha256'],'candidate_native_sha256':file_hash(path),'endpoint_equals_original_native':same,'native_transactions_bounds_equal':work,'full_vectors_equal_original_native':vectors if slot['observer']=='heavy' else None,'vectors_checked':count,'original_historical_R_match':old['historical_R_match'],'interpretation':'Known original counterexample retained, not redefined as reference preservation' if not old['historical_R_match'] else 'Original reference-preserving control'})
passed=all(x['endpoint_equals_original_native'] and x['native_transactions_bounds_equal'] is not False and x['full_vectors_equal_original_native'] is not False for x in result)
save(out,{'status':'NO_NEW_LLAMA_REGRESSION_KNOWN_FAILURE_RETAINED' if passed else 'LLAMA_REGRESSION_CHANGED','historical_manifest_sha256':hashlib.sha256(historical).hexdigest(),'source_commit':BASE,'records':result,'scope':'Equality to original native behavior is separate from R preservation; the original Llama counterexample remains a failure against R.'},exclusive=True);print('History comparison',passed)
