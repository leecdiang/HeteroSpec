// Saved-data validation only. node replay.js PACKET_ROOT FRESH_OUT [public]
// PACKET_ROOT contains data/outputs, data/plans, data/NUMERIC_INVENTORY.json.
// Reuses the CPython-compatible MT19937 from the original S3 independent replay:
// strong_baseline_followup_20261110/RESULTS_S3_20261112/independent_receipts.js.
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const assert = require('assert/strict');
const root = path.resolve(process.argv[2]), out = path.resolve(process.argv[3]);
const publicMode = process.argv[4] === 'public';
assert(!fs.existsSync(out), 'Fresh report directory required');
fs.mkdirSync(out, {recursive: true});
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const sum = xs => xs.reduce((a, b) => a + b, 0);
function sorted(x) {
  if (Array.isArray(x)) return x.map(sorted);
  return x && typeof x === 'object'
    ? Object.fromEntries(Object.keys(x).sort().map(k => [k, sorted(x[k])])) : x;
}
const canon = x => JSON.stringify(sorted(x));
const close = (a, b) => assert(Number.isFinite(a) && Number.isFinite(b)
  && Math.abs(a - b) <= 1e-12 * Math.max(1, Math.abs(a), Math.abs(b)), `${a} != ${b}`);
const write = (p, x) => fs.writeFileSync(path.join(out, p), JSON.stringify(x, null, 2) + '\n', {flag: 'wx'});

class RNG {
  constructor(seed) {
    this.mt = new Uint32Array(624); this.mt[0] = 19650218;
    for (let i = 1; i < 624; i++)
      this.mt[i] = (Math.imul(1812433253, this.mt[i-1] ^ (this.mt[i-1] >>> 30)) + i) >>> 0;
    let i = 1;
    for (let k = 0; k < 624; k++) {
      this.mt[i] = ((this.mt[i] ^ Math.imul(this.mt[i-1] ^ (this.mt[i-1] >>> 30), 1664525)) + seed) >>> 0;
      if (++i >= 624) { this.mt[0] = this.mt[623]; i = 1; }
    }
    for (let k = 0; k < 623; k++) {
      this.mt[i] = ((this.mt[i] ^ Math.imul(this.mt[i-1] ^ (this.mt[i-1] >>> 30), 1566083941)) - i) >>> 0;
      if (++i >= 624) { this.mt[0] = this.mt[623]; i = 1; }
    }
    this.mt[0] = 0x80000000; this.i = 624;
  }
  next() {
    if (this.i >= 624) {
      for (let i = 0; i < 624; i++) {
        const y = (this.mt[i] & 0x80000000) | (this.mt[(i+1) % 624] & 0x7fffffff);
        this.mt[i] = (this.mt[(i+397) % 624] ^ (y >>> 1) ^ ((y & 1) ? 0x9908b0df : 0)) >>> 0;
      }
      this.i = 0;
    }
    let y = this.mt[this.i++]; y ^= y >>> 11; y ^= (y << 7) & 0x9d2c5680;
    y ^= (y << 15) & 0xefc60000; y ^= y >>> 18; return y >>> 0;
  }
  six() { let x; do { x = this.next() >>> 29; } while (x >= 6); return x; }
}
const self = new RNG(20261110);
assert.deepEqual(Array.from({length:24}, () => self.six()), [2,5,1,4,5,5,3,5,5,2,2,1,4,2,1,2,4,4,3,4,1,2,5,4]);
function estimate(points) {
  assert.equal(points.length, 12);
  const rng = new RNG(20261113), samples = [];
  for (let i = 0; i < 20000; i++) {
    const chosen = [];
    for (let j = 0; j < 6; j++) chosen.push(points[rng.six()].mean_log_CB);
    for (let j = 0; j < 6; j++) chosen.push(points[6 + rng.six()].mean_log_CB);
    samples.push(Math.exp(sum(chosen) / 12));
  }
  samples.sort((a,b) => a-b);
  const pct = p => { const x = 19999 * p, i = Math.floor(x); return samples[i] + (samples[Math.ceil(x)] - samples[i]) * (x-i); };
  return {CB: Math.exp(sum(points.map(p => p.mean_log_CB)) / 12),
    CI95: [pct(.025), pct(.975)], simultaneous_CI975: [pct(.0125), pct(.9875)], roots: points};
}

