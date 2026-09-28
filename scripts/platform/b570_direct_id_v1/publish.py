"""Post-measurement publication only: commit verified evidence and refresh an existing draft PR."""
import argparse, hashlib, json, os, subprocess, urllib.request
from pathlib import Path

REPO='leecdiang/HeteroSpec'
BRANCH='experiment/b570-direct-id-qualification-v1'
def git(*args):return subprocess.run(['git',*args],text=True,capture_output=True,check=True).stdout.strip()
def credential():
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never')
    out=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,check=True,env=env).stdout
    values=dict(line.split('=',1) for line in out.splitlines() if '=' in line)
    if not values.get('password'):raise RuntimeError('No noninteractive GitHub credential')
    return values['password']
def api(token,path,method='GET',payload=None):
    request=urllib.request.Request('https://api.github.com/repos/'+REPO+path,
        data=None if payload is None else json.dumps(payload).encode(),method=method,
        headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'HeteroSpec-direct-ID-publication','Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=60) as response:return json.load(response)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--pr-number',type=int,required=True)
    args=parser.parse_args();folder=Path('benchmarks/b570_direct_id_v1')
    runs=json.loads((args.root/'executions.json').read_text(encoding='utf-8'))
    result=json.loads((folder/'FORMAL_ANALYSIS.json').read_text(encoding='utf-8'))
    validation=json.loads((folder/'INDEPENDENT_VALIDATION.json').read_text(encoding='utf-8'))
    protocol=json.loads((folder/'protocol_v1.json').read_text(encoding='utf-8'))
    freeze=json.loads((folder/'FREEZE_MANIFEST.json').read_text(encoding='utf-8'))
    archive=json.loads(Path('artifacts/b570_direct_id_v1/ARCHIVE.json').read_text(encoding='utf-8'))
    if runs['status']!='COMPLETE' or len(runs['executions'])!=270 or validation['status']!='PASS':raise RuntimeError('Publication gate not passed')
    if git('branch','--show-current')!=BRANCH or git('rev-parse','HEAD')!=runs['study_head']:raise RuntimeError('Study branch/HEAD changed before publication')
    if git('diff','--cached','--name-only'):raise RuntimeError('Unrelated staged files present; stop publication')
    for path,want in freeze['files'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=want:raise RuntimeError('Frozen source changed: '+path)
    if git('diff','--name-only'):raise RuntimeError('Tracked files modified before publication; preserve and stop')
    token=credential();pr=api(token,'/pulls/'+str(args.pr_number))
    if not pr['draft'] or pr['state']!='open' or pr['head']['ref']!=BRANCH or pr['base']['ref']!='main':raise RuntimeError('Existing draft PR identity changed')
    git('add',str(folder/'FORMAL_ANALYSIS.json'),str(folder/'FORMAL_REPORT.md'),str(folder/'INDEPENDENT_VALIDATION.json'))
    git('commit','-m','experiment: report B570 direct-ID replication and independent validation')
    git('add','-f',str(folder/'CLOSEOUT.md'),'artifacts/b570_direct_id_v1')
    git('commit','-m','experiment: archive and close B570 direct-ID replication')
    archive_path='artifacts/b570_direct_id_v1/'+archive['archive']
    blob=subprocess.check_output(['git','cat-file','blob','HEAD:'+archive_path])
    if hashlib.sha256(blob).hexdigest()!=archive['archive_sha256']:raise RuntimeError('Git object archive digest mismatch')
    for path in ('artifacts/b570_direct_id_v1/ARCHIVE.json','artifacts/b570_direct_id_v1/SHA256_MANIFEST.json'):
        if subprocess.check_output(['git','cat-file','blob','HEAD:'+path])!=Path(path).read_bytes():raise RuntimeError('Git object byte mismatch: '+path)
    git('push','origin',BRANCH)
    body='## Closed: new direct-generated-ID replication\n\n'
    body+='Prospectively frozen replication with known historical outcomes; not blinded discovery. Historical B570 campaign remains closed and unchanged.\n\n'
    body+=f"- Starting main: `{protocol['starting_main']}`\n- Frozen study HEAD: `{runs['study_head']}`\n- Publication HEAD: `{git('rev-parse','HEAD')}`\n- llama.cpp b10839: `{protocol['upstream_commit']}`\n"
    body+=f"- Instrumentation: observational committed-output-ID sidecar; patch SHA256 `{protocol['instrumentation']['sha256']}`. No logits/sampling/verification/KV/stopping changes.\n"
    body+='- Primary comparison uses actual IDs, no text retokenization: first 128 committed IDs or inclusive first EOG. All raw overshoot IDs retained.\n'
    body+=f"- Dataset SHA256: `{protocol['dataset']['sha256']}`\n- Target SHA256: `{protocol['target']['sha256']}`\n- Draft SHA256: `{protocol['draft']['sha256']}`\n"
    driver=next(g['DriverVersion'] for g in protocol['environment']['gpu'] if g['Name']=='Intel(R) Arc(TM) B570 Graphics')
    body+=f'- Device: Vulkan0 / Intel Arc B570; driver {driver}; target 37/37 and draft 29/29 offload.\n- Expected/completed executions: **270/270**; comparisons: **180/180**.\n\n'
    for condition,path in result['paths'].items():
        body+=f"### {condition}\n\n- **{path['qualification']}**: {path['exact_pairs']}/90 exact pairs; {path['wholly_exact_prompts']}/30 wholly exact prompts.\n"
        indices=[x['first_divergent_output_token_index'] for x in path['mismatches']]
        body+=f"- Mismatches: {len(indices)}; first-divergence index range: {min(indices) if indices else 'none'} to {max(indices) if indices else 'none'} (zero-based). Full IDs/lengths/first divergences in FORMAL_ANALYSIS.json and raw bundle.\n\n"
    body+='Historical fast 45/90 and serialized 60/90 are re-tokenized-text agreement, not direct-ID certificates; unchanged. No Vulkan-wide or hardware-wide causal claim.\n\n'
    body+=f"- Archive SHA256: `{archive['archive_sha256']}`\n- Independent validator: **PASS**, all 270 executions and 180 comparisons recomputed; archive payload and Git-object bytes verified.\n"
    body+='- Parameter changes after formal start: **NO**. Energy/PresentMon/V2 campaign: **NO**. Result-driven search: **NO**. Manuscript/Figure 3/historical CSV edits: **NO**.\n- Hardware-free verification instructions: `artifacts/b570_direct_id_v1/ARCHIVE.json`.\n- No automatic merge. Integration awaits joint review with independent RTX arm.\n'
    updated=api(token,'/pulls/'+str(args.pr_number),'PATCH',{'body':body})
    status={'state':'COMPLETE_PUBLISHED_DRAFT','pr_url':updated['html_url'],'draft':updated['draft'],'publication_head':git('rev-parse','HEAD'),
            'frozen_study_head':runs['study_head'],'archive_sha256':archive['archive_sha256'],'paths':result['paths'],'independent_validation':'PASS'}
    (args.root.parent/(args.root.name+'-controller')/'publication.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'state':status['state'],'pr_url':status['pr_url'],'publication_head':status['publication_head']}))

if __name__=='__main__':main()
