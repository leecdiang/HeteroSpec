"""Closeout, portable evidence packaging and independent archive verification."""
import argparse, hashlib, json, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path
from study import ROOT, PLAN, RAW, SRC, LOCAL, save, sha, utc, git

def closeout():
    validation=PLAN/'INDEPENDENT_VALIDATION.json'
    subprocess.run([sys.executable,str(SRC/'verify_complete.py'),'--root',str(ROOT),'--output',str(validation)],check=True)
    result=json.loads(validation.read_text(encoding='utf-8'))
    subprocess.run([sys.executable,str(SRC/'characterize.py'),'--root',str(ROOT),'--output',str(PLAN/'ENDPOINT_ANALYSIS.json')],check=True)
    status=result['status'];q=json.loads((PLAN/'TECHNICAL_QUALIFICATION.json').read_text(encoding='utf-8'))
    failed=[r for r in q['results'] if not r['pass']]
    text='# B570 live partition intervention V1 closeout\n\n**'+status+'**.\n\n'
    text+=f"New R0 executions: {result['r0_attempts']}. New reserved executions: {result['reserved_attempts']}/72. Eligible reserved forks: {result['reserved_eligible_forks']}.\n\n"
    if status=='INTERVENTION_NOT_FEASIBLE':
        text+='The preregistered same-state engineering gate failed. Formal reserved inference was forbidden and was not started. This is a technical qualification result, with no live causal conclusion and no same-prefix substitute. All started attempts are retained.\n\n'
        text+='Failure details:\n\n```json\n'+json.dumps(failed,indent=2)+'\n```\n\n'
    elif status=='FORMAL_OPERATIONAL_FAILURE':
        text+='Formal interpretation stopped at the first operational failure; all attempted and unattempted scheduled slots are preserved in the execution record. No replacement execution.\n\n'
    else:
        text+=f"Prompt decision effects: {result['prompt_decision_effect_count']}/{result['reserved_prompt_count']}. Execution effects: {result['execution_decision_effect_count']}/{result['reserved_attempts']}. Paired decision events: {result['paired_decision_event_count']}.\n\n"
        text+='These measurements cover the frozen sampled checkpoint rule. Subsequent trajectory differences are secondary, and do not alone prove an immediate target decision effect. Events and repeated executions are correlated within prompts.\n\n'
    text+=f"Raw-score effects: {result.get('score_difference_executions',0)} executions, {result.get('score_difference_prompts',0)} prompts. Downstream trajectory differences: {result.get('trajectory_difference_executions',0)} executions, {result.get('trajectory_difference_prompts',0)} prompts.\n\n"
    text+='The old 72/72 predictor/live and 60/72 reference/live results are read-only design context. No old generated arrays were used as new observations. No manuscript edits, performance/energy measurements, parameter searches or automatic merge.\n\n'
    text+='The independent offline verifier rehashes retained evidence and recomputes exposure selection, state equality, endpoints, paired decisions and qualification checks. Models and runtime binaries are omitted from the public bundle; their recorded identities cannot authenticate omitted bytes offline. Sampler equality uses the pinned recursive clone implementation, recorded chain/seed/history and the same-partition R0 continuation check.\n'
    (PLAN/'CLOSEOUT.md').write_text(text,encoding='utf-8')
    save(PLAN/'CLOSEOUT.json',{'status':status,'created_utc':utc(),'starting_main':git('rev-parse','origin/main'),
        'execution_head':git('rev-parse','HEAD'),'independent_validation_sha256':sha(validation),
        'reserved_executions':result['reserved_attempts'],'r0_attempts':result['r0_attempts'],
        'failed_qualification':failed,'claims_permitted':status=='TARGET_PARTITION_INTERVENTION_EFFECT_ON_TESTED_STATES',
        'manuscript_changed':False,'automatic_merge':False})
    print(status,flush=True)

