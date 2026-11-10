// Independent public B2 saved-data calculation, no Python/GPU calls.
// Usage: node recompute.js RESTORED_ARCHIVE FRESH_REPORT BYTE_SOURCE_SCOPE
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=process.argv[2],output=process.argv[3];assert(root&&output);assert(!fs.existsSync(output));
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const plan=read('data/PLAN.json'),saved=read('data/RESULTS.json');assert.equal(plan.workers.length,16);
assert.equal(read('data/STATE.json').status,'B2_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY');
assert.equal(saved.measurements,64);assert.equal(saved.warmups,64);
const orders=[[0,1,3,2],[1,2,0,3],[2,3,1,0],[3,0,2,1]],cells=[['loop4',248],['loop4',252],['packed',248],['packed',252]];
const geomean=xs=>Math.exp(xs.reduce((s,x)=>s+Math.log(x),0)/xs.length);
const close=(a,b)=>assert(Math.abs(a-b)<1e-12*Math.max(1,Math.abs(a),Math.abs(b)));
const observations=[],records=[];
for(let ordinal=0;ordinal<16;ordinal++){
 const worker=plan.workers[ordinal],round=Math.floor(ordinal/4),position=ordinal%4;
 assert.equal(worker.round,round);assert.deepEqual([worker.core,worker.boundary],cells[orders[round][position]]);
 const record=read('data/checked/'+worker.id+'.json'),job=read('data/'+worker.job);
 assert.deepEqual(record.worker,worker);assert.equal(record.operations.length,8);assert.equal(job.diagnostics.length,8);
 const warm=round%2?['q8','q4pair','q4pair','q8']:['q4pair','q8','q8','q4pair'];
 const measured=round<2?['q4pair','q8','q8','q4pair']:['q8','q4pair','q4pair','q8'];
 assert.deepEqual(job.diagnostics.map(x=>x.execution),warm.concat(measured));
 assert.equal(record.CLOCKS.markers.length,8);let previous=0;
 for(let i=0;i<8;i++){
  const op=record.operations[i],item=job.diagnostics[i],r=read('data/runs/'+worker.id+'/native/'+item.name+'/receipt.json');
  assert.deepEqual(op.item,item);assert.deepEqual(op.receipt,r);assert.equal(op.role,i<4?'warm':'measured');
  assert.equal(r.capture,false);assert(Number.isFinite(r.operation_s)&&r.operation_s>0);
  const marker=record.CLOCKS.markers[i];assert.equal(marker.name,item.name);assert(marker.seconds_after_launch>previous);previous=marker.seconds_after_launch;
  assert.deepEqual(item.ids,job.diagnostics[0].ids);assert.equal(item.ids.length,8);
  assert.equal(item.state_sha256,job.diagnostics[0].state_sha256);assert.equal(item.frontier_sha256,job.diagnostics[0].frontier_sha256);
  observations.push({worker:worker.id,core:worker.core,boundary:worker.boundary,round,ordinal:i%4,role:op.role,
   path:item.execution,operation_s:r.operation_s,actual_host_marker:marker});
 }
 records.push(record);
}
const contrasts=[],sensitivity=[];
for(const [core,boundary]of cells){
 const ratios=[];
 for(let round=0;round<4;round++){
  const xs=observations.filter(x=>x.core===core&&x.boundary===boundary&&x.round===round&&x.role==='measured');
  const sum=p=>xs.filter(x=>x.path===p).reduce((s,x)=>s+x.operation_s,0);
  const ratio=sum('q8')/sum('q4pair');ratios.push(ratio);
  const old=saved.contrasts.find(x=>x.core===core&&x.boundary===boundary).processes.find(x=>x.round===round);
  close(ratio,old.ratio_B_over_A);
 }
 const gm=geomean(ratios),old=saved.contrasts.find(x=>x.core===core&&x.boundary===boundary);
 close(gm,old.geometric_B_over_A);close(Math.min(...ratios),old.minimum);close(Math.max(...ratios),old.maximum);
 contrasts.push({core,boundary,process_ratios:ratios,geometric_B_over_A:gm,minimum:Math.min(...ratios),maximum:Math.max(...ratios)});
 for(const role of ['warm','measured'])for(let ordinal=0;ordinal<4;ordinal++){
  const xs=observations.filter(x=>x.core===core&&x.boundary===boundary&&x.role===role&&x.ordinal===ordinal);
  const A=xs.filter(x=>x.path==='q4pair').map(x=>x.operation_s),B=xs.filter(x=>x.path==='q8').map(x=>x.operation_s);
  assert.equal(A.length,2);assert.equal(B.length,2);
  sensitivity.push({core,boundary,role,ordinal,A_s:A,B_s:B,geometric_B_over_A:geomean(B)/geomean(A),
   scope:'Additional ordinal description across four processes; two samples/path/ordinal, no independent causal inference'});
 }
}
const ledger=fs.readFileSync(path.join(root,'data/ledger.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const reserved=ledger.filter(x=>x.event==='RESERVE');assert.equal(reserved.length,16);
assert.equal(reserved.reduce((s,x)=>s+x.requests,0),128);assert.equal(reserved.reduce((s,x)=>s+x.rows,0),33024);
assert.equal(ledger.filter(x=>x.event==='COMPLETE').length,16);
const report={status:'INDEPENDENT_NODE_B2_RECOMPUTATION_PASSED',statistical_replay:'PASSED_COMPLETE_128_OPERATIONS',
 byte_source:process.argv[4],source_sha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),
 measurements:64,warmups:64,independent_processes_per_cell:4,contrasts,ordinal_sensitivity:sensitivity,observations,
 native_absolute_timestamps:'Unavailable in unchanged legacy binary; no invented ns endpoints',
 limitations:['One exposed root, two boundaries and two projections','Uniform two warms/path do not prove convergence',
  'Process clusters, no live-k7 or model-population inference','Text replay does not repeat GPU numeric qualification']};
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
process.stdout.write(JSON.stringify({status:report.status,measurements:64,warmups:64,contrasts})+'\n');
