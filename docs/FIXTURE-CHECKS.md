# Authored fixture verification

The initial Windows check used Python 3.13.14, Flask 3.1.3 and pytest 9.2.0.
The vulnerable fixture passed 5 cases and failed 12. The authored reference
passed all 17 cases. The collector's seven offline tests pass, including its
refusal to send a request without explicit paid-use opt-in and identified,
credential-free public catalogue requests.

Six additional verification-helper cases also pass. They check cost arithmetic,
key-file parsing, paid-use opt-in and the completeness of recorded results.
`python verify.py` now runs all 13 offline helper/collector cases plus the
vulnerable and authored-reference fixture checks.

Run `python verify.py` to check these expectations again. This does not call
RouterHub, evaluate a model response or start an application server. The
workflow runs the same trusted-fixture checks on Linux.

The initial Linux run passed on GitHub Actions at
https://github.com/routerhubSI/routerhub-model-evals/actions/runs/41261790072.

These outcomes are harness checks, not model scores. Those fixture checks did
not perform inference. Subsequent authorized response collections are recorded
separately in `results/`. The container runbook was subsequently verified on
disposable GitHub Linux runners. Both cohorts include a successful 17/17 authored
reference check before any model candidate is scored.

A read-only public catalogue request also succeeded from the development host
using the collector's explicit application User-Agent. This is not inference.
