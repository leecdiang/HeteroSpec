"""Synthetic contract fixtures; no model output, CUDA or server authority."""
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import random
import sys
import tarfile
import tempfile
import struct
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
sys.path.insert(0,str(Path(__file__).parent.parent))
import analyze
import archive
import optional_analysis
from objects import archive_members
from design_checks import plan
from ledger import Ledger
from support import config_echo,historical_receipt,module_files,normalize,safe_relative,sha
from check_numeric import vectors,state,quantized_chunks
from host import Host,resource,verify_files,verify_public_readback,relevant_environment
from freeze_cpu import public_text
from terminal_guard import terminal_phase
from f1 import caller_cost_proof
import subprocess


def synthetic_rows(phase='S2',ratios=None):
    rows=[];clock=10**12
    ratios=ratios or {'G':1,'B':1,'C':1}
    for w in plan()[{'S2':'q32_diagnostic','S3':'q32_panel','REPLICA':'q32_replica'}[phase]]:
        for ordinal,op in enumerate(w['operations']):
            duration=ratios[w['arm']];stop=clock+round(duration*1e9)
            q=4 if w['slot'] in (0,2) else 32
            r=dict(synthetic=True,operation_id=op['id'],worker_id=w['id'],arm=w['arm'],
                   slot=w['slot'],block=w['round'],ordinal=ordinal,role=op['role'],unit='s',
                   elapsed_s=(stop-clock)/1e9,start_ns=clock,end_ns=stop,fence_ns=stop,
                   owned_ready_ns=stop,q=q,output_rows=q,all_outputs_owned=True,callback_continues=True,
                   input_sha256=hashlib.sha256(str(w.get('primary_root_slot',w['slot'])).encode()).hexdigest(),
                   config_sha256='1'*64,output_sha256='2'*64)
            if phase in ('S3','REPLICA'):r.update(tokens=[42,43],generated_tokens=2,stop_reason='eog')
            rows.append(r);clock=stop+10**6
    return rows


class Records(unittest.TestCase):
    def test_shuffled_is_deterministic(self):
        r=synthetic_rows();random.Random(17).shuffle(r)
        self.assertEqual(normalize(r,'S2'),normalize(synthetic_rows(),'S2'))

    def test_negative_receipts(self):
        for key,value in [('elapsed_s',0),('elapsed_s',-1),('elapsed_s',float('nan')),
                          ('unit','ms'),('output_rows',3),('all_outputs_owned',False),
                          ('callback_continues',False),('fence_ns',0),('owned_ready_ns',0),
                          ('config_sha256','z'*64),('q',True)]:
            with self.subTest(key=key,value=value):
                r=synthetic_rows();r[0][key]=value
                with self.assertRaises(ValueError):normalize(r,'S2')

    def test_missing_duplicate_warm_arm_round(self):
        for role in ('warm','measured'):
            r=synthetic_rows();r.pop(next(i for i,x in enumerate(r)if x['role']==role))
            with self.assertRaises(ValueError):normalize(r,'S2')
        r=synthetic_rows();r[-1]=copy.deepcopy(r[0])
        with self.assertRaises(ValueError):normalize(r,'S2')
        for field,value in [('arm','B'),('block',8),('input_sha256','3'*64)]:
            r=synthetic_rows();r[0][field]=value
            with self.assertRaises(ValueError):normalize(r,'S2')

    def test_registered_order_and_overlap(self):
        r=synthetic_rows()
        for x in r[:2]:
            for k in ('start_ns','end_ns','fence_ns','owned_ready_ns'):x[k]+=10**14
        with self.assertRaises(ValueError):normalize(r,'S2')
        r=synthetic_rows();r[1]['start_ns']=r[0]['start_ns'];r[1]['end_ns']=r[0]['end_ns']
        r[1]['fence_ns']=r[0]['end_ns'];r[1]['owned_ready_ns']=r[0]['end_ns']
        with self.assertRaises(ValueError):normalize(r,'S2')

    def test_missing_complete_tokens_and_mixed_semantics(self):
        for change in ('missing','count','tokens'):
            r=synthetic_rows('S3')
            if change=='missing':r[0]['tokens']=[]
            elif change=='count':r[0]['generated_tokens']=128
            else:r[0]['tokens']=[44,45]
            with self.assertRaises(ValueError):normalize(r,'S3')

    def test_legacy_schema_is_explicit(self):
        self.assertEqual(historical_receipt(dict(heavy=True,service_s=1))['schema'],'scalar-reference')
        self.assertEqual(historical_receipt(dict(capture=False,service_seconds=2))['schema'],'candidate')
        with self.assertRaises(ValueError):historical_receipt(dict(heavy=True,service_seconds=2))
        self.assertEqual(module_files({'a':'a'*64}),module_files({'a':{'sha256':'a'*64}}))

    def test_reserve_and_type_rejection(self):
        j=dict(arm='B',n_ctx=1024,n_ubatch=32,output_reserve=32,kv='F16',
               flash_attention=False,cuda_graphs=False)
        self.assertFalse(config_echo(j)['cuda_initialized'])
        for key,value in [('output_reserve',8),('n_ubatch',4),('cuda_graphs',True),
                          ('flash_attention',0),('kv','Q8'),('arm','renamed-C')]:
            with self.assertRaises(ValueError):config_echo({**j,key:value})


