# The CPU replay oracle is not historical R

The PR183 fixture's `oracle()` creates a fresh CPU context and feeds every token
of its supplied prefix through a separate one-token caller, requesting that
caller's output. This includes all original prompt tokens.

By contrast, the frozen PR151 request uses the selected prompt producer. In the
main NATIVE-prefill path it supplies the entire prompt in one `decode` caller
and requests only its final output, even when R has physical `n_ubatch=1`.
The explicit P1 diagnostic producer is a separate path. Physical ubatch1 alone
therefore does not define the historical reference computation or its requested
output geometry.

The PR183 target fixture itself prefills the whole prompt once, and its local
scalar oracle comparison passed on the documented synthetic CPU cases. This is
finite evidence between those CPU recipes, not evidence that their distinction
is harmless on the original model/GPU/runtime. The journal's correct-row probe
also uses that same CPU replay oracle. Neither should be called the old R or a
frozen-deployment reference qualification.

A future actual-model qualification must first reproduce the frozen prompt
producer, including caller boundaries and logits mask, then replay the actual
continuation prefix under the frozen continuation recipe. Query identity must
include prompt-producer/caller/logits-mask details and continuation recipe in
addition to token IDs, model/runtime/build/device and numerical settings. Equal
metadata does not prove numerical equality; actual source/binary and forced-
prefix vector/state qualification remain required. No such GPU qualification
or corrected replay implementation is delivered in this clarification.
