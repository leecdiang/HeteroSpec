"""A new debugged identity gets one first-chance loader breakpoint."""
CONTINUE=0x00010002
NOT_HANDLED=0x80010001
BREAKPOINT=0x80000003
class ExceptionPolicy:
    def __init__(self):self.pending=set()
    def created(self,identity):self.pending.add(identity)
    def decide(self,identity,code,first_chance):
        if identity is not None and identity in self.pending and code==BREAKPOINT and first_chance==1:
            self.pending.remove(identity);return CONTINUE
        return NOT_HANDLED
