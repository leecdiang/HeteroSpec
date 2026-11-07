"""Pinned supervisor/auditor reuse; fresh lane and immutable attempt IDs."""
from pathlib import Path
V=Path(__file__).resolve().parent
text=(V.parent/'rtx_boundary_confirmation_v1/collect.py').read_text()
text=text[:text.index('\ndef stage(name):')]
text=text[:text.index('\ndef freeze():')]+text[text.index('\ndef occurrence(n,row):'):]
text=text.replace('from study import validate_plan','from plan import validate as validate_plan').replace('rtx-boundary-confirmation-v1','rtx-mechanism-baselines-v1')
# Freeze/verify are replaced below; the inherited functions remain unused aliases
# only until these final definitions are parsed, and no work happens on import.
start=text.index('    if t[\'stage\'] in [\'aa_pilot\',\'confirm\',\'holdout\']:')
end=text.index('    return result,attempt',start)
text=text[:start]+text[end:]
text=text.replace('capture_reference=capture)', 'capture_reference=capture,graph_mode=t["graph_mode"],integrated_q_update=t["stage"].startswith("producer"),producer_source=str(root()/"inputs"/f"q{c[\'q\']}-k256-v{c[\'realization\']}"/"Q.bin"))')
text=text.replace("def env(s):", "def env(s,mode='OFF'):")
text=text.replace("e['GGML_CUDA_DISABLE_GRAPHS']='1';", "e.pop('GGML_CUDA_DISABLE_GRAPHS',None);e.update({'GGML_CUDA_DISABLE_GRAPHS':'1'} if mode=='OFF' else {});")
text=text.replace("120,env(s),s['host_RAM_bytes']", "120,env(s,t['graph_mode']),s['host_RAM_bytes']")
text=text.replace("    save(attempt/'JOB.json',job);", "    job.update(profile=t.get('profile',False),cupti_path=s['cupti']['path'],cupti_sha256=s['cupti']['sha256']);\n    if t.get('alternating'):job['alternate_context']=t['alternate_context']\n    save(attempt/'JOB.json',job);")
text=text.replace("        if expected is not None:assert (data==expected)==row['ordinary_exact']", "        actual_expected=Path(job['alternate_context']['reference']).read_bytes() if job.get('alternate_context') and row['index']%2 else expected\n        if job.get('alternate_context'):\n            current=Path(job['alternate_context']['root']) if row['index']%2 else Path(c['root'])\n            for role in ROLES:assert (n/f\"update_{row['index']}_{role}.bin\").read_bytes()==(current/(role+'.bin')).read_bytes(),'alternate input readback'\n        if actual_expected is not None:assert (data==actual_expected)==row['ordinary_exact']")
text=text.replace("all(x==expected for x in outputs)", "all(x['ordinary_exact'] for x in rr['calls'])")
text=text.replace("    rr,receipt=audit(n,c,job);save", "    rr,receipt=audit(n,c,job);assert rr['graph_mode']==t['graph_mode'];\n    if job['profile']:save(attempt/'MODE_AUDIT.json',trace_audit(n,job))\n    save")
text=text[:text.index('\ndef referenced_inputs():')]
tail=(V/'controller_tail.txt').read_text()
(V/'runner.py').write_text(text+tail)
