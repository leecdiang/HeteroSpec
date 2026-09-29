"""Independent v0.7 source, macro, appendix, figure, scope and archive checks."""
from pathlib import Path
import hashlib,importlib.util,json,re,subprocess
HERE=Path(__file__).resolve().parents[1];REPO=HERE.parents[2];E=HERE.parent/'evidence'
checks=[]
def check(label,value):
    assert value,label
    checks.append(label)
specs=[('RTXBatched','rtx_direct_id_v2','conditions','RTX_BATCHED_K2',75,25,'BLOCKED'),
       ('RTXSerialized','rtx_direct_id_v2','conditions','RTX_SERIALIZED_K2',90,30,'QUALIFIED'),
       ('BFast','b570_direct_id_v1','paths','B570_FAST_K2',60,20,'BLOCKED'),
       ('BSerialized','b570_direct_id_v1','paths','B570_SERIALIZED_K2',78,26,'BLOCKED')]
tex=(HERE/'tables/direct_id_values.tex').read_text()
table=(HERE/'tables/08_direct_id.tex').read_text()
parsed=dict(re.findall(r'\\newcommand\{\\([^}]+)\}\{([^}]+)\}',tex))
check('12 generated macros',len(parsed)==12)
for prefix,study,key,path,pairs,prompts,status in specs:
    data=json.loads((REPO/f'benchmarks/{study}/FORMAL_ANALYSIS.json').read_text(encoding='utf-8'))
    row=data[key][path]
    check('formal endpoint '+path,(row['exact_pairs'],row['wholly_exact_prompts'],row['qualification'])==(pairs,prompts,status))
    comparisons=row['comparisons'] if key=='conditions' else [c for c in data['comparisons'] if c['candidate']==path]
    check('90 comparisons '+path,len(comparisons)==90 and sum(c['exact'] for c in comparisons)==pairs)
    check('wholly exact prompts '+path,sum(all(c['exact'] for c in comparisons if c['task_id']==t) for t in {c['task_id'] for c in comparisons})==prompts)
    for suffix,value in [('Pairs',pairs),('Prompts',prompts),('Status',status)]:
        macro='DI'+prefix+suffix
        check('macro '+macro,parsed[macro]==str(value))
        check('appendix uses '+macro,'\\'+macro in table)
for study,hashkey,digest in [('rtx_direct_id_v2','sha256','fc3676adae93c4f21bf6e29d9787d95d1e60d08c2d7223de30fc58c46c3e0822'),
                            ('b570_direct_id_v1','archive_sha256','58daa4159de12042c73194bbd99abc5e5e23c171578ea873675f07901582db20')]:
    folder=REPO/'artifacts'/study
    meta=json.loads((folder/('archive_manifest.json' if study.startswith('rtx') else 'ARCHIVE.json')).read_text())
    check('archive SHA-256 '+study,hashlib.sha256((folder/meta['archive']).read_bytes()).hexdigest()==meta[hashkey]==digest)
for platform in ('RTX','B570'):
    receipt=json.loads((E/f'DIRECT_ID_{platform}_OFFLINE_V07.json').read_text())
    check('independent archive replay '+platform,receipt['status']=='PASS')
    check('independent coverage '+platform,receipt.get('executions_verified',receipt.get('executions'))==270 and receipt.get('pairs_independently_recomputed',receipt.get('comparisons'))==180)
protocols=[json.loads((REPO/'benchmarks'/s/p).read_text()) for s,p in [('rtx_direct_id_v2','protocol_v2.json'),('b570_direct_id_v1','protocol_v1.json')]]
check('common frozen task IDs',protocols[0]['task_ids']==protocols[1]['task_ids'] and len(protocols[0]['task_ids'])==30)
texts={p.name:p.read_text() for p in [HERE/'main.tex',HERE/'appendix.tex',*list((HERE/'sections').glob('*.tex'))]}
check('explicit historical comparator distinction','historical text-path comparator' in texts['04_outcomes.tex'])
check('no retroactive certification','do not retrospectively certify' in texts['04_outcomes.tex'] and 'without retroactively certifying historical timing' in texts['09_limitations.tex'])
check('not controlled hardware comparison','not a controlled hardware comparison' in texts['05_diagnoses.tex'])
check('separate historical mechanism','A separate historical numerical diagnostic' in texts['05_diagnoses.tex'])
check('unchanged historical headline table',(HERE/'tables/02_headlines_v05.tex').read_bytes()==subprocess.check_output(['git','show','bab0e44:paper/mlsys2027/manuscript/tables/02_headlines_v05.tex'],cwd=REPO))
check('appendix separate qualification table',r'\label{tab:directidqualification}' in table and r'\input{tables/08_direct_id.tex}' in texts['appendix.tex'])
check('B570 launcher recovery','zero formal executions' in texts['appendix.tex'] and 'unchanged frozen runner' in texts['appendix.tex'])
check('RTX driver boundary','616.92' in texts['appendix.tex'] and '616.56' in texts['appendix.tex'])
check('Guard negative finding retained','Guard had higher latency on this comparison' in texts['07_runtime_codesign.tex'])
spec=importlib.util.spec_from_file_location('figure_v07',HERE/'figures/presentation_v07/validate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);figure=module.validate()
check('new figure independent validation',figure['status']=='PASS')
# Preserve every existing evidence record, old output and approved presentation asset.
inventory=subprocess.check_output(['git','ls-tree','-r','bab0e44','artifacts','benchmarks','reports','scripts','paper/mlsys2027/evidence','paper/mlsys2027/manuscript/vendor','paper/mlsys2027/manuscript/output','paper/mlsys2027/manuscript/figures/presentation_v05'],cwd=REPO).decode().splitlines()
protected=[];expected=[]
for line in inventory:
    meta,path=line.split('\t',1);protected.append(path);expected.append(meta.split()[2])
actual=subprocess.check_output(['git','hash-object','--no-filters','--stdin-paths'],input=('\n'.join(protected)+'\n').encode(),cwd=REPO).decode().splitlines()
check('protected inventory coverage',len(actual)==len(protected))
for path,want,got in zip(protected,expected,actual):check('protected base bytes '+path,want==got)

report={'status':'PASS','checks':checks,'check_count':len(checks),'figure':figure,'base':'bab0e44c74f7fa59d2ea42faf4dcf4c51a78e674','no_new_inference':True,'historical_evidence_modified':False,'retroactive_certification':False}
(E/'DIRECT_ID_INTEGRATION_QA_V07.json').write_text(json.dumps(report,indent=2)+'\n')
print('Direct-ID integration PASS:',len(checks),'checks; figure:',figure['check_count'])
