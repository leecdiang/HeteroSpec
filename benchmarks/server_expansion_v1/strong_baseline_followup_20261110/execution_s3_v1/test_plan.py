"""Synthetic whole-stage counts, two-request calibration and exact job bindings."""
import hashlib
from pathlib import Path
import unittest
from plan import construct,canonical


class Plan(unittest.TestCase):
    def test_full_counts_and_schedule(self):
        roots=dict(generated_outputs_seen=False,inputs=[dict(slot=i,id=f'synthetic/{i}',domain='code'if i<6 else'math',cap=128,prompt_ids=[1]*20)for i in range(12)])
        previous=dict(services=[dict(id=f'boundary{i}',input=dict(id=f'old/{i}',prompt_ids=[1]*3,cap=1,family='Qwen32B'))for i in range(6)])
        plan,jobs=construct(roots,previous,Path('/synthetic/model.gguf'))
        self.assertEqual((plan['planned_requests'],len(plan['workers'])),(423,210))
        self.assertEqual(plan['approved_phase_request_ceiling']-plan['planned_requests'],16)
        formal=[w for w in plan['workers']if w['stage']=='formal'];self.assertEqual(len(formal),144)
        for worker in plan['workers']:
            j=jobs[worker['job']]
            self.assertEqual(hashlib.sha256(canonical(j)).hexdigest(),worker['job_sha256'])
            self.assertEqual(len(j['inputs']),len(worker['operations']))
            self.assertTrue(all('role'not in x for x in j['inputs']))
            if worker['stage']=='formal':
                self.assertEqual([x['name']for x in j['inputs']],['warm','measured'])
                self.assertEqual(j['inputs'][0]['input'],j['inputs'][1]['input'])
                self.assertTrue(all(not x['capture']for x in j['inputs']))
        calibrations=[w for w in plan['workers']if w['kind']=='new-root-clean-pair-calibration']
        self.assertEqual([w['arm']for w in calibrations],list('GBC'))
        self.assertTrue(all(w['slot']==0 and len(w['operations'])==2 for w in calibrations))


if __name__=='__main__':unittest.main()