class Statistics(unittest.TestCase):
    def test_equal_and_known_ratios(self):
        for phase in ('S2','S3'):
            a=analyze.analyze(synthetic_rows(phase),phase)
            self.assertTrue(all(x['ratio']==1 for x in a['contrasts']))
            b=analyze.analyze(synthetic_rows(phase,dict(G=2,B=1,C=.8)),phase)
            self.assertAlmostEqual(b['contrasts'][0]['ratio'],.8)
            self.assertAlmostEqual(b['contrasts'][1]['ratio'],.5)
            self.assertAlmostEqual(b['contrasts'][2]['ratio'],.4)
            if phase=='S3':
                self.assertAlmostEqual(b['contrasts'][0]['interval'][0],.8)
                self.assertEqual(b['contrasts'][0]['bootstrap']['unit'],'whole_root_all_four_rounds')

    def test_root_equal_differs_from_totals(self):
        r=synthetic_rows('S3')
        # Preserve the fixed order while making root0 much slower in every arm.
        clock=10**12
        for x in sorted(r,key=lambda x:x['start_ns']):
            duration=(100 if x['slot']==0 else 1)*(2 if x['slot']==0 and x['arm']=='C' else 1)
            x.update(start_ns=clock,end_ns=clock+duration*10**9,fence_ns=clock+duration*10**9,
                     owned_ready_ns=clock+duration*10**9,elapsed_s=duration)
            clock=x['end_ns']+10**6
        a=analyze.analyze(r,'S3')['contrasts'][0]
        self.assertAlmostEqual(a['ratio'],2**(1/12))
        self.assertGreater(a['total_ratio'],1.8)

    def test_strict_thresholds(self):
        self.assertIn('direction_only',analyze.threshold([.98,.99]))
        self.assertIn('C_at_least',analyze.threshold([.97,.989]))
        self.assertNotIn('B_at_least',analyze.threshold([1.01,1.03]))
        self.assertIn('B_at_least',analyze.threshold([1.0102,1.03]))
        self.assertEqual(analyze.threshold([.98,1.02]),'uncertain_not_equivalent')
        self.assertIn('finite_ratio',analyze.threshold([.995,1.005]))

    def test_optional_replica_does_not_pool_roots_or_drop_round(self):
        a=optional_analysis.replica(synthetic_rows('S3'),synthetic_rows('REPLICA'))
        self.assertEqual(a['roots'],6);self.assertFalse(a['pooled'])
        self.assertEqual([r['primary_root_slot']for r in a['paired_root_tables']],[0,1,2,6,7,8])
        with self.assertRaises(ValueError):optional_analysis.replica(synthetic_rows('S3')[:-6],synthetic_rows('REPLICA'))

    def test_b2_process_sum_ratio_and_cold_warms_kept(self):
        rows=[];clock=10**12
        for w in plan()['b2']:
            for op in w['operations']:
                duration=2 if op['path']=='A' else 1
                if op['role']=='warm':duration*=10
                end=clock+duration*10**9
                rows.append(dict(synthetic=True,operation_id=op['id'],worker_id=w['id'],role=op['role'],path=op['path'],
                                 unit='s',elapsed_s=duration,start_ns=clock,end_ns=end,fence_ns=end,
                                 physical_widths=[4,4]if op['path']=='A'else[8],output_rows=8,all_outputs_owned=True,
                                 tokens=list(range(8)),input_state_sha256='a'*64,output_sha256='b'*64))
                clock=end+1000
        a=optional_analysis.b2(rows);self.assertEqual(a['independent_clusters_per_cell'],4)
        self.assertTrue(all(x['geometric_B_over_A']==.5 for x in a['cells'].values()))
        rows[4]['role']='warm'
        with self.assertRaises(ValueError):optional_analysis.b2(rows)


