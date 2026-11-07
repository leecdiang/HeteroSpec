"""Zero-inference metadata corrections before F0; preserve executed snapshots."""
import sys,json,shutil,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'scripts/platform/rtx_trajectory_cost_v4'
sys.path.insert(0,str(SRC))
from prepare import STUDY,save,sha,now
assert not (STUDY/'F0_MANIFEST.json').exists()
# The initial authorization recorded the initial clone; T was subsequently
# extended solely for vocab-only EOG identities, with no numerical worker edit.
auth=json.loads((STUDY/'NEW_STUDY_AUTHORIZATION.json').read_text(encoding='utf-8'))
auth['numeric_cpp_same_as_V3']['tokenizer.cpp']=False
auth['tokenizer_change_scope']='Vocabulary-only llama_vocab_n_tokens/llama_vocab_is_eog query added; zero context, decode, sampling or model forward. P/R worker and query source and the numerical/timer binaries remain byte-identical to V3.'
auth['initial_clone_authorization_copy']='The pre-extension initial clone version is retained in capture-repair/source_snapshot; tokenizer equality in that snapshot describes the clone, not the final F0 source.'
save(STUDY/'NEW_STUDY_AUTHORIZATION.json',auth)
reg=json.loads((STUDY/'CAPTURE_REGRESSION.json').read_text(encoding='utf-8'))
previous=ROOT.with_name('HeteroSpec-v3')
for row,folder in zip(reg['actual_prior_failures_parsed_without_reclassification'],['A-pre-live','B-formal']):
    d=previous/'work'/folder/'runs'/row['original_failed_run_id'];out=ROOT/'work/capture-regression/original-failed-captures'/row['original_failed_run_id']
    if not out.exists():shutil.copytree(d,out)
    assert json.loads((out/'record.json').read_text(encoding='utf-8'))['status']=='OPERATIONAL_FAILURE'
    assert sha(out/'native.log')==row['native_log_sha256']
    row.update(archived_copy=out.relative_to(ROOT).as_posix(),original_record_sha256=sha(out/'record.json'))
reg['positive_raw_copy_archived_utc']=now();reg['positive_archive_copy_model_forwards']=0;save(STUDY/'CAPTURE_REGRESSION.json',reg)
# Make the final metadata generator describe the new authorized study.
p=SRC/'finalize.py';s=p.read_text(encoding='utf-8')
s=s.replace('All 360 fixed exposed-task runs and 40 observer/endpoint runs were captured and independently verified.', 'All 360 fixed exposed-task runs, 40 observer/endpoint runs and 30 fresh capture-repair conditions were captured and independently verified. The capture-repair five gates pass 3/3 each, including actual simultaneous EOS/cap endpoints.')
s=s.replace('Section 10: this preparation freezes F0 and stops.', 'Section 10 is amended by the direct human repair/continuation instruction: publish and fully retrieve the concrete F0 before proceeding.')
s=s.replace('literal authorization/full F0 SHA guards', 'operator authorization bound to the actual full F0 SHA, with the direct human instruction preserved and no literal SHA-review claim')
s=s.replace('After reviewing the exact remote F0 content SHA, author supplies `EXECUTE_FROZEN` and that full SHA.', 'The preserved direct human repair/continuation instruction authorizes this amended study. The operator supplies execution mode `EXECUTE_FROZEN` with the exact fully retrieved F0 SHA. This is not a verbatim human quotation or a claim that the human inspected a future SHA.')
s=s.replace('the command still requires explicit author review of precisely that value.', 'the record explicitly distinguishes operator content binding from human literal input.')
s=s.replace('Use a clean independent checkout for a new preparation.', 'For model reruns use a new study identity and a new exposure audit; the present 19-task cohort becomes exposed once executed. Preparation additionally requires the retained V3 evidence checkout and exposure catalog on this qualified host, as listed in the audit and amendment. Use a clean independent checkout for a new preparation.')
p.write_text(s,encoding='utf-8',newline='\n')
snapshot=ROOT/'work/engineering-attempt1/source_snapshot'
changes={p.name:{'executed_initial_snapshot_sha256':sha(snapshot/p.name) if (snapshot/p.name).exists() else None,'final_pre_F0_sha256':sha(p)} for p in SRC.iterdir() if p.suffix in ['.py','.cpp'] and (not (snapshot/p.name).exists() or sha(snapshot/p.name)!=sha(p))}
numeric=['worker.cpp','query_defaults.cpp','native.py','verify_replay.py','engine.py','native_runner.py','tokenizer.cpp']
assert all(sha(SRC/n)==sha(snapshot/n) for n in numeric)
save(STUDY/'PRE_F0_SOURCE_EVOLUTION.json',{'utc':now(),'status':'PASS','base_engineering_initial_source_snapshot':'work/engineering-attempt1/source_snapshot','numerical_worker_capture_and_independent_replay_bytes_unchanged_through_base_engineering':numeric,'changed_files':changes,'scope':'Preparation/freeze/authorization/publication/offline-verification metadata improvements before F0. Executed source snapshots and initial ENGINEERING_PROTOCOL are preserved. Configuration branch label was corrected on disk while the engineering process held the older metadata module in memory; a fresh zero-inference finalization regenerates the final branch/protocol before F0. No model run was retried or relabeled.','model_forward_calls':0})
for p in SRC.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
print('Metadata/source evolution PASS; no inference',flush=True)
