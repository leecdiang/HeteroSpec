"""Append isolated derived evidence to existing draft #63, then fresh Git readback."""
from pathlib import Path
import json,hashlib,subprocess,shutil,time
ROOT=Path(__file__).parent
WORK=Path('C:/Users/DIANG/.codex/worktrees/b570-closeout-v1/HeteroSpec')
REL='benchmarks/b570_closeout_overnight_v1';DEST=WORK/REL
BRANCH='analysis/b570-overnight-closeout-v1-20261006'
ORIGIN='https://github.com/leecdiang/HeteroSpec.git'
PROMPT_SHA='d99dae9d'  # Exact original Git blob is checked against pinned initial PR below.
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def git(*args,cwd=WORK):return subprocess.check_output(['git',*args],cwd=cwd,text=True,encoding='utf-8',errors='replace').strip()
def verify(head):
 target=ROOT/'archive'/('remote-readback-'+str(time.time_ns()));target.mkdir(exist_ok=False)
 git('init','--quiet',str(target));git('remote','add','origin',ORIGIN,cwd=target)
 git('-c','remote.origin.promisor=true','-c','remote.origin.partialclonefilter=blob:none','fetch','--quiet','--depth=1','--filter=blob:none','origin',BRANCH,cwd=target)
 actual=git('rev-parse','FETCH_HEAD',cwd=target);assert actual==head,(actual,head)
 git('config','core.autocrlf','false',cwd=target)
 git('restore','--source=FETCH_HEAD','--worktree','--',REL,cwd=target)
 files=git('ls-tree','-r','--name-only',head,'--',REL).splitlines();checks=[]
 for f in files:
  a=WORK/f;b=target/f;assert a.read_bytes()==b.read_bytes(),f
  checks.append({'path':f,'sha256':sha(b),'bytes':b.stat().st_size})
 return {'status':'PASS','head':head,'files':checks,'fresh_repository':str(target),'transport':'fresh depth-one filtered Git fetch and checkout, no local object borrowing','remote_branch':BRANCH,'model_forwards':0}
