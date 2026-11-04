from pathlib import Path
import argparse,hashlib,shutil,json
HERE=Path(__file__).resolve().parent
SOURCE_SHA='5a9094517d11dcafe43c51af97bfe3d6afe75d73096be4b899bae7025b1edd31'
def stage(source,out):
 path=source/'ggml/src/ggml-backend.cpp';data=path.read_bytes()
 if hashlib.sha256(data).hexdigest()!=SOURCE_SHA:raise ValueError('unexpected frozen scheduler source')
 if out.exists():raise ValueError('output must be new')
 if source==out or source in out.parents:raise ValueError('nested output')
 shutil.copytree(source,out)
 p=out/'ggml/src/ggml-backend.cpp';s=p.read_text()
 s=s.replace('struct ggml_backend_sched {','struct hs_sched_plan;\nstruct ggml_backend_sched {\n    uint64_t hs_plan_instance, hs_plan_epoch;\n    ggml_cgraph * hs_plan_graph;\n    hs_sched_plan * hs_plan_armed;\n    int hs_plan_result;',1)
 anchor='static enum ggml_status ggml_backend_sched_compute_splits(ggml_backend_sched_t sched) {'
 s=s.replace(anchor,'#include "hs_plan_probe.inc"\n\n'+anchor,1)
 s=s.replace('    const char * GGML_SCHED_DEBUG = getenv(', '    sched->hs_plan_instance = hs_plan_allocate_instance();\n    const char * GGML_SCHED_DEBUG = getenv(',1)
 s=s.replace('    free(sched);','    hs_sched_plan_disarm(sched);\n    free(sched);',1)
 s=s.replace('void ggml_backend_sched_reset(ggml_backend_sched_t sched) {\n    GGML_ASSERT(sched);','void ggml_backend_sched_reset(ggml_backend_sched_t sched) {\n    GGML_ASSERT(sched);\n    if (sched->hs_plan_epoch != UINT64_MAX) ++sched->hs_plan_epoch; // never silently disarm\n    sched->hs_plan_graph = nullptr;',1)
 s=s.replace('void ggml_backend_sched_split_graph(ggml_backend_sched_t sched, struct ggml_cgraph * graph) {', 'void ggml_backend_sched_split_graph(ggml_backend_sched_t sched, struct ggml_cgraph * graph) {\n    sched->hs_plan_graph = nullptr;\n    if (sched->hs_plan_epoch != UINT64_MAX) ++sched->hs_plan_epoch;',1)
 s=s.replace('    sched->is_alloc = true;', '    sched->is_alloc = true;\n    sched->hs_plan_graph = graph;',1)
 old='enum ggml_status ggml_backend_sched_graph_compute_async(ggml_backend_sched_t sched, struct ggml_cgraph * graph) {\n    GGML_ASSERT(sched);'
 new=old+'''\n    // A diagnostic arm cannot become ordinary execution after reset/reallocation.
    if (sched->hs_plan_armed && !sched->is_alloc) {
        sched->hs_plan_result = HS_PLAN_NOT_ALLOCATED;
        return GGML_STATUS_FAILED;
    }'''
 assert old in s;s=s.replace(old,new,1)
 old='    return ggml_backend_sched_compute_splits(sched);'
 new='''    // All scheduler-visible splits/transfers are inspected BEFORE the first
    // input copy, event wait or backend launch. This tool ALWAYS vetoes.
    if (sched->hs_plan_armed) {
        sched->hs_plan_result = hs_sched_plan_compare(sched, graph, sched->hs_plan_armed);
        return GGML_STATUS_FAILED;
    }
'''+old
 assert s.count(old)==1;s=s.replace(old,new,1);p.write_text(s)
 for name in ('hs_plan_probe.h','hs_plan_probe.inc'):shutil.copyfile(HERE/name,out/'ggml/src'/name)
 receipt={'status':'DIAGNOSTIC_DRY_VETO_ONLY','input_scheduler_sha256':SOURCE_SHA,'output_scheduler_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'production_execution':False}
 (out/'PLAN_PROBE_STAGE.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--output',type=Path,required=True);v=a.parse_args();print(stage(v.source.resolve(),v.output.resolve()))
