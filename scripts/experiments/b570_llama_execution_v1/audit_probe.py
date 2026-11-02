"""Read-only native probe/natural trajectory and same-state row audit."""
from array import array
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
import audit
from common import read, write, sha, need


def rows(a, b):
    ba, bb = a.read_bytes(), b.read_bytes()
    aa, ab = array('f'), array('f')
    aa.frombytes(ba); ab.frombytes(bb)
    ai, ah = audit.full_vector(a); bi, bh = audit.full_vector(b)
    return {'q1_sha256':ah, 'q4_sha256':bh, 'q1_argmax':ai, 'q4_argmax':bi,
            'bitwise_equal':ba==bb, 'max_abs':max(abs(x-y) for x,y in zip(aa,ab)),
            'different_fp32_words':sum(ba[i:i+4]!=bb[i:i+4] for i in range(0,len(ba),4))}


def run(epoch, attempt, out, reference_epoch=None):
    epoch=Path(epoch); unit=epoch/'units'/attempt
    receipt=read(unit/'RECEIPT.json')
    need(receipt['success'] and receipt['cleanup_verified'], 'incomplete supervised unit')
    results=[]
    for slot in read(unit/'SLOTS.json'):
        arm=slot['arm']; current=unit/'native'/(slot['id']+'.json')
        baseline=Path(reference_epoch or epoch)/'units/baseline-candidate/native/baseline/i0'/arm/'heavy.json'
        actual=audit.record(current)
        ae, av, ac=actual['endpoint'],actual['vectors'],actual['record']['cycles']
        del actual
        original=audit.record(baseline)
        need(ae==original['endpoint'] and ac==original['record']['cycles'] and av==original['vectors'], 'probe changed natural trajectory or full vectors')
        del original
        probe=current.with_suffix('')/'probe'; control=read(probe/'CONTROL.json')
        need(control['live_source_unchanged'] and control['own_q4_full_vectors_equal'], 'probe native controls failed')
        comparisons=[]
        for i in range(control['actual_query_width']):
            a=probe/'q1'/f'row-{i}.f32';b=probe/'q4'/f'row-{i}.f32'
            need(sha(b)==av[f'target/verify-{slot["probe_cycle"]}-{i}.f32'], 'q4 row does not replay natural path')
            comparisons.append(dict(row=i, **rows(a,b)))
        results.append({'slot':slot['id'],'arm':arm,'cycle':slot['probe_cycle'],'trace':slot['trace'],
                        'native_control':control,'source_state_sha256':sha(probe/'source.state'),
                        'natural_endpoint_cycles_and_vectors_equal':True,'natural_record_sha256':sha(baseline),
                        'probe_record_sha256':sha(current),'rows':comparisons})
    report={'status':'NATIVE_PROBE_CONTROLS_PASS','unit_receipt_sha256':sha(unit/'RECEIPT.json'),'results':results}
    write(out,report)
    print(report['status'],len(results))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--epoch',required=True);p.add_argument('--attempt',required=True);p.add_argument('--out',required=True)
    p.add_argument('--reference-epoch');a=p.parse_args();run(a.epoch,a.attempt,a.out,a.reference_epoch)
