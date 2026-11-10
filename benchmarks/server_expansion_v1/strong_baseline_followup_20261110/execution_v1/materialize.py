"""Frozen job constructors and real-input assembly; no GPU APIs."""
import hashlib
import os
from pathlib import Path
from check_numeric import f32
from prepare import TARGET_SHA,expected_runtime
from support import fresh,need,read,safe_relative,sha


def model_job(manifest,worker,model_path):
    j=dict(family='Qwen32B',target_model=str(model_path),target_sha256=TARGET_SHA,n_ctx=1024,threads=2,
           draft=False,residency='target_only')
    reference=worker['kind'].startswith('pristine-model-')
    if not reference:
        j.update(arm=worker['arm'],n_ubatch=32,output_reserve=32,kv='F16',flash_attention=False,
                 cuda_graphs=False,lowering='WHOLE',draft_width=1,profile=False,k=0,
                 target_output_reserve=32,proposal_mode='live',capability_request=expected_runtime(worker['arm']))
    if worker['kind'].endswith('geometry'):
        case={key:manifest['geometry_case'][key]for key in ('name','forced','observe_positions','state_positions')}
        j['cases']=[case]+manifest['extra_geometry_cases']
        if not reference:
            j['capacity_overflow_probe']=True;j['capture_operands']=worker.get('capture_operands',False)
            if j['capture_operands']:j['operand_capture_classes']=manifest['classes']
    else:
        j['inputs']=[]
        for service in manifest['services']:
            source=service['input'];n=len(source['prompt_ids']);positions=list(range(n,n+source['cap']))
            for role in (('heavy',)if reference else('heavy','clean')):
                entry=dict(name=service['id']if reference else service['id']+'-'+role,input=source,capture=role=='heavy')
                if reference:entry['state_positions']=positions
                j['inputs'].append(entry)
    return j


def slice_sha(path,offset,length):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        f.seek(offset);left=length
        while left:
            b=f.read(min(left,8*1024*1024));need(b,'Truncated GGUF tensor');h.update(b);left-=len(b)
    return h.hexdigest()


def assemble_inputs(manifest,inventory,G_native,model_path,output):
    output=Path(output);output.mkdir();source=Path(G_native)/'operands'
    tensors={x['name']:x for x in inventory['tensors']};entries={}
    for c in manifest['classes']:
        folder=output/c['class_id'];folder.mkdir();name=c['weight_name'];records=[]
        for col in range(32):
            record=read(source/(name+'-col-'+str(col)+'.json'))
            need(record['column']==col and record['capture_width']==32 and record['shape_class']==c,'Real operand class/column order')
            for field,size in (('activation',c['K']*4),('output',c['M']*4)):
                spec=record[field];path=source/safe_relative(spec['file'])
                need(path.stat().st_size==spec['bytes']==size and sha(path)==spec['sha256'],'Captured complete operand bytes')
                f32(path,1,c['K']if field=='activation'else c['M'])
            records.append(record)
        weight=records[0]['weight'];weight_file=source/safe_relative(weight['file'])
        expected_size=c['K']*c['M']//256*(144 if c['type']=='Q4_K' else 210)
        need(weight_file.stat().st_size==weight['bytes']==expected_size and sha(weight_file)==weight['sha256'],
             'Complete captured blocked weights')
        need(slice_sha(model_path,tensors[name]['file_offset'],expected_size)==weight['sha256'],'GPU weight bytes differ from fixed GGUF')
        os.link(weight_file,folder/'weight.bin');columns=[]
        for col,record in enumerate(records):
            path=folder/('column-'+str(col)+'.f32');os.link(source/record['activation']['file'],path)
            columns.append(dict(path=str(path),sha256=sha(path),actual_G_scalar_output=str(source/record['output']['file'])))
        q4_columns=[]
        for col in range(4):
            record=read(source/'q4'/(name+'-col-'+str(col)+'.json'))
            need(record['column']==col and record['capture_width']==4 and record['shape_class']==c,'Actual native q4 capture')
            for field,n in (('activation',c['K']),('output',c['M'])):
                p=source/'q4'/safe_relative(record[field]['file']);f32(p,1,n)
                need(sha(p)==record[field]['sha256'],'Actual q4 payload hash')
            if col==0:
                need(record['weight']['sha256']==weight['sha256'] and
                     sha(source/'q4'/safe_relative(record['weight']['file']))==weight['sha256'],'q4/q32 weight identity')
            path=folder/('q4-column-'+str(col)+'.f32');os.link(source/'q4'/record['activation']['file'],path)
            q4_columns.append(dict(path=str(path),sha256=sha(path),actual_G_scalar_output=str(source/'q4'/record['output']['file'])))
        batches={}
        for q in manifest['widths']:
            path=folder/('q'+str(q)+'.f32')
            with path.open('xb')as f:
                for col in (q4_columns if q==4 else columns[:q]):f.write(Path(col['path']).read_bytes())
            need(path.stat().st_size==q*c['K']*4,'Complete real-column prefix matrix')
            batches[str(q)]=dict(path=str(path),sha256=sha(path),q=q)
        entries[c['class_id']]=dict(shape_class=c,weight=dict(path=str(folder/'weight.bin'),sha256=weight['sha256']),
                                    columns=columns,q4_columns=q4_columns,batches=batches,
                                    provenance='Separate actual native q4/q32 initial exposed-root prefixes; other qualification widths are real q32-column prefix slices')
    fresh(output/'INPUT_BINDINGS.private.json',entries);return entries


