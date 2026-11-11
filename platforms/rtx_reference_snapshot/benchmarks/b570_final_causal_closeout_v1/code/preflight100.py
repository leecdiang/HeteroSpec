from common98 import *
import winreg
assert not (ROOT/'STUDY_STARTED.json').exists()
# Live driver inventory without model loads.
q='[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); @(Get-CimInstance Win32_VideoController | Select-Object Name,PNPDeviceID,DriverVersion,DriverDate) | ConvertTo-Json -Depth 5'
p=subprocess.run([str(PS),'-NoProfile','-NonInteractive','-Command',q],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=45)
(ROOT/'versions/LIVE_HOST.stdout').write_bytes(p.stdout);(ROOT/'versions/LIVE_HOST.stderr').write_bytes(p.stderr);assert p.returncode==0
gpu=json.loads(p.stdout.decode('utf-8-sig'));assert any('DEV_E20C' in x['PNPDeviceID'] and x['DriverVersion']=='32.0.101.9034' for x in gpu)
p=subprocess.run(['C:/VulkanSDK/1.4.357.0/Bin/vulkaninfoSDK.exe','--json'],cwd=ROOT/'versions',capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=45)
(ROOT/'versions/VULKANINFO.stdout').write_bytes(p.stdout);(ROOT/'versions/VULKANINFO.stderr').write_bytes(p.stderr);assert p.returncode==0
files=list((ROOT/'versions').glob('VP_VULKANINFO*.json'));assert files
icds=[]
for hive,path in [(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Khronos\Vulkan\Drivers')]:
 try:
  key=winreg.OpenKey(hive,path)
  for i in range(winreg.QueryInfoKey(key)[1]):
   name,value,typ=winreg.EnumValue(key,i)
   f=Path(name)
   if f.exists():
    d=load(f);dll=Path(d['ICD']['library_path']);dll=dll if dll.is_absolute() else f.parent/dll
    icds.append(dict(manifest=str(f),manifest_sha256=sha(f),DLL=str(dll),DLL_sha256=sha(dll),value=value))
 except FileNotFoundError:pass
models=load(ROOT/'baseline/pr99/ASSET_PREFLIGHT.json')['models']
for x in models:assert TARGET.stat().st_size==x['bytes'] and sha(TARGET)==x['sha256']
dlls=load(ROOT/'baseline/pr99/ASSET_PREFLIGHT.json')['modules']
for x in dlls:assert sha(ROOT/x['path'])==x['sha256']
dump='C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/dumpbin.exe'
for name in ['llama-b570-memory.dll','ggml-base.dll','ggml-vulkan.dll']:
 p=subprocess.run([dump,'/exports',str(ROOT/'build/Release'/name)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
 (ROOT/'versions'/(name+'.exports.txt')).write_bytes(p.stdout);assert p.returncode==0
save(ROOT/'HOST_ADMISSION.json',dict(status='PASS_CPU_ASSET_INSPECTION_NATIVE_ADMISSION_PENDING',gpu=gpu,ICDs=icds,vulkaninfo_files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in files],forward_calls=0))
save(ROOT/'ASSET_PREFLIGHT.json',dict(status='PASS',models=models,modules=dlls,numeric_DLLs_unchanged=True,new_model_forwards=0,design_head='a1925c4a3b040f9ad3db7ec4301042791a82fe75'))
save(ROOT/'F0_RESTORE.json',dict(before_import=True,native_starts=0,contract='BOUNDARY0_COMPLETE_NECESSARY_STATE_EQUIVALENCE_NOT_GENERAL_OPAQUE_CLONE',retained=['all32F16K +32F16V tensors, sequencecell metadata and positions','full ordered128256 FP32 initial logits','stateless native greedy apply +accept ownership','empty committedprefix; first natural token pending and consumed once','UB512/capacity1 clean native receiver scheduler/context reservation','completed queue sync before import; fresh KV clean; readback and exact reserialization; first continuation atN'],omitted_but_reconstructed=['old dynamicoutput_ids/logits buffer replaced by source-equivalent native samplerapply of fullFP32; row0 recreated on first continuation','old graphcache/allocator reused pointers deliberately notcopied; receiver independently initialized identical UB512/context','greedy has no stochastic or acceptance state'],source=['baseline/source/llama-context.cpp','baseline/source/llama-context.h','baseline/source/llama-kv-cache.cpp','baseline/source/llama-sampler.cpp'],hard_gate='Every16 P0 ownpath completeendpoint andrawKV/logits/positions/sampler passes; otherwiseblockall40P2. No hidden forward/no suffix forcing.',invalid_injection_tests=['wrong source hash','croppedFP32vector','NaNFP32','KVmagic','badcellposition','noncontiguous promptpositions','missing P0 donor','wrong first consumed token']))
save(ROOT/'F0_P3.json',dict(status='GPU_TIMELINE_NOT_AVAILABLE',attempted_admission=True,native_P3_starts=0,bounded_metadata_bytes=67108864,reason='Pinned public Vulkan backend API exposes no raw queue/commandbuffer/querypool timestamps. Inspected local Vulkan source has performance logger with fence wait/query but exports aggregated duration log only, discards absolute timestamps and queue/fusion identity; cannot construct required queue interval/overlap timeline without unverified numerical backend substitution. Local source lineage not independently certified; no claim to exact shader identity.',source_file='baseline/source/ggml-vulkan.inspected.cpp',source_sha256=sha(ROOT/'baseline/source/ggml-vulkan.inspected.cpp'),public_header_sha256=sha(ROOT/'baseline/source/ggml-vulkan.h'),export_evidence='versions/ggml-vulkan.dll.exports.txt',CPU_vulkaninfo='HOST_ADMISSION.json',old_stage_wall='MODEL_TIMING_UNAVAILABLE',no_new_ETW_or_API_dump=True))
print('PREFLIGHT_PASS',len(files),flush=True)
