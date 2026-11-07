"""Read-only actual V3 regression and explicit corrupted transport fixtures; no model forward."""
import json,re,importlib.util,shutil
from pathlib import Path
from prepare import ROOT,STUDY,save,sha,now
import native,verify_replay,native_runner
PREVIOUS=ROOT.with_name('HeteroSpec-v3')
def main():
    out=ROOT/'work/capture-regression';out.mkdir(exist_ok=False)
    failed=[(PREVIOUS/'work/A-pre-live/runs/HumanEval-59-r1-A_REFERENCE_UB1','TARGET_REFERENCE'),(PREVIOUS/'work/B-formal/runs/HumanEval-59-r1-B_SERIALIZED_K2_UB1','RTX_SERIALIZED_K2')]
    accepted=[];rejected=[]
    for d,wire in failed:
        before=sha(d/'record.json');r=json.loads((d/'record.json').read_text(encoding='utf-8'));assert r['status']=='OPERATIONAL_FAILURE'
        archived=out/'original-failed-captures'/r['run_id'];shutil.copytree(d,archived)
        result=native.parse_capture(d/'native.log',wire);text=(d/'native.log').read_bytes().replace(b'\r\n',b'\n').decode('latin-1')
        ids,reason=verify_replay.native_commits(text)
        assert ids==result['generated_ids'] and len(ids)==128 and ids[-1]==151645 and reason==result['termination']=='EOS' and result['native_stop_observations']==['limit','EOS']
        accepted.append({'original_failed_run_id':r['run_id'],'archived_copy':archived.relative_to(ROOT).as_posix(),'original_record_sha256':before,'native_log_sha256':sha(d/'native.log'),'array_sha256':result['token_array_sha256'],'length':128,'independent_parser_match':True,'old_failed_status_unchanged':sha(d/'record.json')==before,'scope':'Parser regression only; not a reclassified valid formal run.'})
        stop=re.compile(r'(^[^\n]*process_toke:[^\n]*stopped by (?:EOS|limit)[^\n]*\n)',re.M)
        stop_lines=stop.findall(text);assert len(stop_lines)==2
        variants={'missing_both':stop.sub('',text),'missing_limit':text.replace(stop_lines[0],'',1),'missing_EOS':text.replace(stop_lines[1],'',1),'duplicate_EOS':text.replace(stop_lines[1],stop_lines[1]*2,1),'duplicate_limit':text.replace(stop_lines[0],stop_lines[0]*2,1),'reverse_stops':text.replace(''.join(stop_lines),''.join(reversed(stop_lines)),1)}
        last=list(native.EVENT.finditer(text))[-1];bad=text[:last.start(5)]+'151644'+text[last.end(5):];variants['non_EOG_terminal_dual']=bad
        for label,corrupted in variants.items():
            q=out/(r['run_id']+'-'+label+'.log');q.write_bytes(corrupted.encode('latin-1'))
            for verifier in ['producer','independent']:
                try:native.parse_capture(q,wire) if verifier=='producer' else verify_replay.native_commits(corrupted)
                except ValueError as e:rejected.append({'run_id':r['run_id'],'case':label,'verifier':verifier,'rejected':True,'reason':str(e),'fixture':q.relative_to(ROOT).as_posix(),'fixture_sha256':sha(q)})
                else:raise RuntimeError('corrupted termination accepted '+label+' '+verifier)
    spec=importlib.util.spec_from_file_location('previous_native',PREVIOUS/'scripts/platform/rtx_trajectory_cost_v3/native.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    checked=[]
    for folder in ['engineering-attempt1','engineering-extra']:
        rows=json.loads((PREVIOUS/'work'/folder/'records.json').read_text(encoding='utf-8'))['runs']
        for r in rows:
            if not r.get('implementation'):continue
            d=PREVIOUS/r['path'];wire=native_runner.WIRE[r['wire_condition']]
            a=old.parse_capture(d/'native.log',wire);b=native.parse_capture(d/'native.log',wire)
            assert all(b[k]==v for k,v in a.items()),r['run_id']
            ids,termination=verify_replay.native_commits((d/'native.log').read_bytes().replace(b'\r\n',b'\n').decode('latin-1'));assert ids==a['generated_ids'] and termination==a['termination']
            checked.append({'run_id':r['run_id'],'source_log_sha256':sha(d/'native.log'),'unchanged_existing_fields':True,'independent_parser_match':True})
    save(STUDY/'CAPTURE_REGRESSION.json',{'status':'PASS','utc':now(),'actual_prior_failures_parsed_without_reclassification':accepted,'corruption_rejections':rejected,'prior_valid_native_regressions':checked,'model_processes':0,'model_forward_calls':0,'old_evidence_mutated':False})
    print(json.dumps({'status':'PASS','actual_failure_regressions':len(accepted),'corruption_verifier_rejections':len(rejected),'prior_valid_native_regressions':len(checked),'model_forwards':0}),flush=True)
if __name__=='__main__':main()
