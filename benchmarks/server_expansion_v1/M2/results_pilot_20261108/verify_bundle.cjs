const fs=require('fs'),crypto=require('crypto'),zlib=require('zlib'),{StringDecoder}=require('string_decoder');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');const read=p=>JSON.parse(fs.readFileSync(p));
const bad=/munic[0-9]{4}|\b192\.168\.\d+\.\d+\b|(?<![A-Za-z0-9_])\/home\/[a-zA-Z0-9_-]+\/|GPU-[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}|github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}/i;
async function verify(base){
 const scope=read(base+'/EXPORT_SCOPE.json'),ti=read(base+'/TEXT_INDEX.json'),bi=read(base+'/BINARY_CAPTURE_INDEX.json');
 for(const [name,key]of [['scientific-records.json.gz','bundle_sha256'],['TEXT_INDEX.json','text_index_sha256'],['BINARY_CAPTURE_INDEX.json','binary_index_sha256']])if(hash(base+'/'+name)!==scope[key])throw Error('File hash mismatch '+name);
 const entries=new Map(ti.files.map(x=>[x.path,x]));if(entries.size!==ti.files.length||entries.size!==scope.text_files||bi.files.length!==bi.count||bi.count!==scope.binary_captures)throw Error('Index cardinality');
 const header='{"schema":"linux-transfer.public-text-bundle.v1","records":[',decoder=new StringDecoder('utf8');let head=0,depth=0,quoted=false,escaped=false,parts=[],arrayEnded=false,ended=false,count=0,bytes=0;
 function complete(s){const x=JSON.parse(s),i=entries.get(x.path);if(bad.test(x.text))throw Error('Unreviewed private literal '+x.path);if(!i||typeof x.text!=='string'||Buffer.byteLength(x.text)!==i.exported_bytes||crypto.createHash('sha256').update(x.text).digest('hex')!==i.exported_sha256)throw Error('Record hash/cardinality mismatch '+x.path);entries.delete(x.path);count++;}
 function scan(s){let segment=depth?0:-1;
  for(let i=0;i<s.length;i++){const c=s[i];if(head<header.length){if(c!==header[head++])throw Error('Unexpected canonical bundle header');continue;}
   if(ended){if(!/\s/.test(c))throw Error('Unexpected trailing bytes');continue;}
   if(arrayEnded){if(/\s/.test(c))continue;if(c!=='}')throw Error('Missing bundle terminator');ended=true;continue;}
   if(depth===0){if(c===','||/\s/.test(c))continue;if(c===']'){arrayEnded=true;continue;}if(c!=='{')throw Error('Expected record object');depth=1;segment=i;quoted=false;escaped=false;continue;}
   if(quoted){if(escaped)escaped=false;else if(c==='\\')escaped=true;else if(c==='"')quoted=false;}
   else if(c==='"')quoted=true;else if(c==='{')depth++;else if(c==='}'){depth--;if(depth===0){parts.push(s.slice(segment,i+1));complete(parts.join(''));parts=[];segment=-1;}}
  }
  if(depth&&segment>=0)parts.push(s.slice(segment));
 }
 const stream=fs.createReadStream(base+'/scientific-records.json.gz').pipe(zlib.createGunzip());for await(const chunk of stream){bytes+=chunk.length;scan(decoder.write(chunk));}scan(decoder.end());
 if(!ended||depth||parts.length||entries.size||bytes!==ti.uncompressed_bytes||count!==scope.text_files)throw Error('Truncated/incomplete stream');
 if(bi.files.reduce((a,x)=>a+x.bytes,0)!==bi.bytes||new Set(bi.files.map(x=>x.path)).size!==bi.count)throw Error('Binary index accounting');
 return {text_files:count,uncompressed_bytes_verified:bytes,binary_captures:bi.count,bundle_sha256:scope.bundle_sha256,formal_performance_status:scope.formal_performance_status};
}
(async()=>{const start=Date.now(),result=await verify(process.argv[2]);const proof={passed:true,...result,all_exported_records_byte_verified:true,privacy_scan_pass:true,wall_s:(Date.now()-start)/1000,new_native_jobs:0};fs.writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(proof));})().catch(e=>{console.error(e);process.exitCode=1;});
