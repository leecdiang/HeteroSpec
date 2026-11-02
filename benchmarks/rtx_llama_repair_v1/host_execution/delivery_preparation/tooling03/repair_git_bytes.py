from pathlib import Path
import json,subprocess,hashlib,datetime
root=Path('E:/rtx160/transport01');base=Path('benchmarks/rtx_llama_repair_v1/host_execution/records');index=json.loads((base/'INDEX.json').read_text(encoding='utf-8'))['files'];m=[];missing=[]
for e in index:
 p=base/e['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256']
 r=subprocess.run(['git','show','HEAD:'+p.as_posix()],capture_output=True)
 if r.returncode:missing.append(p.as_posix())
 elif hashlib.sha256(r.stdout).hexdigest()!=e['sha256']:m.append(e['path'])
allowed={str(base/'operations/TOKENIZED_POOL01.json').replace('\\','/'),str(base/'tokenization/COUNTS.json').replace('\\','/'),str(base/'tokenization/TOKENIZATION_RECEIPT.json').replace('\\','/')}
assert set(missing)==allowed,missing
p=Path('.gitattributes');data=p.read_bytes();addition=b'\n# Llama repair evidence and executed source have byte-addressed identities.\nscripts/experiments/rtx_llama_repair_v1/** -text\nbenchmarks/rtx_llama_repair_v1/** -text\nbenchmarks/rtx_llama_repair_v1/host_execution/** whitespace=cr-at-eol\nbenchmarks/rtx_llama_repair_v1/host_execution/**/*.log -whitespace\nbenchmarks/rtx_llama_repair_v1/host_execution/**/*.diff -whitespace\n'
assert b'# Llama repair evidence and executed source' not in data;p.write_bytes(data+addition)
subprocess.run(['git','add','--','.gitattributes'],check=True)
subprocess.run(['git','add','-f','--',*missing],check=True)
subprocess.run(['git','add','--renormalize','--','scripts/experiments/rtx_llama_repair_v1','benchmarks/rtx_llama_repair_v1'],check=True)
for e in index:
 p=base/e['path'];b=subprocess.run(['git','show',':'+p.as_posix()],capture_output=True,check=True).stdout
 assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256'],str(p)
files=subprocess.run(['git','ls-files','-z','--','scripts/experiments/rtx_llama_repair_v1','benchmarks/rtx_llama_repair_v1'],capture_output=True,check=True).stdout.decode().split('\0');count=0
for name in filter(None,files):
 p=Path(name);b=subprocess.run(['git','show',':'+name],capture_output=True,check=True).stdout;assert b==p.read_bytes(),name;count+=1
report={'status':'ALL_SCIENTIFIC_RECEIPTS_AND_STAGED_STUDY_SOURCES_BYTE_EXACT','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scientific_receipts':len(index),'previous_git_eol_mismatches':m,'previously_ignored_receipts_restored':missing,'all_study_files_verified':count,'working_native_sources_changed':False,'raw_archive_changed':False,'native_requests_added':0,'explanation':'Disable Git EOL filtering, retain original working bytes, and explicitly track three non-secret tokenizer receipts matched by broad token* ignore. Earlier commits and immutable raw capsule retained; no numerical working source edit or experiment rerun.'}
(root/'STUDY_GIT_BYTE_EXACT_REPAIR.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('PASS',count,'files;',len(index),'scientific receipts;',len(m),'prior EOL differences;',len(missing),'restored receipts')
