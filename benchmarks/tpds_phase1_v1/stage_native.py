"""Stage independent candidates from explicit, hash-bound PR190 sources.

No downloading, GPU execution, or in-place mutation. The host supplies recovered
source manifests; source staging is not a native build or numerical qualification.
R1 needs two arithmetic cores and one shared frontend, not four new algorithms.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from design import require, write_new

FRONTEND = ('entry.cpp','worker.cpp','resident_context.hpp','phase_plan.hpp','target_capture.hpp')


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def once(text, old, new):
    require(text.count(old)==1, 'Source anchor changed; inspect original and adapt the development overlay: '+old[:90])
    return text.replace(old,new,1)


def residency_patch(text):
    """Patch the reviewed PR190 entry, leaving model computation/request() intact.

    This requires original request/provision to use a null draft only when its
    draft flag is false. The host inspects that call chain and qualifies it.
    Same derivative frontend serves all four R2 arms.
    """
    start='int main(int argc,char**argv){'
    text=once(text,start,start+'\n    const auto phase1_main_started=Clock::now();')
    old='auto start=Clock::now();t=llama_model_load_from_file(job.at("target_model").get<std::string>().c_str(),mp);d=llama_model_load_from_file(job.at("draft_model").get<std::string>().c_str(),mp);need(t&&d,"models");result["model_load_s"]=since(start);'
    new='''const std::string residency=job.value("residency",std::string("matched"));
        need(residency=="matched" || residency=="target_only","unknown residency");
        const bool target_only=residency=="target_only";
        need(!target_only || !job.value("draft",false),"target-only cannot execute draft");
        auto start=Clock::now();
        t=llama_model_load_from_file(job.at("target_model").get<std::string>().c_str(),mp);
        if(!target_only)d=llama_model_load_from_file(job.at("draft_model").get<std::string>().c_str(),mp);
        need(t && (target_only || d),"models");
        result["model_load_s"]=since(start);result["phase1_residency"]=residency;'''
    text=once(text,old,new)
    old='const auto*tv=llama_model_get_vocab(t);const auto*dv=llama_model_get_vocab(d);need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocab size");for(int i=0;i<llama_vocab_n_tokens(tv);++i)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocab mismatch");'
    new='''const auto*tv=llama_model_get_vocab(t);
        if(d){const auto*dv=llama_model_get_vocab(d);
        need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocab size");
        for(int i=0;i<llama_vocab_n_tokens(tv);++i)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocab mismatch");}'''
    text=once(text,old,new)
    text=once(text,'if(!pool.draft)pool.draft=','if(d && !pool.draft)pool.draft=')
    text=once(text,'llama_model_free(d);d=nullptr;','if(d)llama_model_free(d);d=nullptr;')
    # One worker already accepts an ordered inputs array. No per-root process
    # spawning is necessary. The supervisor timestamps each flushed marker.
    marker='dump(dir/"receipt.json",r);result["requests"].push_back'
    replacement='''r["phase1_main_to_result_s"]=since(phase1_main_started);
                dump(dir/"receipt.json",r);
                std::cout << "PHASE1_RESULT_READY " << name << " " << r["phase1_main_to_result_s"] << std::endl;
                result["requests"].push_back'''
    return once(text,marker,replacement)


def snapshot(spec):
    root=Path(spec['root']).resolve(); require(root.is_dir(),'Source root missing')
    require(spec.get('files'), 'Explicit files/hash manifest required')
    data={}
    for relative, expected in spec['files'].items():
        rel=Path(relative)
        require(not rel.is_absolute() and '..' not in rel.parts,'Unsafe relative source path')
        p=root/rel
        require(p.resolve().is_relative_to(root) and p.is_file() and not p.is_symlink(),'Unsafe/missing source file')
        raw=p.read_bytes(); require(hashlib.sha256(raw).hexdigest()==expected,'Source hash mismatch: '+relative)
        data[relative]=raw
    return root,data


def stage(binding, destination, residency=True):
    require(binding.get('base_commit')=='a28f3474acac793d07b6e6f462cb70bbccfa6ceb','Use the reviewed PR190 base; record any development extension separately')
    require(set(binding['cores'])==set(binding['frontends'])=={'loop4','packed'},'Two pinned recipes required')
    snapshots={}; roots=[]
    for kind in ('cores','frontends'):
        for recipe,spec in binding[kind].items():
            root, data=snapshot(spec);roots.append(root);snapshots[(kind,recipe)]=data
    out=Path(destination).resolve()
    require(not out.exists() and all(not out.is_relative_to(r) and not r.is_relative_to(out) for r in roots),'Fresh independent staging root required')
    for recipe in ('loop4','packed'):
        require(set(FRONTEND)<=set(snapshots[('frontends',recipe)]),'Incomplete final frontend snapshot')
    for name in FRONTEND:
        require(snapshots[('frontends','loop4')][name]==snapshots[('frontends','packed')][name],
                'Frontend difference needs development review before factorial attribution: '+name)
    base=snapshots[('frontends','loop4')]
    # Validate anchors before writing output. Both original R and old runtime stay untouched.
    patched=residency_patch(base['entry.cpp'].decode('utf8').replace('\r\n','\n')).encode() if residency else base['entry.cpp']
    for (kind,recipe),files in snapshots.items():
        if kind=='frontends':continue
        for name,raw in files.items():
            p=out/kind/recipe/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    for name,raw in base.items():
        p=out/'frontend'/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(patched if name=='entry.cpp' else raw)
    arms={}
    for arm,cut,recipe in [('W_L4','SIMPLE','loop4'),('W_P','SIMPLE','packed'),('L_L4','LOCAL','loop4'),('L_P','LOCAL','packed')]:
        arms[arm]=dict(core=recipe,frontend='frontend',job_overlay=dict(lowering=cut,draft=False,draft_width=1,residency='matched'))
    r2={'W_M_TARGET_ONLY':dict(lowering='SIMPLE',draft=False,draft_width=1,residency='target_only',core='loop4'),
        'L_M_TARGET_ONLY':dict(lowering='LOCAL',draft=False,draft_width=1,residency='target_only',core='packed'),
        'L_M_MATCHED':dict(lowering='LOCAL',draft=False,draft_width=1,residency='matched',core='packed'),
        'L_D4':dict(lowering='LOCAL',draft=True,draft_width=4,residency='matched',core='packed')}
    core_a=snapshots[('cores','loop4')];core_b=snapshots[('cores','packed')]
    changes=[p for p in sorted(set(core_a)|set(core_b)) if core_a.get(p)!=core_b.get(p)]
    manifest=dict(status='SOURCE_STAGED_NOT_COMPILED_OR_QUALIFIED',arms=arms,burst_arms=r2 if residency else {},residency_overlay=bool(residency),
        core_differences_requiring_attribution_review=changes,source_binding=binding,
        output_files={str(p.relative_to(out)).replace('\\','/'):digest(p) for p in out.rglob('*') if p.is_file()},
        host_work=['Compile both cores/shared frontend','Validate null-draft provision chain','Verify attention recipe identical aside from cut scope',
                   'Observe actual projection dispatch','Native original-R qualification','Persistent-worker first-result clocks'])
    write_new(out/'STAGED.json',manifest)
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('binding',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--factorial-only',action='store_true',help='Stage R1 without blocking on the optional R2 entry overlay')
    a=p.parse_args();stage(json.loads(a.binding.read_text()),a.out,residency=not a.factorial_only)
if __name__=='__main__': main()
