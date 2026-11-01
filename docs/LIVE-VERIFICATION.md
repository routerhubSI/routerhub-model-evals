# RouterHub integration verification

Recorded November 1, 2026. The API key was read only on the operator's workstation.
It was not printed, committed, added to GitHub Secrets or sent to a CI runner.
The original credential file was not changed.

## Verified so far

Both `glm-5.3-abliterated` and `glm-5.3-flash-abliterated` returned the requested
reply through direct Chat Completions, ordinary and streaming. All four checks
returned usage. Those raw records are in `results/2026-11-01/api-smoke`.

The actual LiteLLM SDK on source commit
`2cc7d379933b32989dc6d448fb7d3822127c890a` passed the same four real-provider
checks using the `routerhub/` prefix. Calculated costs match independently
computed costs from reported usage and the proposed pricing entries. SDK records
are in `results/2026-11-01/litellm-sdk/summary.json`.

The actual loopback-only LiteLLM proxy passed four real requests with the same
two models, ordinary and streamed. Non-streamed cost headers and final streamed
usage costs match independent published-rate calculations. The successful
configuration, raw responses and summary are under
`results/2026-11-01/litellm-proxy-attempt-05`.

The proxy was started with the repository's requested two-worker reload command.
Windows Uvicorn logged that the worker flag is ignored with reload, and one
server PID started. No multi-worker or concurrency proof is claimed. Redis and
database-backed spend logging were omitted because the check covers provider
routing and response-cost accounting, not shared-state behavior. The proxy was
stopped after testing. Four earlier startup attempts are retained as failures;
they made no inference requests.

The native extension was built from the exact earlier source commit
`74a78d089053a2043a10d407b98300bd6047ddf5` on a GitHub Windows runner and installed
locally only after SHA-256 verification. The only subsequent source change was
the Python backup catalogue synchronization. Rust sources, the root catalogue,
provider registry, Python code and dependency lockfile are unchanged. The
artifact hash and source comparison are in
`results/2026-11-01/litellm-native-provenance.json`.

Eleven focused provider tests pass locally and in
[organization CI](https://github.com/routerhubSI/routerhub-model-evals/actions/runs/41264905925).
They include the seven new RouterHub cases and four existing Refuseless cases.
The new test file also passes strict type checking, Ruff lint and formatting.
Windows tokenizer resources were restored from their exact Git bytes before
unit testing, so no tokenizer download or external socket is needed in tests.

A mutation check changed the provider's environment-variable name, observed the
credential-resolution test fail, restored the original bytes, and reran all 11
focused tests successfully. The mutation was never pushed.

The documentation site builds successfully on the Linux job in
[the initial integration run](https://github.com/routerhubSI/routerhub-model-evals/actions/runs/41263376517).
The rendered RouterHub page was exported as an artifact. The initial provider
job failed before its assertions because Windows CRLF conversion invalidated the
bundled tokenizer hashes. The follow-up provider run fixes its preparation and
passes; that earlier failure is not presented as a pass.

The updated documentation wording is checked by the follow-up full build at
https://github.com/routerhubSI/routerhub-model-evals/actions/runs/41266757203.

## Scope and remaining gates

These checks do not verify account-level debits, paid inference costs beyond the
published-rate calculation, native Responses, Messages, tools, schema output or
actual cache hits. The short SDK requests reported zero cached input tokens.
Mocked cached-usage accounting tests are separate from live caching behavior.

The provider and documentation pull requests remain drafts. An authorized human
must review the CLA and rewrite the marked summary before requesting review.
Upstream CI authorization, the Vercel preview and merge/release decisions belong
to the upstream maintainers. Organization CI does not replace those checks.
