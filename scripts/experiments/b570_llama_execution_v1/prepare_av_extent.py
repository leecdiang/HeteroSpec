"""Bind certified native AV operands to own-path and physical-extent interventions."""
from pathlib import Path
import argparse,copy,sys,struct
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha,TARGET

def prepare(probe,certificate,model,out):
    probe=Path(probe);out=Path(out);need(not out.exists(),'fresh plan');out.mkdir(parents=True)
    proof=read(certificate);control=read(probe/'CONTROL.json')
    need(proof['status']=='NATIVE_PROBE_CONTROLS_PASS' and any(x['probe_record_sha256']==sha(probe.parent.with_suffix('.json')) for x in proof['results']),'certified capture')
    def node(side,name,base):
        found=[p for p in (probe/side/'trace').glob('*.json') if read(p)['name']==name and read(p)['caller_base']==base]
        need(len(found)==1,'unique actual node');p=found[0];return p,read(p)
    def operand(n,key):
        i=n['raw_operands'][key];m=read(i['meta']);need(m['source_output_disjoint'],'no alias capture');return m,Path(i['payload']).read_bytes(),i
    base=control['base'];q4p,q4=node('q4','hs_qb_av-0',base);v4,bv4,iv4=operand(q4,'src0');p4,bp4,ip4=operand(q4,'src1')
    q4out=q4p.with_suffix('.bin').read_bytes();fixtures=[];checks=[]
    def fixture(id,V,P,Y):
        f={'id':id};h={}
        for key,paths in [('V',V),('P',P),('output',Y)]:
            for suffix,path in zip(('meta','payload'),paths):
                name=key+'_'+suffix;f[name]=str(Path(path).resolve());h[name]=sha(path)
        f['hashes']=h;fixtures.append(f)
    def saved(id,m,b):
        p=out/(id+'.json');write(p,m);p.with_suffix('.bin').write_bytes(b);return p,p.with_suffix('.bin')
    fixture('own-q4',(iv4['meta'],iv4['payload']),(ip4['meta'],ip4['payload']),(q4p,q4p.with_suffix('.bin')))
    for row in range(4):
        q1p,q1=node('q1','kqv-0',base+row);v1,bv1,iv1=operand(q1,'src0');p1,bp1,ip1=operand(q1,'src1');n=v1['ne'][0];big=v4['ne'][0];visible=base+row+1
        need(n<=big and p1['ne']==[n,1,32,1] and p4['ne']==[big,1,32,4],'actual extent geometry')
        # Causally visible values and probabilities must agree before intervening.
        for head in range(8):
            for dim in range(128):
                a=head*v1['nb'][2]+dim*v1['nb'][1];b=head*v4['nb'][2]+dim*v4['nb'][1]
                need(bv1[a:a+visible*2]==bv4[b:b+visible*2],'visible V differs')
        q1k,_=node('q1','kq-0',base+row);q4k,_=node('q4','hs_qb_qk-0',base)
        a=q1k.with_suffix('.bin').read_bytes();b=q4k.with_suffix('.bin').read_bytes()
        for head in range(32):
            x=head*n*4;y=(row*32+head)*big*4
            need(a[x:x+visible*4]==b[y:y+visible*4],'visible QK differs')
            need(bp1[x:x+n*4]==bp4[y:y+n*4],'probability prefix differs')
            need(all(v==0 for v in struct.unpack('<'+'f'*(big-visible),bp4[y+visible*4:y+big*4])),'masked probabilities nonzero')
        fixture('own-q1-row'+str(row),(iv1['meta'],iv1['payload']),(ip1['meta'],ip1['payload']),(q1p,q1p.with_suffix('.bin')))
        checks.append({'row':row,'q1_keys':n,'q4_keys':big,'visible':visible,'visible_V_QK_and_probability_prefix_equal':True,'masked_probabilities_zero':True,'AV_equal':q1p.with_suffix('.bin').read_bytes()==q4out[row*16384:(row+1)*16384]})
        if n==big:continue
        # Crop physical reduction length only; preserve V strides and real query/head probabilities.
        cropped=copy.deepcopy(v4);cropped['ne'][0]=n;span=2+sum((d-1)*s for d,s in zip(cropped['ne'],cropped['nb']));cropped['span_bytes']=span
        vp=saved('crop-V-row'+str(row),cropped,bv4[:span]);pp=saved('crop-P-row'+str(row),p1,b''.join(bp4[(row*32+h)*big*4:((row*32+h)*big+n)*4] for h in range(32)))
        fixture('crop-row'+str(row),vp,pp,(q1p,q1p.with_suffix('.bin')))
        padded=copy.deepcopy(p1);padded['ne'][0]=big;padded['nb']=[4,big*4,big*4,big*32*4];padded['span_bytes']=big*32*4
        pp=saved('pad-P-row'+str(row),padded,b''.join(bp1[h*n*4:(h+1)*n*4]+bytes((big-n)*4) for h in range(32)))
        yp=saved('q4-row'+str(row),q1,q4out[row*16384:(row+1)*16384])
        fixture('pad-row'+str(row),(iv4['meta'],iv4['payload']),pp,yp)
    write(out/'PREFIX_COMPARISON.json',{'control':control,'rows':checks,'scope':'visible V, QK and complete probability prefix; masked probabilities numerically zero; no claim about masked V slots'})
    write(out/'CONFIG.json',{'target_model':str(Path(model).resolve()),'target_sha256':TARGET,'certificate_path':str(Path(certificate).resolve()),'certificate_sha256':sha(certificate),'expected_status':'AV_EXTENT_INTERVENTION_PASS','expected_rows':len(fixtures),'operator_calls':len(fixtures),'fixtures':fixtures,'scope':'native q1/q4 own paths, then fixed visible operands and zero masked probabilities with physical reduction extent exchanged'})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('probe','certificate','model','out'):p.add_argument('--'+k,required=True)
    a=p.parse_args();prepare(a.probe,a.certificate,a.model,a.out)
