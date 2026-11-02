import copy
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import archive
import audit
import budget
import common
import design
import source
import inspect as python_inspect
import importlib.util
spec=importlib.util.spec_from_file_location('trace_inspect',Path(__file__).resolve().parents[1]/'trace_compare.py')
trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)


def item(identifier='x', n=160, domain='math'):
    ids = [1] * (n-1) + [2 + int(hashlib.sha256(identifier.encode()).hexdigest()[:4],16)%1000]
    return {'id': identifier, 'prompt_ids': ids, 'prompt_ids_sha256': common.digest(ids), 'cap':128,
            'domain':domain,'text_sha256':hashlib.sha256(identifier.encode()).hexdigest(),'source_revision':'f'*40}


def ordinary():
    x=item();s=design.slot(x,'R','off','development','test')
    return {'slot':s,'input_id':x['id'],'prompt_ids':x['prompt_ids'],'ids':[4]*128,'eog':[False]*128,
            'length':128,'terminal_id':4,'stop_reason':'CAP','cycles':[], 'diagnostic':False,'performance_eligible':True,'service_seconds':1}


def spec_record():
    x=item();s=design.slot(x,'C_QB','off','development','spec')
    return {'slot':s,'input_id':x['id'],'prompt_ids':x['prompt_ids'],'ids':[4,5,9], 'eog':[False,False,True],
            'length':3,'terminal_id':9,'stop_reason':'EOG','diagnostic':False,'performance_eligible':True,'service_seconds':1,
            'cycles':[{'cycle':0,'base':160,'output_begin':1,'verify_ids':[4,5,6,7],'proposals':[5,6,7],
                       'decisions':[5,9,8,10],'accepted':1,'emitted':[5,9],'bonus':False,'keep':162,'target_kv_max':161,'draft_kv_max':161}]}


class CommonTests(unittest.TestCase):
    def test_input(self): self.assertEqual(common.input_check(item())['cap'],128)
    def test_extent(self):
        with self.assertRaises(ValueError): common.input_check(item(n=900))
    def test_hash(self):
        x=item();x['prompt_ids_sha256']='0'*64
        with self.assertRaises(ValueError): common.input_check(x)
    def test_vocab(self):
        x=item();x['prompt_ids'][0]=128256
        with self.assertRaises(ValueError): common.input_check(x)
    def test_endpoint(self): self.assertEqual(common.endpoint(ordinary())['length'],128)
    def test_truncated(self):
        r=ordinary();r['ids']=r['ids'][:2];r['eog']=[False]*2;r['length']=2
        with self.assertRaises(ValueError): common.endpoint(r)
    def test_terminal(self):
        r=ordinary();r['terminal_id']=5
        with self.assertRaises(ValueError): common.endpoint(r)
    def test_eog_continuation(self):
        r=ordinary();r['eog'][10]=True
        with self.assertRaises(ValueError): common.endpoint(r)
    def test_path(self):
        with self.assertRaises(ValueError): common.confined('/tmp/epoch','../outside')
    def test_write_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';common.write(p,1)
            with self.assertRaises(FileExistsError): common.write(p,2)


class BudgetTests(unittest.TestCase):
    def setUp(self): self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'ledger'
    def tearDown(self): self.temp.cleanup()
    def test_extend(self):
        budget.extend(self.path,10,100,'initial');budget.extend(self.path,20,200,'next mechanism')
        self.assertEqual(budget.totals(self.path)['credit_limit'],30)
    def test_counts_separate(self):
        budget.extend(self.path,100,1000,'initial');budget.reserve(self.path,'a',2,5,100)
        budget.append(self.path,{'event':'END','attempt':'a','completed_model_requests':2,'operator_calls':0,'seconds':3})
        t=budget.totals(self.path);self.assertEqual((t['credits_reserved'],t['completed_model_requests']),(7,2))
    def test_open_attempt(self):
        budget.extend(self.path,10,100,'initial');budget.reserve(self.path,'a',1,0,10)
        with self.assertRaises(ValueError): budget.reserve(self.path,'b',1,0,10)
    def test_renew(self):
        budget.extend(self.path,1,10,'initial')
        with self.assertRaises(ValueError): budget.reserve(self.path,'a',2,0,1)
        budget.extend(self.path,20000,1000000,'larger controlled diagnostic tranche')
        budget.reserve(self.path,'a',2,0,1)
    def test_no_reuse(self):
        budget.extend(self.path,10,100,'initial');budget.reserve(self.path,'a',1,0,1)
        budget.append(self.path,{'event':'END','attempt':'a','completed_model_requests':0,'operator_calls':0,'seconds':1})
        with self.assertRaises(ValueError): budget.reserve(self.path,'a',1,0,1)
    def test_tamper(self):
        budget.extend(self.path,10,100,'initial');self.path.write_text(self.path.read_text().replace('"credits":10','"credits":100'))
        with self.assertRaises(ValueError): budget.load(self.path)
    def test_impossible_counts(self):
        budget.extend(self.path,10,100,'initial');budget.reserve(self.path,'a',1,5,1)
        budget.append(self.path,{'event':'END','attempt':'a','completed_model_requests':6,'operator_calls':0,'seconds':1})
        with self.assertRaises(ValueError): budget.totals(self.path)


