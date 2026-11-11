"""Causal finite-episode policy model and a fail-closed runtime interface.

Nontrivial decisions currently require explicitly synthetic model prices.
PR221's measured macros are never interpreted as resident stage prices.
"""
from __future__ import annotations
from dataclasses import dataclass,fields
import math
from time import perf_counter_ns


class PolicyError(ValueError):pass


def need(ok,message):
    if not ok:raise PolicyError(message)


@dataclass(frozen=True)
class Snapshot:
    deployment_key:str
    state_key:str
    candidate_tokens:tuple[int,...]
    verified_rows:int
    draft_materialized_rows:int
    remaining_cap:int
    known_eog_ids:tuple[int,...]=()
    terminal_kind:str='none'  # none, accepted, correction, bonus
    decoding:str='greedy'
    sunk_draft_nanoseconds:float=0
    target_materialized_rows:int|None=None

    def __post_init__(self):
        k=len(self.candidate_tokens)
        need(self.decoding=='greedy','GREEDY_ONLY')
        need(1<=k<=7 and all(type(t)==int and t>=0 for t in self.candidate_tokens),'CANDIDATE_SCOPE')
        need(type(self.verified_rows)==int and 0<=self.verified_rows<=k+1,'FRONTIER_SCOPE')
        need(type(self.draft_materialized_rows)==int and 0<=self.draft_materialized_rows<=k+1,'DRAFT_FRONTIER_SCOPE')
        need(type(self.remaining_cap)==int and self.remaining_cap>=0,'CAP_MUST_BE_KNOWN_CONFIGURATION')
        need(self.terminal_kind in ('none','accepted','correction','bonus'),'TERMINAL_KIND')
        if self.target_materialized_rows is None:object.__setattr__(self,'target_materialized_rows',self.verified_rows)
        need(type(self.target_materialized_rows)==int and self.verified_rows<=self.target_materialized_rows<=k+1,'TARGET_PHYSICAL_FRONTIER')
        if self.terminal_kind=='none':need(self.target_materialized_rows==self.verified_rows,'NONTERMINAL_MATCHING_FRONTIER_REQUIRED')
        need(math.isfinite(self.sunk_draft_nanoseconds) and self.sunk_draft_nanoseconds>=0,'SUNK_COST')
        need(bool(self.deployment_key) and bool(self.state_key),'STATE_BINDING_REQUIRED')

    @classmethod
    def from_mapping(cls,value):
        unknown=set(value)-{f.name for f in fields(cls)}
        need(not unknown,'FUTURE_OR_UNKNOWN_FIELDS: '+','.join(sorted(unknown)))
        value=dict(value)
        for key in ('candidate_tokens','known_eog_ids'):
            if key in value:value[key]=tuple(value[key])
        return cls(**value)


class PastAcceptance:
    """Conditional-position Beta counts; only completed announced actions update."""
    def __init__(self):
        self.success=[0]*7;self.failure=[0]*7;self.pending=None;self.completed=set()

    def probabilities(self,k):
        need(1<=k<=7,'PREDICTOR_SCOPE')
        return tuple((1+self.success[i])/(2+self.success[i]+self.failure[i]) for i in range(k))

    def announce(self,event_id,verified_rows,width,draft_count):
        need(self.pending is None and event_id not in self.completed,'ACTION_ORDER')
        need(1<=draft_count<=7 and 0<=verified_rows<=draft_count and 1<=width<=draft_count+1-verified_rows,'ANNOUNCED_ACTION_SCOPE')
        self.pending=(event_id,verified_rows,width,draft_count)

    def observe(self,event_id,matches,terminal_after=None):
        need(self.pending is not None and self.pending[0]==event_id,'OBSERVATION_BEFORE_ACTION_OR_WRONG_ID')
        _,start,width,k=self.pending;count=min(width,k-start)
        need(len(matches)==count and all(type(x)==bool for x in matches),'OBSERVED_MATCH_SHAPE')
        need(terminal_after is None or (type(terminal_after)==int and 1<=terminal_after<=width),'OBSERVED_TERMINAL_SCOPE')
        learned=[]
        for offset,match in enumerate(matches):
            if terminal_after is not None and offset>=terminal_after:break
            position=start+offset
            if match:self.success[position]+=1
            else:self.failure[position]+=1
            learned.append((position+1,match))
            if not match:break  # all later comparisons concern an uncommitted suffix
        self.completed.add(event_id);self.pending=None
        return tuple(learned)


@dataclass(frozen=True)
class Price:
    nanoseconds:float
    target_materializations:int
    draft_materializations:int
    postcondition:str

    def __post_init__(self):
        need(math.isfinite(self.nanoseconds) and self.nanoseconds>=0,'PRICE_UNIT_OR_VALUE')
        need(type(self.target_materializations)==int and self.target_materializations>=0 and type(self.draft_materializations)==int and self.draft_materializations>=0,'MATERIALIZATION_COUNTS')
        need(bool(self.postcondition),'POSTCONDITION_REQUIRED')


