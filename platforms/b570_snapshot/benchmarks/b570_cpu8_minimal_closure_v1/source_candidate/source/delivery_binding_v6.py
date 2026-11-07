"""Bind actual orchestrator-captured provider exports; never certifies an external authority."""
import base64,datetime,hashlib,json,re,shlex,subprocess
from pathlib import Path
from evidence_contract import need,member
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())

def utc(value):
 t=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
 need(t.tzinfo is not None,'capture timezone');return t

def guarded_request(original,operation,operation_sha256,python):
 """One explicit supported shell request; shell text is never parsed or executed here."""
 argv=[python,'-I','-S','-B',(original/'source/operation_guard.py').as_posix(),
       '--intent',(original/'tools'/(operation+'.operation.json')).as_posix(),
       '--intent-sha256',operation_sha256]
 return '& '+' '.join("'"+x.replace("'","''")+"'" for x in argv)

def request_check(root,operation,intent,first,guard,operation_sha256):
 campaign=load(root/'CAMPAIGN.json');original=Path(campaign['original_root'])
 # Pre-freeze prerequisite receipts use the pinned tools inventory. Formal receipts
 # must also agree with the immutable execution freeze.
 python=load(member(root,'preflight/TOOLS.json'))['python']['path']
 expected=guarded_request(original,operation,operation_sha256,python)
 req=first['request']
 need(req==intent['request'] and req['cmd']==expected,'actual guarded request')
 need(set(req)=={'cmd','shell','login','workdir','max_output_tokens','yield_time_ms'},'tool request fields')
 need(req['login'] is False and Path(req['workdir'])==original,'tool request environment')
 need(Path(req['shell'])==Path('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'),'supported tool shell')
 need(type(req['max_output_tokens']) is int and 0<req['max_output_tokens']<=2000 and
      type(req['yield_time_ms']) is int and 0<req['yield_time_ms']<=10000,'capture request limits')
 need(Path(guard['image'])==Path(python) and guard['intent_sha256']==operation_sha256,'guard native identity')
 guard_argv=[python,'-I','-S','-B',str(original/'source/operation_guard.py'),
             '--intent',str(original/'tools'/(operation+'.operation.json')),'--intent-sha256',operation_sha256]
 # Native command lines use Win32 quoting, independently of the shell request.
 normalize=lambda x:x.replace('/',chr(92))
 native_argv=[x[1:-1] if x.startswith('"') and x.endswith('"') else x
              for x in shlex.split(guard['command'],posix=False)]
 need(list(map(normalize,native_argv))==list(map(normalize,guard_argv)),'guard native command')
 need(hashlib.sha256(guard['command'].encode()).hexdigest()==guard['command_sha256'],'guard command digest')
 freeze=root/'CAPABILITY_FREEZE.json'
 if freeze.exists():
  frozen=load(freeze)
  need(Path(python)==Path(frozen['python']) and load(root/'preflight/TOOLS.json')['python']['sha256']==frozen['python_sha256'],'frozen guard interpreter')
 return original
def capture(root,op,kind):
 need(re.fullmatch(r'[A-Za-z0-9-]+',op) is not None,'capture id')
 need(re.fullmatch(r'initial|poll[1-9][0-9]*|download',kind) is not None,'capture kind')
 c=load(Path(root)/'CAMPAIGN.json');ext=Path(c['external_root']).resolve()
 original=Path(c['original_root']).resolve()
 need(ext!=original and original not in ext.parents and ext not in original.parents,'capture index must be outside candidate')
 raw=member(root,'tools/'+op+'.'+kind+'.json');index=ext/'capture-index'/(op+'.'+kind+'.json')
 for path in (raw,index):
  for ancestor in [path,*path.parents]:
   need(not ancestor.is_symlink() and not ancestor.is_junction(),'capture ancestor alias')
  need(path.is_file() and not path.is_symlink() and not path.is_junction() and path.stat().st_nlink==1,'capture alias/missing')
 x=load(index);need(Path(x['path']).resolve()==(original/'tools'/(op+'.'+kind+'.json')).resolve() and x['sha256']==h(raw) and x['bytes']==raw.stat().st_size,'capture index bytes')
 z=load(raw);need(x['capture_meta']==z['capture_meta'] and z['capture_meta']['callId'] and z['capture_meta']['itemId'],'actual capture supervisor identity')
 need(z['id']==op and z['kind']==kind,'capture operation identity')
 return z

