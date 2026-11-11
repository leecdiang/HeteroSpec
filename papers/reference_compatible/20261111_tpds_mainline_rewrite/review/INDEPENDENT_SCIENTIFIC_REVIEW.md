# Independent scientific review of the reconstructed manuscript

This read-only reader pass follows the prose-authoring step. It reviewed the first complete 10-page main manuscript, the 5-page standalone supplement, native figures 1–2, and the corresponding LaTeX labels and compilation logs.

- Main PDF SHA-256: d47e17d16c6e2534e796311704385f677b95eca74c21ce9661cc0b7f308dee35
- Supplement SHA-256: 8a301c1fc5336875e5aa0e5d11907aba5836c8f3ad46d72d6bf146d8a3025708

This is a manuscript and evidence-interpretation review. It adds no native model runs or experimental samples.

## 1. What a reader can answer after the first two pages

| Question | Location and answer | Assessment |
|---|---|---|
| What is the problem? | Abstract and Introduction paragraph 1: reorganize known-query work while retaining the output and state of a quantized deployment fixed before optimization. | The problem is concrete and precedes interface terminology. |
| Why is the ordinary batching argument insufficient? | Introduction paragraph 2 and Section 2.1: equal visible operands and a zero masked suffix do not prevent a physical-range-dependent AV result. Vector discrepancy precedes token divergence. | The initiating example supplies a numerical failure with a specific intervention. |
| What does the method do? | Introduction paragraphs 4–5: derive extent groups from live metadata; place whole-graph or attention-local cuts; retain native inner arithmetic while exposing independent groups; own logical outputs and state. | The answer describes executable operations, not only a compatibility definition. |
| What are the contributions? | End of Introduction: mechanism identification and execution construction. Validation and performance measurements support them. | Application speedups are not presented as the isolated method increment. |
| What does hardware awareness mean? | CUDA group width/reduction behavior, Vulkan activation/layout choices, and partial-offload placement. | Concrete backend decisions give the phrase content. |

The first two pages contain enough information to reconstruct this argument. Repetition between the introductory example and Section 2, and between introductory related work and Section 6, was a compression opportunity. The completed humanizer pass has reduced both.

## 2. Circularity and qualification scope

The runtime does not select a plan by observing whether its result matches the reference. It selects a previously specified backend recipe, derives physical extent from occupancy/head/capacity/padding, and forms groups before execution. The 3+1 split at positions 765–768 and the 1+3 split at head 767 demonstrate a generative rule.

The grouping expression gives a minimum for contiguous equal-key runs under a call-width bound. It is not presented as a separate scheduling novelty. The humanizer clarified that maximal equal-key runs are defined before the per-call width bound is imposed.

The composition paragraph is conditional: compatible initial state, a group recipe preserving the required update, and correct output/commit ownership imply compatible subsequent boundaries. Native replay and full-model checks test those premises in the implemented deployments. This does not turn finite qualification into an all-input floating-point theorem. The existing conditional wording and evaluation scope are sufficient.

Evidence distinctions preserved in the prose:

- CUDA extent replay fixes consumer query width at one. The old extent experiment is not described as a measured q4 attention-kernel reduction change.
- F32 versus Q8_1 activation behavior is identified as Vulkan-specific. CUDA Q8 instead has the traced and source-inspected MMVQ reduction-warp change.
- The producer experiment reports serialized-state and initial-vector changes and consumer endpoint dependence. Endpoint evidence is not relabelled as full numerical state equivalence.
- Vulkan p021 is the QK specialization extended across query workgroups. AV retains its own extent/stride/dispatch conditions.
- Backend-loop4 is credited as the strong existing control. Packing replaces successive backend group invocations; graph concatenation is not incorrectly charged to that control.

## 3. Scientific precision of figures 1–2

### Figure 1

The matrix matches the native intervention: positions 765–768, reference extents 768/768/768/1024, and an unsplit 1024 extent. The replay matrix concerns the first affected query, exchanges physical range with consumer width fixed, and refers to matching visible operands. Crop and zero-pad directions reproduce the corresponding AV outputs. Generated-output indices 29 and 81 remain distinct from query positions.