@dataclass(frozen=True)
class SyntheticStage:
    at:int
    width:int
    prices:dict[str,Price]


@dataclass(frozen=True)
class SyntheticModel:
    """Constructed prices only. This type cannot authorize a model/GPU action."""
    deployment_key:str
    initial_state_key:str
    token_value_nanoseconds:float
    policy_overhead_nanoseconds:float
    stages:tuple[SyntheticStage,...]
    stop_prices:dict[tuple[int,str],Price]
    origin:str='SYNTHETIC_NOT_MEASURED'

    def __post_init__(self):
        need(self.origin=='SYNTHETIC_NOT_MEASURED','NO_PRODUCTION_PRICE_BY_LABEL')
        need(math.isfinite(self.token_value_nanoseconds) and self.token_value_nanoseconds>0,'TOKEN_VALUE_UNIT')
        need(math.isfinite(self.policy_overhead_nanoseconds) and self.policy_overhead_nanoseconds>=0,'OVERHEAD_VALUE')
        need(len(self.stages)<=36 and len({(a.at,a.width) for a in self.stages})==len(self.stages),'FINITE_UNIQUE_ACTION_SET')


@dataclass(frozen=True)
class Outcome:
    label:str
    probability:float
    new_tokens:int
    next_frontier:int|None
    target_materializations:int
    draft_materializations:int


def outcomes(snapshot,at,width,probabilities):
    """Enumerate observable branches without reading any actual future match bit."""
    k=len(snapshot.candidate_tokens);end=at+width;cap_at=snapshot.verified_rows+snapshot.remaining_cap
    need(snapshot.verified_rows<=at<k+1 and 1<=width<=k+1-at,'STAGE_SCOPE')
    need(cap_at>at,'NO_TOKENS_BEFORE_KNOWN_CAP')
    branch=[];survival=1.0
    for offset in range(1,width+1):
        position=at+offset
        if position==k+1:
            branch.append(Outcome('bonus',survival,offset,None,0,max(0,k+1-snapshot.draft_materialized_rows)))
            break
        probability=probabilities[position-1]
        # A rejection emits a correction but retains only seed + accepted inputs.
        branch.append(Outcome(f'reject:{position}',survival*(1-probability),offset,None,0,max(0,position-snapshot.draft_materialized_rows)))
        survival*=probability
        terminal=position>=cap_at or snapshot.candidate_tokens[position-1] in snapshot.known_eog_ids
        if terminal:
            # Accepted p_position must be retained, even when this is the last
            # logit row and that token has not yet been a target input.
            keep=position+1
            branch.append(Outcome(f'accepted_terminal:{position}',survival,offset,None,max(0,keep-end),max(0,keep-snapshot.draft_materialized_rows)))
            break
        if offset==width:
            branch.append(Outcome('continue',survival,width,end,0,0))
    need(abs(sum(o.probability for o in branch)-1)<1e-10,'OUTCOME_PROBABILITY_SUM')
    return tuple(branch)


def adequate(price,outcome):
    return price.target_materializations>=outcome.target_materializations and price.draft_materializations>=outcome.draft_materializations


