"""Paid-query decision replay; hidden arrays reside only in the evaluator."""
from copy import deepcopy
from audit import DOC,load,save,action_metrics

class QueryAPI:
    def __init__(self,context):
        self.__context=deepcopy(context)
        self.ledger=[];self.cache={};self.reference_acquired=False;self.baseline_acquired=False
    def request(self,handle,purpose):
        if handle in self.cache:return deepcopy(self.cache[handle])
        # Append charge before looking at a retained outcome, even for UNKNOWN.
        count=len(self.__context['tasks'])*3
        self.ledger.append({'handle':handle,'purpose':purpose,'historical_record_equivalents_requested':count,'charge_before_reveal':True})
        if handle not in ('R','N0') and not(self.reference_acquired and self.baseline_acquired):
            raise ValueError('unpaid initial observations')
        if handle=='R':self.reference_acquired=True
        if handle=='N0':
            if not self.reference_acquired:raise ValueError('reference not acquired')
            self.baseline_acquired=True
        # Reference acquisition must not leak baseline-derived transition labels
        # before the baseline observation is acquired and charged.
        reply=({'status':'PASS','tasks':len(self.__context['tasks']),
                'observations':count,'missing_observations':0,'reference_by_definition':True}
               if handle=='R' else action_metrics(self.__context,handle))
        self.ledger[-1]['available_records']=0 if reply['status']=='UNKNOWN' else count
        self.ledger[-1]['unknown_cells']=reply.get('missing_observations',0)
        self.cache[handle]=reply
        return deepcopy(reply)

def initial(request):
    request('R','common_fixed_reference');request('N0','common_baseline')

def enumerate_actions(actions,request):
    unknown=False
    for a in actions:
        reply=request(a['handle'],'actual_action_and_final_verification')
        if reply['status']=='PASS':return {'decision':'SELECT','action':a['handle']}
        unknown |= reply['status']=='UNKNOWN'
    return {'decision':'ABSTAIN_UNKNOWN' if unknown else 'ABSTAIN','action':None}

def proxy_screen(actions,request):
    unknown=False;screened=[]
    for a in actions:
        if a['proxy'] is not None:
            reply=request(a['proxy'],'paid_proxy_probe')
            if reply['status']!='PASS':
                unknown |= reply['status']=='UNKNOWN';screened.append(a['handle']);continue
        reply=request(a['handle'],'actual_action_and_final_verification')
        if reply['status']=='PASS':return {'decision':'SELECT','action':a['handle'],'screened_unqueried':screened}
        unknown |= reply['status']=='UNKNOWN'
    return {'decision':'ABSTAIN_UNKNOWN' if unknown else 'ABSTAIN','action':None,'screened_unqueried':screened}

def run(context,actions,mode):
    api=QueryAPI(context);initial(api.request)
    if mode=='P2':decision=proxy_screen(actions,api.request)
    elif mode=='enumeration':decision=enumerate_actions(actions,api.request)
    else:
        handle={'reference_fallback':'R','no_change':'N0','ordinary_U2':'U2'}[mode]
        reply=api.request(handle,'baseline_action_and_final_verification')
        decision={'decision':'SELECT' if reply['status']=='PASS' else 'UNKNOWN' if reply['status']=='UNKNOWN' else 'FAILED_GATE','action':handle}
    queries=api.ledger[2:]
    return {'mode':mode,**decision,'common_observation_requested_records':sum(x['historical_record_equivalents_requested'] for x in api.ledger[:2]),
            'additional_requested_records':sum(x['historical_record_equivalents_requested'] for x in queries),
            'additional_available_records':sum(x['available_records'] for x in queries),'unknown_requested_records':sum(x['unknown_cells'] for x in api.ledger),
            'ledger':api.ledger,'note':'Historical array-record equivalents, not new inference or qualified latency; H1 requires two worker processes.'}

def main():
    contexts=load(DOC/'inputs/OUTCOMES.json');catalog=load(DOC/'ACTION_CATALOG.json');rows=[]
    for ctx,entry in zip(contexts,catalog):
        assert ctx['name']==entry['context']
        actions=entry['actions']
        for mode in ('reference_fallback','no_change','ordinary_U2','P2'):
            rows.append({'context':ctx['name'],**run(ctx,actions,mode)})
        orders=[actions] if len(actions)==1 else [actions,list(reversed(actions))]
        for order in orders:
            rows.append({'context':ctx['name'],'order':[a['handle'] for a in order],**run(ctx,order,'enumeration')})
    save(DOC/'REPLAY_RESULTS.json',{'policy_version':1,'policy_revisions':0,'rows':rows,'no_held_out_validation':True,'new_inference_runs':0})
    print('PASS charged CPU replay:',len(rows),'context/comparator rows')

if __name__=='__main__':main()
