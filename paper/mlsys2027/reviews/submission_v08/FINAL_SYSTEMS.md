# Systems review — v0.8 (internal model-review simulation)

Review target: final `manuscript-v0.8.pdf` SHA-256 `d7e16554ae1fbd2b0fd5b8addf66922cc3f63234528c3eeba37b4ea0ffb5efac`; 10 body pages plus references, separate six-page appendix. This is not external peer review.

**Assessment: Borderline / Weak Accept, confidence 3/5.** The main change is substantive. B570 residual divergence is now predicted from target-only UB1 on a reserved workload after the mechanism and predictions were frozen. This changes the systems lesson from simply rechecking the path to a concrete diagnostic order: after a path fails, isolate the target execution partition before blaming live drafting. The 72/72 endpoint is a falsifiable sequence prediction, not a fitted timing curve. RTX direct-ID 75/90→90/90 and B570 60/90→78/90 remain separate qualification results.

The result is constrained to one stack and model pair, one task family and cap, and a target partition contrast. It does not identify the operation responsible for the argmax changes or demonstrate portability. The paper's five evidence levels are related by an argument rather than one controlled end-to-end intervention: B570 explains a B570 qualification failure, 358H explains a cost interface, M4 tests a different continuation controller. That limits a broad systems claim, but is acceptable as a careful characterization paper if the venue values validated negative controls.

The M4 controller remains the main negative payoff: Guard is slower than Always-Spec on the paired secondary comparison. The abstract and Section 7 disclose this. A reviewer could still question whether the separate M4 endpoint distracts from the now strongest B570 finding. I would retain it because it closes the distinction between qualification and profitability, while making the evidence classes explicit.

**Decision question:** H1 materially resolves the v0.7 complaint that B570 had no predictive mechanism within the tested configuration. It does not resolve external transfer. I do not require universal transfer to accept the precise claim, but would not accept a broader runtime or hardware law.