def archive():
    out=ROOT/'artifacts/b570_partition_intervention_v1'
    assert not (out/'ARCHIVE.json').exists(),'No silent archive replacement'
    staging=ROOT/'work/b570_partition_intervention_v1/portable';staging.mkdir(parents=True,exist_ok=True)
    paths=list(PLAN.glob('*'))+list(SRC.glob('*'))+list(RAW.rglob('*'))
    paths += [ROOT/'benchmarks/b570_direct_id_v1/protocol_v1.json',ROOT/'benchmarks/b570_mechanism_v08/RESERVED_VALIDATION_SET.json']
    manifest={}
    for p in paths:
        if not p.is_file() or '__pycache__' in p.parts:continue
        rel=p.relative_to(ROOT);dest=staging/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        manifest[rel.as_posix()]={'sha256':sha(dest),'bytes':dest.stat().st_size}
    # Licensed frozen HumanEval input dataset for offline input checking, following the prior bounded evidence exception.
    data=LOCAL/'datasets/humaneval/HumanEval.jsonl.gz';dest=staging/'datasets/humaneval/HumanEval.jsonl.gz';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(data,dest)
    manifest[dest.relative_to(staging).as_posix()]={'sha256':sha(dest),'bytes':dest.stat().st_size}
    for name in ['LICENSE','common/sampling.cpp','common/sampling.h','include/llama.h','src/llama-context.cpp','src/llama-kv-cache.cpp','ggml/src/ggml-backend.cpp','examples/speculative/speculative.cpp']:
        src=Path('C:/hs/b570-direct-id-v1-src')/name;dest=staging/'provenance/pinned_source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
        manifest[dest.relative_to(staging).as_posix()]={'sha256':sha(dest),'bytes':dest.stat().st_size}
    commits=git('rev-list','--reverse','origin/main..HEAD').splitlines();proof=[]
    for oid in commits:
        rawcommit=subprocess.check_output(['git','cat-file','commit',oid],cwd=ROOT)
        proof.append({'commit':oid,'raw_commit':rawcommit.decode('utf-8'),'git_object_sha1':hashlib.sha1(b'commit '+str(len(rawcommit)).encode()+b'\0'+rawcommit).hexdigest()})
    save(staging/'provenance/GIT_CHECKPOINTS.json',{'created_utc':utc(),'commits':proof,'base':git('rev-parse','origin/main')})
    manifest['provenance/GIT_CHECKPOINTS.json']={'sha256':sha(staging/'provenance/GIT_CHECKPOINTS.json'),'bytes':(staging/'provenance/GIT_CHECKPOINTS.json').stat().st_size}
    save(staging/'MANIFEST.json',{'files':manifest,'exclusions':['model weights','runtime binaries','static libraries','unrelated historical raw runs'],
        'validation_command':'python scripts/platform/b570_partition_intervention_v1/verify_complete.py --root .',
        'dataset_license':'HumanEval MIT; upstream code MIT; source repository retains licensing context.'})
    archive=out/'evidence.tmp.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=1) as ar:
        for p in sorted(staging.rglob('*')):
            if p.is_file():ar.add(p,arcname=p.relative_to(staging).as_posix(),recursive=False)
    archive_hash=sha(archive);pieces=[]
    with archive.open('rb') as src:
        while True:
            block=src.read(48*1024*1024)
            if not block:break
            h=hashlib.sha256(block).hexdigest();part=out/(h+'.part');part.write_bytes(block)
            pieces.append({'path':part.name,'sha256':h,'bytes':len(block)})
    archive.unlink()
    save(out/'ARCHIVE.json',{'created_utc':utc(),'archive_sha256':archive_hash,'parts':pieces,'manifest_sha256':sha(staging/'MANIFEST.json'),
        'content_head':git('rev-parse','HEAD'),'packaging_commit_excluded':'Archive cannot contain its own hash/packaging commit.',
        'restore':'Concatenate ordered parts to evidence.tar.gz; extract; run included verify.py --root extracted root.'})
    (out/'.gitattributes').write_text('*.part -text\n',encoding='ascii')
    subprocess.run([sys.executable,str(SRC/'verify_archive_complete.py'),'--archive',str(out/'ARCHIVE.json')],check=True)
    print('Portable content-addressed evidence verified:',archive_hash,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['closeout','archive']);a=p.parse_args();globals()[a.stage]()