class ArchiveObjects(unittest.TestCase):
    def test_repeated_basenames_identified_by_occurrence(self):
        def member(name,body):
            header=(name+'/').ljust(16)+'0'.ljust(12)+'0'.ljust(6)+'0'.ljust(6)+'644'.ljust(8)+str(len(body)).ljust(10)+'`\n'
            return header.encode()+body+(b'\n'if len(body)%2 else b'')
        with tempfile.TemporaryDirectory()as t:
            p=Path(t)/'lib.a';p.write_bytes(b'!<arch>\n'+member('llama.cpp.o',b'one')+member('llama.cpp.o',b'two'))
            a=archive_members(p);self.assertEqual(len(a),2)
            self.assertEqual(a[0]['member'],a[1]['member']);self.assertNotEqual(a[0]['sha256'],a[1]['sha256'])
            self.assertEqual([e['ordinal']for e in a],[0,1])


class Journal(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);old=self.root/'inherited.jsonl';old.write_text('historical fixture\n')
        self.inherited=dict(ledger_path=str(old),ledger_sha256=sha(old),requests=514,reserved_rows=652026)
        self.approval=dict(scope='S1+S2',status='EXPLICITLY_APPROVED',request_ceiling=516,
                           row_ceiling=652036,incremental_request_ceiling=2,synthetic=True)
        self.j=Ledger(self.root/'ledger.jsonl',self.inherited,self.approval)

    def test_failure_and_cancel_never_refund(self):
        self.j.event('RESERVE','a',5);self.j.event('START','a');self.j.event('FAILED','a')
        self.j.event('RESERVE','b',5);self.j.event('CANCELLED_NO_LAUNCH','b')
        self.assertEqual(self.j.snapshot()['requests'],516)
        with self.assertRaises(ValueError):self.j.event('RESERVE','c',0)

    def test_deduplicate_and_bad_transitions(self):
        self.j.event('RESERVE','a',1)
        with self.assertRaises(ValueError):self.j.event('RESERVE','a',1)
        with self.assertRaises(ValueError):self.j.event('COMPLETE','a')
        with self.assertRaises(ValueError):self.j.event('START','b')
        with self.assertRaises(ValueError):self.j.event('REFUND','a')

    def test_corrupt_or_changed_inheritance(self):
        self.j.event('RESERVE','a',1)
        Path(self.inherited['ledger_path']).write_text('new unaccounted request\n')
        with self.assertRaises(ValueError):self.j.snapshot()

    def test_proposal_cannot_authorize(self):
        self.approval['status']='PROPOSED'
        with self.assertRaises(ValueError):self.j.event('RESERVE','a',1)