def gold_job(worker,inputs):
    entry=inputs[worker['class_id']];c=entry['shape_class']
    def column(op):return entry['q4_columns'if op['source_width']==4 else'columns'][op['column']]
    return dict(role='pristine_scalar_gold',q=1,operand=dict(K=c['K'],M=c['M'],type=c['type'],
                weight_file=entry['weight']['path'],weight_sha256=entry['weight']['sha256']),
                operations=[dict(operation_id=op['operation_id'],activation_file=column(op)['path'],
                     activation_sha256=column(op)['sha256'])for op in worker['operations']])


def projection_job(worker,inputs,manifest,phase):
    class_id=worker.get('class_id',manifest['S2_cells'][0]['class_id']);entry=inputs[class_id];c=entry['shape_class']
    q=worker.get('q',4);batch=entry['batches'][str(q)]
    operand=dict(K=c['K'],M=c['M'],q=q,type=c['type'],weight_file=entry['weight']['path'],
                 weight_sha256=entry['weight']['sha256'],activation_file=batch['path'],activation_sha256=batch['sha256'])
    identity={key:operand[key]for key in ('K','M','q','type','weight_sha256','activation_sha256')}
    input_sha=hashlib.sha256(__import__('json').dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    config_sha=hashlib.sha256(__import__('json').dumps(dict(arm=worker['arm'],identity=identity,n_ctx=1024,n_ubatch=32,
                  output_reserve=32,kv='F16',flash_attention=False,cuda_graphs=False),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    ops=[dict(operation_id=op['operation_id'],worker_id=worker['worker_id'],ordinal=i,
              role=op['kind'],slot=worker.get('cell',-1),block=worker.get('block',-1),
              input_sha256=input_sha,config_sha256=config_sha,requested_output_rows=q,all_outputs_owned=True,
              phase=phase)for i,op in enumerate(worker['operations'])]
    job=dict(arm=worker['arm'],n_ctx=1024,n_ubatch=32,output_reserve=32,kv='F16',flash_attention=False,
             cuda_graphs=False,capture_quantization=worker.get('capture_quantization',False),operand=operand,operations=ops)
    expected_error=None
    if worker['kind']=='expected-native-negative':
        change=worker['negative']
        if change=='empty-K':operand['K']=0;expected_error='Descriptor dimensions'
        elif change=='q0':operand['q']=0;expected_error='Descriptor dimensions'
        elif change=='q33':operand['q']=33;expected_error='Descriptor dimensions'
        elif change=='wrong-type':operand['type']='F32';expected_error='Block type'
        elif change=='wrong-stride':operand['nb']=[4,1,1,1];expected_error='Unsupported operand descriptor field; no ignored stride/mask'
        elif change=='partial-output-mask':ops[0]['requested_output_rows']=q-1;expected_error='All original output rows required'
        elif change=='empty-operations':job['operations']=[];expected_error='Registered one/two operations'
        else:raise ValueError('Unregistered negative branch')
    return job,expected_error
