"""Synthetic review-regression tests. No native model execution."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import baselines as bs
import build_freeze as bf
import design as d
import analyze as a
import receipts as r
import stage_native as st
from test_phase1 import roots, baseline_review, flat
import test_phase1 as original_tests


class BaselineCoverage(unittest.TestCase):
    def test_all_four_controls(self):
        p=d.burst(roots(),['EXPOSED/a','EXPOSED/b'],baseline_review(True))
        self.assertEqual(len(p),24);self.assertEqual(sum(len(x['requests']) for x in p),432)
        self.assertEqual(len(p[0]['baseline_coverage']['target_only_arms']),4)
        result=a.analyze_burst(p,original_tests.Analysis().burst_records(p),draws=100)
        self.assertEqual(result['primary']['family_size'],4)
        self.assertEqual({x['denominator'] for x in result['primary']['contrasts']},set(bs.TARGET_ARMS.values()))
    def test_missing_mixed_strategy(self):
        x=baseline_review();del x['strategies']['W_P']
        with self.assertRaises(ValueError):bs.baseline_set(x)
    def test_speed_cannot_exclude(self):
        x=baseline_review();x['strategies']['W_P']=dict(status='INAPPLICABLE',reason='SLOW')
        with self.assertRaises(ValueError):bs.baseline_set(x)
    def test_equivalence_needs_cost_path(self):
        x=baseline_review();del x['strategies']['W_P']['frontend_and_cost_window_equivalence']
        with self.assertRaises(ValueError):bs.baseline_set(x)
    def test_equivalence_cannot_chain(self):
        x=baseline_review();x['strategies']['W_P']['representative']='L_L4'
        with self.assertRaises(ValueError):bs.baseline_set(x)
    def test_unsupported_is_explicit(self):
        x=baseline_review(True);x['strategies']['W_P']=dict(status='INAPPLICABLE',reason='UNSUPPORTED_NATIVE_PATH',failure_evidence='synthetic',bounded_diagnosis='synthetic',scope_consequence='synthetic')
        self.assertEqual(len(bs.baseline_set(x)['arms']),5)
    def test_cannot_exclude_development_best(self):
        x=baseline_review(True);x['observed_development_best']='W_P'
        x['strategies']['W_P']=dict(status='INAPPLICABLE',reason='CAPACITY_NOT_ADMITTED',failure_evidence='x',bounded_diagnosis='x',scope_consequence='x')
        with self.assertRaises(ValueError):bs.baseline_set(x)
    def test_confirmation_ranking_rejected(self):
        x=baseline_review();x['selection_scope']='R2_fastest'
        with self.assertRaises(ValueError):bs.baseline_set(x)
    def test_mixed_coverage_rejected(self):
        p=d.burst(roots(),['EXPOSED/a','EXPOSED/b'],baseline_review(True))
        p[1]['baseline_coverage']=bs.baseline_set(baseline_review())
        with self.assertRaises(ValueError):a.analyze_burst(p,original_tests.Analysis().burst_records(p),draws=10)
    def test_old_plan_not_reinterpreted(self):
        p=d.burst(roots(),['EXPOSED/a','EXPOSED/b'],baseline_review());del p[0]['protocol_version']
        with self.assertRaises(ValueError):a.analyze_burst(p,original_tests.Analysis().burst_records(p),draws=10)
    def test_frozen_version_kept(self):
        x=dict(status='STARTED',code_commit='old',host_observation='seen',panel_version='old',freeze_receipt='receipt')
        self.assertIn('NO_MID_PANEL_CHANGE',bs.adoption_action(x))
    def test_unknown_does_not_mean_unstarted(self):
        self.assertIn('CHECK_HOST_STATE',bs.adoption_action({'status':'UNKNOWN'}))


class CostCoverage(unittest.TestCase):
    def calc(self,rows,expected=2,roots_list=None):
        f=dict(arms={'D4':dict(rows=rows,expected_requests=expected)})
        if roots_list is not None:f['roots']=roots_list
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'cost.json';p.write_text(json.dumps({'families':{'Q':f}}))
            return r.saved_costs(p,expected_sessions=2)['Q']['D4']
    def test_nested_missing_does_not_sum_as_total(self):
        x=self.calc([{'service_s':1,'draft_phases':{'PROPOSE':.2}}, {'service_s':2,'draft_phases':{}}])
        self.assertIsNone(x['draft_phases_s']['PROPOSE'])
        self.assertEqual(x['phase_coverage']['draft_phases']['PROPOSE']['observed_sum_s'],.2)
        self.assertEqual(x['totals']['service_s'],3)
    def test_missing_request_invalidates_total(self):
        x=self.calc([{'service_s':1,'draft_phases':{'PROPOSE':.2}}])
        self.assertIsNone(x['totals']['service_s']);self.assertEqual(x['coverage']['service_s']['observed_sum_s'],1)
    def test_unmeasured_default_zero_is_null(self):
        x=self.calc([{'service_s':1,'draft_phases':{'DRAFT_SYNC':0}}],1)
        self.assertIsNone(x['draft_phases_s']['DRAFT_SYNC'])
    def test_measured_zero_preserved(self):
        row=dict(service_s=1,draft_phases={'DRAFT_SYNC':0},phase_measurement_status={'draft_phases':{'DRAFT_SYNC':'MEASURED'}})
        self.assertEqual(self.calc([row],1)['draft_phases_s']['DRAFT_SYNC'],0)
    def test_not_applicable_is_not_measured_zero(self):
        row=dict(service_s=1,phase_measurement_status={'draft_phases':{'PROPOSE':'NOT_EXECUTED'}})
        x=self.calc([row],1)
        self.assertIsNone(x['draft_phases_s']['PROPOSE']);self.assertEqual(x['phase_coverage']['draft_phases']['PROPOSE']['status'],'NOT_APPLICABLE')
    def test_unknown_expected_is_not_full_total(self):
        self.assertIsNone(self.calc([{'service_s':1}],None)['totals']['service_s'])
    def test_duplicate_root_slot_rejected(self):
        row=dict(root='r',session=0,service_s=1)
        with self.assertRaises(ValueError):self.calc([row,row],2,['r'])
    def test_declared_matrix_rejects_missing_session_total(self):
        self.assertIsNone(self.calc([dict(root='r',session=0,service_s=1)],None,['r'])['totals']['service_s'])
    def test_nonfinite_cost_rejected(self):
        with self.assertRaises(ValueError):self.calc([dict(service_s=1,draft_phases={'PROPOSE':float('nan')})],1)


class AppendWindow(unittest.TestCase):
    def receipt(self):
        return dict(service_seconds=99,capacity_observed=4096,requested_mask='last',observed_copied_rows=1,
                    phase1_clean=True,prefill_outside_append=True,append_includes_phase_bind_sync_and_requested_copy=True,
                    append_begin_us=1000000,append_end_us=1002000,append_ms=2,
                    append_observer_calls=dict(state_exports=0,state_imports=0,reference_replays=0,heavy_captures=0),
                    native_admission_receipt='SYNTHETIC/allocation-reserve-clean-check')
    def normalize(self,value):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'r.json';p.write_text(json.dumps(value))
            return r.normalize_receipt(p,'s','R',True,window='append_after_valid_state',
                    coordinate=dict(capacity=4096,width=32,requested_outputs='last'))
    def test_append_not_service(self):self.assertEqual(self.normalize(self.receipt())['service_s'],.002)
    def test_no_fallback_to_service(self):
        x=self.receipt();del x['append_ms']
        with self.assertRaises(ValueError):self.normalize(x)
    def test_capacity_label_not_observation(self):
        x=self.receipt();x['capacity']=4096;del x['capacity_observed']
        with self.assertRaises(ValueError):self.normalize(x)
    def test_heavy_observer_rejected(self):
        x=self.receipt();x['append_observer_calls']['heavy_captures']=1
        with self.assertRaises(ValueError):self.normalize(x)
    def test_clean_flag_not_observation(self):
        x=self.receipt();del x['append_observer_calls']
        with self.assertRaises(ValueError):self.normalize(x)
    def test_q32_all_output_not_original_mask(self):
        x=self.receipt();x['requested_mask']='all';x['observed_copied_rows']=32
        with self.assertRaises(ValueError):self.normalize(x)
    def test_clock_mismatch(self):
        x=self.receipt();x['append_ms']=99
        with self.assertRaises(ValueError):self.normalize(x)
    def test_analysis_rejects_full_service_structural(self):
        p=d.structural('b570');records=flat(p);records[0]['window']='complete_resident_service'
        with self.assertRaises(ValueError):a.analyze_structural(p,records)


class BuildClosure(unittest.TestCase):
    def fixture(self,p):
        roles={'main.cpp':'source','needed.hpp':'header','generated.hpp':'generated','flags.rsp':'response',
               'CMakeCache.txt':'build_config','compiler.exe':'toolchain','linker.exe':'toolchain',
               'core.lib':'link_input','backend.dll':'runtime_module','worker.exe':'executable',
               'raw-deps.json':'dependency_report','deps.json':'dependency_report','modules.json':'runtime_report'}
        for name in roles:(p/name).write_text('synthetic '+name)
        (p/'deps.json').write_text(json.dumps(dict(source='msvc_source_dependencies',original_reports=[str(p/'raw-deps.json')],
            units=[dict(source=str(p/'main.cpp'),dependencies=[str(p/'needed.hpp'),str(p/'generated.hpp')])])) )
        (p/'modules.json').write_text(json.dumps(dict(observed_after_qualification=True,
            modules=[dict(path=str(p/n),sha256=bf.sha(p/n)) for n in ('backend.dll','worker.exe') ])))
        return dict(schema='phase1.build-inputs.v2',phase='after_native_qualification_before_formal_timing',
            files={n:dict(path=str(p/n),role=role) for n,role in roles.items()},dependency_report='deps.json',runtime_report='modules.json',
            compile_commands=[dict(source=str(p/'main.cpp'),working_directory=str(p),argv=['compiler.exe','@flags.rsp','main.cpp'],compiler='compiler.exe',response_files=['flags.rsp'])],
            link_commands=[dict(working_directory=str(p),argv=['linker.exe','core.lib'],linker='linker.exe',inputs=['core.lib'])],
            generated_files=['generated.hpp'],build_configuration_files=['CMakeCache.txt'],build_environment={'CXXFLAGS':'/O2'},
            qualification_binding='SYNTHETIC_only')
    def test_capture_verify(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(Path(t));f=bf.capture(c);self.assertTrue(bf.verify(c,f,f['loaded_modules']))
    def test_missing_transitive_header(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(Path(t));del c['files']['needed.hpp']
            with self.assertRaises(ValueError):bf.capture(c)
    def test_changed_generated_file(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);c=self.fixture(p);f=bf.capture(c);(p/'generated.hpp').write_text('changed')
            with self.assertRaises(ValueError):bf.verify(c,f)
    def test_changed_options(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(Path(t));f=bf.capture(c);c['compile_commands'][0]['argv'].append('/fp:fast')
            with self.assertRaises(ValueError):bf.verify(c,f)
    def test_changed_loaded_module(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);c=self.fixture(p);f=bf.capture(c);(p/'backend.dll').write_text('changed')
            with self.assertRaises(ValueError):bf.verify(c,f)
    def test_additional_loaded_module(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(Path(t));f=bf.capture(c)
            with self.assertRaises(ValueError):bf.verify(c,f,f['loaded_modules']+[dict(path='extra.dll',sha256='0'*64)])
    def test_unlisted_source_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'main.cpp').write_text('synthetic');(p/'needed.hpp').write_text('synthetic')
            with self.assertRaises(ValueError):st.snapshot(dict(root=t,files={'main.cpp':st.digest(p/'main.cpp')}))
    def test_complete_manifest_accepted(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'main.cpp').write_text('synthetic');(p/'needed.hpp').write_text('synthetic')
            _,data=st.snapshot(dict(root=t,files={x.name:st.digest(x) for x in p.iterdir()}))
            self.assertEqual(len(data),2)

if __name__=='__main__':unittest.main()