class Archives(unittest.TestCase):
    def test_safe_paths(self):
        for p in ('../a','/a','a/../b','a\\b','C:/file','.','a//b','a\nb'):
            with self.assertRaises(ValueError):safe_relative(p)

    def test_complete_roundtrip_and_no_overwrite(self):
        with tempfile.TemporaryDirectory()as t:
            r=Path(t);(r/'test.json').write_text('{"synthetic":true}\n')
            s=dict(schema='hs.strong.public-selection.v1',terminal_status='COMPLETE',
                   private_literals=['private-uuid-value'],files=[dict(path='test.json',bytes=19,
                   sha256=sha(r/'test.json'),payload_kind='utf8-text',
                   public_review='TEXT_REVIEWED_NO_PRIVATE_IDENTIFIERS')],
                   withheld_numeric_payloads=[dict(logical_id='not-public',sha256='a'*64,bytes=4)])
            f=r/'archive.tar.gz';result=archive.create(r,s,f)
            replay=archive.replay(f,r/'restored',result['archive_sha256'])
            self.assertEqual(replay['unavailable_numeric_payloads'],1)
            self.assertEqual((r/'restored/test.json').read_bytes(),(r/'test.json').read_bytes())
            with self.assertRaises(ValueError):archive.replay(f,r/'restored',result['archive_sha256'])
            s['terminal_status']='RUNNING'
            with self.assertRaises(ValueError):archive.create(r,s,r/'active.tar.gz')

    def test_traversal_and_missing_index(self):
        with tempfile.TemporaryDirectory()as t:
            r=Path(t)
            for name in ('../outside','test.json'):
                f=r/('bad-'+str(len(name))+'.tar.gz')
                with tarfile.open(f,'w:gz')as tf:
                    m=tarfile.TarInfo(name);m.size=2;tf.addfile(m,io.BytesIO(b'{}'))
                with self.assertRaises(ValueError):archive.replay(f,r/'out',sha(f))


class SavedNumericContracts(unittest.TestCase):
    def test_all64_KV_layout_and_nonfinite(self):
        profile=dict(format='dense_seq_f16_v1',writer_sha256='1'*64,target_model_sha256='2'*64,
                     layer_map_source_sha256='3'*64,host_writer_reviewed=True,capacity=1024,
                     layers=[dict(id=i,k_elements=2,v_elements=2)for i in range(64)])
        raw=struct.pack('<IiII',0xaf143cd8,0,1,1)+struct.pack('<iIi',0,1,0)+struct.pack('<II',0,64)
        for _ in range(128):raw+=struct.pack('<iQHH',1,4,0x3c00,0x4000)
        with tempfile.TemporaryDirectory()as t:
            a=Path(t)/'a.bin';b=Path(t)/'b.bin';a.write_bytes(raw);b.write_bytes(raw)
            result=state(a,b,1,profile);self.assertEqual(result['layers'],64)
            b.write_bytes(raw[:-2]+struct.pack('<H',0x7c00))
            with self.assertRaises(ValueError):state(a,b,1,profile)
            b.write_bytes(raw+b'padding')
            with self.assertRaises(ValueError):state(a,b,1,profile)
            with self.assertRaises(ValueError):state(a,a,1,{**profile,'layers':profile['layers'][:-1]})

    def test_complete_F32_no_tolerance(self):
        with tempfile.TemporaryDirectory()as t:
            a=Path(t)/'a';b=Path(t)/'b';a.write_bytes(struct.pack('<ff',1,2));b.write_bytes(a.read_bytes())
            self.assertEqual(vectors(a,b,2,1)['bytes'],8)
            b.write_bytes(struct.pack('<II',0x3f800001,0x40000000))
            with self.assertRaises(ValueError):vectors(a,b,2,1)
            b.write_bytes(struct.pack('<ff',1,float('nan')))
            with self.assertRaises(ValueError):vectors(a,b,2,1)

    def test_actual_quantized_padding_and_column_order(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);gold=[]
            for i in range(2):
                p=root/('gold'+str(i));p.write_bytes(bytes([i])*36);gold.append(p)
            p=root/'batch';p.write_bytes(gold[0].read_bytes()+gold[1].read_bytes())
            d=dict(file='batch',rows=2,bytes=72,sha256=sha(p))
            self.assertEqual(quantized_chunks(root,[d],gold,2)['rows'],2)
            with self.assertRaises(ValueError):quantized_chunks(root,[d],list(reversed(gold)),2)


