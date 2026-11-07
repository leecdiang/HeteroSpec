"""CPU read-only archive/selected B evidence authentication. Never invokes native code."""
import argparse, hashlib, json, zipfile
from pathlib import Path
from datetime import datetime, timezone

def digest(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,data):
    q=Path(p).with_suffix(Path(p).suffix+'.tmp')
    q.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n');q.replace(p)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',required=True);ap.add_argument('--restored',required=True);ap.add_argument('--phase2',required=True);ap.add_argument('--phase2-archive',required=True);a=ap.parse_args()
    out=Path(__file__).parent;arc=Path(a.archive);root=Path(a.restored);phase=Path(a.phase2)
    assert arc.stat().st_size==122395102
    assert digest(arc)=='88ff7d52da4815dee11d7232e36b292fd77fe18a414e01aca41e860cdd4cade5'
    entries=[]
    with zipfile.ZipFile(arc) as z:
        assert z.testzip() is None
        idx=json.loads(z.read('INDEX.json'))
        assert idx['source_head']=='250058d62ff4c335374ba94b31520f8a7a347182'
        assert len(idx['files'])==10151 and idx['unique_objects']==6542
        selected=[i for i in idx['files'] if i['path'].startswith('experiment/runs/b/') or i['path'] in ['experiment/B_MANIFEST.json','experiment/B_INPUTS.json','experiment/SOURCE_BINDINGS.json','experiment/close_server.py','experiment/close_base.py','experiment/run_b.py','experiment/analyze_bcd.py','experiment/generated/B_RESULTS.json']]
        for i in selected:
            p=root/i['path'];assert p.is_file(),i['path'];assert p.stat().st_size==i['bytes'];assert digest(p)==i['sha256'],i['path']
            entries.append({'namespace':'archive_restored','path':i['path'],'bytes':i['bytes'],'sha256':i['sha256']})
        rehydrate=z.read('rehydrate.py').decode('utf-8')
        # Only inspect text; neither restore script nor runner is imported/executed.
        write(out/'ARCHIVE_ACCESS.json',{'status':'PASS','archive_sha256':digest(arc),'archive_bytes':arc.stat().st_size,'zip_crc_all_members':'PASS','logical_files':len(idx['files']),'unique_objects':idx['unique_objects'],'packaged_source_head':idx['source_head'],'public_PR62_head':'8dfa60a2492e0639a0774f7bac842273485ca26a','selected_restored_files_checked':len(selected),'restoration_this_round':False,'rehydrate_text_read_only':True,'rehydrate_sha256':hashlib.sha256(rehydrate.encode()).hexdigest(),'no_native_program_invoked':True,'access_scope':'B raw requests, warmups, commands/logs/environment, manifests, request/analyzer source; separately retained Phase2 timer implementation. No C/D raw re-audit.'})
    sb=json.loads((root/'experiment/SOURCE_BINDINGS.json').read_text())
    for rel in ['tools/server/server-context.cpp','src/llama-context.cpp','src/llama-graph.cpp']:
        p=phase/'generated/source'/rel;assert digest(p)==sb['phase2_build']['changed_source_files'][rel]
    phase_arc=Path(a.phase2_archive)
    assert digest(phase_arc)==sb['phase2_archive_sha256']
    with zipfile.ZipFile(phase_arc) as z:phase_idx={i['path']:i for i in json.loads(z.read('INDEX.json'))['files']}
    for rel in ['base.py','server.py','generated/source/tools/server/server-common.h','generated/source/tools/server/server-common.cpp','generated/source/tools/server/server-context.cpp','generated/source/common/live_capture.h','generated/source/common/hs_observer.h','generated/source/src/hs_scope.h']:
        p=phase/rel
        assert p.exists(),rel
        assert digest(p)==phase_idx['experiment/'+rel]['sha256'],rel
        entries.append({'namespace':'phase2','path':rel,'bytes':p.stat().st_size,'sha256':digest(p),'authentication':'selected file matches identity-verified immutable Phase2 archive INDEX'})
    assert digest(root/'experiment/runs/b/RECORDS.json')=='a6e562625f229fd38eed31a9492bb04db269f78355391ab41cf31c6d2dce6bd4'
    write(out/'UNIT_MANIFEST.json',{'units':entries,'archive':{'sha256':digest(arc),'bytes':arc.stat().st_size},'phase2_archive':{'sha256':digest(phase_arc),'bytes':phase_arc.stat().st_size},'scope':'selected old inputs/source; unchanged recheck required'})
    write(out/'INPUT_BINDINGS.json',{'archive_sha256':digest(arc),'B_records_sha256':digest(root/'experiment/runs/b/RECORDS.json'),'B_manifest_sha256':digest(root/'experiment/B_MANIFEST.json'),'B_inputs_sha256':digest(root/'experiment/B_INPUTS.json'),'SOURCE_BINDINGS_sha256':digest(root/'experiment/SOURCE_BINDINGS.json'),'scientific_run_source':'7b8c6fbecde9d173fb9f9e1cac390f58fd4fca24','packaged_source':'250058d62ff4c335374ba94b31520f8a7a347182','public_PR62':'8dfa60a2492e0639a0774f7bac842273485ca26a','public_PR65':'8783cb1eaed8da900d81065957da58c88c00b814','expected_server_sha256':sb['phase2_build']['server_sha256'],'protocol_sha256':digest(out/'PROTOCOL.json'),'timer_source_entries':[e for e in entries if e['namespace']=='phase2']})
    with (out/'LEDGER.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'stage':'identity','status':'PASS','utc':datetime.now(timezone.utc).isoformat(),'units':len(entries),'new_model_requests':0})+'\n')
    write(out/'STATUS.json',{'stage':'identity','status':'PASS','new_model_requests':0,'new_target_draft_forwards':0,'new_warmups':0})
    print(json.dumps({'status':'PASS','authenticated_B_scope_files':len(entries),'archive_bytes':arc.stat().st_size}))
if __name__=='__main__':main()
