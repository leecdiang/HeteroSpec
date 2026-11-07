"""Package already compiled portable source/fixture; no additional native request."""
from host import *
import zipfile

def pack():
 kit=ROOT/'portable-final';output=ROOT/'b570-prefix-native-source-kit.zip'
 guide='''# B570 frozen native source and fixture

This is the candidate03 source used by B570 result PR175, plus the independent
original scalar source and PR169 historical libraries. The exact portable layout
was compiled successfully for both variants on the source host. This is not an
external native replication claim. The earlier progress README under adapter is
the source snapshot's documentation; consult PR175 for completed study results.

Requirements: Windows x64, Visual Studio 2022 C++ tools, CMake, an Intel Arc B570
with the recorded Vulkan driver, and independently obtained Qwen3-8B Q8_0 model
SHA256 408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6.
No model weights are included. Original driver: 32.0.101.9150.

Configure using absolute paths for LLAMA_SOURCE and HISTORICAL_LIBS:

    cmake -S portable-final/adapter -B candidate-build -G "Visual Studio 17 2022" -A x64 -DCANDIDATE=ON -DLLAMA_SOURCE=ABS/portable-final/candidate-source -DHISTORICAL_LIBS=ABS/portable-final/historical-libs/candidate
    cmake --build candidate-build --config Release --parallel 4

For the original, set CANDIDATE=OFF and use original-source plus original libs.
Copy all corresponding historical bin/Release DLLs next to frontier.exe. For the
candidate replace only llama.dll with candidate-build/runtime/src/Release/llama.dll.
The unchanged Vulkan/ggml arithmetic is supplied by the authenticated historical
DLLs. The complete source of these libraries is included for inspection.

fixture.json supplies a real calibration request and cached history token array.
The worker accepts frontier.exe JOB.json FRESH_OUTPUT_DIRECTORY. A seed slot with
ids=request_ids and heads=[effective_head] produces the scalar prefix snapshot;
service slots reference that snapshot by key/path/head/SHA256. Complete executed
JOB.json and supervisor commands are in the raw release's units directories.
Rebind target, snapshot, output and vector-store paths on the receiving machine.
Rebuild its runtime manifest and run through the supplied Windows Job supervisor;
never reuse source-host loaded-file attestations as evidence for another host.

Every model request in a replication is new work; this package does not run any.
Keep the original scalar reference separate from candidate outputs and retain
failed attempts. This kit is an exact frozen source snapshot, not a request to
retune the completed test panel or repeat formal timing for a better mean.
'''
 with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
  archive.writestr('README.md',guide)
  archive.write(ROOT/'portable-build-proof/BUILD_RECEIPT.json','BUILD_RECEIPT.json')
  for p in sorted(kit.rglob('*')):
   if p.is_file():archive.write(p,'portable-final/'+p.relative_to(kit).as_posix())
 with zipfile.ZipFile(output) as archive:assert archive.testzip() is None
 write(ROOT/'PORTABLE_ZIP_RECEIPT.json',dict(utc=utc(),name=output.name,bytes=output.stat().st_size,sha256=sha(output),portable_manifest_sha256=sha(kit/'PORTABLE_MANIFEST.json'),zip_crc_readback=True,native_build_receipt_sha256=sha(ROOT/'portable-build-proof/BUILD_RECEIPT.json'),model_requests=0,external_native_replication=False))

if __name__=='__main__':pack()
