# LiteLLM integration work

RouterHub's proposed named integration is developed in
[routerhubSI/litellm](https://github.com/routerhubSI/litellm/tree/litellm_routerhub_provider).
Companion documentation is in
[routerhubSI/litellm-docs](https://github.com/routerhubSI/litellm-docs/tree/litellm_routerhub_docs).
These are organization forks, not an endorsement or a released upstream feature.

The upstream drafts are [provider PR 49550](https://github.com/BerriAI/litellm/pull/49550)
and [documentation PR 2770](https://github.com/BerriAI/litellm-docs/pull/2770).
Both were opened from RouterHub organization forks. Neither is merged.

The first proposal adds the JSON provider entry, two GLM abliterated price/limit
entries and mocked routing, authentication, usage-cost, streaming and error tests.
No native Responses or Anthropic Messages capability is advertised for these
Chat Completions entries. No tool, reasoning or structured-output capability flag
is added without verification.

Ruff lint/format checks and the new test file's strict type check pass locally.
A real source-built native extension was built on GitHub, hash-verified and
installed locally. All 11 focused provider tests now pass locally and in the
organization's verification workflow. No stand-in native module was used.

Both GLM entries now pass ordinary and streamed requests through direct HTTP,
the actual LiteLLM SDK and a real local proxy. Returned usage and calculated
costs match independent token-rate calculations. Redacted artifacts and exact
scope are documented in [LIVE-VERIFICATION.md](LIVE-VERIFICATION.md). Account
debits, actual cache hits, tools, Responses and Messages remain unverified.

Before a maintainer review, the human contributor must review and sign the
[LiteLLM CLA](https://cla-assistant.io/BerriAI/litellm), rewrite the marked PR
summary in their own words. Live testing was subsequently authorized and the
key was read privately on the test machine. Never place a key in GitHub comments
or send it in a public chat.

Run the documented SDK and proxy flow against real RouterHub inference, both
ordinary and streamed Chat Completions. Record exact commands, redacted replies,
usage and pricing calculations at the tested commit. Validate cache accounting
only when actual cache-hit usage is returned. Do not mark mock output as live
proof. Confirm required CI and reviewer checks before marking the PR ready.
