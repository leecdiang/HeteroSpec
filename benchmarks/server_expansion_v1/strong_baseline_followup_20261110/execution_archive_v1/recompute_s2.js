// Independent saved-data calculation. No Python analysis code or GPU access.
// Usage: node recompute_s2.js RESTORED_ARCHIVE OUTPUT_JSON [BYTE_SOURCE_SCOPE]
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const root=process.argv[2],output=process.argv[3];
assert(root&&output,'Restored archive and fresh output are required');
assert(!fs.existsSync(output),'Never overwrite a replay report');
const read=relative=>JSON.parse(fs.readFileSync(path.join(root,relative),'utf8'));
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const rows=read('data/S2/S2_ROWS.json');
const original=read('data/S2/S2_ANALYSIS.json');
const plan=read('F1/F1_DATA/S2_COMPLETE_WORKERS.json');
assert.equal(rows.length,72);assert.equal(plan.length,36);
const byId=new Map(rows.map(r=>[r.operation_id,r]));assert.equal(byId.size,72);
const expectedIds=plan.flatMap(w=>w.operations.map(o=>o.operation_id));
assert.equal(new Set(expectedIds).size,72);
assert.deepEqual([...byId.keys()].sort(),expectedIds.slice().sort());
let previousEnd=0,warm=0,measured=0;
for(const worker of plan){
  assert.equal(worker.operations.length,2);
  for(let ordinal=0;ordinal<2;ordinal++){
    const op=worker.operations[ordinal],r=byId.get(op.operation_id);
    assert.equal(r.worker_id,worker.worker_id);assert.equal(r.arm,worker.arm);
    assert.equal(r.slot,worker.cell);assert.equal(r.block,worker.block);
    assert.equal(r.ordinal,ordinal);assert.equal(r.role,ordinal?'measured':'warm');
    assert.equal(r.phase,'S2');assert.equal(r.unit,'s');
    assert(Number.isFinite(r.elapsed_s)&&r.elapsed_s>0);
    assert(Number.isSafeInteger(r.start_ns)&&Number.isSafeInteger(r.end_ns));
    assert(r.start_ns>=previousEnd&&r.end_ns>r.start_ns);previousEnd=r.end_ns;
    assert(r.fence_ns>=r.start_ns&&r.fence_ns<=r.end_ns);
    assert(r.owned_ready_ns>=r.start_ns&&r.owned_ready_ns<=r.end_ns);
    assert(Math.abs((r.end_ns-r.start_ns)/1e9-r.elapsed_s)<1e-8);
    assert.equal(r.q,worker.q);assert.equal(r.output_rows,r.q);
    assert.equal(r.requested_output_rows,r.q);assert.equal(r.all_outputs_owned,true);
    assert.equal(r.callback_continues,true);
    for(const key of ['input_sha256','output_sha256','config_sha256'])assert.match(r[key],/^[0-9a-f]{64}$/);
    const c=r.work_counters,q=r.q;
    assert.equal(c.quant_calls,r.arm==='G'?q:1);assert.equal(c.quant_rows,q);
    assert.equal(c.scalar_dot_dispatches,r.arm==='C'?1:q);assert.equal(c.scalar_dot_columns,q);
    assert.equal(c.backend_loop_entries,r.arm==='B'?1:0);
    assert.equal(c.kernel_application_launch_calls,r.arm==='G'?3*q-1:r.arm==='B'?q+1:2);
    assert.equal(c.opaque_library_internal_launches,null);
    ordinal?measured++:warm++;
  }
}
assert.equal(warm,36);assert.equal(measured,36);
for(let slot=0;slot<4;slot++){
  const xs=rows.filter(r=>r.slot===slot);
  assert.equal(new Set(xs.map(r=>r.input_sha256)).size,1);
  assert.equal(new Set(xs.map(r=>r.output_sha256)).size,1);
}
const lookup=new Map(rows.filter(r=>r.role==='measured').map(r=>[`${r.slot}/${r.block}/${r.arm}`,r.elapsed_s]));
assert.equal(lookup.size,36);
const close=(a,b)=>assert(Math.abs(a-b)<1e-12*Math.max(1,Math.abs(a),Math.abs(b)),`${a} != ${b}`);
const contrasts=[];
for(const [candidate,baseline]of[['C','B'],['B','G'],['C','G']]){
  const old=original.contrasts.find(x=>x.candidate===candidate&&x.baseline===baseline);
  assert(old);let totalCandidate=0,totalBaseline=0,allLogs=[];const cells=[];
  for(let slot=0;slot<4;slot++){
    const logs=[],ratios=[];
    for(let block=0;block<3;block++){
      const a=lookup.get(`${slot}/${block}/${candidate}`),b=lookup.get(`${slot}/${block}/${baseline}`);
      assert(a>0&&b>0);ratios.push(a/b);logs.push(Math.log(a/b));totalCandidate+=a;totalBaseline+=b;
    }
    const geometric=Math.exp(logs.reduce((a,b)=>a+b,0)/3);
    close(geometric,old.per_cell_geometric_ratio[String(slot)]);
    logs.forEach((x,i)=>close(x,old.per_slot_log_ratios[String(slot)][i]));allLogs.push(...logs);
    cells.push({slot,block_ratios:ratios,geometric_ratio:geometric,percent_change:100*(geometric-1)});
  }
  const geometric=Math.exp(allLogs.reduce((a,b)=>a+b,0)/12),total=totalCandidate/totalBaseline;
  close(geometric,old.ratio);close(total,old.total_ratio);
  contrasts.push({candidate,baseline,cells,equal_cell_geometric_ratio:geometric,total_ratio:total});
}
const report={status:'INDEPENDENT_NODE_STATISTICAL_RECOMPUTATION_PASSED',statistical_replay:'PASSED_COMPLETE_72_OPERATIONS',
  scope:process.argv[4]||'Caller-provided restored archive bytes; this script performs no network fetch',
  implementation:'Independent Node Math calculation; no import/call of the Python analyze function',
  measured,warmups:warm,workers:36,complete_manifest_order_clock_ownership_hash_and_dispatch_checks:true,
  source_sha256:hash(__filename),rows_sha256:hash(path.join(root,'data/S2/S2_ROWS.json')),
  analysis_sha256:hash(path.join(root,'data/S2/S2_ANALYSIS.json')),contrasts,
  limitations:['Four exposed cells, three blocks, descriptive only','One warm is not proof of steady state',
    'No independent GPU numeric rerun or full-model speed extrapolation']};
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
process.stdout.write(JSON.stringify({status:report.status,measured,warmups:warm,workers:36,contrasts})+'\n');