The figure does not combine the CUDA intervention with Vulkan contiguity/dispatch evidence. It supports the physical-range dependency at the stated level.

### Figure 2

The top panel depicts physical-extent groups; the second depicts independent projection arithmetic groups. The 3+1 query partition is not equated with the Q8 four-column or mixed-Q4 scalar-column recipe. Whole explicitly uses two ordered graph calls. Local branches describe dataflow structure, without claiming measured overlap.

One unit required correction: the [K,1,q] mapping creates one independent channel per query column, not per output dot product. Each column produces multiple weight-row dot products. The figure author changed “per dot” to “per column” and labels the cells “col. 1” through “col. 8”.

The caption editor also clarified that projection/attention/FFN schematize repeated transformer blocks, preserving the distinction between a complete Whole graph call and the block-level drawing.

## 4. Issues identified and disposition

| Finding | Consequence | Disposition |
|---|---|---|
| “5.2.0.1 Typed extension to mixed quantization.:” | Spurious hierarchy and repeated punctuation turn a short extension into a new nested branch. | Root owns correction to an unnumbered inline heading or proper subsubsection. |
| Seven-step Table 1 has no prose reference | Execution summary is an unintroduced float. | Humanizer added an introduction in Section 3.4. |
| Section 2.2 asks whether extent matching suffices, then presents activation-first repair evidence | Reader expects an extent-only experiment at that point. | Humanizer introduced width-dependent choices outside attention. |
| Standalone supplement imports main bibliography labels and defines records/gsm8k again | Duplicate labels risk bibliography or link ambiguity. | Root applied the installed xr package's externaldocument no-citation option, pending compiled verification. |
| Figure 2 says “per dot” | Confuses a query-column channel with one scalar output product. | Figure author corrected it to “per column”. |
| Section 2.3 says the original producer must remain in the candidate execution | Read literally, this forbids CUDA candidate prefill regrouping and contradicts the source of the measured packing increment. | The original producer defines the reference numerical state. CUDA candidates may regroup known prompt rows under the compatible recipe and are qualified against that state; the resident Vulkan implementation retains its UB128 producer calls. Root has received the correction, including the related “original phase history” phrase in Section 3.4. |

Main figures 1–6 follow intervention, method, factorial, geometry, application and width. The supplement's external references resolve to main Figures 3, 4 and 6a; its own figures use S1–S3 and tables S1–S11. The inspected PDFs had no unresolved question-mark references.

## 5. Targeted final verification

After the final layout pass, check the producer-semantics correction, mixed-quantization heading, Table 1 prose reference, no-citation external import and regenerated Figure 2. Re-render the first pages after Figure 1 moves earlier, ensuring its caption still describes the first-query native intervention. These checks concern the edits above, not a new evidence round.

## 6. Recheck of the revised build

The revised main PDF remains 10 pages, SHA-256 5ed1a1d2a8185256866bbf44cc28d7977ee028e57a99acb0853c00acc0f57283. The standalone supplement remains 5 pages, SHA-256 f0a9e272b3bef907aa0b474e9c4b65a60e0ff2285909ccf5dc6b27f03daa3b7f.

- Figure 1 now appears on page 2. Its rendered caption and replay matrix retain the first-query, fixed-consumer-width scope.
- Figure 2 now appears on page 4. The rendered mapping says “per column”, its cells identify columns, and its caption explains the repeated transformer blocks.
- The mixed-quantization subsection renders as 5.2.1 with no extra punctuation.
- Section 3.4 introduces Table 1 in prose.
- Section 2.2 introduces numerical choices outside attention, without implying an unshown extent-only test.
- Section 2.3 explicitly permits regrouped CUDA candidate prefill under the reference state requirement and distinguishes the resident Vulkan UB128 producer. Section 3.4 refers to the same logical phase history, not identical physical producer calls.
- Main and supplement logs contain no undefined or multiply defined reference warnings. The supplement still resolves the external figures as 3, 4 and 6a and gives its own references separate citation numbers.
- The conditional composition argument and its finite native/full-model qualification remain distinct in the revised prose.

The targeted recheck found no remaining scientific misstatement or cross-reference error in the reviewed changes. The first two pages state the problem, demonstrate the physical-range failure, describe the execution construction and identify the two contributions.
