# Draft X thread based on the recorded run

Post from the RouterHub account. The linked report discloses affiliation and
includes all failed attempts. Do not present this as an independent review or a
general model ranking. This is draft copy, not a published social post.

## First post

```text
GLM 5.3 Abliterated used all 4,096 tokens on reasoning. No code, in 3 attempts.

We set reasoning_effort="low".

Same toy task, same token cap: 3/3 attempts passed all 17 tests. Median request: 3.31s.

Raw outputs, failures and limits:
https://github.com/routerhubSI/routerhub-model-evals/blob/main/RESULTS.md
```

## Reply with the comparison

```text
We also tested standard GLM 5.3 and the uncensored entry.

All three passed the 17 tests in all three low-effort attempts.

So this doesn't prove abliterated is "better." It shows why the exact API entry, settings and task matter more than the label.
```

## Reply with access

```text
Want hosted GLM 5.3 or Flash abliterated access without managing GPUs?

RouterHub offers OpenAI-compatible Chat Completions with prepaid token billing. These entries are currently preview.

Exact IDs, supported APIs and current pricing:
https://routerhub.si/models?utm_source=x&utm_medium=organic_social&utm_campaign=glm_upload_eval
```

Attach `../assets/glm-reasoning-result.png` as a result card. Its editable source
is `../assets/glm-reasoning-result.svg`. It summarizes recorded results, not a live screen
recording. For a video, show the real sandbox test logs and label any replay or
time compression. Never include API keys or private terminal history.
