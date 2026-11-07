"""Resume the uniquely identified existing draft after its tag lookup returned 404."""
import datetime
import json
import shutil
import subprocess
import sys
from closeout_sequence import REPO,CODE,OPS,ROOT,TRANSPORT,ARCHIVE,TAG,PR,ENV,read,save,logged,run,command


def main():
    assert read(OPS/'POST_CONFIRMATION04.json')['exit_code']==0
    assert read(OPS/'FINALIZE_SCIENCE01.json')['exit_code']==0
    assert not (ROOT/'transport01/CONFIG.json').exists() and not ARCHIVE.exists()
    assert not __import__('pathlib').Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    snapshot=read(TRANSPORT/'SNAPSHOT.json')['stdout'].strip()
    command('NATIVE_SOURCE_UNCHANGED',['git','diff','--exit-code',snapshot,'--',
      'scripts/experiments/rtx_llama_repair_v1',
      'benchmarks/rtx_llama_repair_v1/host_execution/prefix_extent.py',
      'benchmarks/rtx_llama_repair_v1/host_execution/build_combined.py',
      'benchmarks/rtx_llama_repair_v1/host_execution/qwen_regression.py'])
    transport_snapshot=command('TRANSPORT_SNAPSHOT',['git','rev-parse','HEAD'])
    identified=read(TRANSPORT/'RELEASE_LOOKUP_RECOVERY.json')['selected_release']
    release=json.loads(command('RELEASE_METADATA_BY_ID',['gh','api',f'repos/leecdiang/HeteroSpec/releases/{identified["id"]}']))
    assert release['draft'] and release['tag_name']==TAG and release['target_commitish']==snapshot and not release['assets']
    shutil.copy2(OPS/'DELIVERY_CLOSEOUT01.json',TRANSPORT/'CLOSEOUT_ATTEMPT01.json')
    save(TRANSPORT/'CONFIG.json',{'tag':TAG,'release_id':release['id'],'snapshot':snapshot,
      'transport_source_snapshot':transport_snapshot,'result_pr':PR,'archive':str(ARCHIVE),'upload':str(TRANSPORT/'upload01'),
      'resume_reason':'Existing authenticated draft bound by numeric release ID after by-tag lookup 404. Scientific/native source unchanged; no duplicate release and no new native work.'})
    prior=TRANSPORT/'empty_prior';prior.mkdir();(prior/'UPLOADED_PARTS.jsonl').write_text('')
    packing=subprocess.Popen(logged('PACK01',CODE/'pack_evidence.py',['--out',ARCHIVE,'--repo',REPO]),cwd=REPO,env=ENV)
    uploading=subprocess.Popen(logged('UPLOAD01',ROOT/'parent159/diagnostics/parallel_upload.py',[ARCHIVE,TRANSPORT/'upload01',prior,TAG,release['id']]),cwd=REPO,env=ENV)
    codes=[packing.wait(),uploading.wait()]
    assert codes==[0,0],f'packing/upload failed {codes}; all partial evidence retained'
    run('DELIVERY_FINISH01',CODE/'finish_transport.py',['--archive',ARCHIVE,'--upload',TRANSPORT/'upload01','--root',TRANSPORT,'--tag',TAG,'--snapshot',snapshot,'--result-pr',PR])
    save(TRANSPORT/'CLOSEOUT_READY.json',{'status':'ALL_SCIENCE_AND_DRAFT_DELIVERY_GATES_PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'release_published':False,'result_pr':PR,'snapshot':snapshot,'transport_source_snapshot':transport_snapshot,'tag':TAG,'release_id':release['id']})
    print('ALL_SCIENCE_AND_DRAFT_DELIVERY_GATES_PASS',flush=True)


if __name__=='__main__':main()
