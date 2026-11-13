import contextlib, copy, hashlib, io, json, os, stat, sys, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import common, sources, host, jobs, analysis, compare

class Tools(unittest.TestCase):
    def setUp(self):self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name)
    def tearDown(self):self.t.cleanup()
    def file(self,name,data=b'x'):
        p=self.p/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return p
    def archive(self,entries,manifest=True):
        p=self.p/'kit.zip'
        with zipfile.ZipFile(p,'w') as z:
            for k,v in entries.items():z.writestr(k,v)
            if manifest:z.writestr('SOURCE_ASSET_MANIFEST.json',json.dumps({'files':{k:{'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} for k,v in entries.items()}}))
        return p
    def test_need_under_optimization(self):
        with self.assertRaises(RuntimeError):common.need(False,'x')
    def test_write_once(self):
        common.save(self.p/'x.json',{'a':1})
        with self.assertRaises(FileExistsError):common.save(self.p/'x.json',{})
    def test_tree_identity(self):
        self.file('src/x.hpp');m=common.inventory(self.p/'src');common.verify_tree(self.p/'src',m)
        self.file('src/missing-header.hpp')
        with self.assertRaises(RuntimeError):common.verify_tree(self.p/'src',m)
    def test_symlink_refused(self):
        self.file('x');(self.p/'l').symlink_to(self.p/'x')
        with self.assertRaises(RuntimeError):common.inventory(self.p)
    def test_archive_roundtrip(self):
        z=self.archive({'native/a':b'abc'});m=sources.extract(z,self.p/'out',common.sha(z));self.assertEqual(m['native/a'],hashlib.sha256(b'abc').hexdigest())
    def test_bad_archive_hash(self):
        z=self.archive({'x':b'x'})
        with self.assertRaises(RuntimeError):sources.extract(z,self.p/'out','0'*64)
    def test_zip_traversal(self):
        for i,path in enumerate(('../x','/x','C:/x','a\\b')):
            z=self.p/f'bad{i}.zip'
            with zipfile.ZipFile(z,'w') as f:f.writestr(path,b'x')
            with self.subTest(path=path),self.assertRaises(RuntimeError):sources.extract(z,self.p/f'o{i}',common.sha(z))
    def test_zip_symlink(self):
        z=self.p/'s.zip';r=zipfile.ZipInfo('link');r.create_system=3;r.external_attr=(stat.S_IFLNK|0o777)<<16
        with zipfile.ZipFile(z,'w') as f:f.writestr(r,'/tmp')
        with self.assertRaises(RuntimeError):sources.extract(z,self.p/'out',common.sha(z))
    def test_zip_expansion(self):
        z=self.archive({'x':b'x'*100})
        with self.assertRaises(RuntimeError):sources.extract(z,self.p/'out',common.sha(z),10)
    def test_missing_manifest_member(self):
        z=self.archive({'x':b'x'});out=self.p/'out';sources.extract(z,out,common.sha(z));self.assertTrue((out/'x').exists())
    def test_balanced_function_parser(self):
        s='static json modules(){auto x="}"; /* } */ if(true){x="{";}return {}; }\nint tail=1;'
        x,n=sources.function_replace(s,'modules','static json modules(){return {}; }');self.assertEqual(n,1);self.assertIn('int tail=1;',x)
    def test_unknown_function(self):self.assertEqual(sources.function_replace('abc','modules','x'),('abc',0))
    def test_unterminated_function(self):
        with self.assertRaises(RuntimeError):sources.function_replace('static json modules(){','modules','x')
    def test_reviewed_frontend_port(self):
        f=self.p/'front';f.mkdir();(f/'entry.cpp').write_text('#include <windows.h>\nstatic json module_inventory(){return {}; }\nvoid init(){wchar_t exe[32768];GetModuleFileNameW(nullptr,exe,32768);auto base=LoadLibraryW(L"x");auto init=(void(*)())GetProcAddress(base,"ggml_time_init");init();}\n#include "profiler.inc"\nint arithmetic=123;')
        r=sources.port(f);self.assertEqual(r['status'],'SOURCE_PORTED_NOT_BUILT');s=(f/'entry.cpp').read_text();self.assertIn('int arithmetic=123;',s);self.assertIn('ggml_time_init();',s);self.assertNotIn('LoadLibraryW(',s)
    def test_unknown_windows_call_is_not_stubbed(self):
        f=self.p/'front';f.mkdir();(f/'worker.cpp').write_text('void f(){LoadLibraryW(x);}')
        self.assertEqual(sources.port(f)['status'],'PORT_ADAPTATION_REQUIRED')
    def test_private_environment_not_forwarded(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'x','GH_TOKEN':'x','HS_UNKNOWN':'x','LD_PRELOAD':'x'}):
            e=host.environment('GPU-test');self.assertNotIn('GH_TOKEN',e);self.assertNotIn('LD_PRELOAD',e);self.assertEqual(e['CUDA_VISIBLE_DEVICES'],'GPU-test')
    def test_gpu_csv(self):self.assertEqual(host.csv_rows('1, GPU-x, RTX A5000\n'),[['1','GPU-x','RTX A5000']])
    def test_unknown_process_schema(self):
        with patch.object(host,'query',return_value={'ok':True,'stdout':'bad'}),self.assertRaises(RuntimeError):host.processes('GPU-test')
    def test_reservation(self):
        j={'inputs':[{'input':{'prompt_ids':[1,2],'cap':128}}]};self.assertEqual(host.reservation(j),(1,2052))
        self.assertEqual(host.reservation({'cases':[{'forced':[{'ids':[1,2]}]}]}),(1,2))
    def test_unsupported_empty_job(self):
        with self.assertRaises(RuntimeError):host.reservation({})
    def test_bad_cap(self):
        with self.assertRaises(RuntimeError):host.reservation({'inputs':[{'input':{'prompt_ids':[1],'cap':0}}]})
    def comparisons(self,mode='candidate_vs_reference',different=False):
        a=self.file('a.bin',b'1234');b=self.file('b.bin',b'1235' if different else b'1234')
        return {'mode':mode,'reference_core':'pristine-upstream','reference_executable_sha256':'a','candidate_executable_sha256':'a' if mode=='reference_repeat' else 'b','scope':'fixture only','pairs':[{'kind':'full_requested_logits','reference':str(a),'candidate':str(b)}]}
    def test_exact_comparison(self):self.assertTrue(compare.compare(self.comparisons())['passed'])
    def test_difference_retained(self):self.assertFalse(compare.compare(self.comparisons(different=True))['passed'])
    def test_reference_repeat(self):self.assertTrue(compare.compare(self.comparisons('reference_repeat'))['passed'])
    def test_self_comparison_refused(self):
        m=self.comparisons();m['pairs'][0]['candidate']=m['pairs'][0]['reference']
        with self.assertRaises(RuntimeError):compare.compare(m)
    def test_candidate_cannot_be_reference(self):
        m=self.comparisons();m['reference_core']='candidate'
        with self.assertRaises(RuntimeError):compare.compare(m)
    def make_panel(self):
        target=self.file('target',b't');draft=self.file('draft',b'd')
        models={'target_model':str(target),'target_sha256':common.sha(target),'draft_model':str(draft),'draft_sha256':common.sha(draft)}
        roots=[{'id':f'r{i:02}','family':'Qwen','prompt_ids':[1,2],'cap':128} for i in range(16)]
        pre=[{'id':f'p{i}','family':'Qwen','prompt_ids':[1,2],'cap':128} for i in range(2)]
        common.save(self.p/'inputs.json',{'inputs':roots});common.save(self.p/'primers.json',{'inputs':pre});common.save(self.p/'models.json',models)
        jobs.panel(self.p/'inputs.json',self.p/'primers.json',self.p/'models.json',self.p/'panel')
        plan=common.read(self.p/'panel/PLAN.json');records=[]
        for w in plan['workers']:
            requests=[{'root':r,'service_s':1. if w['arm'].endswith('D4') else 2.,'reference_id':'fixture','reference_compatible':True,'trace_valid':True} for r in w['primers']+w['roots']]
            records.append({'id':w['id'],'job_sha256':w['job_sha256'],'status':'COMPLETE','native_checks_passed':True,'requests':requests,'actual_host_clocks':{'launch_to_first_result_s':2.,'launch_to_first_test_result_s':4.,'test_burst_wall_s':32.,'worker_wall_s':40.}})
        return plan,records
    def test_six_arm_complete_schedule(self):
        p,r=self.make_panel();self.assertEqual(len(r),24);self.assertEqual(p['formal_requests'],384)
        for w in p['workers']:
            j=common.read(self.p/'panel'/w['job'])
            if w['arm'].endswith('_M'):self.assertNotIn('draft_model',j)
    def test_statistics_known_ratio(self):
        p,r=self.make_panel();o=analysis.analyze(p,r);self.assertAlmostEqual(o['contrasts'][0]['total_ratio'],.5);self.assertEqual(o['contrasts'][0]['adjusted_interval'],[.5,.5]);self.assertEqual(o['contrasts'][-1]['total_ratio'],1.)
    def test_no_partial_confirmation(self):
        p,r=self.make_panel()
        with self.assertRaises(RuntimeError):analysis.analyze(p,r[:-1])
    def test_no_duplicate_workers(self):
        p,r=self.make_panel()
        with self.assertRaises(RuntimeError):analysis.analyze(p,r+[r[0]])
    def test_no_failed_subset_analysis(self):
        p,r=self.make_panel();r[0]['native_checks_passed']=False
        with self.assertRaises(RuntimeError):analysis.analyze(p,r)
    def test_no_mixed_reference(self):
        p,r=self.make_panel();r[0]['requests'][3]['reference_id']='other'
        with self.assertRaises(RuntimeError):analysis.analyze(p,r)
    def test_no_changed_job(self):
        p,r=self.make_panel();r[0]['job_sha256']='x'
        with self.assertRaises(RuntimeError):analysis.analyze(p,r)
    def test_no_changed_order(self):
        p,r=self.make_panel();r[0]['requests'][2],r[0]['requests'][3]=r[0]['requests'][3],r[0]['requests'][2]
        with self.assertRaises(RuntimeError):analysis.analyze(p,r)
    def test_missing_actual_clocks(self):
        p,r=self.make_panel();r[0]['actual_host_clocks']['test_burst_wall_s']=None
        with self.assertRaises(RuntimeError):analysis.analyze(p,r)
    def test_missing_reference_identity(self):
        p,r=self.make_panel();r[0]['requests'][0]['reference_id']=None
        with self.assertRaises(RuntimeError):analysis.analyze(p,r)
    def test_nan_rejected(self):
        p,r=self.make_panel();r[0]['requests'][3]['service_s']=float('nan')
        with self.assertRaises(RuntimeError):analysis.analyze(p,r)

if __name__=='__main__':unittest.main()
