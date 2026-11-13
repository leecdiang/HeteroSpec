"""Editorial/numerical regression tests for the recovery-based final revision.
These checks inspect sources/projections, not new GPU execution or universal equality.
"""
from pathlib import Path
import csv,hashlib,json,math,re,unittest
import numpy as np
P=Path(__file__).resolve().parents[1]
def read(n):return json.loads((P/n).read_text())
class FinalRevision(unittest.TestCase):
 def test_recovery_input_not_refined(self):
  b=read('revision/BASELINE_IDENTITY.json');self.assertIn('Author_Reconstructed',b['source_author_zip']);self.assertIn('not a byte-identical',b['provenance'])
 def test_all_19_original_files_unchanged(self):
  b=read('revision/BASELINE_IDENTITY.json');self.assertEqual(len(b['original_data_files']),19)
  for path,h in b['original_data_files'].items():self.assertEqual(hashlib.sha256((P/path).read_bytes()).hexdigest(),h)
 def test_all_six_equations_unchanged(self):
  b=read('revision/BASELINE_IDENTITY.json');count=0
  for name,old in b['equations'].items():
   new=re.findall(r'\\begin\{equation\}.*?\\end\{equation\}',(P/'sections'/name).read_text(),re.S);self.assertEqual(new,old);count+=len(new)
  self.assertEqual(count,6)
 def test_equal_work_exact_origins(self):
  d=read('data/q8_equal_work.json');self.assertEqual(set(d['origins']),{'APPS/train/65','GSM8K/test/70','GSM8K/test/806','GSM8K/test/986'})
 def test_equal_work_separate_from_live(self):
  a=set(read('data/q8_equal_work.json')['origins']);b=set(read('data/q8_root_sums.json')['roots']);self.assertFalse(a&b)
 def test_equal_work_adverse_origin_retained(self):
  d=read('generated/analysis.json')['equal_work'];self.assertTrue(any(v>1 for c in d for v in c['root_ratios']));self.assertTrue(all(c['ratio']<1 for c in d))
 def test_eight_pilot_arms_retained(self):
  d=read('data_added/a5000_pilot_source_projection.json');self.assertEqual(len(d['live']),8);self.assertEqual(d['root_count'],4);self.assertEqual(d['measurements_per_arm'],8)
 def test_pilot_cost_reconciles(self):
  d=read('generated/A5000_PILOT_RECHECK.json')['local_k7_minus_k3'];self.assertAlmostEqual(d['service_s'],sum(d[x] for x in ('prefill_s','verify_s','draft_s','residual_s')),places=12)
 def test_pilot_not_population_CI(self):
  d=read('generated/A5000_PILOT_RECHECK.json');self.assertEqual(d['intervals'],'None: descriptive pilot');self.assertFalse(d['raw_GPU_replay'])
 def test_all_published_application_points(self):
  d=read('data_added/application_root_ratios.json');self.assertEqual(sum(sum(map(len,s['ratios'])) for s in d['studies']),176)
 def test_application_geometric_field_checks(self):
  for s in read('data_added/application_root_ratios.json')['studies']:
   for row,expected in zip(s['ratios'],s['published_geometric']):self.assertAlmostEqual(math.exp(sum(map(math.log,row))/len(row)),expected,places=14)
 def test_llama_adverse_root_visible(self):
  s=read('data_added/application_root_ratios.json')['studies'][2];self.assertTrue(any(v>1 for x in s['ratios'] for v in x))
 def test_factor_reconstruction_levels(self):
  d=read('generated/FACTOR_RECHECK.json');self.assertEqual(d['recomputed_interval_endpoints'],12);self.assertIsInstance(d['studies']['8B']['primary_intervals'],list);self.assertIsInstance(d['studies']['14B']['primary_intervals'],str)
 def test_sensitivity_does_not_replace_primary(self):
  d=read('generated/SUPPLEMENTARY_SENSITIVITY.json');self.assertIn('Post-hoc',d['label']);self.assertEqual(len(d['q8_live']),4);self.assertEqual(len(d['q32']),3)
 def test_shared_task_identity_not_separate_inputs(self):
  s=(P/'sections/05_results.tex').read_text();self.assertNotIn('separate inputs, references',s);self.assertIn('reuse the Windows task records',s)
 def test_interval_caption_correct(self):
  s=(P/'sections/05_results.tex').read_text();self.assertNotIn('estimates include 1',s);self.assertIn('intervals that include 1',s)
 def test_five_comparison_family_explained(self):
  s=(P/'sections/05_results.tex').read_text();self.assertIn('four M comparisons shown here and the W-L4-D4 comparison',s)
 def test_scalar_column_baseline_preserved(self):
  s=(P/'sections/05_results.tex').read_text();self.assertIn('graph-level scalar-column',s);self.assertIn('14.00',s)
 def test_fig2_title_is_bounded(self):
  s=(P/'figures/arithmetic.tex').read_text();self.assertNotIn('Independent-group packing',s);self.assertIn('at (6.49,3.61) {Group packing}',s)
 def test_historical_plot_is_full_width(self):
  s=(P/'supplement_body.tex').read_text();pat=r'\\begin\{figure\*\}\[t\]\s*\\centering\\includegraphics\[width=\\textwidth\]\{figures/supp_historical_geometry.pdf\}'
  self.assertRegex(s,pat)
 def test_aggregate_width_title(self):
  s=(P/'scripts/build_figures.py').read_text();self.assertIn('(a) Equal work: lower aggregate cost',s);self.assertNotIn('(a) Equal work: q8 is faster',s)
 def test_source_pilot_distinct_from_diagnostic(self):
  s=(P/'supplement_body.tex').read_text();self.assertIn('A5000 live pilot and subsequent startup diagnostic',s);self.assertIn('2d076402',s);self.assertIn('unmatched first-use histories',s)
 def test_operator_and_full_service_levels_separate(self):
  s=(P/'supplement_body.tex').read_text();self.assertIn('f419a89d',s);self.assertIn('full-model B comparison',s);self.assertIn('no performance results in this fixed version',s)
 def test_s2_all_36_public_ratios(self):
  d=read('generated/STRONG_S2_RECHECK.json');self.assertEqual(d['published_paired_ratios_checked'],36);self.assertEqual(d['per_cell_estimates_recomputed'],12)
 def test_s2_q6_q4_adverse_block(self):
  d=read('data_added/strong_s2_source_projection.json');self.assertTrue(any(x>1 for x in d['contrasts'][0]['block_ratios'][2]))
 def test_s2_is_not_native_reproduction(self):
  d=read('generated/STRONG_S2_RECHECK.json');self.assertFalse(d['raw_time_receipts_read_this_revision']);self.assertFalse(d['full_model_S3_completed']);self.assertEqual(d['new_GPU_requests'],0)
 def test_s2_unmerged_status(self):
  d=read('data_added/strong_s2_source_projection.json');self.assertTrue(d['PR_status']['draft']);self.assertFalse(d['PR_status']['merged'])
 def test_no_control_chars_in_tex(self):
  for f in [*P.glob('*.tex'),*(P/'sections').glob('*.tex'),*(P/'figures').glob('*.tex')]:
   self.assertFalse(any(ord(c)<32 and c not in '\n\t\r' for c in f.read_text()),f.name)
 def test_all_48_structural_values_after_reflow(self):
  s=(P/'supplement_body.tex').read_text();records=read('data/rtx_factor_cells.json');lookup={r['cell']:r for r in records};count=0
  for q,state,nums in re.findall(r'^(q\d+) / (inside|crossing) & ([0-9 .&]+) \\\\',s,re.M):
   actual=[float(x.strip()) for x in nums.split('&')];self.assertEqual(len(actual),8)
   expected=[]
   for model in ('Qwen','Smol'):
    row=lookup[f'{model}-{q}-{state}']
    expected += [float(f"{row[a+'_mean_ms']:.2f}") for a in ('W_L4','W_P','L_L4','L_P')]
   self.assertEqual(actual,expected);count+=len(actual)
  self.assertEqual(count,48)
 def test_full_live_table_reference_after_added_s2(self):
  s=(P/'sections/05_results.tex').read_text();self.assertIn('Table~S6 preserve',s)
 def test_original_statistical_files_are_preserved(self):
  d=read('revision/BASELINE_IDENTITY.json');
  for n in ('factor8.json','factor14.json','q8_recomputed.json'):
   self.assertEqual(hashlib.sha256((P/'data'/n).read_bytes()).hexdigest(),d['original_data_files']['data/'+n])
if __name__=='__main__':unittest.main()
