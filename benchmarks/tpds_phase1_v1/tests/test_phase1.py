"""Synthetic tests only; no model, GPU or native-library qualification."""
import collections
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import design as d
import analyze as a
import receipts as r
import stage_native as s
import stage_b570_probe as b


def roots(family='Qwen',n=16):
    return [dict(root=f'SYNTHETIC/{family}/{i}',content_sha256=hashlib.sha256(f'{family}/{i}'.encode()).hexdigest(),
                 domain='math' if i<n//2 else 'code',prompt_tokens=200+i) for i in range(n)]

def flat(plan,values=None):
    values=values or {}
    return [dict(slot_id=x['slot_id'],status='COMPLETE',qualified=True,reference_id='SYNTHETIC_R_'+x['family'],
                 service_s=values.get(x['arm'],1.)*(1+x.get('root_index',0)/100)) for x in plan]

class Scheduling(unittest.TestCase):
    def test_williams(self):
        for i in range(4):self.assertEqual(sorted(row[i] for row in d.WILLIAMS),list(range(4)))
        self.assertEqual(len({(row[i],row[i+1]) for row in d.WILLIAMS for i in range(3)}),12)
    def test_rtx_counts(self):
        x=d.structural('rtx');self.assertEqual(len(x),192);self.assertEqual(sum(y['kind']=='measurement' for y in x),96)
    def test_b570_counts(self):
        x=d.structural('b570');self.assertEqual(len(x),216);self.assertEqual(len({y['root'] for y in x}),12)
    def test_geometry_masks(self):
        for x in d.structural('b570'):
            self.assertLessEqual(x['head']+x['width'],x['capacity'])
            self.assertEqual(x['requested_outputs'],'last' if x['width']==32 else 'all')
            self.assertEqual(x['head'],x['boundary']-(x['width'] if x['relation']=='inside' else 1))
    def test_structural_pairs(self):
        x=d.structural('rtx')
        for i in range(0,len(x),2):
            self.assertEqual((x[i]['kind'],x[i+1]['kind']),('warmup','measurement'))
            self.assertEqual(x[i]['arm'],x[i+1]['arm']);self.assertEqual(x[i]['root'],x[i+1]['root'])
    def test_natural_counts(self):
        c={f:roots(f) for f in ('Qwen','Smol')};x=d.natural(c)
        self.assertEqual(len(x),1024);self.assertEqual(x,d.natural(c));self.assertEqual(len({y['slot_id'] for y in x}),1024)
    def test_natural_balance(self):
        x=d.natural({f:roots(f) for f in ('Qwen','Smol')})
        positions=collections.Counter((y['family'],y['root'],y['arm'],y['arm_position']) for y in x if y['kind']=='measurement')
        self.assertEqual(set(positions.values()),{1})
    def test_outcome_rejected(self):
        x=roots();x[0]['latency']=1
        with self.assertRaises(ValueError):d.validate_roots(x)
    def test_capacity_rejected(self):
        x=roots();x[0]['prompt_tokens']=897
        with self.assertRaises(ValueError):d.validate_roots(x)
    def test_bool_token_rejected(self):
        x=roots();x[0]['prompt_tokens']=True
        with self.assertRaises(ValueError):d.validate_roots(x)
    def test_duplicate_root_rejected(self):
        x=roots();x[1]['root']=x[0]['root']
        with self.assertRaises(ValueError):d.validate_roots(x)
    def test_duplicate_text_rejected(self):
        x=roots();x[1]['content_sha256']=x[0]['content_sha256']
        with self.assertRaises(ValueError):d.validate_roots(x)
    def test_selection_exclusions(self):
        x=roots(n=40);y=d.panel(x,[x[0]['root']],[x[-1]['content_sha256']])
        self.assertEqual(len(y['selected']),16);self.assertNotIn(x[0],y['selected']);self.assertNotIn(x[-1],y['selected'])
    def test_selection_order(self):
        x=roots(n=40);self.assertEqual(d.panel(x,[],[]),d.panel(list(reversed(x)),[],[]))
    def test_burst_shape(self):
        x=d.burst(roots(),['EXPOSED/a','EXPOSED/b']);self.assertEqual(len(x),16)
        self.assertEqual(sum(len(w['requests']) for w in x),288)
        for w in x:self.assertEqual([r['kind'] for r in w['requests'][:2]],['primer','primer'])
    def test_burst_shared_order(self):
        x=d.burst(roots(),['EXPOSED/a','EXPOSED/b'])
        for session in range(4):
            orders={tuple(r['root'] for r in w['requests']) for w in x if w['session']==session};self.assertEqual(len(orders),1)
    def test_primer_overlap_rejected(self):
        with self.assertRaises(ValueError):d.burst(roots(),[roots()[0]['root'],'EXPOSED/b'])
    def test_write_new(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'x.json';d.write_new(p,{'x':1})
            with self.assertRaises(FileExistsError):d.write_new(p,{})

class Analysis(unittest.TestCase):
    def test_factor_exact(self):
        p=d.natural({f:roots(f) for f in ('Qwen','Smol')});rr=flat(p,dict(W_L4=1,W_P=.9,L_L4=.95,L_P=.8))
        x=a.analyze_natural(p,rr,draws=100)
        for f in ('Qwen','Smol'):
            q=x['families'][f];self.assertEqual(q['family_size'],5)
            self.assertAlmostEqual(q['contrasts'][0]['total_ratio'],.95)
            self.assertAlmostEqual(q['packing_by_cut_interaction']['ratio'],(.8/.95)/.9)
    def test_incomplete_rejected(self):
        p=d.structural('rtx')
        with self.assertRaises(ValueError):a.complete(p,flat(p)[:-1])
    def test_failure_rejected(self):
        p=d.structural('rtx');rr=flat(p);rr[0]['status']='FAILED'
        with self.assertRaises(ValueError):a.complete(p,rr)
    def test_unqualified_rejected(self):
        p=d.structural('rtx');rr=flat(p);rr[0]['qualified']=False
        with self.assertRaises(ValueError):a.complete(p,rr)
    def test_duplicate_rejected(self):
        p=d.structural('rtx');rr=flat(p);rr[-1]=rr[0]
        with self.assertRaises(ValueError):a.complete(p,rr)
    def test_nan_rejected(self):
        p=d.structural('rtx');rr=flat(p);rr[0]['service_s']=float('nan')
        with self.assertRaises(ValueError):a.complete(p,rr)
    def test_mixed_reference_rejected(self):
        p=d.natural({f:roots(f) for f in ('Qwen','Smol')});rr=flat(p);rr[1]['reference_id']='OTHER'
        with self.assertRaises(ValueError):a.analyze_natural(p,rr,draws=20)
    def test_structural_no_global_mean(self):
        p=d.structural('b570');x=a.analyze_structural(p,flat(p));self.assertEqual(len(x['coordinates']),12);self.assertNotIn('speedup',x)
    def burst_records(self,p):
        rr=[]
        for w in p:
            calls=[dict(x,status='COMPLETE',qualified=True,reference_id='SYNTHETIC_R',service_s=.8 if w['draft'] else 1.) for x in w['requests']]
            rr.append(dict(worker_id=w['worker_id'],status='COMPLETE',process_count=1,provision_count=1,requests=calls,
                           launch_to_first_result_s=2.,launch_to_first_test_result_s=4.,test_burst_wall_s=20.,worker_wall_s=30.,model_setup_s=1.,peak_device_bytes=100))
        return rr
    def test_burst_analysis(self):
        p=d.burst(roots(),['EXPOSED/a','EXPOSED/b']);x=a.analyze_burst(p,self.burst_records(p),draws=100)
        self.assertEqual(x['primary']['family_size'],2);self.assertAlmostEqual(x['primary']['contrasts'][0]['total_ratio'],.8)
    def test_fake_multiple_workers_rejected(self):
        p=d.burst(roots(),['EXPOSED/a','EXPOSED/b']);rr=self.burst_records(p);rr[0]['process_count']=16
        with self.assertRaises(ValueError):a.analyze_burst(p,rr,draws=20)
    def test_missing_host_clock_rejected(self):
        p=d.burst(roots(),['EXPOSED/a','EXPOSED/b']);rr=self.burst_records(p);del rr[0]['test_burst_wall_s']
        with self.assertRaises(ValueError):a.analyze_burst(p,rr,draws=20)
    def test_burst_order_rejected(self):
        p=d.burst(roots(),['EXPOSED/a','EXPOSED/b']);rr=self.burst_records(p);rr[0]['requests'].reverse()
        with self.assertRaises(ValueError):a.analyze_burst(p,rr,draws=20)

class HostTools(unittest.TestCase):
    def evidence(self):return dict(four_arms_qualified=True,distinct_mechanism=False,unanswered_natural_question=False,
        source_review=True,trace_review=True,numerical_failure=False,engineering_open=False,budget_available=True)
    def test_independent_branch_skip(self):self.assertEqual(r.natural_decision(self.evidence()),'CLOSE_R1_NATURAL_ONLY_CONTINUE_R2_AND_PORTABILITY')
    def test_engineering_continues(self):
        e=self.evidence();e['engineering_open']=True;self.assertEqual(r.natural_decision(e),'CONTINUE_HOST_INTEGRATION')
    def test_qualified_new_question(self):
        e=self.evidence();e.update(distinct_mechanism=True,unanswered_natural_question=True);self.assertEqual(r.natural_decision(e),'FREEZE_NEW_R1_NATURAL_PANEL')
    def test_numerical_repair(self):
        e=self.evidence();e['numerical_failure']=True;self.assertEqual(r.natural_decision(e),'REPAIR_DEVELOPMENT_VERSION_KEEP_ORACLE')
    def test_partial_trace_rejected(self):
        with self.assertRaises(ValueError):r.signature([{'group_rows':4}])
    def test_saved_missing_null(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'a.json';p.write_text(json.dumps({'families':{'Q':{'arms':{'M':{'rows':[{'service_s':1.,'target_phases':{'PREFILL':.5}}]}}}}}))
            x=r.saved_costs(p);self.assertIsNone(x['Q']['M']['totals']['planning_s']);self.assertEqual(x['Q']['M']['totals']['service_s'],1.)
    def test_source_bundle(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'a.cpp').write_text('// source\n');m=dict(root=t,files={'a.cpp':s.digest(p/'a.cpp')})
            x=r.source_bundle(m,p/'out.zip');self.assertEqual(x['files'],1)
            self.assertEqual(zipfile.ZipFile(p/'out.zip').namelist(),['a.cpp'])
    def test_secret_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'.env').write_text('SYNTHETIC=1');m=dict(root=t,files={'.env':s.digest(p/'.env')})
            with self.assertRaises(ValueError):r.source_bundle(m,p/'out.zip')
    def test_factorial_stage_independent_of_r2(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);binding=dict(base_commit='a28f3474acac793d07b6e6f462cb70bbccfa6ceb',cores={},frontends={})
            for recipe in ('loop4','packed'):
                core=root/recipe/'source';front=root/recipe/'front';core.mkdir(parents=True);front.mkdir()
                (core/'core.cpp').write_text('// synthetic '+recipe)
                binding['cores'][recipe]=dict(root=str(core),files={'core.cpp':s.digest(core/'core.cpp')})
                for name in s.FRONTEND:(front/name).write_text('// synthetic common frontend, not native')
                binding['frontends'][recipe]=dict(root=str(front),files={name:s.digest(front/name) for name in s.FRONTEND})
            result=s.stage(binding,root/'out',residency=False)
            self.assertEqual(len(result['arms']),4);self.assertEqual(result['burst_arms'],{})
            self.assertEqual(result['arms']['W_P']['core'],'packed')
            self.assertEqual(result['arms']['L_L4']['job_overlay']['lowering'],'LOCAL')
            self.assertEqual(result['core_differences_requiring_attribution_review'],['core.cpp'])
            self.assertFalse(result['residency_overlay'])
            with self.assertRaises(ValueError):s.stage(binding,root/'out',residency=False)
    def test_staging_anchor_failure(self):
        with self.assertRaises(ValueError):s.residency_patch('unrelated input')
    def test_overlay_keeps_request(self):
        text='''int main(int argc,char**argv){
        auto start=Clock::now();t=llama_model_load_from_file(job.at("target_model").get<std::string>().c_str(),mp);d=llama_model_load_from_file(job.at("draft_model").get<std::string>().c_str(),mp);need(t&&d,"models");result["model_load_s"]=since(start);
        const auto*tv=llama_model_get_vocab(t);const auto*dv=llama_model_get_vocab(d);need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocab size");for(int i=0;i<llama_vocab_n_tokens(tv);++i)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocab mismatch");
        if(!pool.draft)pool.draft=make_context();
        const auto request_unchanged=request(t,d,input,spec,"resident",capture,"NATIVE",dir,pool);
        dump(dir/"receipt.json",r);result["requests"].push_back(record);
        llama_model_free(d);d=nullptr;
        }'''
        patched=s.residency_patch(text)
        self.assertIn('if(d && !pool.draft)',patched);self.assertIn('PHASE1_RESULT_READY',patched)
        self.assertIn('request(t,d,input,spec,"resident",capture,"NATIVE",dir,pool)',patched)
        self.assertNotIn('n_outputs_max=',patched)
    def test_source_path_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):s.snapshot(dict(root=t,files={'../secret':'0'*64}))


class VulkanOverlay(unittest.TestCase):
    def fixture(self):
        return """if(req.contains("known_suffix")) {
 if(input.size()+prelude.size()+suffix.size()+2>1024)throw std::runtime_error("probe context");
 observer.evidence.commit(ctx);
 const auto probe_phase=econ_phase(ctx,observer,width,-1);
 for(int j=0;j<count;++j)common_batch_add(b,suffix[at+j],int(all.size()+j),{0},true);
 all.insert(all.end(),suffix.begin()+at,suffix.begin()+at+count);observer.evidence.commit(ctx);
 const int rollback=req.value("rollback",0);
 observer.evidence.commit(ctx);
 observer.evidence.commit(ctx);
 pj metrics={{"explicit_output_reserve",32}};
}"""
    def test_actual_capacity_and_mask(self):
        x=b.patch(self.fixture());self.assertIn('llama_n_ctx(ctx)',x)
        self.assertIn('width<=4 || at+size_t(j)+1==suffix.size()',x)
        self.assertNotIn('explicit_output_reserve',x);self.assertNotIn('+2>1024',x)
        self.assertIn('append_ms',x)
    def test_capture_after_append_clock(self):
        x=b.patch(self.fixture());pos=x.index('const auto phase1_append_end=')
        self.assertGreater(x.index('if(!phase1_clean)observer.evidence.commit(ctx);',pos),pos)
    def test_anchor_drift_rejected(self):
        with self.assertRaises(ValueError):b.patch(self.fixture().replace('explicit_output_reserve','other'))
    def test_staged_probe_binding(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);src=p/'old.inc';src.write_text(self.fixture());out=p/'new.inc'
            b.stage(src,s.digest(src),out)
            j=json.loads((p/'new.inc.binding.json').read_text());self.assertFalse(j['core_changed'])
            self.assertEqual(j['output_sha256'],s.digest(out))
            with self.assertRaises(ValueError):b.stage(src,s.digest(src),out)
    def test_wrong_source_hash_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);src=p/'old.inc';src.write_text(self.fixture())
            with self.assertRaises(ValueError):b.stage(src,'0'*64,p/'new.inc')

if __name__=='__main__':unittest.main()
