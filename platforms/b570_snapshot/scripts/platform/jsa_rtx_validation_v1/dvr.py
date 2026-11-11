from common import *
class DVRServer(Server):
    def __init__(self,d,model_pair,warm,fixtures=False):
        c={'name':'E32','mask':0,'spec':False,'ub':32,'k':0};exe=LOCAL/'native/build/bin/jsa-dvr-server.exe'
        super().__init__(d,c,False,model_pair,exe,warm)
        self.command=[str(exe),model_pair['target']['path'],str(exe.parent),str(self.port)]+(['fixtures'] if fixtures else [])
        if fixtures:os.environ['JSA_E_STATE_DIR']=str(self.d.parent/'state-proof')
