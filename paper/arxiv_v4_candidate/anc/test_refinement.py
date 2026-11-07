"""Additional manuscript/figure regression tests; no native model execution."""
from pathlib import Path
import csv, importlib.util, math, re, unittest
ROOT = Path(__file__).resolve().parents[1]

def luminance(rgb):
    c = [int(rgb[i:i+2],16)/255 for i in (0,2,4)]
    c = [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c]
    return sum(v*w for v,w in zip(c,(.2126,.7152,.0722)))

class RefinementChecks(unittest.TestCase):
    def test_pq_service_derived_from_existing_pairs(self):
        spec=importlib.util.spec_from_file_location('gen',ROOT/'scripts/generate_followup_figures.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        panels=mod.load()
        for platform, rows in panels.items():
            self.assertEqual(len(rows),16)
            for row in rows:
                self.assertAlmostEqual(row['pq_economics']*row['layout'],row['economics'],places=12)
        with (ROOT/'anc/closure/rtx_blocks.csv').open(newline='') as stream:
            direct=list(csv.DictReader(stream))
        for row,saved in zip(panels['RTX'],direct):
            self.assertAlmostEqual(row['pq_economics'],float(saved['PQ_R']),places=12)
    def test_both_speculative_comparators_drawn(self):
        text=(ROOT/'figures/service_panels.tex').read_text()
        for token in ('QB 0.5823','PQ 0.5886','QB 2.6198','PQ 2.6325','max. task imbalance 5.21','max. task imbalance 0.75'):
            self.assertIn(token,text)
        self.assertIn('log scale',text)
        self.assertEqual(text.count('mark size=1.1pt'),4)
    def test_ratio_screen_definitions_not_conflated(self):
        text=(ROOT/'sections/04_design.tex').read_text()
        self.assertIn('1-1/1.02',text)
        self.assertIn('1.96',text)
        self.assertIn('2\\%',text)
    def test_service_reduction_wording(self):
        text=(ROOT/'sections/08_request_service.tex').read_text()
        self.assertNotIn('41.8\\% faster',text)
        self.assertIn('41.8\\% service-time reduction',text)
    def test_small_text_palette_contrast(self):
        text=(ROOT/'preamble.tex').read_text()
        colors=dict(re.findall(r'\\definecolor\{([^}]+)\}\{HTML\}\{([A-Fa-f0-9]+)\}',text))
        for name in ('target','qualified','draft','aux','linkblue'):
            self.assertGreaterEqual(1.05/(luminance(colors[name])+.05),4.5,name)
    def test_endpoint_labels_unambiguous(self):
        text=(ROOT/'figures/composition.tex').read_text()
        self.assertIn('rec.: recipient',text)
        self.assertIn('don.: donor',text)
        self.assertIn('new: third endpoint',text)

if __name__=='__main__': unittest.main(verbosity=2)
