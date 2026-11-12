// Independent saved-data verification. Never initializes a GPU or invokes Python.
// node recompute.js RESTORED_ARCHIVE FRESH_REPORT BYTE_SOURCE_SCOPE
// node recompute.js --self-test
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
class CPythonRandom {
 constructor(seed){this.mt=new Uint32Array(624);this.mt[0]=19650218;
  for(let i=1;i<624;i++)this.mt[i]=(Math.imul(1812433253,this.mt[i-1]^(this.mt[i-1]>>>30))+i)>>>0;
  let i=1;for(let k=0;k<624;k++){this.mt[i]=((this.mt[i]^Math.imul(this.mt[i-1]^(this.mt[i-1]>>>30),1664525))+seed)>>>0;
   if(++i>=624){this.mt[0]=this.mt[623];i=1;}}
  for(let k=0;k<623;k++){this.mt[i]=((this.mt[i]^Math.imul(this.mt[i-1]^(this.mt[i-1]>>>30),1566083941))-i)>>>0;
   if(++i>=624){this.mt[0]=this.mt[623];i=1;}}
  this.mt[0]=0x80000000;this.index=624;
 }
 next(){if(this.index>=624){for(let i=0;i<624;i++){const y=(this.mt[i]&0x80000000)|(this.mt[(i+1)%624]&0x7fffffff);
   this.mt[i]=(this.mt[(i+397)%624]^(y>>>1)^((y&1)?0x9908b0df:0))>>>0;}this.index=0;}
  let y=this.mt[this.index++];y^=y>>>11;y^=(y<<7)&0x9d2c5680;y^=(y<<15)&0xefc60000;y^=y>>>18;return y>>>0;
 }
 six(){let r;do{r=this.next()>>>29;}while(r>=6);return r;}
}
function rngTest(){const r=new CPythonRandom(20261110);assert.deepEqual(Array.from({length:24},()=>r.six()),[2,5,1,4,5,5,3,5,5,2,2,1,4,2,1,2,4,4,3,4,1,2,5,4]);}
const close=(a,b)=>assert(Math.abs(a-b)<1e-12*Math.max(1,Math.abs(a),Math.abs(b)),`${a} != ${b}`);
function percentile(xs,p){const at=(xs.length-1)*p,lo=Math.floor(at),hi=Math.ceil(at);return xs[lo]+(xs[hi]-xs[lo])*(at-lo);}
function estimate(rows){
 const lookup=new Map(rows.filter(x=>x.role==='measured').map(x=>[`${x.slot}/${x.block}/${x.arm}`,x.elapsed_s]));assert.equal(lookup.size,144);
 const output=[];
 for(const [candidate,baseline]of[['C','B'],['B','G'],['C','G']]){
  const roots=[];for(let slot=0;slot<12;slot++){
   const logs=[];for(let round=0;round<4;round++){const a=lookup.get(`${slot}/${round}/${candidate}`),b=lookup.get(`${slot}/${round}/${baseline}`);assert(a>0&&b>0);logs.push(Math.log(a/b));}
   roots.push(logs.reduce((s,x)=>s+x,0)/4);
  }
  const rng=new CPythonRandom(20261110),samples=[];
  for(let i=0;i<20000;i++){let code=0,math=0;for(let j=0;j<6;j++)code+=roots[rng.six()];for(let j=0;j<6;j++)math+=roots[6+rng.six()];samples.push(Math.exp((code/6+math/6)/2));}
  samples.sort((a,b)=>a-b);const tail=candidate==='C'&&baseline==='B'?.025:.0125;
  const total=arm=>rows.filter(x=>x.role==='measured'&&x.arm===arm).reduce((s,x)=>s+x.elapsed_s,0);
  output.push({candidate,baseline,ratio:Math.exp(roots.reduce((s,x)=>s+x,0)/12),interval:[percentile(samples,tail),percentile(samples,1-tail)],
   total_ratio:total(candidate)/total(baseline),per_root_ratio:roots.map(Math.exp),confidence:tail===.025?.95:.975});
 }
 return output;
}
rngTest();
if(require.main!==module){module.exports={estimate,CPythonRandom};
}else if(process.argv[2]==='--self-test'){
 const rows=[];for(let s=0;s<12;s++)for(let b=0;b<4;b++)for(const arm of ['G','B','C'])rows.push({role:'measured',slot:s,block:b,arm,elapsed_s:(s+1)*(b+1)*(arm==='C'?.8:arm==='B'?1:1.25)});
 const result=estimate(rows);close(result[0].ratio,.8);result[0].interval.forEach(x=>close(x,.8));
 process.stdout.write('Independent Node RNG, stratification and constant-ratio fixture passed; zero GPU.\n');
}else{
 const root=process.argv[2],output=process.argv[3];assert(root&&output&&!fs.existsSync(output));
 const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
 const rows=read('data/S3_ROWS.json'),saved=read('data/S3_ANALYSIS.json'),plan=read('data/FROZEN_MANIFEST.json');assert.equal(rows.length,288);
 const map=new Map(rows.map(x=>[x.operation_id,x]));assert.equal(map.size,288);
 const orders=['GBC BCG CGB GCB','BCG CGB GBC CBG','CGB GBC BCG BGC','GCB CBG BGC GBC','CBG BGC GCB BCG','BGC GCB CBG CGB'].map(x=>x.split(' '));
 const formal=plan.workers.filter(x=>x.stage==='formal');assert.equal(formal.length,144);let lastEnd=0,position=0;
 for(let round=0;round<4;round++)for(let ri=0;ri<12;ri++){
  const slot=(ri+3*round)%12;for(const arm of orders[slot%6][round]){
   const w=formal[position++];assert.equal(w.arm,arm);assert.equal(w.slot,slot);assert.equal(w.block,round);assert.equal(w.operations.length,2);
   let warm;
   for(let i=0;i<2;i++){const r=map.get(w.operations[i].operation_id);assert(r);assert.equal(r.worker_id,w.worker_id);assert.equal(r.role,i?'measured':'warm');assert.equal(r.ordinal,i);
    assert.equal(r.arm,arm);assert.equal(r.slot,slot);assert.equal(r.block,round);assert.equal(r.phase,'S3');assert.equal(r.unit,'s');
    assert(Number.isSafeInteger(r.start_ns)&&Number.isSafeInteger(r.end_ns)&&r.start_ns>=lastEnd&&r.end_ns>r.start_ns);lastEnd=r.end_ns;
    assert(r.fence_ns>=r.start_ns&&r.fence_ns<=r.end_ns&&r.owned_ready_ns>=r.start_ns&&r.owned_ready_ns<=r.end_ns);
    close((r.end_ns-r.start_ns)/1e9,r.elapsed_s);assert.equal(r.all_outputs_owned,true);assert.equal(r.callback_continues,true);
    assert.equal(r.q,r.output_rows);assert.equal(r.generated_tokens,r.tokens.length);assert(r.tokens.length>=1&&r.tokens.length<=128);
    assert(['eog','cap'].includes(r.stop_reason));if(r.stop_reason==='cap')assert.equal(r.tokens.length,128);
    const raw=read('data/S3/workers/'+w.worker_id+'/native/'+r.role+'/receipt.json');assert.deepEqual(raw.ids,r.tokens);assert.equal(raw.S3_service.elapsed_s,r.elapsed_s);
    assert.equal(raw.S3_service.initial_reset_included,true);assert(raw.S3_service.empty_after_reset_min<0&&raw.S3_service.empty_after_reset_max<0);
    if(i){assert.deepEqual(warm.tokens,r.tokens);for(const key of ['input_sha256','config_sha256','output_sha256'])assert.equal(warm[key],r[key]);}else warm=r;
   }
  }
 }
 const contrasts=estimate(rows);for(const c of contrasts){const old=saved.contrasts.find(x=>x.candidate===c.candidate&&x.baseline===c.baseline);assert(old);close(c.ratio,old.ratio);close(c.total_ratio,old.total_ratio);c.interval.forEach((x,i)=>close(x,old.interval[i]));c.per_root_ratio.forEach((x,i)=>close(x,old.per_root_ratio[String(i)]));}
 const report={status:'INDEPENDENT_NODE_S3_RECOMPUTATION_PASSED',statistical_replay:'PASSED_COMPLETE_288_FORMAL_OPERATIONS',byte_source:process.argv[4],
  measurements:144,warmups:144,root_units:12,bootstrap:{seed:20261110,replicates:20000,strata:[6,6],unit:'whole_root_all_four_rounds',percentile:'linear_R7',rng:'Independent CPython-compatible MT19937/getrandbits rejection implementation'},contrasts,
  limitations:['Finite12-root predefined short-input panel','Public text replay does not repeat GPU numeric qualification','Exact prescribed order checked; no general randomization/carryover claim']};
 fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});process.stdout.write(JSON.stringify(report)+'\n');
}
