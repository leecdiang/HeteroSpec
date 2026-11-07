"""Lossless offline delivery; flat KV originals are retained on the host."""
from host_b570 import *
import ast,base64,struct
import numpy as np
MIRROR=Path('E:/HeteroSpec/b570-phase1-delivery-source-20261107-v2')
PACK=Path('E:/HeteroSpec/b570-phase1-pack-20261107-v2')
REMOTE=Path('E:/HeteroSpec/b570-phase1-readback-20261107-v2')
RESTORED=Path('E:/HeteroSpec/b570-phase1-restored-20261107-v2')
TAG='b570-phase1-review-v2-evidence-20261107'
TITLE='B570 phase-one C1024 and C4096 review-v2 native evidence'
def codec_text():
 source=HERE.parent/'b570_decisive_v1/smol_state.py';text=source.read_text();node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='decode');decode='\n'.join(text.splitlines()[node.lineno-1:node.end_lineno]);assert decode.count('0<n<=1024')==1;decode=decode.replace('0<n<=1024','0<n<=4096')
 source2=HERE.parent/'b570_economics_v1/fast_storage.py';text=source2.read_text();node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='encode');encode='\n'.join(text.splitlines()[node.lineno-1:node.end_lineno])
 return 'import numpy as np,base64,struct\n'+decode+'\n\n'+encode+'\n',dict(decoder_sha256=sha(source),encoder_sha256=sha(source2),change='Only decoder capacity guard 1024 -> 4096; writer layout and bit patterns unchanged',native_arithmetic_changed=False)
