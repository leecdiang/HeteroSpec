from host import *
def main():
    s=(HERE/'final_calibration07.py').read_text().replace('provisional-cohort.json','common-cohort.json').replace('cal-r-','common-r-').replace('cal-q07-','common-q-').replace('calibration-qualification07.json','COMMON_CALIBRATION_QUALIFICATION.json').replace('cal-cost07-','common-cost-')
    pos=s.index("if __name__=='__main__':")
    s=s[:pos]+'''def references():
    cohort=read(ROOT/'common-cohort.json')
    for link,r in zip(cohort['reference_reuse'],cohort['calibration']):
        i=link['index'];out=ROOT/f'common-r-{i:02}'
        if link['previous_index'] is not None:
            old=Path(link['original_reference']);inputs=read(old/'input.json')['units']
            assert all(u['tokens']==r['request_ids'] and u['head']==study.lcp(r['cached_ids'],r['request_ids']) for u in inputs)
            out.mkdir()
            for role in ('r0','r1'):
                previous='r'+str(int(role[-1]))
                shutil.copytree(old/previous,out/role,copy_function=os.link)
            put(out/'REUSED_ORIGINAL_REFERENCE.json',dict(source=str(old),reference_native=read(old/'launch.json')['exe'],reason='exact same input tokens, head, capacity, output flags and immutable scalar original; no new R replaces old R'))
        else:
            run(f'common-r-{i:02}','oracle02',dict(mode='requests',capacity=4096,units=[dict(id=f'r{k}',tokens=r['request_ids'],head=study.lcp(r['cached_ids'],r['request_ids']),arm='R',cap=128,capture=True) for k in range(2)]),requests=2)
''' +s[pos:]
    (HERE/'common_calibration.py').write_text(s)
if __name__=='__main__':main()