def publish():
 assert read(ROOT/'ARCHIVE_RESTORE.json')['status']=='PASS'
 assert read(ROOT/'ASSET_POST.json')['status']=='PASS'
 assert read(ROOT/'INDEPENDENT_VERIFICATION.json')['status'].startswith('PASS')
 assert git('branch','--show-current')==BRANCH
 assert not git('status','--porcelain'),'Managed PR worktree unexpectedly dirty'
 original=git('rev-parse','aaa18acd2619dc8c0f91482b3308885d53bbf02e:'+REL+'/EXECUTION_PROMPT.md')
 assert git('hash-object',str(DEST/'EXECUTION_PROMPT.md'))==original,'Prompt v1 modified'
 remote=git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]
 assert remote==git('rev-parse','HEAD'),'Remote branch changed; no force or silent conflict resolution'
 code=DEST/'code';code.mkdir(exist_ok=True)
 for file in ROOT.glob('*.py'):shutil.copy2(file,code/file.name)
 shutil.copytree(ROOT/'src',code/'src',dirs_exist_ok=True)
 public=['STARTUP.json','RECOVERY_AMENDMENT.json','TIMER_AMENDMENT.json','G0_ACCOUNTING.json','G0.json','G0_REBUILT.json','G0_SHAM.json','G0_WIDTH.json','G0_ETA.json','TOKENIZATION_PROOF.json','PROTOCOL.json','EXECUTION_FREEZE.json','INPUTS.json','EXPOSURE_AUDIT.json','ASSET_MANIFEST.json','ASSET_POST.json','B_SUMMARY.json','C_SUMMARY.json','C_ANCHOR_SUMMARY.json','D_GATE.json','D_RESET_SUMMARY.json','D_TIMING_SUMMARY.json','E_PLAN.json','E_SELECTION.json','E_CAPTURE_SUMMARY.json','E_PILOT_SUMMARY.json','E_CONFIRM_SUMMARY.json','E_LONG_SUMMARY.json','E_D_RESET_SUMMARY.json','E_D_TIMING_SUMMARY.json','E_DECISION.json','MECHANISM_PLAN.json','MECHANISM.json','INDEPENDENT_VERIFICATION.json','STAGE_COUNTS.json','DECISION.json','RTX_B570_COMPARISON.json','RTX_B570_COMPARISON.csv','REQUEST_ACCOUNTING.json','COLD_LOAD_ACCOUNTING.json','RESEARCH_BOUNDARIES.md','REPORT.md','ARCHIVE_RESTORE.json','BUDGET_DEGRADATION.json']
 public+=['WORK_ACCOUNTING.json','WORK_ACCOUNTING.csv','WORK_ACCOUNTING_HANDOFF.json','WORK_ACCOUNTING_AMENDMENT.json']
 for name in public:
  if (ROOT/name).exists():shutil.copy2(ROOT/name,DEST/name)
 for name in ['MATCHED_RESERVATION_AMENDMENT.json','CPU_GRAPH_ZERO_AMENDMENT.json','AMENDMENT_INDEX.json','G0_TARGET_FINAL.json','FINAL_TARGET_SCOPE_PROOF.json','ENVIRONMENT_OBSERVATIONS.json','DEVICE_RECOVERY_AMENDMENT.json','DEVICE_RECOVERY_FREEZE.json','DEVICE_RECOVERY_FAILURE.json','CPU_DELIVERY_CLARIFICATION.json','CONTINUATION_AMENDMENT.json','CONTINUATION_FREEZE.json','CONTINUATION_FAILURE.json','CONTINUATION_CPU_SOURCES_AT_FREEZE.json','OFFLINE_VERIFIER_CONTINUATION_AMENDMENT.json','CPU_PAYLOAD_RECOVERY.json','CPU_PAYLOAD_RECOVERY_PAUSE.json','PAUSE_RESUME_AMENDMENT.json','PAUSE.json','G0_CONTINUATION_QUAL.json','G0_CONTINUATION_QUAL_SCHEDULE.json','G0_DEVICE_REQUALIFICATION.json','G0_DEVICE_REQUALIFICATION_SCHEDULE.json','G0_ETA_N0.json','ETA_CURRENT_REFERENCE_AMENDMENT.json','CPU_REVIEW_HANDOFF.json','FINAL_CPU_CONTINUATION.json']:
  if (ROOT/name).exists():shutil.copy2(ROOT/name,DEST/name)
 if (ROOT/'recovery/CPU_GRAPH_ZERO_AMENDMENT.json').exists():shutil.copy2(ROOT/'recovery/CPU_GRAPH_ZERO_AMENDMENT.json',DEST/'CPU_GRAPH_ZERO_AMENDMENT.json')
 if (ROOT/'recovery/RESUME_PAYLOAD_GUARD_AMENDMENT.json').exists():shutil.copy2(ROOT/'recovery/RESUME_PAYLOAD_GUARD_AMENDMENT.json',DEST/'RESUME_PAYLOAD_GUARD_AMENDMENT.json')
 for name in ['CPU_DELIVERY_PATCH_BEFORE.json','CPU_DELIVERY_PATCH_AMENDMENT.json','CPU_DELIVERY_COMMIT.json','CONTINUATION_CPU_COMMIT.json']:
  if (ROOT/'recovery'/name).exists():shutil.copy2(ROOT/'recovery'/name,DEST/name)
 save(DEST/'RESUME_STOP.json',{'execution_status':read(ROOT/'STAGE_COUNTS.json'),'inference_stopped_for_archive':not (ROOT/'LOCK.json').exists(),'stop_marker':str(ROOT/'STOP'),'experiment_cutoff_utc':read(ROOT/('CONTINUATION_AMENDMENT.json' if (ROOT/'CONTINUATION_AMENDMENT.json').exists() else 'RECOVERY_AMENDMENT.json'))['new_experiment_stop_utc'],'original_deadline_preserved':True,'resume':'Validate original frozen unique units and exact source/numerical hashes before resuming a PARTIAL batch; complete scientific outputs must not be repeated. New inference after cutoff requires a timestamped amendment. Clean archive validation uses CPU only.'})
 if (ROOT/'derived').exists():shutil.copytree(ROOT/'derived',DEST/'derived',dirs_exist_ok=True)
 (DEST/'.gitattributes').write_text('* -text\n',encoding='ascii',newline='\n')
 (DEST/'README.md').write_text('# B570 finite closeout\n\nSee REPORT.md, DECISION.json, STAGE_COUNTS.json and REMOTE_READBACK.json. Prompt v1 is preserved unchanged. Raw/state/private binaries and frozen source history live in the local immutable archive named by ARCHIVE_RESTORE.json; weights and runtime binaries remain external hash-bound dependencies. No merge or manuscript update.\n',encoding='utf-8',newline='\n')
 (DEST/'REPRODUCE.md').write_text('# Restore and reproduce\n\nThe public code is for review. Recover the full private study-root layout from the CAS ZIP in ARCHIVE_RESTORE.json using INDEX.json: verify ZIP CRC, every object SHA256, safe relative paths and every restored file hash. Do not overwrite the old study. Run the restored independent_verify.py with the restored root as its first argument; all derivations must match the sealed INDEPENDENT_VERIFICATION.json. The clean restoration already performed this without model forwards.\n\nInference replay requires the exact external target/draft hashes, old source/library/compiler/runtime bindings in ASSET_POST.json, actual B570 Vulkan0 and the archived private executables. Restore code/inputs together; set HETEROSPEC_B570_STUDY_ROOT, HETEROSPEC_B570_OLD_ROOT and HETEROSPEC_ASSET_ROOT for runner.py. CMake supports PINNED_SOURCE/PINNED_BUILD cache paths. The generator preserves the exact old native decoding loop. Old absolute dependency paths in other study scripts must be rebound explicitly, never silently replaced with current main.\n\nResume only the original frozen unique units and hash-verified complete results. A stop marker at study-root STOP prevents new experiments; both inference controller and pipeline hold PID+creation identities. Do not extend the frozen deadline without another timestamped user-authorized amendment. Replaying inference is a new batch, not clean archive verification.\n',encoding='utf-8',newline='\n')
 save(DEST/'SOURCE_BINDINGS.json',{'formal_freeze':read(ROOT/'EXECUTION_FREEZE.json') if (ROOT/'EXECUTION_FREEZE.json').exists() else None,'source_base_b570':'196ed563b36d0e16a3cdb667b6996a4afd98da1d','RTX_comparison_head':'8dfa60a2492e0639a0774f7bac842273485ca26a','old_G0_build':read(ROOT/'engineering-g0-build-v1/BUILD_IDENTITY.json') if (ROOT/'engineering-g0-build-v1/BUILD_IDENTITY.json').exists() else read(ROOT/'RECOVERY_AMENDMENT.json')['unchanged_numerical_assets'],'final_model_runtime_assets':read(ROOT/'ASSET_POST.json'),'source_git_bundle':read(ROOT/'ARCHIVE_RESTORE.json')['source_bundle_sha256']})
 def manifest():
  save(DEST/'EVIDENCE_MANIFEST.json',{'files':{str(f.relative_to(DEST)).replace('\\','/'):sha(f) for f in DEST.rglob('*') if f.is_file() and f.name!='EVIDENCE_MANIFEST.json'},'raw_archive_sha256':read(ROOT/'ARCHIVE_RESTORE.json')['archive_sha256'],'scope':'Only this study; no weights/runtime payloads/bulk raw telemetry','self_hash':'Verified by fresh remote Git blob readback, avoiding recursive self-hash'})
 manifest();git('add','--',REL)
 changed=git('diff','--cached','--name-only').splitlines();assert changed and all(n.startswith(REL+'/') for n in changed)
 assert REL+'/EXECUTION_PROMPT.md' not in changed
 git('commit','-m','Append B570 frozen finite experiment evidence, independent audit and restore')
 head=git('rev-parse','HEAD');git('push','origin','HEAD:refs/heads/'+BRANCH)
 receipt=verify(head);save(ROOT/'REMOTE_READBACK.json',receipt);save(DEST/'REMOTE_READBACK.json',receipt)
 d=read(ROOT/'DECISION.json');d['archive_restore']='PASS';d['remote_readback']='PASS';d['closure']='COMPLETE_FINITE_SCOPE' if read(ROOT/'STAGE_COUNTS.json')['core_complete_measured'] else 'PARTIAL';save(ROOT/'DECISION_FINAL.json',d);save(DEST/'DECISION.json',d)
 with (DEST/'REPORT.md').open('a',encoding='utf-8',newline='\n') as f:f.write(f"\n## 已核验交付\n\n本地 immutable CAS 包与干净恢复通过；{len(receipt['files'])} 个研究文件从全新 Git 存储回读字节一致。科学证据提交 `{head}`。对应范围状态：**{d['closure']}**。PR #63 保持 Draft，未合并。完整原始证据、历史 bundle 及私有程序位于 ARCHIVE_RESTORE.json 指定的本地包；该包不是远端 raw 上传。\n")
 manifest();git('add','--',REL);git('commit','-m','Record successful B570 archive restoration and fresh remote readback')
 finalhead=git('rev-parse','HEAD');git('push','origin','HEAD:refs/heads/'+BRANCH)
 final=verify(finalhead);final['closure']=d['closure'];final['archive_sha256']=read(ROOT/'ARCHIVE_RESTORE.json')['archive_sha256'];save(ROOT/'DELIVERY_VERIFIED.json',final)
 print({'status':final['closure'],'PR':'https://github.com/leecdiang/HeteroSpec/pull/63','head':finalhead,'remote_files':len(final['files'])},flush=True)
if __name__=='__main__':publish()
