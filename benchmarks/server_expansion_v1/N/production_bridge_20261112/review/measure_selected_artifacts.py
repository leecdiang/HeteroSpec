"""Read-only stat/hash of an explicit retained-artifact selection.

Input is private JSON: aliases->roots, files, tree selections and SOURCE_LOCK
selections. It never scans unrelated worktrees, invokes executables or loads a
model. It prints one receipt and writes nothing on the audited host.
"""
import datetime,hashlib,json,os,pathlib,sys

cfg=json.loads(sys.argv[1]);roots={k:pathlib.Path(v) for k,v in cfg['roots'].items()}
selected={};issues=[]
def add(alias,relative,category,want=None):
 p=roots[alias]/relative
 try:
  if not p.is_file():raise ValueError('not a regular file')
  key=str(p.absolute())
  if key not in selected:selected[key]={'root':alias,'relative_path':relative,'categories':[],'expected_sha256':want}
  x=selected[key];x['categories'].append(category)
  if want is not None:
   if x['expected_sha256'] not in (None,want):raise ValueError('conflicting expected SHA')
   x['expected_sha256']=want
 except (OSError,ValueError) as e:issues.append({'root':alias,'relative_path':relative,'reason':str(e)})
for row in cfg.get('files',[]):add(row['root'],row['relative_path'],row['category'],row.get('sha256'))
for row in cfg.get('trees',[]):
 base=roots[row['root']]/row['relative_path']
 if not base.is_dir():issues.append({'root':row['root'],'relative_path':row['relative_path'],'reason':'missing selected tree'});continue
 for p in sorted(base.rglob('*')):
  if str(p.relative_to(base)) in row.get('exclude',[]):continue
  if any(part in row.get('exclude_parts',[]) for part in p.relative_to(base).parts):continue
  if p.is_symlink():issues.append({'root':row['root'],'relative_path':str(p.relative_to(roots[row['root']])),'reason':'unselected symlink in tree'});continue
  if p.is_file():add(row['root'],str(p.relative_to(roots[row['root']])),row['category'])
for row in cfg.get('source_locks',[]):
 lock=json.loads((roots[row['root']]/row['lock']).read_text())
 for relative,want in lock['sources'][row['role']].items():add(row['root'],str(pathlib.PurePosixPath(row['source_root'])/relative),row['category'],want)

rows=[];unique={};bycategory={}
for name,x in selected.items():
 p=pathlib.Path(name)
 try:
  before=p.stat();h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  after=p.stat()
  if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):raise ValueError('changed during measurement')
  actual=h.hexdigest()
  if x['expected_sha256'] is not None and actual!=x['expected_sha256']:raise ValueError('expected SHA conflict')
  result=dict(x,bytes=after.st_size,sha256=actual);rows.append(result)
  unique[(after.st_dev,after.st_ino)]={'logical_bytes':after.st_size,'allocated_bytes':after.st_blocks*512}
  for category in x['categories']:bycategory[category]=bycategory.get(category,0)+after.st_size
 except (OSError,ValueError) as e:issues.append({'root':x['root'],'relative_path':x['relative_path'],'reason':str(e)})
logical=sum(x['bytes'] for x in rows);cap=7*1024**3
print(json.dumps({'schema':'hs.production-bridge.measured-retained-selection.v1','selection_id':cfg['selection_id'],'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'MEASURED_SELECTION_UNDER_CAP_NOT_ADMISSION' if not issues and logical<=cap else 'BLOCKED_SELECTION','cap_bytes':cap,'selected_path_count':len(rows),'selected_path_logical_bytes':logical,'unique_resolved_inode_count':len(unique),'unique_resolved_inode_logical_bytes':sum(x['logical_bytes'] for x in unique.values()),'unique_resolved_inode_allocated_bytes':sum(x['allocated_bytes'] for x in unique.values()),'by_category_logical_bytes':bycategory,'issues':issues,'files':rows,'exclusions':cfg['exclusions'],'pending_replacements':cfg.get('pending_replacements',[]),'scope':'EXPLICIT_FILE_SELECTION_ONLY_NOT_ALL_HISTORY_OR_LOADED_RUNTIME','native_actions':0,'model_creations':0,'execution_authorized':False},indent=2))
