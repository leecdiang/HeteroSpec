"""Causal/model counterexamples using explicitly synthetic prices, no model calls."""
from dataclasses import replace
import unittest
from causal_policy import (Snapshot,PastAcceptance,Price,SyntheticStage,SyntheticModel,
                           outcomes,solve_model,CausalController,PolicyError)


def price(ns,target=0,draft=0):return Price(ns,target,draft,'SYNTHETIC_reference_frontier')


def single_proposal(overhead=1):
    snapshot=Snapshot('deployment','initial',(11,),0,1,96)
    stages=(SyntheticStage(0,1,{'reject:1':price(20),'continue':price(20)}),
            SyntheticStage(1,1,{'bonus':price(20,draft=1)}),
            SyntheticStage(0,2,{'reject:1':price(100),'bonus':price(100,draft=1)}))
    model=SyntheticModel('deployment','initial',100,overhead,stages,{(1,'none'):price(0)})
    return snapshot,model


def cap_four(target_materialization=1):
    snapshot=Snapshot('deployment','initial',(11,12,13,14,15,16,17),0,7,4)
    prices={f'reject:{i}':price(20) for i in range(1,5)}
    prices['accepted_terminal:4']=price(70,target=target_materialization)
    model=SyntheticModel('deployment','initial',100,1,(SyntheticStage(0,4,prices),),{})
    return snapshot,model


