"""Publish only after the complete transport chain passes; no native work or merge."""
import datetime,json,os,subprocess,sys,time
from pathlib import Path
root=Path('E:/rtx160/transport01');ops=Path('D:/rtx160/operations');repo=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr160')
policy=json.loads((root/'TRANSPORT_RESOURCE_POLICY02.json').read_text(encoding='utf-8'))
deadline=datetime.datetime.fromisoformat(policy['overall_deadline_utc'])
receipt=ops/'DELIVERY_FINISH08.json'
while not receipt.exists():
 assert datetime.datetime.now(datetime.timezone.utc)<deadline,'finite cumulative transport gate wait expired'
 time.sleep(5)
assert json.loads(receipt.read_text(encoding='utf-8'))['exit_code']==0,'Delivery gate failed; no publication'
command=[sys.executable,'-B',str(ops/'run_logged.py'),'PUBLISH_EVIDENCE01',sys.executable,'-B',str(repo/'benchmarks/rtx_llama_repair_v1/host_execution/publish_delivery.py'),'--archive','F:/rtx160/archive01','--transport',str(root),'--notes',str(root/'RELEASE_NOTES.md'),'--out',str(root/'publication01'),'--tag','rtx-llama-repair-v1-evidence-20261102','--snapshot','70086c63af202cd844a3062eff3929218152f73c','--release-id','431658377']
subprocess.run(command,cwd=repo,env=dict(os.environ,GODEBUG='http2client=0',PYTHONUTF8='1'),check=True)
assert json.loads((root/'publication01/PUBLICATION.json').read_text(encoding='utf-8'))['status']=='PUBLISHED_PRIVATE_RELEASE_AND_AUTHENTICATED_INDEX_READBACK_PASS'
print('VERIFIED_EVIDENCE_PUBLISHED_RESULT_PR_REMAINS_DRAFT',flush=True)