class ExecutionAdmission(unittest.TestCase):
    def test_complete_caller_does_not_bill_warmup_twice(self):
        classes=[dict(cell=cell,arm=arm,max_observed_caller_s=1)for cell in range(4)for arm in 'GBC']
        proof=caller_cost_proof(classes,3,100)
        self.assertEqual(proof['caller_bound_s'],45);self.assertEqual(proof['required_s'],1153)
        self.assertFalse(proof['whole_phase_fits'])
        with self.assertRaises(ValueError):caller_cost_proof(classes[:-1],3,100)

    def test_premature_export_checks_actual_child(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);(root/'STATE.json').write_text(json.dumps(dict(status='RUNNING')))
            with self.assertRaises(ValueError):
                with terminal_phase(dict(output_root=str(root)),{'COMPLETE'}):pass
            (root/'STATE.json').write_text(json.dumps(dict(status='COMPLETE')))
            (root/'LOCK_RELEASED.private.json').write_text('{}');w=root/'workers/test';w.mkdir(parents=True)
            p=subprocess.Popen(['/usr/bin/sleep','30'])
            try:
                ticks=Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
                (w/'LAUNCH.private.json').write_text(json.dumps(dict(pid=p.pid,start_ticks=ticks)))
                with self.assertRaises(ValueError):
                    with terminal_phase(dict(output_root=str(root)),{'COMPLETE'}):pass
            finally:p.terminate();p.wait(timeout=5)
    def test_optional_phase_and_incomplete_S2_never_launch(self):
        h=Host.__new__(Host);h.c=dict(execution_phase='S2')
        with patch('host.subprocess.Popen',side_effect=RuntimeError('FORBIDDEN'))as launch:
            with self.assertRaises(ValueError):h.run({}, {},'operand',phase='S3')
            with self.assertRaises(ValueError):h.run({}, {},'operand',phase='S2')
            launch.assert_not_called()

    def test_no_public_freeze_no_host_admission(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);manifest=root/'manifest.json';manifest.write_text('{}')
            config=root/'config.json';config.write_text(json.dumps(dict(output_root=str(root/'out'),
                manifest=str(manifest),manifest_sha256=sha(manifest),schema='hs.strong.host-admission.v1',
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                parent_environment=relevant_environment(),
                GPU_authorized=True,F0_public_readback=dict(status='NOT_RUN'))))
            with self.assertRaises(ValueError):Host(config)

    def test_only_assigned_GPU_conflict_pauses(self):
        import types
        with tempfile.TemporaryDirectory()as t:
            c=dict(gpu_uuid='GPU-assigned',gpu_reserve_bytes=1,ram_reserve_bytes=1,
                   disk_required_free_bytes=1,output_root=t)
            def query(other):
                return [types.SimpleNamespace(stdout='GPU-assigned,24000,1,0,30,300,20\n'),
                        types.SimpleNamespace(stdout=other)]
            with patch('host.subprocess.run',side_effect=query('GPU-other,999\n')):
                resource(c)
            with patch('host.subprocess.run',side_effect=query('GPU-assigned,888\n')):
                with self.assertRaises(ValueError):resource(c)
            with patch('host.subprocess.run',side_effect=query('GPU-assigned,123\n')):
                self.assertEqual(resource(c,own_pid=123)['selected_processes'],[123])

    def test_changed_frozen_source_rejected(self):
        with tempfile.TemporaryDirectory()as t:
            p=Path(t)/'source';p.write_text('frozen');binding={str(p):sha(p)};p.write_text('changed')
            with self.assertRaises(ValueError):verify_files(binding)

    def test_public_readback_bytes_and_private_path_transform(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);a=root/'source';b=root/'download';a.write_text('synthetic');b.write_text('synthetic')
            proof=dict(status='COMPLETE_FILE_BYTES_MATCHED',commit='a'*40,files=[dict(public_path='test',
                url='https://raw.githubusercontent.com/leecdiang/HeteroSpec/'+'a'*40+'/test',
                source_file=str(a),downloaded_file=str(b),sha256=sha(a),bytes=9)])
            verify_public_readback(proof);b.write_text('truncated')
            with self.assertRaises(ValueError):verify_public_readback(proof)
            self.assertEqual(public_text('stb_image_communicate',root),'stb_image_communicate')
            transformed=public_text('stb_image_communicate '+str(root/'file'),root)
            self.assertEqual(transformed,'stb_image_communicate ${HS_ROOT}/file')


if __name__=='__main__':unittest.main()
