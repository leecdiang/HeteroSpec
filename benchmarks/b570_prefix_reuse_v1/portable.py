"""Stage source and a small native fixture independent of source-host paths."""
from host import *
def stage():
 out=ROOT/'portable-final';out.mkdir()
 shutil.copytree(ROOT/'source-00',out/'candidate-source')
 shutil.copytree(ORACLE/'clean-source2/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2',out/'original-source')
 for label,base in [('candidate',OLD/'build-00'),('original',ORACLE/'build')]:
  for rel in ('runtime/ggml/src/Release','runtime/src/Release','bin/Release'):
   dest=out/'historical-libs'/label/rel;dest.mkdir(parents=True)
   for p in (base/rel).iterdir():
    if p.suffix.lower() in ('.lib','.dll'):shutil.copyfile(p,dest/p.name)
 code=out/'adapter';code.mkdir()
 for p in HERE.iterdir():
  if p.is_file():shutil.copyfile(p,code/p.name)
 # A genuinely executed calibration path; no special padded/crossing fixture.
 panel=read(ROOT/'panel.json');row=next(r for r in read(ROOT/'manifest.json')['rows'] if r['id']==panel['calibration'][0]['id'])
 write(out/'fixture.json',row)
 for name in ('CMakeLists.txt','worker.cpp','allocator_probe.cpp','companion_scope.cpp','companion_scope.hpp'):assert (code/name).is_file()
 write(out/'PORTABLE_MANIFEST.json',dict(utc=utc(),source_design_head='bba256cf04bbd2038029fd59447df9722b24c197',scientific_ancestor='8ca17478c292275b3515a91b51d0e791a8fae256',model_sha256=read(ROOT/'INHERITED_AUTHENTICATION.json')['model']['sha256'],files=[dict(path=p.relative_to(out).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()],native_external_replication=False))
if __name__=='__main__':stage()