class DesignTests(unittest.TestCase):
    def test_baseline(self): self.assertEqual(len(design.baseline([item(str(i)) for i in range(3)])),30)
    def test_references(self): self.assertEqual(len(design.references([item(str(i)) for i in range(24)])),48)
    def test_qualification(self): self.assertEqual(len(design.qualification([item(str(i)) for i in range(24)])),240)
    def test_timing_counts(self): self.assertEqual(sum(len(design.timing([item(str(i)) for i in range(24)],s)) for s in range(6)),1728)
    def test_williams(self): self.assertTrue(design.timing_balance([item(str(i)) for i in range(24)]))
    def test_period(self):
        with self.assertRaises(ValueError): design.timing([item()],6)
    def test_natural_pool(self):
        pool=[item(f'{d}-{b}-{j}',160 if b==0 else 600,d) for d in ('code','math') for b in (0,1) for j in range(8)]
        self.assertEqual(len(design.select(pool,[],24)),24)
    def test_no_fabricated_length(self):
        with self.assertRaises(ValueError): design.select([item(str(i),160) for i in range(100)],[],24)
    def test_exclusion(self):
        pool=[item(f'{d}-{b}-{j}',160 if b==0 else 600,d) for d in ('code','math') for b in (0,1) for j in range(4)]
        selected=design.select(pool,[pool[0]['id']],12);self.assertNotIn(pool[0]['id'],[x['id'] for x in selected])
    def test_platform_reference(self):
        keys=('target_sha256','draft_sha256','vocabulary_sha256','template_sha256','n_ctx','kv_dtype','k','cap','greedy','panel_sha256')
        a={k:k for k in keys};b=dict(a,backend='Vulkan',draft_gpu_layers=0)
        r=design.compatible_contract(a,b);self.assertTrue(r['same_model_request_contract']);self.assertFalse(r['requires_CUDA_Vulkan_reference_equality'])
    def test_quantization_not_substituted(self):
        a={'target_sha256':'q8'};b={'target_sha256':'q6'}
        self.assertFalse(design.compatible_contract(a,b)['same_model_request_contract'])