def prepare():
 assert not nh.LOCK.exists() and (ROOT/'AUDIT.json').exists() and not MIRROR.exists()
 text,proof=codec_text();codec={};exec(text,codec);decode=codec['decode'];encode=codec['encode']
 delivery=ROOT/'delivery';delivery.mkdir();(delivery/'state_codec.py').write_text(text);write(delivery/'STATE_CODEC_SOURCE.json',proof)
 repo=ROOT/'repro/repository/benchmarks';repo.mkdir(parents=True,exist_ok=True)
 for source in (HERE,HERE.parent/'b570_economics_v1',HERE.parent/'b570_decisive_v1',HERE.parent/'tpds_decisive_v1'):shutil.copytree(source,repo/source.name,ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
 shutil.copytree(ECO/'repro/native-inputs/pr169-ggml',ROOT/'repro/pr169-ggml')
 for name in ('PR169_SOURCE_BINDING.json','PR169_LICENSE','PR169_CMakeLists.txt'):shutil.copyfile(ECO/'repro/native-inputs'/name,ROOT/'repro'/name)
 shutil.copyfile(OLD/'campaign02/runs/test-8-oldR/0.json',ROOT/'repro/OLD_EOG_CONTROL.json')
 for name in ('object_archive.py','recover_release.py','publish_delivery.py'):
  text=(ECO/'delivery'/name).read_text();text=text.replace('B570 native resident and target-parallel economics evidence',TITLE).replace('Independent B570 native economics result', 'Independent B570 phase-one review-v2 result').replace('b570-economics-native-evidence','b570-phase1-review-v2-native-evidence');(delivery/name).write_text(text)
 (delivery/'README.md').write_text((HERE/'REPRODUCE_B570.md').read_text())
 wrapper='''from pathlib import Path
import sys,json
root=Path(sys.argv[1]).resolve()
def confined(event,args):
 if event in ('subprocess.Popen','os.system','os.exec','os.posix_spawn'):raise RuntimeError('No process launch in evidence reconstruction')
 if event=='open' and args and isinstance(args[0],(str,bytes)) and str(args[0]).lower().endswith('.gguf'):raise RuntimeError('No model-weight access in evidence reconstruction')
sys.addaudithook(confined)
sys.path.insert(0,str(root/'repro/repository/benchmarks/tpds_phase1_v1'))
sys.path.insert(0,str(root/'delivery'))
from read_only_b570 import recompute
from state_codec import encode,decode
import hashlib,numpy as np
verified={};recipes=sorted(root.rglob('*.bin.pack.json'))
for p in recipes:
 m=json.loads(p.read_text());h=m['raw_sha256']
 if h in verified:continue
 chunks=[]
 for k in m['tokens']:
  data=(root/'state-token-cas'/k[:2]/k).read_bytes();assert len(data)==196608 and hashlib.sha256(data).hexdigest()==k;chunks.append(data)
 a=np.frombuffer(b''.join(chunks),dtype='<u2').reshape(len(chunks),24,4096);raw=encode(a,m['framing']);assert len(raw)==m['raw_bytes'] and hashlib.sha256(raw).hexdigest()==h
 back,_=decode(raw);assert np.array_equal(back,a);verified[h]=len(raw)
report=recompute(root);report['state_storage']={'recipes':len(recipes),'unique_serialized_states':len(verified),'unique_raw_bytes_reencoded':sum(verified.values()),'every_token_and_raw_state_authenticated':True}
with Path(sys.argv[2]).open('x') as f:json.dump(report,f,indent=2);f.write('\\n')
print('RESTORED_FULL_CPU_AUDIT_PASS',report['performance_slots'],len(recipes),len(verified))
''';(delivery/'recompute.py').write_text(wrapper)
 MIRROR.mkdir();cas=MIRROR/'state-token-cas';memo={};members=[];exclusions=[]
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(ROOT);isstate=False
  if p.suffix=='.bin':
   with p.open('rb') as f:isstate=f.read(4)==struct.pack('<I',0xaf143cd8)
  if isstate:
   h=sha(p)
   if h not in memo:
    raw=p.read_bytes();a,framing=decode(raw);assert encode(a,framing)==raw;tokens=[]
    for row in a:
     data=row.tobytes();k=hashlib.sha256(data).hexdigest();q=cas/k[:2]/k;q.parent.mkdir(parents=True,exist_ok=True)
     if not q.exists():q.write_bytes(data)
     tokens.append(k)
    memo[h]=dict(format='smol-dense-seq-token-pack-v2',raw_sha256=h,raw_bytes=len(raw),tokens=tokens,framing=framing,capacity_guard=4096)
   q=MIRROR/(str(rel)+'.pack.json');write(q,memo[h]);members.append(dict(path=rel.as_posix(),raw_sha256=h,raw_bytes=p.stat().st_size,recipe=str(rel).replace('\\','/')+'.pack.json'));continue
  # Exact formal link objects stay; other rebuildable intermediates are recorded.
  if p.suffix.lower() in ('.obj','.pdb','.ilk','.exp') and not (len(rel.parts)>2 and rel.parts[:2]==('native02','build01') and p.suffix.lower()=='.obj'):
   exclusions.append(dict(path=rel.as_posix(),bytes=p.stat().st_size,reason='regenerable non-formal build intermediate; source, commands and binaries retained'));continue
  if '__pycache__' in rel.parts or p.suffix.lower()=='.pyc':continue
  assert p.suffix.lower()!='.gguf';q=MIRROR/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 write(MIRROR/'STATE_STORAGE.json',dict(flat_states=members,original_flat_files_retained_on_host=True,unique_states=len(memo),decoder_source=proof,models_included=False))
 write(MIRROR/'DELIVERY_EXCLUSIONS.json',dict(regenerable_intermediates=exclusions,raw_KV='lossless authenticated token recipes, not deleted; full re-encoding checked by recompute.py'))
 print('DELIVERY_SOURCE_READY',len(members),'states',len(memo),'unique',flush=True)
def pack():
 sys.path.insert(0,str(MIRROR/'delivery'));import object_archive
 object_archive.pack(MIRROR,PACK)
 for name in ('object_archive.py','recompute.py','README.md'):shutil.copyfile(MIRROR/'delivery'/name,PACK/name)
 print(object_archive.verify(PACK),flush=True)
def publish(commit):
 sys.path.insert(0,str(MIRROR/'delivery'));import publish_delivery
 publish_delivery.run(PACK,REMOTE,TAG,commit)
def restore():
 sys.path.insert(0,str(MIRROR/'delivery'));import object_archive
 object_archive.restore(REMOTE,RESTORED)
 command([sys.executable,'-B',RESTORED/'delivery/recompute.py',RESTORED,RESTORED.parent/'b570-phase1-RESTORED_AUDIT-20261107-v2.json'],RESTORED.parent/'b570-phase1-restored-audit-20261107-v2.log')
if __name__=='__main__':
 started=time.monotonic();ok=False
 try:{'prepare':prepare,'pack':pack,'publish':publish,'restore':restore}[sys.argv[1]](*sys.argv[2:]);ok=True
 finally:write(ROOT.parent/('phase1-delivery-'+sys.argv[1]+'-'+str(time.time_ns())+'.json'),dict(success=ok,wall_seconds=time.monotonic()-started,model_requests=0,not_additive_to_native_cost=True))
