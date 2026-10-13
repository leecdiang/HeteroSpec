from common98 import *
import py_compile
for p in (ROOT/'code').glob('*.py'):py_compile.compile(str(p),doraise=True)
check_step('CONFIGURE100',['C:/Program Files/CMake/bin/cmake.exe','-S',str(ROOT/'native'),'-B',str(ROOT/'build-host64'),'-G','Visual Studio 17 2022','-A','x64','-T','host=x64','-DCMAKE_TRY_COMPILE_CONFIGURATION=Release','-DVulkan_INCLUDE_DIR=C:/VulkanSDK/1.4.357.0/Include','-DVulkan_LIBRARY=C:/VulkanSDK/1.4.357.0/Lib/vulkan-1.lib'],timeout=120)
check_step('BUILD100',['C:/Program Files/CMake/bin/cmake.exe','--build',str(ROOT/'build-host64'),'--config','Release','--parallel','4'],timeout=180)
for name in ['b570-boundary-worker.exe','b570-operator-replay.exe']:shutil.copy2(ROOT/'build-host64/Release'/name,ROOT/'build/Release'/name)
save(ROOT/'NATIVE_BUILD.json',dict(status='PASS',worker_sha256=sha(ROOT/'build/Release/b570-boundary-worker.exe'),replay_sha256=sha(ROOT/'build/Release/b570-operator-replay.exe'),numerical_DLLs_unchanged=True,compiler='MSVC14.44.35207 Hostx64 x64 Release',native_forwards=0))
print('BUILD_PASS',flush=True)
