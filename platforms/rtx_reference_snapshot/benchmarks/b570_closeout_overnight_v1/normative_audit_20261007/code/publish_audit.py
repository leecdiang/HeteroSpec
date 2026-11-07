"""Append review to existing Draft PR; no merge, no force push, fresh blob readback."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,subprocess,importlib.util
ROOT=Path(__file__).parent;BASE=Path('C:/hs/b570-closeout-v1');WORK=Path('C:/Users/DIANG/.codex/worktrees/b570-closeout-v1/HeteroSpec');REL='benchmarks/b570_closeout_overnight_v1';DEST=WORK/REL;AUD=DEST/'normative_audit_20261007';BRANCH='analysis/b570-overnight-closeout-v1-20261006'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=WORK,text=True).strip()
assert load(ROOT/'SUPPLEMENT_VERIFICATION.json')['status']==load(ROOT/'ASSET_REAUDIT.json')['status']==load(ROOT/'SUPPLEMENT_ARCHIVE_RESTORE.json')['status']=='PASS'
assert load(ROOT/'CORE_REVIEW.json')['status']=='PASS_WITH_REQUIRED_SUPPLEMENT'
assert not (ROOT/'LOCK.json').exists() and not (BASE/'LOCK.json').exists()
assert git('branch','--show-current')==BRANCH and not git('status','--porcelain')
prior=git('rev-parse','HEAD');assert prior==load(ROOT/'AMENDMENT.json')['prior_science_head']
assert git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]==prior
AUD.mkdir(exist_ok=False);(AUD/'code').mkdir()
for n in ['AMENDMENT.json','STARTUP.json','BUILD_FREEZE.json','CORE_REVIEW.json','ASSET_REAUDIT.json','EXPLICIT_SYNC_COUNTS.json','SUPPLEMENT_VERIFICATION.json','SUPPLEMENT_ARCHIVE_RESTORE.json','AUDIT_DECISION.json','BRIDGE_QUALIFICATION.json','BRIDGE_SCHEDULE.json','MECHANISM_SUPPLEMENT_SCHEDULE.json','DONE.json','REVIEW_REPORT.md']:
 shutil.copy2(ROOT/n,AUD/n)
for p in ROOT.glob('*.py'):shutil.copy2(p,AUD/'code'/p.name)
shutil.copytree(ROOT/'src',AUD/'code/src')
save(AUD/'DELIVERY_AMENDMENT.json',dict(utc=datetime.now(timezone.utc).isoformat(),reason='CPU-only report update after supplement sealing with actual archive SHA and restore receipt; preserve pre-seal report/decision in supplement archive. No raw/numeric/model changes.',source_archive_head=load(ROOT/'SUPPLEMENT_ARCHIVE_RESTORE.json')['source_head'],supplement_archive_sha256=load(ROOT/'SUPPLEMENT_ARCHIVE_RESTORE.json')['archive_sha256'],additional_model_forwards=0,private_report_sha256=sha(ROOT/'REVIEW_REPORT.md')))
with (DEST/'REPORT.md').open('a',encoding='utf-8',newline='\n') as f:
 f.write('\n## 2026-10-07 规范性审核及缺项补齐\n\n用户要求的独立规范性审核发现原机制selector仅检查C，未覆盖E失败，现以新冻结补充自然诊断补齐。原1,456核心和所有速度不变；增加18非热身+14热身，只作诊断，0新增正式性能样本。原机制GATED记录只适用于C，当前两个失败pair的真实logit/trace见 [规范性审核报告](normative_audit_20261007/REVIEW_REPORT.md)。前端显式同步调用数已按冻结源码/实际分支另行派生，内部同步仍未知。原包不变，补充包恢复通过；本审核最终远端回读完成后宣布本轮完整有限闭环。\n')
decision=load(DEST/'DECISION.json');decision['normative_audit']=dict(status='PASS_PENDING_REMOTE_READBACK',path='normative_audit_20261007/AUDIT_DECISION.json',core_audit_checks=load(ROOT/'CORE_REVIEW.json')['checks'],mechanism_current_status='COMPLETED_TRACE_DIAGNOSTIC',causal_status='NOT_CAUSALLY_IDENTIFIED',supplement_nonwarm=18,supplement_warm=14,original_raw=1961,total_raw=1993,new_performance_samples=0,original_archive_unchanged=True,remaining_core_experiments=[]);save(DEST/'DECISION.json',decision)
def manifest():save(DEST/'EVIDENCE_MANIFEST.json',dict(files={p.relative_to(DEST).as_posix():sha(p) for p in DEST.rglob('*') if p.is_file() and p.name!='EVIDENCE_MANIFEST.json'},raw_archive_sha256=load(ROOT/'AMENDMENT.json')['prior_archive_sha256'],supplement_archive_sha256=load(ROOT/'SUPPLEMENT_ARCHIVE_RESTORE.json')['archive_sha256'],scope='Only this study and normative supplement; no weights/runtime binaries/bulk raw telemetry',self_hash='Checked by fresh Git readback to avoid recursive self-hash'))
def commit_push(message):
 manifest();git('add','--',REL);changed=git('diff','--cached','--name-only').splitlines();assert changed and all(p.startswith(REL+'/') for p in changed) and REL+'/EXECUTION_PROMPT.md' not in changed
 git('commit','-m',message);head=git('rev-parse','HEAD');git('push','origin','HEAD:refs/heads/'+BRANCH);return head
head=commit_push('Audit B570 experimental compliance and close bounded natural-diagnostic omission')
spec=importlib.util.spec_from_file_location('transport',BASE/'publish_evidence.py');transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport);transport.ROOT=ROOT
receipt=transport.verify(head);save(ROOT/'AUDIT_REMOTE_READBACK.json',receipt);save(AUD/'REMOTE_READBACK.json',receipt)
ad=load(AUD/'AUDIT_DECISION.json');ad['status']='COMPLETE_FINITE_SCOPE_AUDITED';ad['remote_readback']='PASS';ad['verified_scientific_audit_head']=head;save(AUD/'AUDIT_DECISION.json',ad)
decision['normative_audit']['status']='PASS';decision['normative_audit']['verified_audit_head']=head;decision['closure']='COMPLETE_FINITE_SCOPE_AUDITED';save(DEST/'DECISION.json',decision)
with (AUD/'REVIEW_REPORT.md').open('a',encoding='utf-8',newline='\n') as f:f.write(f'\n## 最终交付已核验\n\n审核科学/派生提交 `{head}` 的全部{len(receipt["files"])}个研究文件，经全新Git存储从GitHub抓取、干净checkout与逐文件字节比对通过。**本平台本轮状态：COMPLETE_FINITE_SCOPE_AUDITED。可以宣布按PR #63 prompt的完整有限实验闭环。**原/补充包恢复通过，无剩余核心实验漏项，负结果及机制限制保留，Draft不合并。交付收据和manifest另提交后再次完整回读；最终提交身份见PR和本机final receipt。\n')
with (DEST/'REPORT.md').open('a',encoding='utf-8',newline='\n') as f:f.write('\n规范审核与缺项补齐完成，新增科学/派生证据GitHub完整字节回读通过。当前状态 **COMPLETE_FINITE_SCOPE_AUDITED**：本平台本轮按原prompt完整有限闭环，保留科学负结果与NOT_CAUSALLY_IDENTIFIED，不合并PR。\n')
finalhead=commit_push('Record audited B570 finite closure and successful complete GitHub readback')
final=transport.verify(finalhead);final.update(closure='COMPLETE_FINITE_SCOPE_AUDITED',prior_science_head=prior,original_archive_sha256=load(ROOT/'AMENDMENT.json')['prior_archive_sha256'],supplement_archive_sha256=load(ROOT/'SUPPLEMENT_ARCHIVE_RESTORE.json')['archive_sha256']);save(ROOT/'AUDIT_DELIVERY_VERIFIED.json',final)
print(dict(status=final['closure'],head=finalhead,remote_files=len(final['files']),raw=1993,PR='https://github.com/leecdiang/HeteroSpec/pull/63'),flush=True)