def _postseal_file(root, subdir, filename):
 """Only platform-owned postseal evidence. Never fallback to the sealed root."""
 root=Path(root).resolve()
 campaign=load(root/'CAMPAIGN.json')
 original=Path(campaign['original_root']).resolve()
 outside=Path(campaign['external_root']).resolve()
 need(root==original and outside!=original and
      original not in outside.parents and outside not in original.parents,
      'postseal evidence requires the actual original/external pair')
 need(re.fullmatch(r'[A-Za-z0-9_.-]+',filename) is not None,'postseal filename')
 need(subdir in ('captures','capture-index','intents','native-exits','stdout'),
      'postseal evidence kind')
 path=outside/'postseal'/subdir/filename
 for ancestor in [path,*path.parents]:
  need(not ancestor.is_symlink() and not ancestor.is_junction(),
       'postseal alias')
 need(path.is_file() and path.stat().st_nlink==1,'postseal evidence missing')
 return path

def postseal_capture(root,operation,kind):
 """Read a download/restore provider return without changing any sealed byte."""
 need(re.fullmatch(r'[A-Za-z0-9-]+',operation) is not None,'postseal operation id')
 need(re.fullmatch(r'initial|poll[1-9][0-9]*|download',kind) is not None,
      'postseal capture kind')
 name=operation+'.'+kind+'.json'
 raw=_postseal_file(root,'captures',name)
 index=_postseal_file(root,'capture-index',name)
 doc=load(index);capture=load(raw)
 need(Path(doc['path']).resolve()==raw and doc.get('sha256')==h(raw)
      and doc.get('bytes')==raw.stat().st_size and
      doc.get('capture_meta')==capture.get('capture_meta'),
      'postseal capture index/bytes')
 meta=capture.get('capture_meta',{})
 need(meta.get('callId') and meta.get('itemId'),'postseal provider capture identity')
 need(capture.get('id')==operation and capture.get('kind')==kind,
      'postseal operation/kind')
 return capture

