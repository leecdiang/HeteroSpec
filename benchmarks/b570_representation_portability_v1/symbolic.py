"""Independent inverse-address oracle over actual exported graph descriptors."""

def ptr(t, coord):
    return t['view_offset']+sum(a*b for a,b in zip(coord,t['nb']))

def verify(row, layout):
    f=row['geometry'];q,k,h,hk=(f[n] for n in ('q','k','h','hk'))
    graph=row['layouts'][layout]['graph'];inputs=row['inputs'];storage=f['storage']
    # The expected buffer is labeled with integer coordinate tuples, never F16 labels.
    qlabels={4*(8+(j*h+head)*128+d if storage else (head*q+j)*128+d):(j,head,d)
             for j in range(q) for head in range(h) for d in range(128)}
    kl={(head*k+key)*256+2*d:(head,key,d) for head in range(hk) for key in range(k) for d in range(128)}
    vl={(head*128+d)*k*2+key*2:(head,d,key) for head in range(hk) for d in range(128) for key in range(k)}
    ml={(j*k+key)*4:(j,key) for j in range(32) for key in range(k)}
    softs=[i for i,t in enumerate(graph) if t['op']=='SOFT_MAX'];checks=0
    for z,index in enumerate(softs):
        score_i=max(i for i in range(index) if graph[i]['op']=='MUL_MAT')
        score=graph[score_i]
        qi=next(t for t in reversed(graph[:score_i]) if t['op']=='VIEW' and t['ne'][0]==128 and t['ne'][2]==h)
        mi=inputs['mask'] if layout==0 or q==1 else next(t for t in reversed(graph[:index]) if t['op']=='VIEW' and t['ne'][2]==1)
        av=next(t for t in graph[index+1:] if t['op']=='MUL_MAT')
        perm=next(t for t in graph[index+1:] if t['op']=='PERMUTE')
        for j in range(q):
            if layout==1 and q==2 and z!=j:continue
            col=j if layout==0 or q==1 else 0;batch=j if layout==2 and q==2 else 0
            for head in range(h):
                actual_head=head//(score['ne'][2]//hk)
                if row.get('mutant_gqa_rule')=='modulo':actual_head=head%hk
                if actual_head!=head//(h//hk):return dict(kind='GQA',coord=[j,head],actual=actual_head,expected=head//(h//hk))
                for d in range(128):
                    address=ptr(qi,[d,col,head,batch]);checks+=1
                    if qlabels.get(address)!=(j,head,d):return dict(kind='query_address',coord=[j,head,d],address=address,label=qlabels.get(address))
                    # Output cont traverses logical permuted elements in dim0-first order.
                    c=[d,head,col,batch];actual=ptr(perm,c)
                    expected=4*(d+128*(col+av['ne'][1]*(head+av['ne'][2]*batch)))
                    checks+=1
                    if actual!=expected:return dict(kind='output_recombine',coord=[j,head,d],actual=actual,expected=expected)
                for key in range(k):
                    addr=ptr(mi,[key,col,head%mi['ne'][2],batch%mi['ne'][3]]);checks+=1
                    if ml.get(addr)!=(j,key):return dict(kind='mask_column',coord=[j,head,key],address=addr,label=ml.get(addr))
                    for d in range(128):
                        a=ptr(inputs['k'],[d,key,actual_head,0]);b=ptr(inputs['v'],[key,d,actual_head,0]);checks+=2
                        if kl.get(a)!=(head//(h//hk),key,d) or vl.get(b)!=(head//(h//hk),d,key):return dict(kind='KV',coord=[j,head,key,d])
    return dict(status='EXACT_ADDRESS_MATCH',checks=checks)
