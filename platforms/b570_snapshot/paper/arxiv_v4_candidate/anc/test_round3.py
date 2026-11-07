"""Fail-closed mutation tests for retrospective comparisons and submission layout."""
import json
import test_release
from pathlib import Path
import unittest

class Round3Checks(unittest.TestCase):
    def test_complete(self):
        self.assertEqual(test_release.ReleaseChecks().exercise()['status'],'PASS')
    def test_interaction_cannot_be_promoted(self):
        def mutate(root):
            p=root/'anc/repair_interaction.json';v=json.loads(p.read_text())
            v['families']['SmolLM2']['local_repair_crosses_draft_parity']=True
            p.write_text(json.dumps(v))
        with self.assertRaises(ValueError):test_release.ReleaseChecks().exercise(mutate)
    def test_derived_gamma_mutation_rejected(self):
        def mutate(root):
            p=root/'anc/repair_interaction.json';v=json.loads(p.read_text())
            v['families']['Qwen3']['gamma_QB_from_GS']=1.95;p.write_text(json.dumps(v))
        with self.assertRaises(ValueError):test_release.ReleaseChecks().exercise(mutate)
    def test_plot_cannot_hide_pq(self):
        def mutate(root):
            p=root/'figures/cost.tex';p.write_text(p.read_text().replace('1.125118952936','1.000000000000'))
        with self.assertRaises(ValueError):test_release.ReleaseChecks().exercise(mutate)
    def test_arxiv_ancillary_no_tex(self):
        def mutate(root):(root/'anc/unwanted.tex').write_text('not a compile dependency\n')
        with self.assertRaises(ValueError):test_release.ReleaseChecks().exercise(mutate)

if __name__=='__main__':unittest.main(verbosity=2)