def restore_postseal_invocation(root,operation,argv,report):
 """Fixed isolated recompute chain whose tool/native outputs live outside F0.

 This verifies externally recorded bytes and identities, not the undisclosed
 provider's service OS lifecycle. C admission must separately authenticate it.
 """
 need(re.fullmatch(r'[A-Za-z0-9-]+',operation) is not None,'restore operation id')
 root=Path(root).resolve()
 campaign=load(root/'CAMPAIGN.json')
 frozen_sha=h(root/'CAPABILITY_FREEZE.json')
 intent_path=_postseal_file(root,'intents',operation+'.json')
 intent=load(intent_path)
 need(intent.get('schema')=='B570_POSTSEAL_RESTORE_V1' and
      intent.get('task_uuid')==campaign.get('task_uuid') and
      intent.get('operation_id')==operation and
      intent.get('freeze_sha256')==frozen_sha and
      intent.get('argv')==argv,'postseal restore prospective operation')
 first=postseal_capture(root,operation,'initial')
 original=Path(campaign['original_root']).resolve()
 outside=Path(campaign['external_root']).resolve()
 need(first['request']==intent['request'],'postseal actual first request')
 clips=sorted((outside/'postseal'/'captures').glob(operation+'.poll*.json'),
              key=lambda p:int(p.name.split('.poll')[1].split('.')[0]))
 need([p.name for p in clips]==[operation+'.poll'+str(i)+'.json'
                               for i in range(1,len(clips)+1)],
      'postseal poll sequence')
 events=[first]+[postseal_capture(root,operation,
          p.name[len(operation)+1:-5]) for p in clips]
 previous=utc(intent['registered_utc'])
 session=first['response'].get('session_id')
 need(session is None or (type(session) is int and session>0),
      'postseal session type')
 output=[]
 for i,e in enumerate(events):
  now=utc(e['observed_utc'])
  need(previous<=now,'postseal capture order')
  previous=now
  if i:
   need(type(session) is int and e['request']=={'session_id':session},
        'postseal poll session')
  response=e['response']
  need(type(response.get('output')) is str and
       response.get('session_id',session)==session and
       response.get('isError') is False,
       'postseal provider response/session')
  code=response.get('exit_code')
  need(code is None or (i==len(events)-1 and type(code) is int and code==0),
       'postseal provider terminal')
  output.append(response['output'])
 terminal=events[-1]['response']
 need(type(terminal.get('exit_code')) is int and terminal['exit_code']==0,
      'postseal terminal response missing')
 native_path=_postseal_file(root,'native-exits',operation+'.json')
 native=load(native_path)
 report=Path(report).resolve()
 need(outside in report.parents and report.is_file() and
      not report.is_symlink() and not report.is_junction() and
      report.stat().st_nlink==1,'postseal report must be external')
 stdout=_postseal_file(root,'stdout',operation+'.bin')
 born=int(native['created_filetime']);end=int(native['exit_filetime'])
 epoch=datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)
 need(0<born<end and
      utc(intent['registered_utc'])<=epoch+datetime.timedelta(microseconds=born//10)
      and epoch+datetime.timedelta(microseconds=end//10)<=previous,
      'postseal native/provider lifetime')
 need(native.get('task_uuid')==campaign.get('task_uuid')
      and native.get('operation_id')==operation
      and native.get('freeze_sha256')==frozen_sha
      and native.get('intent_sha256')==h(intent_path)
      and native.get('argv')==argv
      and native.get('command')==subprocess.list2cmdline(argv)
      and native.get('pid',0)>0 and native.get('parent_pid',0)>0
      and native.get('image')==argv[0]
      and native.get('exit_code')==0
      and native.get('all_owned_handles_closed') is True
      and native.get('descendants_exited') is True
      and native.get('job_empty') is True,
      'postseal actual native OS identity/exit/cleanup')
 need(report.read_bytes()==stdout.read_bytes()
      and h(report)==native.get('report_sha256')
      and h(stdout)==native.get('stdout_sha256'),
      'postseal full output bytes not authenticated')
 return dict(status='POSTSEAL_RESTORE_CAPTURE_BOUND',
             report_sha256=h(report),native_receipt_sha256=h(native_path),
             session_id=session,provider_chunk_ids=[
                 e['response'].get('chunk_id') for e in events],
             provider_call_id='UNKNOWN_NOT_EXPOSED',
             scope='External owner OS/provider capture and exact full bytes; independent provider authentication still required')

def download(root,operation,row,commit):
 z=postseal_capture(root,operation,'download')
 ext=Path(load(Path(root)/'CAMPAIGN.json')['external_root'])
 intent=load(ext/'download-intents'/(operation+'.json'))
 need(z['request']==intent['request'],'download actual request')
 req=z['request'];need(req['repository_full_name']=='leecdiang/HeteroSpec' and req['ref']==commit and re.fullmatch('[0-9a-f]{40}',commit),'download immutable repo/ref')
 need(req['path']==row['remote_path'],'download remote path')
 result=z['response'];need(result.get('isError') is False,'download provider error')
 r=result['structuredContent'];need(r['sha']==row['remote_blob_sha'],'download actual blob')
 need(r['encoding'] in ('utf-8','base64'),'download encoding')
 data=r['content'].encode('utf8') if r['encoding']=='utf-8' else base64.b64decode(r['content'],validate=True)
 need(data==Path(row['path']).read_bytes(),'download actual output bytes')
 need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==r['sha'],'download Git blob digest')
 need(utc(intent['registered_utc'])<=utc(z['observed_utc']),'download prospective order')
 return dict(status='ACTUAL_PROVIDER_DOWNLOAD_BOUND',commit=commit,blob=r['sha'],capture_call=z['capture_meta']['callId'],provider_call_id='UNKNOWN_NOT_EXPOSED',scope='Actual provider return bytes and outside-candidate capture index; auditable consistency, no external certification')
def invocation(root,operation,argv,report):
 root=Path(root);need(re.fullmatch(r'[A-Za-z0-9-]+',operation) is not None,'invocation id')
 intent=load(member(root,'tools/'+operation+'.intent.json'));op_path=member(root,'tools/'+operation+'.operation.json');op=load(op_path)
 need(op['argv']==argv,'restore actual argv')
 first=capture(root,operation,'initial');need(first['request']==intent['request'],'restore actual tool request')
 need(intent['operation_sha256']==h(root/'tools'/(operation+'.operation.json')),'restore prospective operation')
 paths=sorted((root/'tools').glob(operation+'.poll*.json'),key=lambda p:int(p.name.split('.poll')[1].split('.')[0]))
 need([p.name for p in paths]==[operation+'.poll'+str(i)+'.json' for i in range(1,len(paths)+1)],'poll sequence')
 events=[first]+[capture(root,operation,p.name.split('.')[1]) for p in paths]
 terminal=False;sid=first['response'].get('session_id')
 need(sid is None or (type(sid) is int and sid>0),'tool session type')
 previous=utc(intent['registered_utc']);output=[]
 for i,e in enumerate(events):
  need(not terminal,'event after terminal')
  observed=utc(e['observed_utc']);need(previous<=observed,'capture order');previous=observed
  if i:need(sid is not None and type(e['request']['session_id']) is int and e['request']['session_id']==sid,'restore actual poll session')
  r=e['response'];need(type(r['output']) is str,'restore actual output')
  need(r.get('session_id') is None or (type(r['session_id']) is int and r['session_id']>0),'provider session type')
  need(r.get('session_id',sid)==sid,'changed provider session');output.append(r['output'])
  need(not r.get('isError',False),'provider error')
  if r.get('exit_code') is not None:need(type(r['exit_code']) is int and r['exit_code']==0,'restore terminal exit');terminal=True
 need(terminal,'restore missing actual completion')
 folder=member(root,'operations/'+operation,directory=True)
 data=member(root,'operations/'+operation+'/EVENTS.jsonl').read_bytes()
 need(data.endswith(b'\n'),'partial native journal');rs=[json.loads(x) for x in data.splitlines()]
 need(all(r['seq']==i+1 for i,r in enumerate(rs)) and all(x['at_ns']<=y['at_ns'] for x,y in zip(rs,rs[1:])),'native journal order')
 def one(event):
  got=[r for r in rs if r['event']==event];need(len(got)==1,'restore '+event);return got[0]
 guard=one('GUARD_START');begin=one('OP_CREATED_SUSPENDED');end=one('OP_OS_EXIT');close=one('GUARD_END')
 original=request_check(root,operation,intent,first,guard,h(op_path))
 need(op['id']==operation and Path(op['root'])==original,'operation root identity')
 need(begin['argv']==argv and begin['command']==subprocess.list2cmdline(argv),'restore actual OS command')
 need(begin['created_filetime']==end['created_filetime'] and begin['pid']==end['pid'] and int(end['exit_filetime'])>int(begin['created_filetime']) and end['exit_code']==0,'restore actual OS exit')
 receipt=load(member(root,'operations/'+operation+'/RECEIPT.json'))
 need(close==rs[-1] and close['receipt']==receipt,'native terminal receipt bytes')
 need(receipt['status']=='CLOSED' and receipt['job_empty'] is True and receipt['error'] is None and receipt['child_exit_code']==0 and receipt['intent_sha256']==h(op_path),'restore actual Job closure')
 handles=one('MEMBER_HANDLES_CLOSED');job_close=one('OP_JOB_HANDLE_CLOSED')
 need(receipt.get('member_exits_complete') is True and handles['complete'] is True and job_close['job_empty'] is True,'native member closure')
 identities={(begin['pid'],begin['created_filetime'])}
 retained=[r for r in rs if r['event']=='MEMBER_IDENTITY']
 terminals=[r for r in rs if r['event']=='MEMBER_TERMINAL_OS']
 keys=lambda rr:[(r['pid'],r['created_filetime']) for r in rr]
 need(len(keys(retained))==len(set(keys(retained))) and sorted(keys(retained))==sorted(keys(terminals)),'native member exit inventory')
 need(all(int(r['exit_filetime'])>int(r['created_filetime']) for r in terminals),'native member exit time')
 identities.update(keys(retained))
 need(type(receipt['total_job_processes']) is int and receipt['total_job_processes']==len(identities) and handles['count']==len(retained),'native complete start inventory')
 need(end['at_ns']<handles['at_ns']<job_close['at_ns']<close['at_ns'],'native handle closure order')
 need(guard['at_ns']<=begin['at_ns']<=end['at_ns']<=close['at_ns'] and begin['parent_pid']==guard['pid'],'guard child lifecycle')
 born=int(guard['created_filetime']);child_born=int(begin['created_filetime']);child_end=int(end['exit_filetime'])
 epoch=datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)
 need(0<born<=child_born<child_end,'native process time order')
 need(utc(intent['registered_utc'])<=epoch+datetime.timedelta(microseconds=born//10) and
      epoch+datetime.timedelta(microseconds=child_end//10)<=utc(events[-1]['observed_utc']),'native/provider prospective interval')
 need(all(r['writer_pid']==guard['pid'] for r in rs),'native journal writer')
 need(utc(op['registered_utc'])<=utc(intent['registered_utc'])<=utc(events[0]['observed_utc']),'request prospective order')
 summary=dict(operation=operation,status='CLOSED',error=None,job_empty=True,child_exit_code=0)
 # Provider output is the guard summary, not the child's potentially untrusted stdout.
 emitted=''.join(output).replace('\r\n','\n')
 lines=emitted.splitlines();need(len(lines)==1 and json.loads(lines[0])==summary,'actual provider terminal output')
 need('-I' in argv and '-S' in argv and '-B' in argv,'restore isolated flags')
 need(Path(argv[0]).resolve()==Path(begin['image']).resolve(),'restore actual interpreter')
 need(Path(report).is_file() and Path(report).read_bytes()==(folder/'stdout.log').read_bytes(),'restore actual emitted report bytes')
 return dict(status='ACTUAL_PROVIDER_RESTORE_BOUND',pid=begin['pid'],created_filetime=begin['created_filetime'],exit_filetime=end['exit_filetime'],session_id=sid,report_sha256=h(report),provider_chunk_ids=[e['response'].get('chunk_id') for e in events],provider_call_id='UNKNOWN_NOT_EXPOSED',outer_lifecycle='UNKNOWN',scope='Recorded request/session terminal + native process identity/closure + actual stdout report; chunk IDs are not provider call IDs')
