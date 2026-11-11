"""One identity model for normal observation and failure cleanup."""
def key(pid,ident):
    value=ident['created_filetime']
    if type(pid) is not int or pid<=0 or not isinstance(value,str) or not value.isdigit() or int(value)<=0:
        raise ValueError('INVALID_PROCESS_IDENTITY')
    return pid,value

class Registry:
    def __init__(self,api,journal):
        self.api=api;self.journal=journal
        self.observed={};self.closed={};self.live={};self.handles={}
        self.orphans={};self.coverage_errors=[];self.root_key=None
    def create(self,pid,process_handle,image_handle=None):
        h=None
        try:
            self.journal.emit('PROCESS_CREATE_RECEIVED',pid=pid)
            h=self.api.retain(process_handle)
            orphan_id=id(h)
            self.orphans[orphan_id]=dict(handle=h,pid=pid,identity=None)
            ident=self.api.identity(h);identity_key=key(pid,ident)
            self.orphans[orphan_id]['identity']=ident
            # Preserve the triggering identity and current mapping BEFORE admission.
            self.journal.emit('PROCESS_CREATE_OBSERVED',pid=pid,**ident,
                              active_identity=list(self.live[pid]) if pid in self.live else None,
                              historical_identities=[list(k) for k in self.observed if k[0]==pid])
            if pid in self.live:raise ValueError('DUPLICATE_ACTIVE_PID')
            if identity_key in self.observed:raise ValueError('DUPLICATE_PROCESS_IDENTITY')
            self.journal.emit('PROCESS_CREATE',pid=pid,role='root' if identity_key==self.root_key else 'descendant',**ident)
            self.observed[identity_key]=ident;self.handles[identity_key]=h;self.live[pid]=identity_key
            del self.orphans[orphan_id]
            return identity_key
        except BaseException as e:
            self.coverage_errors.append(dict(event='create',pid=pid,error=repr(e)))
            raise
        finally:
            if image_handle:self.api.checked(self.api.close(image_handle),'debug image close')
    def exit_observed(self,pid,code):
        identity_key=self.live.get(pid)
        self.journal.emit('EXIT_OBSERVED',pid=pid,exit_code=code,
                          created_filetime=identity_key[1] if identity_key else None)
        if identity_key is None:
            self.coverage_errors.append(dict(event='exit',pid=pid,error='UNMATCHED_EXIT'))
            raise ValueError('UNMATCHED_EXIT')
        return identity_key
    def complete_exit(self,identity_key,code):
        h=self.handles[identity_key]
        if self.api.wait_handle(h,5000)!=0:raise ValueError('EXIT_SIGNAL_MISSING')
        times=self.api.os_times(h)
        if key(identity_key[0],times)!=identity_key or int(times['exit_filetime'])<=int(times['created_filetime']):
            raise ValueError('EXIT_IDENTITY_MISMATCH')
        actual_code=self.api.exit_code(h)
        if code is not None and actual_code!=code:raise ValueError('EXIT_CODE_MISMATCH')
        row=dict(pid=identity_key[0],exit_code=actual_code,
                 lifetime_seconds=(int(times['exit_filetime'])-int(times['created_filetime']))/1e7,**times)
        if identity_key not in self.closed:
            self.journal.emit('PROCESS_CLOSED',**row);self.closed[identity_key]=row
        if self.live.get(identity_key[0])==identity_key:del self.live[identity_key[0]]
        self.api.checked(self.api.close(h),'retained process close')
        del self.handles[identity_key]
        self.journal.emit('HANDLE_CLOSED',pid=identity_key[0],created_filetime=identity_key[1],handle_kind='retained_process')
    def finish_signalled(self):
        for identity_key,h in list(self.handles.items()):
            if self.api.wait_handle(h,0)==0:self.complete_exit(identity_key,None)
        for orphan_id,record in list(self.orphans.items()):
            h=record['handle']
            if self.api.wait_handle(h,0)==0:
                times=self.api.os_times(h)
                self.journal.emit('REJECTED_PROCESS_OS_EXIT',pid=record['pid'],**times)
                self.api.checked(self.api.close(h),'rejected retained close');del self.orphans[orphan_id]
    def complete(self):
        return (not self.live and not self.handles and not self.orphans and
                not self.coverage_errors and set(self.observed)==set(self.closed))
    def unresolved(self):
        return [dict(pid=k[0],created_filetime=k[1]) for k in self.handles]+[dict(pid=r['pid'],identity=r['identity']) for r in self.orphans.values()]
    def release_remaining(self):
        # OS handle disposal at observer exit is not evidence of process exit.
        for h in list(self.handles.values())+[r['handle'] for r in self.orphans.values()]:self.api.close(h)
