# LiteLLM integration work

RouterHub's proposed named integration is developed in
[routerhubSI/litellm](https://github.com/routerhubSI/litellm/tree/litellm_routerhub_provider).
Companion documentation is in
[routerhubSI/litellm-docs](https://github.com/routerhubSI/litellm-docs/tree/litellm_routerhub_docs).
These are organization forks, not an endorsement or a released upstream feature.

The first proposal adds the JSON provider entry, two GLM abliterated price/limit
entries and mocked routing, authentication, usage-cost, streaming and error tests.
No native Responses or Anthropic Messages capability is advertised for these
Chat Completions entries. No tool, reasoning or structured-output capability flag
is added without verification.

Before a maintainer review, the human contributor must review and sign the
[LiteLLM CLA](https://cla-assistant.io/BerriAI/litellm), rewrite the marked PR
summary in their own words, approve a limited live-testing budget and provide
credentials privately on the test machine. Never place a key in GitHub comments
or send it in a public chat.

Run the documented SDK and proxy flow against real RouterHub inference, both
ordinary and streamed Chat Completions. Record exact commands, redacted replies,
usage and pricing calculations at the tested commit. Validate cache accounting
only when actual cache-hit usage is returned. Do not mark mock output as live
proof. Confirm required CI and reviewer checks before marking the PR ready.
