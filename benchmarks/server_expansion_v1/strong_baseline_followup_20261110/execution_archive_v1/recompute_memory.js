// Inspect original published telemetry without relabeling total-used as free.
// Usage: node recompute_memory.js F1_TRANSPORT_DIRECTORY FRESH_REPORT
const fs=require('fs'),path=require('path'),zlib=require('zlib'),crypto=require('crypto'),assert=require('assert/strict');
const root=process.argv[2],report=process.argv[3];assert(root&&report&&!fs.existsSync(report));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const pkg=JSON.parse(fs.readFileSync(path.join(root,'F1_ARCHIVE/PACKAGE.json'),'utf8'));
const parts=pkg.ordered_parts.map(p=>{const b=fs.readFileSync(path.join(root,p.path));assert.equal(b.length,p.bytes);assert.equal(hash(b),p.sha256);const x=Buffer.from(b.toString().trim(),'base64');assert.equal(x.length,p.decoded_bytes);return x;});
const gzip=Buffer.concat(parts);assert.equal(hash(gzip),pkg.archive.archive_sha256);assert.equal(gzip.length,pkg.archive.archive_bytes);
const tar=zlib.gunzipSync(gzip),files=new Map();
const word=b=>b.toString('utf8').split('\0')[0];
for(let at=0;at+512<=tar.length;){const h=tar.subarray(at,at+512);if(h.every(x=>x===0))break;
 let name=word(h.subarray(0,100)),prefix=word(h.subarray(345,500));if(prefix)name=prefix+'/'+name;
 assert(!name.startsWith('/')&&!name.split('/').includes('..')&&!files.has(name));
 assert.equal(String.fromCharCode(h[156]),'0');const size=parseInt(word(h.subarray(124,136)).trim(),8);
 assert(Number.isSafeInteger(size)&&size>=0&&at+512+size<=tar.length);files.set(name,tar.subarray(at+512,at+512+size));at+=512+Math.ceil(size/512)*512;
}
const index=JSON.parse(files.get('INDEX.json').toString());assert.equal(index.files.length,2398);
for(const x of index.files){const b=files.get(x.path);assert(b);assert.equal(b.length,x.bytes);assert.equal(hash(b),x.sha256);}
let telemetryFiles=0,samples=0,maxUsed=0,minDifference=Infinity;const workers=[];
for(const [name,b]of files){if(!name.includes('TELEMETRY')||!name.endsWith('.jsonl'))continue;
 let count=0,maximum=0,minimum=Infinity;
 for(const line of b.toString().split('\n')){if(!line.trim())continue;const x=JSON.parse(line),g=x.allocated_GPU_metrics;if(!g)continue;
  count++;samples++;maximum=Math.max(maximum,Number(g.used_MiB));minimum=Math.min(minimum,Number(g.total_MiB)-Number(g.used_MiB));}
 if(count){telemetryFiles++;maxUsed=Math.max(maxUsed,maximum);minDifference=Math.min(minDifference,minimum);workers.push({file:name,samples:count,max_used_MiB:maximum,min_total_minus_used_MiB:minimum});}
}
const out={status:'ORIGINAL_PUBLIC_S1_TELEMETRY_INDEPENDENTLY_AUDITED',logical_text_files:2398,telemetryFiles,samples,
 max_sampled_used_MiB:maxUsed,min_sampled_total_minus_used_MiB:minDifference,actual_old_memory_free:'NOT_SEPARATELY_RECORDED',
 driver_reserved_memory:'Not subtracted by original host gate; do not relabel difference as actual free',
 scope:'Periodic retained observations, not a continuous peak or retrospective proof of actual-free reserve',
 correction:'S3 RESOURCE02 uses explicit NVML memory.free before any new S3 GPU request; old measurements remain unchanged',workers};
fs.writeFileSync(report,JSON.stringify(out,null,2)+'\n',{flag:'wx'});process.stdout.write(JSON.stringify({...out,workers:undefined})+'\n');
