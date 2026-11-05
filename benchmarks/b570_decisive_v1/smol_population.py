"""Retain/recompute the full natural population, not just selected input IDs."""
from smol import *
from design import select

def retain():
 pool=Path('I:/HeteroSpec/b570-prefix-reuse-20261104');dest=SROOT/'provenance/corpus';dest.mkdir()
 for n in ('messages.jsonl.gz','paths.jsonl','EXPOSURE_AUDIT.json','PATH_SELECTION.json','PR171-natural-inputs.json','LICENSE'):
  shutil.copyfile(pool/'corpus'/n,dest/n)
 shutil.copyfile(pool/'panel.json',dest/'PR175-panel.json')
 out=SROOT/'provenance/tokenizer';out.mkdir()
 for p in (SMOL/'tokenizer-build/Release').iterdir():
  if p.suffix.lower() in ('.dll','.exe'):shutil.copyfile(p,out/p.name)
 shutil.copyfile(SMOL/'code/tokenizer.cpp',out/'tokenizer.cpp')
 write(SROOT/'provenance/POPULATION_FILES.json',dict(files=[dict(path=p.relative_to(SROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for base in (dest,out) for p in sorted(base.iterdir()) if p.is_file()],models_included=False))

def recompute():
 for f in read(SROOT/'provenance/POPULATION_FILES.json')['files']:
  p=SROOT/f['path'];assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256']
 folder=SROOT/'cohort';source=[json.loads(x) for x in (SROOT/'provenance/corpus/paths.jsonl').read_text(encoding='utf-8').splitlines()]
 stream=(folder/'tokenized.jsonl').read_text(encoding='utf-8').splitlines();vocab=json.loads(stream[0]);assert vocab==read(SROOT/'provenance/VOCAB_TARGET.json')
 rendered=[json.loads(x) for x in (folder/'rendered.jsonl').read_text(encoding='utf-8').splitlines()]
 rows=[];allinputs={}
 for r,line,text in zip(source,stream[1:],rendered,strict=True):
  x=json.loads(line);assert x['id']==r['id']==text['id'] and x['forward_calls']==0
  ids=x['prompt_ids']
  if r['history_exposed'] or len(ids)+127+1+4>1024:continue
  rows.append(dict(id=r['id'],root_id=r['root_id'],tokens=len(ids),native_tokenized=True,admitted=True))
  allinputs[r['id']]=dict(id=r['id'],root_id=r['root_id'],prompt_ids=ids,formatted_sha256=hashlib.sha256(text['formatted_prompt'].encode()).hexdigest(),source_message_ids=r['message_ids'])
 old=read(SROOT/'provenance/corpus/PR175-panel.json');excluded={r['root_id'] for g in ('calibration','test') for r in old[g]}
 initial=select(rows,excluded);actual=read(folder/'PANEL.json');assert initial==actual
 extra=read(folder/'EXPOSURE_SUPPLEMENT.json');exposure=set()
 for proof in extra['sources']:
  p=SROOT/'provenance/PR177'/PureWindowsPath(proof['path']).name;assert sha(p)==proof['git_bytes_sha256'];v=read(p)
  exposure.update(x['root_id'] for x in v) if isinstance(v,list) else exposure.update(v['root_ids'])
 assert exposure==set(extra['additional_authenticated_roots'])
 revised=select(rows,excluded|exposure)
 assert all(actual[g]==revised[g] for g in ('development','test'))
 expected={r['id']:allinputs[r['id']] for g in ('development','test') for r in actual[g]};assert expected==read(folder/'INPUTS.json')
 assert sha(SROOT/'provenance/corpus/messages.jsonl.gz')=='2ff4aa8999c911ffec7972ddf70359f220b3da184b731f3649f68b1391e19341'
 assert sha(SROOT/'provenance/tokenizer/b570-tokenizer.exe')==read(SROOT/'provenance/TOKENIZATION_BINDINGS.json')['tokenizer_executable_sha256']
 return dict(status='FULL_POPULATION_AND_FIXED_SELECTION_RECOMPUTED',source_paths=len(source),initial_eligible_roots=initial['eligible_roots'],supplemented_eligible_roots=revised['eligible_roots'],selected_development_roots=4,selected_test_roots=12,selected_identities_and_order_unchanged=True,selected_prompt_ids_and_rendered_bytes_bound=True,actual_native_tokenizer_sha256=sha(SROOT/'provenance/tokenizer/b570-tokenizer.exe'),model_forwards=0)

if __name__=='__main__':
 if sys.argv[1]=='retain':retain()
 elif sys.argv[1]=='exposure':
  dest=SROOT/'provenance/PR177';dest.mkdir()
  for proof in read(SROOT/'cohort/EXPOSURE_SUPPLEMENT.json')['sources']:
   raw=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show',proof['commit']+':'+proof['path']],cwd=HERE);assert hashlib.sha256(raw).hexdigest()==proof['git_bytes_sha256'];(dest/PureWindowsPath(proof['path']).name).write_bytes(raw)
 else:write(SROOT/'cohort/POPULATION_RECOMPUTATION.json',recompute())
