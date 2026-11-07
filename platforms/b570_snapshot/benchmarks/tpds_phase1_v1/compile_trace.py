"""Record the actual compiler invocation and MSVC-produced dependency closure."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
args=sys.argv[1:]
source=next(x for x in args if x.lower().endswith('.cpp'))
root=Path(os.environ['PHASE1_DEPS']);root.mkdir(parents=True,exist_ok=True)
key=hashlib.sha256(json.dumps([os.getcwd(),args]).encode()).hexdigest()[:20]
report=root/(key+'.dependencies.json')
argv=args+['/sourceDependencies',str(report)]
(root/(key+'.command.json')).write_text(json.dumps(dict(argv=argv,cwd=os.getcwd(),source=str(Path(source).resolve()),environment={k:v for k,v in os.environ.items() if k in ('PATH','INCLUDE','LIB','LIBPATH','VULKAN_SDK','VSLANG')}),indent=2))
raise SystemExit(subprocess.call(argv))
