from common98 import *
OLD=ROOT.parent/'b570-phasebinding-boundary-v1'
for name,argv in [
 ('CMAKE_CONFIGURE',['C:/Program Files/CMake/bin/cmake.exe','-S',str(ROOT/'native'),'-B',str(ROOT/'build-host64'),'-G','Visual Studio 17 2022','-A','x64','-T','host=x64','-DCMAKE_TRY_COMPILE_CONFIGURATION=Release','-DVulkan_INCLUDE_DIR=C:/VulkanSDK/1.4.357.0/Include','-DVulkan_LIBRARY=C:/VulkanSDK/1.4.357.0/Lib/vulkan-1.lib']),
 ('CMAKE_BUILD',['C:/Program Files/CMake/bin/cmake.exe','--build',str(ROOT/'build-host64'),'--config','Release','--parallel','4'])]:check_step(name,argv,timeout=240)
shutil.copy2(ROOT/'build-host64/Release/b570-boundary-worker.exe',ROOT/'build/Release/b570-boundary-worker.exe')
pin=load(ROOT/'baseline/PR97_ASSET_PREFLIGHT.json')['models'][0]
assert TARGET.stat().st_size==pin['bytes'] and sha(TARGET)==pin['sha256']
mods=[]
for p in (ROOT/'build/Release').glob('*.dll'):
 assert p.read_bytes()==(OLD/'build/Release'/p.name).read_bytes()
 mods.append(dict(path=str(p.relative_to(ROOT)).replace(chr(92),'/'),bytes=p.stat().st_size,sha256=sha(p)))
save(ROOT/'ASSET_PREFLIGHT.json',dict(status='PASS',models=[pin],numeric_DLLs_unchanged=True,modules=mods,new_model_forwards=0,parent_head='5a66653bd0ce413d4eb9aef3a4501b93c138071b',utc=now()))
save(ROOT/'NATIVE_BUILD.json',dict(status='PASS',only_frontend_changed=True,numeric_DLLs_unchanged=True,worker_sha256=sha(ROOT/'build/Release/b570-boundary-worker.exe'),source_sha256=sha(ROOT/'native/worker.cpp'),parent_worker_sha256=sha(ROOT/'baseline/worker97.cpp'),utc=now()))
print('BUILD_ASSETS_PASS',flush=True)
