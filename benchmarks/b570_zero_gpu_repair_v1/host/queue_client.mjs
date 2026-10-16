// Runs in the pre-existing tool service; creates no task child processes.
// The broker never sees a .request.json until all bytes are flushed and closed.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
const base='C:/hs/b570-zero-gpu-repair-v1-20261016';
export async function publish(index,id,argv,extra={}) {
  if(!/^[A-Za-z0-9_-]+$/.test(id)) throw Error('invalid request ID');
  // Submission is serialized, including the broker's between-command inventory.
  // A result must be completely parseable before another publication starts.
  for(const name of await fs.readdir(base+'/queue-v2')) {
    if(!name.endsWith('.request.json')) continue;
    const result=base+'/queue-v2/'+name.replace('.request.json','.result.json');
    try {JSON.parse(await fs.readFile(result,'utf8'));} catch(e) {throw Error('prior command has not closed: '+name);}
  }
  const stem=base+'/queue-v2/'+String(index).padStart(4,'0')+'-'+id;
  const data=Buffer.from(JSON.stringify({id,argv,...extra,env:{TEMP:base+'/tmp',TMP:base+'/tmp',PYTHONDONTWRITEBYTECODE:'1',PYTHONIOENCODING:'utf-8',...extra.env}}));
  if(data.length>65536) throw Error('request reservation');
  try {await fs.access(stem+'.request.json');throw Error('request already registered');} catch(e) {if(e.code!=='ENOENT')throw e;}
  const f=await fs.open(stem+'.partial','wx');
  try {await f.writeFile(data);await f.sync();} finally {await f.close();}
  await fs.rename(stem+'.partial',stem+'.request.json');
  await fs.writeFile(stem+'.published.json',JSON.stringify({id,bytes:data.length,sha256:crypto.createHash('sha256').update(data).digest('hex'),clock_domain:'tool-service wall time only; not a supervision clock',published_utc:new Date().toISOString(),method:'exclusive staged file; complete fsync/close; atomic rename'},null,2),{flag:'wx'});
  return stem+'.result.json';
}
