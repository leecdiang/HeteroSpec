"""CPU diagnostic ULP wrapper; admission remains the frozen exact-byte rule."""
import argparse,struct
import audit_rtx

def error_metrics(actual,expected):
    assert len(actual)==len(expected) and len(actual)%4==0
    aa=struct.unpack('<'+'f'*(len(actual)//4),actual);bb=struct.unpack('<'+'f'*(len(expected)//4),expected)
    def ordered(word):
        x=struct.unpack('<I',word)[0]
        return 0x80000000-(x&0x7fffffff) if x&0x80000000 else 0x80000000+x
    wrong=[i for i in range(len(aa)) if actual[4*i:4*i+4]!=expected[4*i:4*i+4]]
    return dict(words=len(aa),different_words=len(wrong),max_abs=max((abs(x-y) for x,y in zip(aa,bb)),default=0),max_ULP=max((abs(ordered(actual[4*i:4*i+4])-ordered(expected[4*i:4*i+4])) for i in wrong),default=0),first_word=wrong[0] if wrong else None)

def main(out):
    # Explicit correction of the diagnostic sign ordering only. No admission,
    # tolerance, bitwise decision, timing, exclusion or statistical change.
    audit_rtx.mismatch=error_metrics;audit_rtx.main(out)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',required=True);z=a.parse_args();main(z.out)