class AuditTests(unittest.TestCase):
    def test_cycle_mapping(self): self.assertEqual(audit.transactions(spec_record())[2],'verify-0-1')
    def test_short_proposal_rejected(self):
        r=spec_record();r['cycles'][0]['proposals']=r['cycles'][0]['proposals'][:2];r['cycles'][0]['decisions']=r['cycles'][0]['decisions'][:3]
        with self.assertRaises(ValueError): audit.transactions(r)
    def test_wrong_pending(self):
        r=spec_record();r['cycles'][0]['verify_ids'][0]=44
        with self.assertRaises(ValueError): audit.transactions(r)
    def test_wrong_accept(self):
        r=spec_record();r['cycles'][0]['accepted']=2
        with self.assertRaises(ValueError): audit.transactions(r)
    def test_wrong_keep(self):
        r=spec_record();r['cycles'][0]['keep']=163
        with self.assertRaises(ValueError): audit.transactions(r)
    def test_missing_cycle(self):
        r=spec_record();r['cycles']=[]
        with self.assertRaises(ValueError): audit.transactions(r)
    def test_extra_cycle(self):
        r=spec_record();r['cycles']*=2
        with self.assertRaises(ValueError): audit.transactions(r)
    def test_complete_vector(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.f32';values=[0.0]*common.VOCAB;values[77]=10.;p.write_bytes(struct.pack('<%df'%len(values),*values));self.assertEqual(audit.full_vector(p)[0],77)
    def test_vector_truncation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.f32';p.write_bytes(b'\0'*4)
            with self.assertRaises(ValueError): audit.full_vector(p)
    def test_vector_nonfinite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.f32';p.write_bytes(struct.pack('<f',float('nan'))+b'\0'*(4*(common.VOCAB-1)))
            with self.assertRaises(ValueError): audit.full_vector(p)
    def test_first_max(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.f32';p.write_bytes(b'\0'*common.VOCAB*4);self.assertEqual(audit.full_vector(p)[0],0)
    def test_diagnostic_timing(self):
        r=ordinary();r['slot']['stage']='measured';r['slot']['session']=0;r['slot']['label']='R';r['diagnostic']=True
        with self.assertRaises(ValueError): audit.performance([r],['x'])
    def test_incomplete_costs(self):
        with self.assertRaises(ValueError): audit.performance([],['x'])
    def test_cost_arithmetic_dual(self):
        rows=[]
        for s in range(6):
            for arm in design.TIMING:
                r=ordinary();r['slot']=design.slot(item(),arm,'off','measured',f'{s}-{arm}',s)
                r['service_seconds']={'R':10,'M_PQ':8,'M_QB':8,'C_PQ_A':6,'C_PQ_B':4,'C_QB':4}[arm];rows.append(r)
        a=audit.performance(rows,['x']);self.assertAlmostEqual(a['means']['layout'],.8);self.assertFalse(a['practical_layout_screen'])
    def test_all_blocks_retained(self):
        rows=[]
        for s in range(6):
            for arm in design.TIMING:
                r=ordinary();r['slot']=design.slot(item(),arm,'off','measured',f'{s}-{arm}',s);r['service_seconds']=4. if arm=='C_QB' else 5.;rows.append(r)
        r=rows[-1];r['service_seconds']=9.
        a=audit.performance(rows,['x']);self.assertEqual(a['QB_slower_blocks'],1);self.assertFalse(a['practical_layout_screen'])


class StorageAndTraceTests(unittest.TestCase):
    def test_archive_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'raw';root.mkdir();(root/'state.bin').write_bytes(b'1234');(root/'model.gguf').write_bytes(b'not shipped')
            dest=Path(d)/'delivery';archive.pack(root,dest,2);self.assertEqual(archive.verify(dest)['members'],1)
    def test_archive_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'raw';root.mkdir();(root/'x').write_text('data');dest=Path(d)/'delivery';archive.pack(root,dest)
            (dest/'part-0000.zip').write_bytes(b'bad')
            with self.assertRaises(ValueError): archive.verify(dest)
    def test_trace_stride(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tensor';p.write_bytes(struct.pack('<6f',1,2,99,3,4,99))
            m={'type':'f32','ne':[2,2,1,1],'nb':[4,12,24,24],'bytes':24}
            self.assertEqual(trace.logical_row(p,m,1,1),struct.pack('<2f',3,4))
    def test_trace_bounds(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tensor';p.write_bytes(b'\0'*16)
            with self.assertRaises(ValueError):trace.logical_row(p,{'type':'f32','ne':[2,2,1,1],'nb':[4,99,16,16],'bytes':16},1,1)
    def test_source_anchor_fail_closed(self):
        with self.assertRaises(ValueError):source.graph_port('wrong source')
    def test_duplicate_anchor(self):
        with self.assertRaises(ValueError):source.once('a a','a','b')
    def test_cpp_cycle(self):
        compiler=shutil.which('g++');self.assertIsNotNone(compiler)
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'test.cpp';exe=Path(d)/'test'
            src.write_text(r'''#include "cycle.hpp"
#include <cassert>
int main(){
 for(int n=1;n<=3;n++)for(int mask=0;mask<(1<<n);mask++)for(int remaining=1;remaining<=5;remaining++){
  std::vector<int> p,d;for(int i=0;i<n;i++){p.push_back(10+i);d.push_back(mask&(1<<i)?10+i:20+i);}d.push_back(30);
  auto x=hs_cycle::select(p,d,remaining,[](int){return false;});int a=0;std::vector<int> expected;
  for(int i=0;i<n;i++){bool eq=p[i]==d[i];if(eq)a++;expected.push_back(d[i]);if(int(expected.size())==remaining||!eq)break;}
  bool bonus=(int(expected.size())<remaining&&a==n);if(bonus)expected.push_back(30);
  assert(x.accepted==a&&x.emitted==expected&&x.bonus==bonus);
 }
 auto e=hs_cycle::select(std::vector<int>{9,10},std::vector<int>{9,10,11},8,[](int t){return t==9;});assert(e.stopped&&e.accepted==1&&e.emitted.size()==1&&!e.bonus);
}''')
            subprocess.run([compiler,'-std=c++17','-Wall','-Wextra','-Werror','-I',str(Path(__file__).resolve().parents[1]),str(src),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True,capture_output=True)

if __name__=='__main__':unittest.main()