if (fs.existsSync(path.join(root, 'INDEX.json'))) {
  for (const entry of read('INDEX.json').files) {
    const file = path.resolve(root, entry.path);
    assert(file.startsWith(root + path.sep) && fs.lstatSync(file).isFile());
    const bytes = fs.readFileSync(file); assert.equal(bytes.length, entry.bytes); assert.equal(hash(bytes), entry.sha256);
  }
}
const inventory = read('data/NUMERIC_INVENTORY.json');
const rows = [], results = {}, costs = [];
for (const panel of ['R1', 'R2', 'H1']) {
  const base = `data/outputs/${panel}/`;
  if (!fs.existsSync(path.join(root, base, 'STATUS.json'))) { results[panel] = {status:'NOT_STARTED'}; continue; }
  const status = read(base + 'STATUS.json');
  if (status.status !== 'COMPLETE') { results[panel] = {status:status.status, inference:'Partial; no full-panel CI'}; continue; }
  const manifest = read(`data/plans/${panel}/MANIFEST.json`), roots = manifest.roots.inputs;
  const tapes = read(base + 'TAPES.json'), formal = manifest.workers.filter(w => w.stage === 'formal');
  assert.equal(formal.length, 48); assert.equal(roots.length, 12);
  const qualified = read(base + 'QUALIFIED.json'); assert.equal(qualified.status, 'ALL_REGISTERED_ROOT_BRIDGES_PASSED');
  let previous = 0;
  for (const worker of formal) {
    const wb = base + 'workers/' + worker.worker_id + '/';
    const actual = read(wb + 'WORKER.json'), job = read(wb + 'JOB.json'), host = read(wb + 'HOST.json');
    const native = read(wb + 'native/result.json');
    assert.deepEqual(actual, worker); assert.equal(host.returncode, 0); assert.equal(host.error, null);
    assert.equal(native.status, 'COMPLETE'); assert.deepEqual(native.native_capability, job.capability_request);
    assert.equal(job.inputs.length,2);
    assert.deepEqual(native.requests,[{name:'warm',record:'warm/receipt.json'},{name:'measured',record:'measured/receipt.json'}]);
    for (const [k,v] of Object.entries({draft:false,k:0,cuda_graphs:false,flash_attention:false,n_ctx:1024,n_ubatch:32,output_reserve:32,target_output_reserve:32,threads:2,lowering:'WHOLE',residency:'target_only'})) assert.deepEqual(job[k], v);
    assert.equal(native.native_capability.arm, worker.arm);
    for (const [k,v] of Object.entries({greedy:true,native_planner:'SIMPLE',kv_K:'f16',kv_V:'f16'})) assert.deepEqual(native.native_capability[k],v);
    const slot = worker.slot, refPanel = panel === 'R2' && ![0,6].includes(slot) ? 'R1' : panel;
    const refDay = refPanel === 'R2' ? 2 : 1, cohort = panel[0];
    const ref = read(`data/outputs/${refPanel}/workers/${cohort}-d${refDay}-q${String(slot).padStart(2,'0')}-R0/native/new-root${String(slot).padStart(2,'0')}/receipt.json`);
    const runtime = {...job}; delete runtime.inputs;
    let warm = null;
    for (let ordinal = 0; ordinal < 2; ordinal++) {
      const role = ordinal ? 'measured' : 'warm', entry = job.inputs[ordinal];
      const request = wb + 'native/' + role + '/', r = read(request + 'receipt.json');
      const tape = read(request + 'semantic-tape.json'), x = r.S3_service, n = roots[slot].prompt_ids.length, q = r.ids.length;
      assert.equal(entry.name, role); assert.equal(entry.capture, false); assert.equal(entry.input.id, roots[slot].id);
      assert.deepEqual(entry.input.prompt_ids, roots[slot].prompt_ids); assert.equal(entry.input.cap,128);
      assert.deepEqual(r.prompt_ids, entry.input.prompt_ids); assert.deepEqual(r.ids, ref.ids); assert.deepEqual(r.eog, ref.eog);
      assert.equal(r.stop_reason, ref.terminal_kind); assert(q >= 1 && q <= 128);
      assert.deepEqual(r.endpoint.ids,r.ids); assert.deepEqual(r.endpoint.eog,r.eog); assert.equal(r.endpoint.length,q);
      assert.equal(r.endpoint.stop_reason,r.stop_reason); assert.equal(r.terminal_id,r.ids.at(-1));
      assert.equal(r.ids.length, r.eog.length); assert(!r.eog.slice(0,-1).some(Boolean));
      if (r.stop_reason === 'CAP') assert.equal(q,128); else { assert.equal(r.stop_reason,'EOG'); assert.equal(r.eog.at(-1),true); }
      assert.deepEqual(r.target_final_kv,{min:0,max:n+q-2}); assert.equal(ref.pending_position,n+q-1);
      assert.equal(r.draft_enabled,false); assert.equal(r.capture,false); assert.equal(r.target_output_reserve,32);
      for (const k of ['draft_calls','k','online_reference_replays','online_state_exports','online_state_imports','online_context_creates']) assert.equal(r[k],0);
      assert.deepEqual(r.observed_API_calls_within_service,{context_creates:0,heavy_captures:0,state_exports:0,state_imports:0});
      assert.equal(x.clock,'CLOCK_MONOTONIC'); assert.equal(x.unit,'s');
      for (const k of ['start_ns','reset_end_ns','fence_ns','owned_ready_ns','end_ns']) assert(Number.isSafeInteger(x[k]) && x[k] > 0);
      assert(previous <= x.start_ns && x.start_ns <= x.reset_end_ns && x.reset_end_ns <= x.fence_ns && x.fence_ns <= x.end_ns);
      assert(x.end_ns > x.start_ns);
      assert(x.start_ns <= x.owned_ready_ns && x.owned_ready_ns <= x.end_ns);
      assert(host.launch_begin_monotonic_ns <= x.start_ns && x.end_ns <= host.exit_observed_monotonic_ns); previous = x.end_ns;
      close(x.elapsed_s,(x.end_ns-x.start_ns)/1e9); close(x.reset_s,(x.reset_end_ns-x.start_ns)/1e9);
      for (const k of ['initial_reset_included','all_required_outputs_owned','post_service_receipt_state_export_serialization_excluded']) assert.equal(x[k],true);
      assert.equal(x.empty_after_reset_min,-1); assert.equal(x.empty_after_reset_max,-1); assert.equal(x.stop_separate_s,null);
      const widths = []; for (let i=0;i<n;i+=32) widths.push(Math.min(32,n-i)); for (let i=1;i<q;i++) widths.push(1);
      assert.deepEqual(r.executions.map(e=>e.width),widths);
      assert.deepEqual(r.phase_executions,r.executions); assert.equal(r.target_calls,widths.length);
      let position = 0;
      for (const e of r.executions) {
        assert.equal(e.position,position); assert.equal(e.active_cells,position+e.width);
        assert.equal(e.phase,position<n?'PREFILL':'ORDINARY');
        assert.deepEqual(e.requested_rows,position+e.width<n?[]:position<n?[n-1]:[0]);
        const ext = Array.from({length:e.width},(_,j)=>Math.max(256,Math.ceil((position+j+1)/256)*256));
        assert.deepEqual(e.expected_extents,ext); assert.equal(e.actual_attention_extent,Math.max(...ext)); position += e.width;
      }
      assert.equal(position,n+q-1); assert.equal(r.application_work.backend_loop_entries>0,worker.arm==='B' && n>1);
      assert.equal(r.application_work.opaque_library_internal_launches,null);
      assert.deepEqual(tape,{executions:r.executions,ids:r.ids,prompt_ids:r.prompt_ids,stop_reason:r.stop_reason,target_final_kv:r.target_final_kv});
      assert.equal(hash(canon(tape)),r.semantic_tape_sha256); assert.equal(r.semantic_tape_sha256,tapes[`${slot}:${worker.arm}`]);
      const terminal = inventory[request + 'post-service-terminal/frontier.f32']; assert(terminal && terminal.bytes === 151936*4);
      const row = {operation_id:worker.worker_id+':'+role,worker_id:worker.worker_id,cohort,day:manifest.day,round:worker.round,pair_id:worker.pair_id,
        root_id:roots[slot].id,slot,arm:worker.arm,ordinal,role,elapsed_s:x.elapsed_s,start_ns:x.start_ns,end_ns:x.end_ns,
        reset_s:x.reset_s,prefill_s:r.target_phases.PREFILL||0,decode_s:r.target_phases.ORDINARY||0,planning_s:r.planning_s,
        owned_output_copy_s:r.output_copy_s,input_sha256:hash(canon(entry.input)),output_sha256:terminal.sha256,
        tokens:r.ids,generated_tokens:q,stop_reason:r.stop_reason.toLowerCase(),actual_forward_rows:n+q-1};
      if (!publicMode) row.config_sha256 = hash(canon(runtime));
      if (warm) { assert.deepEqual(row.tokens,warm.tokens); assert.equal(row.output_sha256,warm.output_sha256); }
      else warm = row;
      rows.push(row);
    }
    costs.push({panel,worker_id:worker.worker_id,model_load_s:native.model_load_s,pool_setup_s:native.pool_setup_s,worker_wall_s:host.wall_s});
  }
  const measured = rows.filter(r=>r.cohort===panel[0] && r.day===manifest.day && r.role==='measured');
  const points = roots.map((r,slot)=>{
    const pairs = [1,2].map(round=>{
      const selected = measured.filter(x=>x.slot===slot && x.round===round), b = selected.find(x=>x.arm==='B'), c = selected.find(x=>x.arm==='C');
      assert(b && c); return {round,CB:c.elapsed_s/b.elapsed_s,B_s:b.elapsed_s,C_s:c.elapsed_s,first:b.start_ns<c.start_ns?'B':'C'};
    });
    assert.notEqual(pairs[0].first,pairs[1].first);
    return {slot,root_id:r.id,domain:slot<6?'code':'math',mean_log_CB:sum(pairs.map(p=>Math.log(p.CB)))/2,rounds:pairs};
  });
  results[panel] = {status:'COMPLETE',estimate:estimate(points)};
}
if (results.R1.estimate && results.R2.estimate) {
  const points = results.R1.estimate.roots.map((a,i)=>({...a,mean_log_CB:(a.mean_log_CB+results.R2.estimate.roots[i].mean_log_CB)/2}));
  results.R_combined = {estimate:estimate(points),scope:'Conditional on the two tested dates; no population-of-days inference'};
}
const journal = fs.readFileSync(path.join(root,'data/outputs/requests.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const reservations = journal.filter(e=>e.event==='RESERVE'), exits = journal.filter(e=>e.event==='EXIT');
assert.equal(new Set(reservations.map(e=>e.worker_id)).size,reservations.length);
assert.equal(new Set(exits.map(e=>e.worker_id)).size,exits.length);
const accounting = {}; let completeRequests=0, failedRequests=0, actualRows=0;
for (const cohort of ['R','H','ALL']) {
  const selected = reservations.filter(e=>cohort==='ALL' || e.cohort===cohort);
  accounting[cohort] = {requests:sum(selected.map(e=>e.requests)),reserved_rows:sum(selected.map(e=>e.reserved_rows)),workers:selected.length};
  assert(accounting[cohort].requests <= ({R:292,H:176,ALL:468})[cohort]);
  assert(accounting[cohort].reserved_rows <= ({R:93440,H:56320,ALL:149760})[cohort]);
}
for (const e of reservations) {
  const wb = `data/outputs/${e.cohort}${e.day}/workers/${e.worker_id}/`, job = read(wb+'JOB.json'), host = read(wb+'HOST.json');
  const exit = exits.find(x=>x.worker_id===e.worker_id); assert(exit);
  for (const [k,v] of Object.entries(host)) assert.deepEqual(exit[k],v);
  assert.equal(e.requests,e.roles.length); assert.equal(e.requests,job.inputs.length);
  assert.equal(e.reserved_rows,sum(job.inputs.map(x=>x.input.prompt_ids.length+128)));
  if (!publicMode) assert.equal(hash(fs.readFileSync(path.join(root,wb+'JOB.json'))),e.job_sha256);
  if (host.returncode===0 && host.error===null) {
    assert.equal(read(wb+'native/result.json').status,'COMPLETE');
    const counts = read(wb+'ACTUAL_REQUESTS.json'); assert.equal(counts.length,job.inputs.length);
    for (let i=0;i<counts.length;i++) {
      const entry=job.inputs[i], receipt=read(wb+'native/'+entry.name+'/receipt.json');
      assert.equal(counts[i].actual_forward_rows,entry.input.prompt_ids.length+receipt.ids.length-1);
      actualRows += counts[i].actual_forward_rows;
    }
    completeRequests += e.requests;
  } else {
    // Only the documented, pre-model admission rejection has known zero work.
    assert.equal(host.returncode,2);
    assert.equal(fs.readFileSync(path.join(root,wb+'stderr.log'),'utf8').trim(),'Invalid model reservation/freeze/GPU binding');
    assert(!fs.existsSync(path.join(root,wb+'native/result.json')));
    failedRequests += e.requests;
  }
}
// Compare only after reconstructing clocks, requests, endpoints and estimates.
const saved = read('data/outputs/ANALYSIS.json');
for (const panel of ['R1','R2','H1','R_combined']) {
  if (!results[panel]?.estimate) continue;
  const expected = saved[panel].estimate, actual = results[panel].estimate;
  close(actual.CB,expected.CB); actual.CI95.forEach((v,i)=>close(v,expected.CI95[i]));
  actual.simultaneous_CI975.forEach((v,i)=>close(v,expected.simultaneous_CI975[i]));
}
for (const panel of ['R1','R2','H1']) {
  if (results[panel].status !== 'COMPLETE') continue;
  const rr = read(`data/outputs/${panel}/ROWS.json`), actual = rows.filter(r=>r.cohort===panel[0] && r.day===(panel==='R2'?2:1));
  assert.equal(actual.length,rr.length);
  for (let i=0;i<actual.length;i++) for (const [k,v] of Object.entries(actual[i])) {
    if (k==='actual_forward_rows') continue;
    if (typeof v==='number') close(v,rr[i][k]); else assert.deepEqual(v,rr[i][k]);
  }
}
write('RECONSTRUCTED_ROWS.json',rows); write('WORKER_COSTS.json',costs);
write('INDEPENDENT_REPORT.json',{status:'INDEPENDENT_RAW_RECEIPT_AND_BOOTSTRAP_REPLAY_PASS',model_calls:0,public_mode:publicMode,
  original_runtime_config_hashes_checked:publicMode?0:rows.length,
  accounting,completed_requests:completeRequests,charged_failed_requests:failedRequests,actual_forward_rows:actualRows,
  bootstrap:{seed:20261113,draws:20000,unit:'whole paired root within six-code/six-math strata; dates and rounds attached'},results,
  limitation:'Saved text/statistical replay; numerical bytes are represented by the retained native check proofs and private inventory, not independently repeated tensor comparisons. Public mode does not reconstruct original runtime/job hashes containing the redacted study-root path.'});
console.log(JSON.stringify({status:'PASS',rows:rows.length,results:Object.fromEntries(Object.entries(results).map(([k,v])=>[k,v.estimate?{CB:v.estimate.CB,CI95:v.estimate.CI95}:v]))}));
