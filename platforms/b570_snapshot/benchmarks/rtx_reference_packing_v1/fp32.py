"""Integer significand/exponent F32 RN-even, never host-double accumulation."""
def decode(b):
    if type(b)is not int or not 0<=b<2**32 or ((b>>23)&255)==255:
        raise ValueError('finite F32 bit pattern required')
    exp=(b>>23)&255;mant=b&0x7fffff
    return (-1 if b>>31 else 1)*(mant+(1<<23) if exp else mant), exp-150 if exp else -149

def nearest(n,shift):
    if shift<=0:return n<<-shift
    q,r=divmod(n,1<<shift);half=1<<(shift-1)
    return q+int(r>half or (r==half and q&1))

def encode(n,exp,negative_zero=False):
    sign=0x80000000 if n<0 or (n==0 and negative_zero) else 0;n=abs(n)
    if not n:return sign
    top=n.bit_length()-1+exp
    if top < -126:
        return sign|nearest(n,-149-exp)
    shift=n.bit_length()-24;mant=nearest(n,shift);top=exp+shift+23
    if mant==1<<24:mant>>=1;top+=1
    if top>127:raise OverflowError('F32 overflow outside admitted finite domain')
    return sign|((top+127)<<23)|(mant&0x7fffff)

def mul(a,b):
    x,ex=decode(a);y,ey=decode(b)
    return encode(x*y,ex+ey,bool((a^b)>>31))

def add(a,b):
    x,ex=decode(a);y,ey=decode(b);low=min(ex,ey)
    return encode((x<<(ex-low))+(y<<(ey-low)),low,a==b==0x80000000)
