"""CPU-only follow-up data/figure audit; no native inference or raw-logit claims."""
from pathlib import Path
import csv,hashlib,importlib.util,json,math,re

def gm(xs):
    xs=list(xs)
    if not xs or not all(math.isfinite(x) and x>0 for x in xs):raise ValueError('finite positive ratios required')
    return math.exp(math.fsum(map(math.log,xs))/len(xs))

def derived_json_equal(actual, expected):
    """Compare generated summaries, allowing at most one ULP for finite floats.

    libm exp/log results can differ in their last bit across platforms. Only
    derived JSON uses this comparison: source blobs and rendered TeX remain
    exact. Types, keys, list ordering, integers, and nonnumeric leaves stay exact.
    """
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, float):
        return (math.isfinite(actual) and math.isfinite(expected)
                and actual in (expected, math.nextafter(expected, -math.inf),
                               math.nextafter(expected, math.inf)))
    if isinstance(expected, dict):
        return (actual.keys() == expected.keys()
                and all(derived_json_equal(actual[k], v) for k, v in expected.items()))
    if isinstance(expected, list):
        return (len(actual) == len(expected)
                and all(derived_json_equal(a, e) for a, e in zip(actual, expected)))
    return actual == expected

def read_derived_json(text):
    """Reject duplicate keys and JSON extensions before numerical comparison."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('Non-finite JSON number: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)

def verify(check,root:Path):
    data=root/'anc/closure'; records=json.loads((data/'reported_summary.json').read_text())
    result={}
    for name in ('rtx','b570'):
        p=data/(name+'_blocks.csv');body=p.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
        check(name+': saved CSV exact Git blob identity',blob==records[name]['blob'])
        with p.open(newline='') as f:rows=list(csv.DictReader(f))
        ids=list(dict.fromkeys(r['input_id'] for r in rows))
        check(name+': complete 4 inputs x 4 sessions',len(rows)==16 and len(ids)==4 and {(int(r['session']),r['input_id']) for r in rows}=={(s,i) for s in range(4) for i in ids})
        if name=='rtx':
            rr=[]
            for row in rows:
                r,a,b,q=(float(row[k]) for k in ('R','PQ_A','PQ_B','QB'))
                check('RTX positive service seconds '+row['session']+'/'+row['input_id'],all(math.isfinite(v) and v>0 for v in (r,a,b,q)))
                calc=(q/((a+b)/2),q/r,((a+b)/2)/r,a/b)
                for key,val in zip(('QB_dual_PQ','QB_R','PQ_R','PQ_A_PQ_B'),calc):
                    check('RTX direct service ratio '+row['session']+'/'+row['input_id']+'/'+key,abs(val-float(row[key]))<3e-14)
                rr.append(dict(input=row['input_id'],session=int(row['session']),layout=calc[0],economics=calc[1],pq_economics=calc[2],aa=calc[3]))
        else:
            rr=[dict(input=r['input_id'],session=int(r['session']),layout=float(r['service_QB_over_dualPQ']),economics=float(r['service_QB_over_R']),aa=float(r['service_PQA_over_PQB'])) for r in rows]
        est={k:gm(r[k] for r in rr) for k in ('layout','economics')}
        est['aa']=max(abs(gm(r['aa'] for r in rr if r['input']==i)-1) for i in ids)
        est['sessions']=[gm(r['layout'] for r in rr if r['session']==s) for s in range(4)]
        check(name+': original reported layout ratio',abs(est['layout']-records[name]['layout'])<6e-9)
        check(name+': original reported speculative economics',abs(est['economics']-records[name]['economics'])<6e-9)
        check(name+': original A/A imbalance',abs(est['aa']-records[name]['aa'])<(5e-7 if name=='b570' else 1e-13))
        screen=1-est['layout']>max(.02,est['aa']) and all(v<1 for v in est['sessions'])
        check(name+': no established practical layout benefit',not screen)
        check(name+': independent inputs not technical repeats',records[name]['independent_inputs']==4 and records[name]['measured']==64)
        if name=='rtx':
            check('RTX: two session reversals retained',sum(v>1 for v in est['sessions'])==2)
            check('RTX: A/A exceeds practical margin',est['aa']>.02)
            check('RTX: every paired QB/R below one',all(r['economics']<1 for r in rr))
            est['pq_economics']=gm(r['pq_economics'] for r in rr)
            check('RTX: PQ already repays draft cost',abs(est['pq_economics']-records[name]['pq_economics'])<1e-13 and est['pq_economics']<1)
            check('RTX: 148 requests and 2900 vector accounting',8+12+64+64==148 and records[name]['reference_vectors']+records[name]['qualification_vectors']==records[name]['raw_vectors']==2900)
        else:
            check('B570: every paired QB/R above one',all(r['economics']>1 for r in rr))
            check('B570: corrected HumanEval/65 ratio',abs(gm(r['layout'] for r in rr if r['input']=='HumanEval/65')-.9920027931021794)<1e-13)
        result[name]=est
    cpu=records['cpu_policy'];check('CPU1: four-session geometric mean agrees',abs(gm(cpu['sessions'])-cpu['ratio'])<1e-13 and cpu['ratio']>1)
    pf=records['prefill_followup'];check('Prefill submission: numerical-only published result',pf['status']=='QUALIFIED_NO_COMPLETE_TIMING_RECORD_IN_REVIEWED_TREE' and pf['full_logit_pairs']==346 and pf['physical_q']==1 and pf['draft_prefill_api_calls']==1)
    spec=importlib.util.spec_from_file_location('generate_followup_figures',root/'scripts/generate_followup_figures.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for name,expected in mod.outputs().items():
        actual=(root/name).read_text()
        if name=='anc/closure/derived_summary.json':
            check('Derived summary numerical consistency (one ULP): '+name,
                  derived_json_equal(read_derived_json(actual),read_derived_json(expected)))
        else:
            check('Generated figure/table byte consistency: '+name,actual==expected)
    text=(root/'sections/08_request_service.tex').read_text()
    for value in ('0.989284','5.208','0.582325','41.8','0.588633','0.995144','2.619763','1.003994'):
        check('Service manuscript value '+value,value in text)
    check('Speculation percentage derived from service ratio',f"{100*(1-result['rtx']['economics']):.1f}"=='41.8')
    check('No bare percent truncates abstract',re.search(r'(?<!\\)%',(root/'abstract.tex').read_text()) is None)
    check('Shared original/new bibliography all used',len(re.findall(r'^@\w+\{', (root/'references.bib').read_text(),re.M))==31)
    return result
