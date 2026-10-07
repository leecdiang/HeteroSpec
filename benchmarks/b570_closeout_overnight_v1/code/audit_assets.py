from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).parent
OLD=Path('C:/hs/b570-prefill-v1')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
old=json.loads((OLD/'benchmarks/b570_prefill_diagnostic_v1/ASSET_MANIFEST.json').read_text(encoding='utf-8-sig'))
checked={};fail=[]
for name,h in old['files'].items():
 p=Path(name)
 if not p.exists():fail.append({'file':name,'error':'missing'});continue
 actual=sha(p);checked[name]={'sha256':actual,'bytes':p.stat().st_size}
 if actual!=h:fail.append({'file':name,'expected':h,'actual':actual})
for p in list((ROOT/'src').glob('*'))+list((ROOT/'build/Release').glob('*.exe'))+list((ROOT/'build/Release').glob('*.dll')):
 if p.is_file():checked[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
env=json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',"[Console]::OutputEncoding=[Text.UTF8Encoding]::new();[ordered]@{os=(Get-CimInstance Win32_OperatingSystem|Select-Object Caption,Version,BuildNumber);gpu=@(Get-CimInstance Win32_VideoController|Select-Object Name,DriverVersion);vulkan_runtime=(Get-Item C:\\Windows\\System32\\vulkan-1.dll).VersionInfo.FileVersion}|ConvertTo-Json -Depth 5"],encoding='utf-8-sig'))
archive=OLD/'artifacts/b570_prefill_diagnostic_v1/capsule/raw-capsule-v1.tar.gz'
checked[str(archive)]={'sha256':sha(archive),'bytes':archive.stat().st_size,'dependency':'immutable old capsule; not duplicated'}
if checked[str(archive)]['sha256']!='4ce6f65211c2847088ca4318746d47da369ea7596a88469be11c0e6aaecc5896':fail.append({'file':str(archive),'error':'old archive hash'})
result={'status':'PASS' if not fail else 'FAIL','checked':checked,'failures':fail,'environment':env,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'historical_environment':old['environment'],'unknown':['opaque sampler byte authentication','driver package digest','unique Vulkan kernel dispatch'],'model_forwards':0}
dest=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'ASSET_MANIFEST.json')
if dest.exists():raise RuntimeError('Refuse to overwrite asset snapshot')
dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print({'status':result['status'],'checked':len(checked),'failures':fail,'environment':env},flush=True)
