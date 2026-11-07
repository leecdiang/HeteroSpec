"""Compile the delivered source-layout independently; performs no model request."""
from host import *

def check():
 kit=ROOT/'portable-final';proof=ROOT/'portable-build-proof';proof.mkdir()
 for role in ('candidate','original'):
  out=proof/role/'build';out.parent.mkdir()
  command(['cmake','-S',kit/'adapter','-B',out,'-G','Visual Studio 17 2022','-A','x64','-DCANDIDATE='+('ON' if role=='candidate' else 'OFF'),'-DLLAMA_SOURCE='+(kit/(role+'-source')).as_posix(),'-DHISTORICAL_LIBS='+(kit/'historical-libs'/role).as_posix()],out.parent/'configure.log')
  command(['cmake','--build',out,'--config','Release','--parallel','4'],out.parent/'compile.log')
  assert (out/'Release/frontier.exe').is_file()
 write(proof/'BUILD_RECEIPT.json',dict(utc=utc(),status='PORTABLE_LAYOUT_BOTH_NATIVE_BUILDS_SUCCEEDED',manifest_sha256=sha(kit/'PORTABLE_MANIFEST.json'),candidate_exe_sha256=sha(proof/'candidate/build/Release/frontier.exe'),original_exe_sha256=sha(proof/'original/build/Release/frontier.exe'),model_requests=0,same_host_compile=True,external_native_replication=False,scope='Source and library paths bound only within delivered portable-final layout; compiler/system dependencies remain external. No additional model forward or timing.'))

if __name__=='__main__':check()