def solve_model(snapshot,model,probabilities):
    """Backward recursion in floating arithmetic; no request-optimality certificate."""
    need(model.deployment_key==snapshot.deployment_key and model.initial_state_key==snapshot.state_key,'MODEL_STATE_OR_DEPLOYMENT_MISMATCH')
    k=len(snapshot.candidate_tokens)
    need(len(probabilities)==k and all(math.isfinite(p) and 0<=p<=1 for p in probabilities),'CAUSAL_PROBABILITY_VECTOR')
    need(all(snapshot.verified_rows<=a.at<=k and 1<=a.width<=k+1-a.at for a in model.stages),'STAGE_SET_SCOPE')
    rejected=[];values={};choices={};legal_counts={}
    terminal=snapshot.terminal_kind!='none' or snapshot.remaining_cap==0
    if terminal:
        kind=snapshot.terminal_kind
        need(kind!='none','TERMINAL_ROLE_REQUIRED_FOR_CONVERGENCE')
        price=model.stop_prices.get((snapshot.verified_rows,kind))
        keep=snapshot.verified_rows+int(kind=='accepted')
        extra=max(0,keep-snapshot.target_materialized_rows)
        requirement=Outcome('known_terminal',1,0,None,extra,max(0,keep-snapshot.draft_materialized_rows))
        if price is None or not adequate(price,requirement):
            return {'action':None,'reason':'MISSING_TERMINAL_CONVERGENCE','model_value_nanoseconds':None,'rejected_actions':[]}
        return {'action':'RECONCILE_TERMINAL','reason':'KNOWN_TERMINAL_ONLY','model_value_nanoseconds':-price.nanoseconds-model.policy_overhead_nanoseconds,'rejected_actions':[]}
    cap_at=snapshot.verified_rows+snapshot.remaining_cap
    for at in range(k+1,snapshot.verified_rows-1,-1):
        options=[]
        stop=model.stop_prices.get((at,'none'))
        if at>0 and stop is not None:
            requirement=Outcome('stop',1,0,None,0,max(0,at-snapshot.draft_materialized_rows))
            if adequate(stop,requirement):options.append((-stop.nanoseconds,0,'STOP',None))
        if at<min(k+1,cap_at):
            for action in (a for a in model.stages if a.at==at):
                branches=outcomes(snapshot,at,action.width,probabilities)
                reason=None;value=0
                if set(action.prices)!={o.label for o in branches}:reason='MISSING_OR_EXTRA_OUTCOME_PRICE'
                else:
                    for outcome in branches:
                        price=action.prices[outcome.label]
                        if not adequate(price,outcome):reason='UNPRICED_REQUIRED_MATERIALIZATION';break
                        if outcome.next_frontier is not None and outcome.next_frontier not in values:
                            reason='NO_LEGAL_CONTINUATION_OR_STOP';break
                        future=0 if outcome.next_frontier is None else values[outcome.next_frontier]
                        value+=outcome.probability*(model.token_value_nanoseconds*outcome.new_tokens-price.nanoseconds+future)
                if reason:rejected.append({'at':at,'width':action.width,'reason':reason})
                else:options.append((value,action.width,'VERIFY_NEXT',action.width))
        legal_counts[at]=len(options)
        if options:
            best=max(options,key=lambda x:(x[0],-x[1]))  # deterministic shorter-action tie break
            values[at]=best[0]-model.policy_overhead_nanoseconds;choices[at]=(best[2],best[3])
    start=snapshot.verified_rows
    if start not in values:return {'action':None,'reason':'NO_LEGAL_ACTION','model_value_nanoseconds':None,'rejected_actions':rejected}
    action,width=choices[start]
    return {'action':action,'width':width,'reason':'FINITE_EPISODE_SURROGATE','model_value_nanoseconds':values[start],
            'rejected_actions':rejected,'model_future_choices':{str(k):{'action':v[0],'width':v[1]} for k,v in choices.items()},
            'legal_option_counts':legal_counts}


class CausalController:
    def __init__(self,overhead_limit_nanoseconds=1_000_000,clock=perf_counter_ns):
        need(type(overhead_limit_nanoseconds)==int and overhead_limit_nanoseconds>0,'OVERHEAD_LIMIT')
        self.history=PastAcceptance();self.clock=clock;self.limit=overhead_limit_nanoseconds;self.disabled=False;self.calls=0;self.total_nanoseconds=0

    def _finish(self,began,decision):
        elapsed=self.clock()-began;need(elapsed>=0,'NONMONOTONE_CONTROLLER_CLOCK')
        self.calls+=1;self.total_nanoseconds+=elapsed
        if elapsed>self.limit:self.disabled=True;decision.update(action=None,reason='CONTROLLER_OVERHEAD_LIMIT_EXCEEDED')
        decision.update(controller_span_nanoseconds=elapsed,controller_span_total_nanoseconds=self.total_nanoseconds,
                        controller_disabled=self.disabled,actuation_allowed=False,
                        span_scope='Decision body until final ledger starts; caller must time the complete call, feature construction and adapter for total overhead.')
        return decision

    def decide_runtime(self,snapshot,cost_artifact=None):
        began=self.clock()
        if self.disabled:reason='CONTROLLER_DISABLED_AFTER_OVERHEAD'
        elif isinstance(cost_artifact,SyntheticModel):reason='SYNTHETIC_PRICES_NOT_RUNTIME_EVIDENCE'
        elif cost_artifact is None:reason='NO_ADMITTED_STAGE_COSTS'
        elif cost_artifact.get('schema')!='heterospec.typed-macro-costs.v2':reason='UNTRUSTED_OR_LEGACY_COST_ARTIFACT'
        else:reason='MACRO_CAPTURE_COSTS_ARE_NOT_RESIDENT_STAGE_COSTS'
        # An abstention is not an unpriced q1 or rewind instruction. The owner
        # retains control at its existing legal frontier; already spent H stays.
        return self._finish(began,{'status':'ABSTAIN','action':None,'reason':reason,'state_key':snapshot.state_key})

    def decide_model(self,snapshot,model):
        """Executable causal recommendation with synthetic prices, never actuation."""
        began=self.clock()
        if self.disabled:return self._finish(began,{'status':'ABSTAIN','action':None,'reason':'CONTROLLER_DISABLED_AFTER_OVERHEAD'})
        decision=solve_model(snapshot,model,self.history.probabilities(len(snapshot.candidate_tokens)))
        decision.update(status='SYNTHETIC_MODEL_ONLY',sunk_draft_nanoseconds=snapshot.sunk_draft_nanoseconds,
                        cost_origin=model.origin,whole_request_optimality=False,performance_claim=False)
        return self._finish(began,decision)
