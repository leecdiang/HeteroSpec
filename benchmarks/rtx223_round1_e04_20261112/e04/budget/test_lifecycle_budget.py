import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest

from lifecycle_budget import *


SHA="a"*64
POLICY={a:"b"*64 for a in REQUIRED_ACTORS}


def fixture(overrides=None, extra_certs=()):
    overrides=overrides or {}
    phases=[]; certs=[]
    for phase in REQUIRED_PHASES:
        route="mock:"+phase
        bound=overrides.get(phase,0)
        node=Node("opaque",route,"MOCK:"+phase,SHA)
        certs.append(Certificate(node.proof_id,phase,route,"opaque",bound,SHA))
        phases.append(Phase(phase,(node,)))
    return tuple(phases),MockProofRegistry(certs+list(extra_certs))


class LifecycleBudget(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="CPU-MOCK-e04-")
        self.root=Path(self.tmp.name)
        self.ledger=MockFamilyLedger(self.root/"CPU-MOCK-family.sqlite","CPU-MOCK-family","parent-fingerprint",0,mock_root=self.root)
        self.notes=[]

    def tearDown(self):
        self.ledger.close()
        keep=os.environ.get("HS_E04_KEEP_ROOT")
        if keep:
            target=Path(keep)/self._testMethodName
            shutil.copytree(self.root,target)
            (target/"TEST_NOTES.json").write_text(json.dumps(self.notes,indent=2),encoding="utf8")
        self.tmp.cleanup()

    def plan(self,changes=None):
        p,r=fixture(changes)
        return Planner(r).bind(p,POLICY)

    def run_plan(self,plan,scripts=None,on_enter=None,lease="lease1"):
        backend=MockBackend(scripts,on_enter)
        c=MockController(self.ledger,plan,lease,"e04",backend)
        result=c.run()
        self.notes.append({"result":result,"ledger":self.ledger.snapshot()})
        return c,result

    def test_native_manifest_cannot_release_before_DLL_load(self):
        phases,_=fixture({"numerical_dll_load":0})
        result=inspect_native_candidate(phases,POLICY)
        self.assertEqual(result["decision"],"BLOCKED_BEFORE_NUMERICAL_DLL_LOAD")
        self.assertIsNone(result["complete_lifecycle_upper_bound"])
        self.assertEqual(result["normal_DLL_loads"],0)
        self.assertFalse(result["native_release"])
        self.notes.append(result)

    def test_missing_required_bootstrap_target_draft_cleanup_rejected(self):
        phases,registry=fixture()
        for missing in ("worker_bootstrap","numerical_dll_load","draft_model_load","draft_kv_init","capture","error_cleanup","teardown"):
            with self.subTest(missing=missing),self.assertRaisesRegex(BudgetRefusal,"LIFECYCLE"):
                Planner(registry).bind(tuple(p for p in phases if p.name!=missing),POLICY)

    def test_duplicate_extra_and_empty_phases_do_not_count_as_coverage(self):
        phases,registry=fixture()
        for variant in (phases+(phases[0],), phases+(Phase("self_declared_extra",()),), (Phase(phases[0].name,()),)+phases[1:]):
            with self.assertRaisesRegex(BudgetRefusal,"LIFECYCLE"):
                Planner(registry).bind(variant,POLICY)

    def test_unknown_zero_or_library_init_bound_rejected_before_entry(self):
        phases,_=fixture()
        _,registry=fixture()
        registry._certificates.pop("MOCK:library_init")
        with self.assertRaisesRegex(BudgetRefusal,"Missing mock certificate"):
            Planner(registry).bind(phases,POLICY)
        self.assertEqual(self.ledger.charged(),0)

    def test_complete_lifecycle_sums_init_library_transfer_warmup_cleanup(self):
        changes={"worker_bootstrap":2,"numerical_dll_load":3,"cuda_context_init":4,"library_init":5,
                 "target_model_load":2,"draft_model_load":1,"transfers":4,"warmup":3,"target_verify":6,
                 "capture":2,"error_cleanup":2,"teardown":1}
        plan=self.plan(changes)
        self.assertEqual(plan.total_upper_bound,sum(changes.values()))
        _,result=self.run_plan(plan)
        self.assertEqual(result["status"],"COMPLETE")
        self.assertEqual(result["observed_mock_emissions"],sum(changes.values())-2)
        self.assertEqual(self.ledger.charged(),sum(changes.values()))

    def test_exact_4096_whole_lifecycle_boundary(self):
        plan=self.plan({"numerical_dll_load":1,"target_verify":4094,"error_cleanup":1})
        self.assertEqual(plan.total_upper_bound,4096)
        _,result=self.run_plan(plan)
        self.assertEqual(result["observed_mock_emissions"],4095)
        self.assertEqual(self.ledger.charged(),4096)
        with self.assertRaisesRegex(BudgetRefusal,"FAMILY_BUDGET"):
            MockController(self.ledger,self.plan({"cuda_context_init":1}),"lease2","new-epoch",MockBackend())

    def test_known_partial_4096_plus_unknown_cannot_form_complete_bound(self):
        phases,registry=fixture({"target_verify":4096})
        registry._certificates.pop("MOCK:worker_bootstrap")
        with self.assertRaises(BudgetRefusal) as error:
            Planner(registry).bind(phases,POLICY)
        self.assertIsNone(error.exception.total_upper_bound)
        self.assertEqual(self.ledger.charged(),0)

    def test_over_4096_rejected_during_prebinding(self):
        with self.assertRaisesRegex(BudgetRefusal,"BUDGET"):
            self.plan({"target_verify":4096,"teardown":1})
        self.assertEqual(self.ledger.charged(),0)

    def test_boolean_float_and_nonfinite_bounds_rejected(self):
        for value in (True,1.0,float("inf"),float("nan"),-1):
            with self.subTest(value=value),self.assertRaisesRegex(BudgetRefusal,"COUNT"):
                self.plan({"library_init":value})

    def graph_plan(self,kind="static_graph",repeat=3):
        phases,registry=fixture()
        phase="target_verify"
        kernel=Node("kernel","mock:kernel","MOCK:kernel",SHA)
        nested=Node("static_graph","mock:child","MOCK:child",SHA,(kernel,),2)
        graph=Node(kind,"mock:graph","MOCK:graph",SHA,(kernel,nested),repeat)
        for n,b in ((kernel,1),(nested,0),(graph,0)):
            registry._certificates[n.proof_id]=Certificate(n.proof_id,phase,n.route,n.kind,b,SHA)
        phases=tuple(Phase(p.name,(graph,)) if p.name==phase else p for p in phases)
        return Planner(registry).bind(phases,POLICY)

    def test_nested_static_graph_replay_counts_nodes_not_one_API(self):
        plan=self.graph_plan()
        graph_steps=[s for s in plan.steps if s.phase=="target_verify"]
        self.assertEqual([s.upper_bound for s in graph_steps],[3,3,3])
        self.assertEqual(plan.total_upper_bound,9)
        controller,result=self.run_plan(plan)
        self.assertEqual(result["observed_mock_emissions"],9)
        with self.assertRaisesRegex(BudgetRefusal,"ORDER"):
            controller._perform(graph_steps[-1])
        self.assertEqual(controller.emitted,9)

    def test_graph_while_conditional_device_launch_callback_unknown_denied(self):
        for kind in ("while","conditional","device_launch","dynamic","host_callback","unknown"):
            with self.subTest(kind=kind),self.assertRaisesRegex(BudgetRefusal,"GRAPH_OR_OPAQUE"):
                self.graph_plan(kind)

    def test_graph_recursive_identity_and_zero_replay_rejected(self):
        with self.assertRaisesRegex(BudgetRefusal,"GRAPH"):
            self.graph_plan(repeat=0)
        phases,registry=fixture()
        child=Node("static_graph","same","MOCK:child",SHA,(Node("kernel","k","MOCK:k",SHA),))
        root=Node("static_graph","same","MOCK:root",SHA,(child,))
        for n,b in ((root,0),(child,0),(child.children[0],1)):
            registry._certificates[n.proof_id]=Certificate(n.proof_id,"target_verify",n.route,n.kind,b,SHA)
        p=tuple(Phase(x.name,(root,)) if x.name=="target_verify" else x for x in phases)
        with self.assertRaisesRegex(BudgetRefusal,"recursion"):
            Planner(registry).bind(p,POLICY)

    def test_wrapper_does_not_double_count_underlying_kernel(self):
        phases,registry=fixture()
        k=Node("kernel","k","MOCK:k",SHA)
        w=Node("wrapper","wrapper","MOCK:w",SHA,(k,))
        for n,b in ((k,1),(w,0)):
            registry._certificates[n.proof_id]=Certificate(n.proof_id,"target_verify",n.route,n.kind,b,SHA)
        p=tuple(Phase(x.name,(w,k)) if x.name=="target_verify" else x for x in phases)
        plan=Planner(registry).bind(p,POLICY)
        self.assertEqual(plan.total_upper_bound,2)

    def test_phase_bound_violation_stops_before_extra_mock_kernel(self):
        controller,result=self.run_plan(self.plan({"library_init":2}),{"library_init":{"emissions":3}})
        self.assertEqual(result["status"],"FAILED")
        self.assertEqual(controller.emitted,2)
        self.assertEqual(controller.backend.emissions,2)
        self.assertEqual(self.ledger.charged(),2)

    def test_failure_cleanup_reserved_upfront_and_no_retry_refund(self):
        plan=self.plan({"target_verify":3,"error_cleanup":2,"teardown":1})
        _,result=self.run_plan(plan,{"target_verify":{"emissions":3,"raise_after":1}})
        self.assertEqual(result["status"],"FAILED")
        self.assertEqual(result["observed_mock_emissions"],4)
        self.assertEqual(self.ledger.charged(),6)
        with self.assertRaisesRegex(BudgetRefusal,"FAMILY_STOPPED"):
            MockController(self.ledger,plan,"retry-new-id","e05",MockBackend())

    def test_reentry_and_foreign_thread_cannot_dispatch(self):
        plan=self.plan({"library_init":1})
        c=None
        def reenter(step):
            if step.phase=="library_init": c.run()
        c=MockController(self.ledger,plan,"r","e04",MockBackend(on_enter=reenter))
        errors=[]
        thread=threading.Thread(target=lambda:self.capture_error(c.run,errors))
        thread.start();thread.join()
        self.assertEqual(len(errors),1)
        self.assertIn("OWNER",str(errors[0]))
        result=c.run()
        self.assertEqual(result["status"],"FAILED")
        self.assertIn("REENTRY",result["failure"])

    @staticmethod
    def capture_error(callback,out):
        try: callback()
        except BaseException as exc: out.append(exc)

    def test_same_family_reopen_new_epoch_does_not_renew4096(self):
        self.run_plan(self.plan({"target_verify":3000}))
        self.ledger.close()
        self.ledger=MockFamilyLedger(self.root/"CPU-MOCK-family.sqlite","CPU-MOCK-family","parent-fingerprint",0,mock_root=self.root)
        self.assertEqual(self.ledger.charged(),3000)
        with self.assertRaisesRegex(BudgetRefusal,"FAMILY_BUDGET"):
            MockController(self.ledger,self.plan({"target_verify":1097}),"e05","e05",MockBackend())
        with self.assertRaisesRegex(BudgetRefusal,"FAMILY_BINDING"):
            MockFamilyLedger(self.root/"CPU-MOCK-family.sqlite","CPU-MOCK-family","new-parent",0,mock_root=self.root)

    def test_poststats_cannot_refund_complete_or_failed_or_populate_native_proofs(self):
        plan=self.plan({"target_verify":20})
        self.run_plan(plan,{"target_verify":{"emissions":1}})
        self.ledger.attach_poststats("lease1",{"kernels":0,"verified":True,"coverage":"complete","allow_GPU":True})
        self.assertEqual(self.ledger.charged(),20)
        phases,_=fixture()
        self.assertFalse(inspect_native_candidate(phases,POLICY)["native_release"])
        self.assertEqual(len(PRODUCTION_PROOF_ALLOWLIST),0)

    def test_policy_mismatch_across_arms_draft_reference_is_rejected(self):
        phases,registry=fixture()
        for actor in REQUIRED_ACTORS:
            policy=dict(POLICY);policy[actor]="c"*64
            with self.subTest(actor=actor),self.assertRaisesRegex(BudgetRefusal,"POLICY"):
                Planner(registry).bind(phases,policy)

    def test_changed_artifact_plan_or_proof_does_not_execute(self):
        phases,registry=fixture()
        first=phases[0].operations[0]
        changed=Node(first.kind,first.route,first.proof_id,"f"*64)
        with self.assertRaisesRegex(BudgetRefusal,"IDENTITY"):
            Planner(registry).bind((Phase(phases[0].name,(changed,)),)+phases[1:],POLICY)
        plan=self.plan({"library_init":1})
        object.__setattr__(plan,"total_upper_bound",0)
        with self.assertRaisesRegex(BudgetRefusal,"IDENTITY"):
            MockController(self.ledger,plan,"mutated","e04",MockBackend())

    def test_production_ledger_path_cannot_be_opened_by_mock_controller(self):
        with self.assertRaisesRegex(BudgetRefusal,"MOCK_ONLY"):
            MockFamilyLedger(self.root/"family-ledger.sqlite","CPU-MOCK-family","parent",0,mock_root=self.root)
        self.assertFalse((self.root/"family-ledger.sqlite").exists())

    def test_cpu_prefix_does_not_authorize_symlink_or_hardlink_alias(self):
        sentinel=self.root/"sentinel.txt"
        sentinel.write_bytes(b"own harmless sentinel; must never become SQLite")
        before=sentinel.read_bytes()
        alias=self.root/"CPU-MOCK-hardlink.sqlite"
        try:
            os.link(sentinel,alias)
        except OSError as exc:
            self.notes.append({"hardlink_fixture":"NOT_RUN_OS_REFUSED_CREATION","reason":str(exc)})
        else:
            with self.assertRaisesRegex(BudgetRefusal,"MOCK_ALIAS"):
                MockFamilyLedger(alias,"CPU-MOCK-alias","parent",0,mock_root=self.root)
            self.assertEqual(sentinel.read_bytes(),before)
        link=self.root/"CPU-MOCK-symlink.sqlite"
        try:
            link.symlink_to(sentinel)
        except OSError as exc:
            self.notes.append({"symlink_fixture":"OS_REFUSED_CREATION","reason":str(exc)})
        else:
            with self.assertRaisesRegex(BudgetRefusal,"MOCK_ALIAS"):
                MockFamilyLedger(link,"CPU-MOCK-alias","parent",0,mock_root=self.root)
            self.assertEqual(sentinel.read_bytes(),before)

    def test_existing_nonmock_database_is_not_modified_by_preflight(self):
        import hashlib,sqlite3
        path=self.root/"CPU-MOCK-foreign.sqlite"
        db=sqlite3.connect(path);db.execute("CREATE TABLE sentinel(x)");db.execute("INSERT INTO sentinel VALUES(37)");db.commit();db.close()
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(BudgetRefusal,"MOCK_FORMAT"):
            MockFamilyLedger(path,"CPU-MOCK-alias","parent",0,mock_root=self.root)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)

    def test_pending_or_running_lease_requires_separate_recovery(self):
        plan=self.plan({"target_verify":10})
        self.ledger.reserve("pending","e04",plan)
        self.ledger.mark_running("pending")
        self.ledger.close()
        self.ledger=MockFamilyLedger(self.root/"CPU-MOCK-family.sqlite","CPU-MOCK-family","parent-fingerprint",0,mock_root=self.root)
        with self.assertRaisesRegex(BudgetRefusal,"RECOVERY_REQUIRED"):
            MockController(self.ledger,plan,"new-id","e05",MockBackend())
        self.assertEqual(self.ledger.charged(),10)
        self.ledger.attach_poststats("pending",{"kernels":0,"recover":True})
        with self.assertRaisesRegex(BudgetRefusal,"RECOVERY_REQUIRED"):
            MockController(self.ledger,plan,"newer-id","e06",MockBackend())

    def test_nonhex_policy_digest_is_not_a_SHA256_binding(self):
        phases,registry=fixture()
        with self.assertRaisesRegex(BudgetRefusal,"POLICY"):
            Planner(registry).bind(phases,{a:"z"*64 for a in REQUIRED_ACTORS})

    def test_unexpected_observed_mock_overrun_is_durable_and_stops_family(self):
        plan=self.plan({"target_verify":2})
        self.ledger.reserve("fault-counter","e04",plan)
        self.ledger.mark_running("fault-counter")
        status=self.ledger.finish("fault-counter","FAILED",4097,"Injected above-family-cap counter fault")
        self.assertEqual(status,"OVERRUN")
        self.assertEqual(self.ledger.snapshot()["leases"][0]["emitted_mock"],4097)
        self.assertEqual(self.ledger.charged(),4097)
        self.ledger.attach_poststats("fault-counter",{"kernels":0,"cleared":True})
        self.assertEqual(self.ledger.charged(),4097)
        with self.assertRaisesRegex(BudgetRefusal,"FAMILY_STOPPED"):
            MockController(self.ledger,plan,"e05-retry","e05",MockBackend())


if __name__=="__main__": unittest.main()
