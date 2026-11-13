'use strict';
const fs=require('fs'),crypto=require('crypto');const {validateTokenIDs}=require('../contracts.js');
const [originalInput,actualOutput,out]=process.argv.slice(2);if(!originalInput||!actualOutput||!out)throw Error('node prepare_control_fixtures.js INPUT01 OUTPUT01 FRESH_INPUT02');if(fs.existsSync(out))throw Error('fresh control input');const a=JSON.parse(fs.readFileSync(originalInput)),b=JSON.parse(fs.readFileSync(actualOutput));if(b.eog_ids.length!==6||b.n_vocab!==151936)throw Error('actual vocab binding');const prep=new Map(b.tokenize_cases.map(x=>[x.id,x.ids]));const seed=a.bridge_cases[0],cases=[];
function add(id,sampled,cap,terminal,expect,detail){if(expect==='PASS')validateTokenIDs(sampled,{n_vocab:b.n_vocab,label:id});cases.push({id,source_kind:'EXPLICIT_SYNTHETIC_CPU_BOUNDARY_CONTROL_NOT_MODEL_OUTPUT',messages:seed.messages,sampled_ids:sampled,cap,terminal,next_user:seed.next_user,expected_class:expect,boundary:detail});}
for(const eog of b.eog_ids)add('eog:'+eog,[eog],128,'EOG','PASS','Every actual EOG token, empty response, pending token not presumed materialized');
add('eog_cap1_priority',[b.eos_id],1,'EOG','PASS','EOG at output cap is EOG');
add('cap1_ascii',[...prep.get('ascii_a')],1,'CAP','PASS','One output pending, valid ASCII');
add('cap128_ascii',Array(128).fill(prep.get('ascii_a')[0]),128,'CAP','PASS','Synthetic cap bound; never a measured or natural episode');
add('empty_think_generated',[...prep.get('empty_think'),b.eos_id],128,'EOG','PASS','Actual parser receives returned generation prefix plus an explicit empty-think output');
add('special_boundary',[...prep.get('special_boundary'),b.eos_id],128,'EOG','PASS','Actual special=false/preserved-token piece policy; other control token suppressed');
add('empty_ids',[],128,'EOG','REJECT','No sampled terminal');
add('early_eog_then_token',[b.eos_id,64],128,'EOG','REJECT','Tokens after early EOG');
add('cap_declares_eog',[b.eos_id],1,'CAP','REJECT','Terminal category mismatch');
add('eog_declares_non_eog',[64],128,'EOG','REJECT','Terminal category mismatch');
add('cap_count_mismatch',[64],2,'CAP','REJECT','Cap reached condition not satisfied');
add('cap0',[64],0,'CAP','REJECT','Invalid cap');
add('id_out_of_vocab',[151936],1,'CAP','REJECT','Native integer/range validation');
add('id_negative',[-1],1,'CAP','REJECT','Native integer/range validation');
add('id_fractional',[1.5],1,'CAP','REJECT','Native JSON type validation');
add('id_null',[null],1,'CAP','REJECT','Native JSON type validation');
add('id_string',['64'],1,'CAP','REJECT','Native JSON type validation');
// Saved native vocabulary identifies ID172 as the single byte F0. Actual bridge
// token-to-piece verifies its bytes; incomplete UTF8 needs a real server policy.
add('incomplete_utf8_cap',[172],1,'CAP','BLOCK','Unsupported truncated UTF8 output route must remain an explicit gate');
const job={schema:a.schema,expected_template_utf8:a.expected_template_utf8,profile:a.profile,render_cases:[],tokenize_cases:[],bridge_cases:cases,prepared_from:{input01_sha256:crypto.createHash('sha256').update(fs.readFileSync(originalInput)).digest('hex'),output01_sha256:crypto.createHash('sha256').update(fs.readFileSync(actualOutput)).digest('hex')},selection:'All actual EOG IDs and fixed boundary cases; no geometry/latency/acceptance selection'};fs.writeFileSync(out,JSON.stringify(job)+'\n');console.log(JSON.stringify({CPU_boundary_cases:cases.length,expected_positive:cases.filter(x=>x.expected_class==='PASS').length,expected_reject:cases.filter(x=>x.expected_class==='REJECT').length,expected_block:cases.filter(x=>x.expected_class==='BLOCK').length}));
