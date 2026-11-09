const fs=require('fs'),path=require('path'),crypto=require('crypto');
const [source,dest]=process.argv.slice(2);if(!source||!dest)throw Error('Usage: node assemble_archive.cjs RESULT_DIR FRESH_BUNDLE');
const read=n=>JSON.parse(fs.readFileSync(path.join(source,n))),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const parts=read('PARTS.json'),manifest=read('BUNDLE.json'),buffers=[];
for(const p of parts.parts){if(path.isAbsolute(p.path)||p.path.split('/').includes('..'))throw Error('Unsafe part path');const b=fs.readFileSync(path.join(source,p.path));if(b.length!==p.bytes||sha(b)!==p.sha256)throw Error('Part mismatch');buffers.push(b);}
const b=Buffer.concat(buffers);if(b.length!==parts.bytes||sha(b)!==parts.sha256||b.length!==manifest.bytes||sha(b)!==manifest.sha256)throw Error('Whole gzip mismatch');
fs.mkdirSync(dest);fs.writeFileSync(path.join(dest,manifest.file),b,{flag:'wx'});
for(const n of ['BUNDLE.json','TEXT_INDEX.json','BINARY_CAPTURE_INDEX.json','COSTS.json','RESOURCE_CHECKED.json'])fs.copyFileSync(path.join(source,n),path.join(dest,n),fs.constants.COPYFILE_EXCL);
console.log(JSON.stringify({passed:true,parts:parts.parts.length,bytes:b.length,sha256:sha(b)}));
