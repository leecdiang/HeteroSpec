"""Source-shape fixtures, not original native compilation or model execution."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import Invalid
from stage_sources import b570_draft,observe_b570,rtx_draft

FIXTURE='''#include <bcrypt.h>
// policy.precision DecodeScope scope(role,phase)
NativeContext(llama_model*m,int ub,bool capture,std::string label):heavy(capture){
 p.n_ubatch=ub;p.n_outputs_max=ub;p.n_outputs_max_per_seq=ub;
 c=llama_init_from_model(m,p);need(c,"context");
}
json run_request(llama_model*t,llama_model*d,const json&input,const json&slot,const json&donor){
 target.prefill(prompt,lengths);
 draft=std::make_unique<NativeContext>(d,1,heavy,"draft");
 draft->prefill(prompt,std::vector<int>(prompt.size(),1));
 bool done=commit(next);
 next=target.sample(-1,"target_ordinary/"+std::to_string(ids.size()));done=commit(next);
 draft->decode({proposal},base+1,false,"PROPOSE");
 target.trim(keep);draft->trim(keep);
 out["endpoint"]={};
}
void admission(){NativeContext draft(d,1,false,"draft");}
'''
class StageTests(unittest.TestCase):
    def test_four_source_shapes(self):
        for c,u in ((1,1),(4,1),(4,2),(4,4)):
            s=b570_draft(FIXTURE.encode(),c,u).decode()
            self.assertIn('p.n_outputs_max=ub;p.n_outputs_max_per_seq=ub;',s)
            self.assertIn('target.prefill(prompt,lengths);',s)
            self.assertIn('draft->decode({proposal},base+1,false,"PROPOSE");',s)
            self.assertIn(f'hs_draft_caller={c}, hs_draft_ubatch={u}',s)
    def test_admission_uses_actual_width(self):
        s=b570_draft(FIXTURE.encode(),4,4).decode()
        self.assertIn('NativeContext draft(d,1,false,"draft",hs_draft_ubatch);',s)
        self.assertNotIn('NativeContext draft(d,1,false,"draft");',s)
    def test_observer_frontier(self):
        s=observe_b570(b570_draft(FIXTURE.encode(),4,2)).decode()
        self.assertIn('target.boundary(target.logits(accepted))',s)
        self.assertIn('if(heavy)',s)
    def test_crlf_preserved(self):
        s=b570_draft(FIXTURE.replace('\n','\r\n').encode(),4,4)
        self.assertNotIn(b'\n',s.replace(b'\r\n',b''))
    def test_drift_rejected(self):
        with self.assertRaises(Invalid):b570_draft(FIXTURE.replace('p.n_ubatch=ub;','p.n_ubatch=8;').encode(),4,4)
    def test_unknown_combo(self):
        with self.assertRaises(Invalid):b570_draft(FIXTURE.encode(),1,4)
    def test_rtx_hash_refuses_fake(self):
        with self.assertRaises(Invalid):rtx_draft(FIXTURE.encode(),2)
if __name__=='__main__':unittest.main()
