"""Post-build disk metadata only; does not load or call a numerical DLL."""
from pathlib import Path
import collections,hashlib,json,shutil

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze_path=ROOT/'e04/freeze/v2/FREEZE.json';freeze=json.loads(freeze_path.read_bytes());build=HERE/'build-v2'
source=HERE/'source-v1';source_rows={str(Path(p).relative_to(source)).replace('\\','/'):r['sha256'] for p,r in freeze['inputs'].items() if source in Path(p).parents}
receipt={'schema':'heterospec.e04.complete-source-receipt.v1','source_files':len(source_rows),'extensions':dict(sorted(collections.Counter(Path(p).suffix.lower() for p in source_rows).items())),'source_files_sha256':source_rows,'freeze_sha256':sha(freeze_path),'numerical_source_equals_e03_uniform_tree':source_rows==json.loads((HERE/'inputs/e03_FINAL_SOURCE_IDENTITIES.json').read_bytes())['source_files_sha256'],'e03_caveat':'e03 initial CUDA-only catalog omitted non-CUDA .h and provider sync timing was not recorded; those historical limits remain. e04 fresh batch uses this new complete source/dependency freeze.'}
(HERE/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
state=json.loads((HERE/'link-v3/BUILD.json').read_bytes())
if state['status']!='NUMERICAL_DLL_LINKED_NOT_LOADED_NOT_QUALIFIED':raise SystemExit('link continuation not successful')
dll=HERE/'link-v3/bin/ggml-cuda.dll'
resources={'schema':'heterospec.e04.compiler-resource-availability.v1','kind':'UNKNOWN_NO_FRESH_RESOURCE_MEASUREMENT','DLL_sha256':sha(dll),'registers':'unknown','shared_memory':'unknown','stack':'unknown','spill':'unknown','occupancy':'unknown','DRAM':'unknown','L2':'unknown','latency':'unknown','model_requests':0,'GPU_launches':0,'numerical_DLL_loaded':False,'limit':'Main frozen compilation used original numerical flags without ptxas verbose; portable toolkit has no cuobjdump. No extra assembly replay or GPU APIs. Historical e03 resource numbers are not attributed to this DLL.'}
(HERE/'COMPILER_RESOURCES.json').write_text(json.dumps(resources,indent=2),encoding='utf8')
subcommands=HERE/'compiler-subcommands';subcommands.mkdir(exist_ok=False);copied=[]
for p in sorted((build/'generated').rglob('*.res')):
 dest=subcommands/p.relative_to(build/'generated');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 copied.append({'generated':str(p),'copied':str(dest),'sha256':sha(p)})
(subcommands/'MANIFEST.json').write_text(json.dumps({'kind':'ACTUAL_NVCC_RETAINED_RESPONSE_FILES','files':copied},indent=2),encoding='utf8')
print(json.dumps({'source_files':len(source_rows),'header_h_files':receipt['extensions'].get('.h',0),'resource_attributes':'unknown','actual_nvcc_response_files':len(copied),'DLL_sha256':sha(dll)}))
