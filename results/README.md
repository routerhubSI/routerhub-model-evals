# Model results

Live responses were collected on November 1, 2026 with explicit credit-use
approval. `2026-11-01` contains three attempts per model with default reasoning
settings. `2026-11-01-low` repeats the same task with `reasoning_effort=low`.
Sandbox scoring is complete. Each cohort's `sandbox` folder contains the actual
test reports. Raw responses include failed and truncated attempts.

The `api-smoke` folder contains successful direct non-streaming and streaming
Chat Completions checks for the two GLM abliterated catalogue entries. These
are direct HTTP checks, not LiteLLM SDK or proxy verification.

Local fixture checks validate the benchmark harness only. The reference solution
is an authored fixture, not evidence of GLM or any other model's performance.

Generated runs are ignored by Git. Before publishing selected artifacts, review
them for secrets and private content, preserve failed runs, and record the exact
commit, model ID, settings, repetitions and provider-reported charges.

Collected token usage supports a published-rate cost estimate. Account billing
has not been independently inspected, so estimated cost is not labelled as a
verified account charge. Provider wrappers and upstream checkpoint provenance
are not controlled by this small hosted-endpoint experiment.
