from pathlib import Path
import json,shutil,difflib
r=Path(__file__).parent;p=Path("C:/hs/b570-formal-request-20261020")
s=(p/"formal.cpp").read_text();s=s[:s.index("void endpoint(")]
orig=s
s=s.replace('Clock::time_point whole;double deadline=230;', 'int draft_threads=8;\nClock::time_point whole;double deadline=230;')
s=s.replace('fs::path path,bool cap):','fs::path path,bool cap,int threads=8):')
s=s.replace('p.n_threads=8;p.n_threads_batch=8;','p.n_threads=threads;p.n_threads_batch=threads;')
s=s.replace('std::make_unique<Context>(d,1,dir/"draft",capture)','std::make_unique<Context>(d,1,dir/"draft",capture,draft_threads)')
s=s.replace('o.record["target_calls"]=target.calls;', 'o.record["draft_cpu_threads"]=draft_threads;o.record["target_calls"]=target.calls;')
assert s!=orig and 'capture,draft_threads)'in s
(r/"host-prefix.patch").write_text("".join(difflib.unified_diff(orig.splitlines(True),s.splitlines(True),fromfile="PR134/request-prefix",tofile="candidate/request-prefix")))
(r/"draft_cpu.cpp").write_text(s+(r/"main.cpp.inc").read_text())
for name in ("INPUT_PANEL.json","MODEL_IDENTITY.json"):shutil.copy2(p/name,r/name)
c=(p/"CMakeLists.txt").read_text().replace("b570_formal","b570_draft_cpu").replace("formal","draft_cpu")
(r/"CMakeLists.txt").write_text(c)
print("Prepared single intervention: draft CPU threads8 ->1; runtime/GPU graphs/prefill untouched")
