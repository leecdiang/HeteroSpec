"""Reuse PR187's object transport for only the new experiment and source inputs."""
from native_host import *
PACK=Path('E:/HeteroSpec/b570-economics-pack-20261106')
REMOTE=Path('E:/HeteroSpec/b570-economics-readback-20261106')
RESTORED=Path('E:/HeteroSpec/b570-economics-restored-20261106')
TAG='b570-economics-v1-evidence-20261106'
TITLE='B570 native resident and target-parallel economics evidence'

def inputs():
 assert not LOCK.exists() and (ROOT/'DEVELOPMENT_DECISION.json').exists()
 deps=ROOT/'repro/native-inputs';assert not deps.exists();deps.mkdir(parents=True)
 old=OSMOL/'portable';pin=read(old/'INPUTS.json')
 for f in pin['files']:
  p=old/f['path'];assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256']
 shutil.copytree(old/'source',deps/'source');shutil.copytree(old/'libs',deps/'libs')
 (deps/'generated').mkdir();shutil.copyfile('C:/hs/b570-direct-id-v1-build/src/llama-version.h',deps/'generated/llama-version.h')
 # Capture the exact inherited backend implementation and its shader sources.
 par=Path('I:/HeteroSpec/b570-parallel-20261103');proof=read(par/'SOURCE_BINDING-candidate-D.json')
 for path,h in proof['compiled_source'].items():assert sha(par/'source-00'/path)==h
 shutil.copytree(par/'source-00/ggml',deps/'pr169-ggml',ignore=shutil.ignore_patterns('.git','build','__pycache__'))
 shutil.copyfile(par/'SOURCE_BINDING-candidate-D.json',deps/'PR169_SOURCE_BINDING.json')
 for n in ('LICENSE','CMakeLists.txt'):
  p=par/'source-00'/n
  if p.exists():shutil.copyfile(p,deps/('PR169_'+n))
 write(deps/'INPUTS.json',dict(files=[dict(path=p.relative_to(deps).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(deps.rglob('*')) if p.is_file()],PR187_portable_inputs_sha256=sha(old/'INPUTS.json'),PR169_binding_sha256=sha(par/'SOURCE_BINDING-candidate-D.json'),models_included=False))

def prepare():
 assert not LOCK.exists() and (ROOT/'AUDIT.json').exists()
 repo=ROOT/'repro/repository/benchmarks';repo.mkdir(parents=True)
 for source in (HERE,PREVIOUS,TOOLKIT):shutil.copytree(source,repo/source.name,ignore=shutil.ignore_patterns('__pycache__'))
 transport=ROOT/'delivery';transport.mkdir()
 for name in ('object_archive.py','recover_release.py','publish_delivery.py'):
  text=(OLD/'delivery-v2'/name).read_text(encoding='utf-8')
  text=text.replace('B570 PR185 repair continuation and Smol native evidence',TITLE).replace('B570 PR185 result','B570 native economics result').replace('b570-decisive-native-evidence','b570-economics-native-evidence')
  (transport/name).write_text(text,encoding='utf-8',newline='\n')
 wrapper='''import os,sys,json
from pathlib import Path
root=Path(sys.argv[1]).resolve();prior=Path(sys.argv[2]).resolve()
os.environ['HS_ECON_ROOT']=str(root);os.environ['HS_ECON_PR187']=str(prior);os.environ['HS_DECISIVE_ROOT']=str(prior)
historical=[Path(p).resolve() for p in ('I:/HeteroSpec/b570-economics-20261106','I:/HeteroSpec/b570-decisive-20261105','E:/HeteroSpec/b570-decisive-recovery-restored-20261105')]
def confined(event,args):
 if event in ('subprocess.Popen','os.system','os.exec','os.posix_spawn'):raise RuntimeError('Native/process launch refused during read-only reconstruction')
 if event!='open' or not isinstance(args[0],(str,bytes,os.PathLike)):return
 p=Path(os.fsdecode(args[0])).resolve()
 if p.suffix.lower()=='.gguf':raise RuntimeError('Model-weight access refused during read-only reconstruction')
 if any(p==r or r in p.parents for r in (root,prior)):return
 if any(p==r or r in p.parents for r in historical):raise RuntimeError('Original-host evidence fallback refused: '+str(p))
sys.addaudithook(confined)
sys.path.insert(0,str(root/'repro/repository/benchmarks/b570_economics_v1'))
from audit_host import audit
print(json.dumps(audit(),indent=2))
'''
 (transport/'recompute.py').write_text(wrapper,encoding='utf-8',newline='\n')
 shutil.copyfile(HERE/'REPRODUCE.md',transport/'README.md')

def pack():
 assert not LOCK.exists();sys.path.insert(0,str(ROOT/'delivery'));import object_archive
 object_archive.pack(ROOT,PACK)
 for name in ('object_archive.py','recompute.py','README.md'):shutil.copyfile(ROOT/'delivery'/name,PACK/name)
 print(json.dumps(object_archive.verify(PACK)),flush=True)

def publish(commit):
 sys.path.insert(0,str(ROOT/'delivery'));import publish_delivery
 publish_delivery.run(PACK,REMOTE,TAG,commit)

def restore():
 sys.path.insert(0,str(ROOT/'delivery'));import object_archive
 object_archive.restore(REMOTE,RESTORED)

if __name__=='__main__':
 action=sys.argv[1];started=utc();wall=time.monotonic();ok=False
 try:
  if action=='publish':publish(sys.argv[2])
  else:{'inputs':inputs,'prepare':prepare,'pack':pack,'restore':restore}[action]()
  ok=True
 finally:write(ROOT.parent/('b570-economics-delivery-'+action+'-'+started.replace(':','').replace('.','')+'.json'),dict(started_utc=started,finished_utc=utc(),wall_seconds=time.monotonic()-wall,success=ok,model_requests=0,not_additive_to_experiment_native_or_service=True))
