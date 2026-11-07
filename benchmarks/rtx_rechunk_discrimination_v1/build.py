"""Only synchronized phase boundaries and setup accounting differ from PR174."""
from host import *
import difflib
def main():
    old=OLD/'candidate07';binding=read(old/'binding.json');base=old/'compiled-source.cpp';assert sha(base)==binding['source']
    s=base.read_text(encoding='utf8');original=s
    replacements={
      'double import_s=seconds(t);':'llama_synchronize(c);auto phase_ready=Clock::now();double import_s=std::chrono::duration<double>(phase_ready-t).count();',
      'double append_s=seconds(t);':'llama_synchronize(c);auto append_done=Clock::now();double append_s=std::chrono::duration<double>(append_done-t).count();',
      'double service=seconds(t);':'auto response_done=Clock::now();double service=std::chrono::duration<double>(response_done-t).count();',
      '{"service_s",service},':'{"service_s",service},{"lookup_import_ready_s",std::chrono::duration<double>(phase_ready-t).count()},{"append_execution_s",std::chrono::duration<double>(append_done-phase_ready).count()},{"continuation_s",std::chrono::duration<double>(response_done-append_done).count()},',
      'check(bool(ctx),"context");':'check(bool(ctx),"context");save(out/"context_init.json",{{"seconds",seconds(t)}});'
    }
    for a,b in replacements.items():assert s.count(a)==1,a;s=s.replace(a,b)
    (HERE/'worker.cpp').write_bytes(s.encode());(HERE/'timing-only.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='PR174-worker_service.cpp',tofile='worker.cpp')),encoding='utf8')
    out=ROOT/'candidate01';out.mkdir();shutil.copy2(HERE/'worker.cpp',out/'compiled-source.cpp')
    for name,h in binding['modules'].items():assert sha(old/name)==h;shutil.copy2(old/name,out/name)
    commands=[]
    for i,cmd in enumerate(binding['commands']):
        cmd=[str(HERE/'worker.cpp') if x.endswith('worker_service.cpp') else x.replace(str(old),str(out)) for x in cmd];commands.append(cmd)
        t=time.monotonic()
        with (out/f'build-{i}.log').open('xb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=600)
        put(out/f'build-{i}.json',dict(argv=cmd,code=r.returncode,seconds=time.monotonic()-t));r.check_returncode()
    put(out/'binding.json',dict(commands=commands,source=sha(HERE/'worker.cpp'),exe=sha(out/'worker.exe'),core=binding['core'],modules=binding['modules'],parent_source=binding['source']))
    f=read(OLD/'SOURCE_POLICY_FREEZE.json');assert sha(MODEL)==f['model_sha256']
    put(ROOT/'INHERITED_IDENTITY.json',dict(parent_commit='aa7ff4e64752be3de0d7974febbce453ae3a96c0',design_head='6987317a4a4d4495fa9f1543bf922d978e13d4f8',model_sha256=f['model_sha256'],tokenizer_identity=f['native_tokenizer_identity'],original_oracle=read(OLD/'oracle02/binding.json'),original_candidate=binding,new_candidate=read(out/'binding.json'),no_numeric_or_caller_change=True))
if __name__=='__main__':main()
