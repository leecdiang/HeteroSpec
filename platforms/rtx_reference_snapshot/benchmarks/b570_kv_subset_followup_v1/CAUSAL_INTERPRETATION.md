# Causal interpretation memo

Control gate: PASS; complete repeatable prescribed study: True.

Q1. Smaller-than-full KV selectors reproducing a distinguishable donor endpoint in two independent processes: KV_early, KV_late, KV_layer0, KV_middle, KV_prefix128, KV_tail128, K_all, K_layer0, V_all, V_layer0. Selectors producing a valid third endpoint: KV_early, KV_late, KV_layer0, KV_middle, KV_prefix128, KV_tail128, K_all, K_layer0, V_all, V_layer0. The former identify a sufficient manipulated state subset for historical donor-endpoint reproduction under this intervention; the latter establish continuation change without donor-endpoint reproduction.

Q2. Among the four affected task/direction coordinates, V_layer0 reproduces the donor endpoint in 3/4, K_layer0 in 1/4 and KV_layer0 in 2/4; both repeats agree for every coordinate. This is a descriptive concentration among the fixed primary selectors, not V exclusivity. Other roles and layer groups also reproduce the donor in some coordinates. Prefix and tail each reproduce the donor in 2/4 affected coordinates, with task/direction dependence; the 128 cutoff is inherited from the prefill partition and is not a universal causal threshold. Descriptive endpoint concentrations do not establish exclusivity or necessity. Third-trajectory selectors: KV_early, KV_late, KV_layer0, KV_middle, KV_prefix128, KV_tail128, K_all, K_layer0, V_all, V_layer0.

Q3. Projection difference mediation is not directly established. The intervention manipulates serialized retained K/V with recipient initial logits fixed; it does not manipulate a projection output upstream and measure a mediated effect through the selected subset. Natural reachability of mixed states and a unique causal projection are not established.

This strengthens the finite retained-state part of the statement 'B570 reveals retained-state boundary limiting local repair transfer' by identifying finite retained-state subsets that reproduce the donor endpoint or alter the continuation. The two outcomes are reported separately. Local repair transfer itself is not newly tested here. The historical full-KV result remains separate evidence.

Stronger claims still unsupported: a uniquely causal projection kernel; complete or exclusive mediation of the prefill partition effect; necessity or minimality of any subset; a universally sufficient layer/role/position; natural reachability of mixed states; generalization to unseen tasks/models/devices/quantizations; successful general local repair transfer; speedup or qualified paid-cost improvements.

Endpoint equivalence is observational. A recipient-equivalent suffix is recorded as D against EMPTY; a distinct A recovery mechanism would require a separately specified reversal experiment. Both directions and both independent repeats are retained, including stable-task overlap and nulls.

## Small sufficient subsets

K_layer0 and V_layer0 each select 1/64 (1.5625%) of the full K/V value bytes. K_layer0 reproduces the donor endpoint for GSM8K/test/1248 A->B (329728 selected bytes, 113464 changed bytes). V_layer0 reproduces it for GSM8K/test/1248 in both directions (329728 selected, 122089 changed), and GSM8K/test/831 A->B (272384 selected, 128441 changed). All these observations repeat in two independent processes. We identified a sufficient manipulated state subset under this intervention; minimality, necessity and projection-kernel mediation are not established.

V_layer0 GSM8K/test/831 B->A is a repeatable third trajectory, not donor reproduction. Stable-task mixed subsets produce 32 third-trajectory request outcomes and 48 endpoint nulls; their original A/B endpoints overlap. This confirms that stable original endpoints do not guarantee all mixtures remain on that endpoint.

## Layer-0 combinations

GSM8K/test/1248 B->A: K_layer0=D, V_layer0=B, KV_layer0=D. The joint K/V intervention has a different endpoint class from V alone.
At least one V_layer0 donor-reproducing intervention loses that outcome when K_layer0 is added. Observed donor-endpoint sufficiency is therefore not monotone under this specific subset addition.

This comparison does not establish a unique responsible projection, necessity of V, or a universal interaction rule.

## Descriptive concentration across the four affected task/direction coordinates

| Selector | Affected classes (one row per direction) | Stable classes | Selected fraction of full KV values |
|---|---|---|---:|
| KV_early | {'D': 2, 'C': 1, 'B': 1} | {'D': 3, 'C': 1} | 25.00000% |
| KV_late | {'B': 1, 'C': 2, 'D': 1} | {'C': 2, 'D': 2} | 25.00000% |
| KV_layer0 | {'D': 1, 'B': 2, 'C': 1} | {'D': 3, 'C': 1} | 3.12500% |
| KV_middle | {'D': 3, 'B': 1} | {'C': 1, 'D': 3} | 50.00000% |
| KV_prefix128 | {'B': 2, 'D': 2} | {'C': 2, 'D': 2} | 96.24060% |
| KV_tail128 | {'B': 2, 'D': 2} | {'C': 2, 'D': 2} | 32.63158% |
| K_all | {'B': 1, 'D': 1, 'C': 2} | {'C': 2, 'D': 2} | 50.00000% |
| K_layer0 | {'D': 1, 'B': 1, 'C': 2} | {'C': 2, 'D': 2} | 1.56250% |
| V_all | {'B': 1, 'D': 1, 'C': 2} | {'C': 2, 'D': 2} | 50.00000% |
| V_layer0 | {'B': 3, 'C': 1} | {'D': 3, 'C': 1} | 1.56250% |

These are descriptions of this fixed intervention matrix; complementary selections or nulls do not prove that an effective subset is necessary or exclusive.

## Position interaction

| Task | Direction | Prefix [0,128) | Tail [128,N) | ALL control |
|---|---|---|---|---|
| GSM8K/test/1248 | A->B | D | D | B |
| GSM8K/test/1248 | B->A | B | B | B |
| GSM8K/test/831 | A->B | B | B | B |
| GSM8K/test/831 | B->A | D | D | B |

Both independent repeats agree. In two directions, each position region alone reproduces the donor; in the reverse directions, neither alone does, while ALL does. There is no uniquely sufficient position region across these exposed inputs. For /831 A->B, the five-token tail selects 655360 bytes (5/133 of K/V values) and changes 399839 bytes. The result does not identify 128 as a general threshold.