class CausalPolicyTests(unittest.TestCase):
    def test_future_fields_and_stochastic_domain_are_rejected(self):
        data={'deployment_key':'d','state_key':'s','candidate_tokens':[1],
              'verified_rows':0,'draft_materialized_rows':1,'remaining_cap':96}
        for field in ('accepted_prefix','future_target_ids','final_output_length','hindsight_route','root'):
            with self.subTest(field=field),self.assertRaises(PolicyError):Snapshot.from_mapping(dict(data,**{field:7}))
        with self.assertRaises(PolicyError):Snapshot.from_mapping(dict(data,decoding='stochastic'))

    def test_feedback_requires_announced_chronological_action(self):
        history=PastAcceptance()
        with self.assertRaises(PolicyError):history.observe('future',[True])
        history.announce('a',0,2,7)
        with self.assertRaises(PolicyError):history.observe('other',[True,True])
        history.observe('a',[True,False])
        with self.assertRaises(PolicyError):history.announce('a',0,1,7)
        self.assertEqual(history.success,[1,0,0,0,0,0,0]);self.assertEqual(history.failure,[0,1,0,0,0,0,0])

    def test_post_rejection_and_post_terminal_suffixes_are_censored(self):
        left=PastAcceptance();right=PastAcceptance()
        for h in (left,right):h.announce('a',0,4,7)
        left.observe('a',[True,False,True,True]);right.observe('a',[True,False,False,False])
        self.assertEqual(left.success,right.success);self.assertEqual(left.failure,right.failure)
        terminal=PastAcceptance();terminal.announce('a',0,4,7)
        self.assertEqual(terminal.observe('a',[True,True,False,True],terminal_after=2),((1,True),(2,True)))
        self.assertEqual(terminal.failure,[0]*7)

    def test_two_future_worlds_have_same_predecision_action(self):
        snapshot,model=single_proposal();controllers=[CausalController(),CausalController()]
        for controller in controllers:
            controller.history.announce('past',0,1,1);controller.history.observe('past',[True])
        before=[c.decide_model(snapshot,model) for c in controllers]
        self.assertEqual((before[0]['action'],before[0]['width']),(before[1]['action'],before[1]['width']))
        # Opposite next outcomes become visible only after that same decision.
        for controller,outcome in zip(controllers,(True,False)):
            controller.history.announce('next',0,1,1);controller.history.observe('next',[outcome])
        self.assertNotEqual(controllers[0].history.probabilities(1),controllers[1].history.probabilities(1))

    def test_q4_macro_cost_does_not_authorize_an_intermediate_stage(self):
        snapshot,model=single_proposal();controller=CausalController()
        macro={'schema':'heterospec.typed-macro-costs.v2','status':'VALIDATED_MACRO_DIAGNOSTIC_ONLY',
               'scope':'CAPTURE_CONDITIONED_TARGET_OPERATION_ONLY','macro_costs':[{'schedule':[4,4],'operation_nanoseconds':1}]}
        answer=controller.decide_runtime(snapshot,macro)
        self.assertEqual(answer['reason'],'MACRO_CAPTURE_COSTS_ARE_NOT_RESIDENT_STAGE_COSTS')
        self.assertIsNone(answer['action']);self.assertFalse(answer['actuation_allowed'])
        self.assertEqual(controller.decide_runtime(snapshot,model)['reason'],'SYNTHETIC_PRICES_NOT_RUNTIME_EVIDENCE')
        self.assertEqual(controller.decide_runtime(snapshot,{'status':'PASS_RECORDED_RESULT_AND_RAW_REPLAY'})['reason'],'UNTRUSTED_OR_LEGACY_COST_ARTIFACT')

    def test_missing_cost_or_legal_action_never_invents_q1(self):
        snapshot,model=single_proposal();empty=replace(model,stages=(),stop_prices={})
        self.assertIsNone(solve_model(snapshot,empty,(0.5,))['action'])
        broken=SyntheticStage(0,1,{'reject:1':price(1)})
        answer=solve_model(snapshot,replace(empty,stages=(broken,)),(0.5,))
        self.assertEqual(answer['reason'],'NO_LEGAL_ACTION')
        self.assertEqual(answer['rejected_actions'][0]['reason'],'MISSING_OR_EXTRA_OUTCOME_PRICE')

    def test_q4_accepted_terminal_requires_pending_target_materialization(self):
        snapshot,broken=cap_four(0)
        answer=solve_model(snapshot,broken,(0.5,)*7)
        self.assertIsNone(answer['action'])
        self.assertEqual(answer['rejected_actions'][0]['reason'],'UNPRICED_REQUIRED_MATERIALIZATION')
        _,complete=cap_four(1);good=solve_model(snapshot,complete,(0.5,)*7)
        self.assertEqual((good['action'],good['width']),('VERIFY_NEXT',4))
        # Hand calculation: E[new tokens]=1+.5+.25+.125=1.875;
        # cost=20*(15/16)+70/16=23.125, then one unit of control overhead.
        self.assertAlmostEqual(good['model_value_nanoseconds'],163.375)
        eog=replace(snapshot,remaining_cap=96,known_eog_ids=(14,))
        self.assertIsNone(solve_model(eog,broken,(0.5,)*7)['action'])

    def test_zero_estimated_probability_does_not_waive_state_requirements(self):
        snapshot,broken=cap_four(0)
        self.assertIsNone(solve_model(snapshot,broken,(0.0,)*7)['action'])
        prices=dict(broken.stages[0].prices);del prices['accepted_terminal:4']
        self.assertIsNone(solve_model(snapshot,replace(broken,stages=(SyntheticStage(0,4,prices),)),(0.0,)*7)['action'])

    def test_deferred_draft_tail_is_charged_even_at_terminal(self):
        snapshot=Snapshot('d','s',tuple(range(7)),0,7,7)
        prices={f'reject:{i}':price(1) for i in range(1,8)}
        prices['accepted_terminal:7']=price(2,target=1,draft=0)
        model=SyntheticModel('d','s',100,1,(SyntheticStage(0,7,prices),),{})
        self.assertIsNone(solve_model(snapshot,model,(0.5,)*7)['action'])
        prices=dict(prices);prices['accepted_terminal:7']=price(30,target=1,draft=1)
        self.assertEqual(solve_model(snapshot,replace(model,stages=(SyntheticStage(0,7,prices),)),(0.5,)*7)['width'],7)

    def test_sunk_draft_is_not_refunded_for_short_verification(self):
        snapshot,model=single_proposal()
        first=solve_model(replace(snapshot,sunk_draft_nanoseconds=100),model,(0.5,))
        second=solve_model(replace(snapshot,sunk_draft_nanoseconds=100000),model,(0.5,))
        self.assertEqual(first,second)

    def test_future_control_overhead_can_reverse_the_model_choice(self):
        snapshot,cheap=single_proposal(overhead=1);_,expensive=single_proposal(overhead=200)
        self.assertEqual(solve_model(snapshot,cheap,(0.5,))['width'],1)
        self.assertEqual(solve_model(snapshot,expensive,(0.5,))['width'],2)

    def test_abstention_and_disabled_calls_still_pay_observed_overhead(self):
        ticks=iter([0,101,200,205]);controller=CausalController(100,lambda:next(ticks));snapshot,_=single_proposal()
        first=controller.decide_runtime(snapshot)
        self.assertEqual(first['reason'],'CONTROLLER_OVERHEAD_LIMIT_EXCEEDED')
        second=controller.decide_runtime(snapshot)
        self.assertEqual(second['reason'],'CONTROLLER_DISABLED_AFTER_OVERHEAD')
        self.assertEqual(second['controller_span_total_nanoseconds'],106)

    def test_frontier_and_deployment_binding_cannot_be_reused(self):
        snapshot,model=single_proposal()
        for altered in (replace(snapshot,state_key='different-cache'),replace(snapshot,deployment_key='other-GPU')):
            with self.assertRaises(PolicyError):solve_model(altered,model,(0.5,))
        with self.assertRaises(PolicyError):replace(model,origin='QUALIFIED_GPU_MEASURED')

    def test_known_terminal_does_not_issue_another_verification(self):
        snapshot,_=cap_four();snapshot=replace(snapshot,verified_rows=4,target_materialized_rows=4,remaining_cap=0,terminal_kind='accepted')
        missing=SyntheticModel('deployment','initial',100,1,(),{})
        self.assertEqual(solve_model(snapshot,missing,(0.5,)*7)['reason'],'MISSING_TERMINAL_CONVERGENCE')
        complete=replace(missing,stop_prices={(4,'accepted'):price(70,target=1)})
        self.assertEqual(solve_model(snapshot,complete,(0.5,)*7)['action'],'RECONCILE_TERMINAL')

    def test_terminal_inside_a_wider_call_uses_actual_physical_frontier(self):
        snapshot,_=cap_four()
        snapshot=replace(snapshot,verified_rows=4,target_materialized_rows=8,remaining_cap=0,terminal_kind='accepted')
        model=SyntheticModel('deployment','initial',100,1,(),{(4,'accepted'):price(9)})
        # p4 is already materialized by the wide call; a priced trim/convergence
        # can suffice. Do not invent another q1 from the visible token count.
        self.assertEqual(solve_model(snapshot,model,(0.5,)*7)['action'],'RECONCILE_TERMINAL')


if __name__=='__main__':unittest.main()
