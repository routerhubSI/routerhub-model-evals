# GLM upload-repair experiment

Recorded November 1, 2026. Maintained by RouterHub, the commercial API provider used in these runs.

## Result

Reasoning configuration changed the result more than the model label on this small task. All three entries passed all 17 public acceptance tests in all three low-effort attempts. The abliterated default-effort attempts returned no code after exhausting the 4,096-token reasoning budget.

| Configuration | Exact API ID | Full passes | Tests passed per attempt | Median request time | Mean estimated token cost |
|---|---|---:|---|---:|---:|
| Default reasoning | `glm-5.3` | 3/3 | 17/17, 17/17, 17/17 | 19.34 s | $0.001007 |
| Default reasoning | `glm-5.3-uncensored` | 2/3 | 0/17, 17/17, 17/17 | 16.42 s | $0.002356 |
| Default reasoning | `glm-5.3-abliterated` | 0/3 | 0/17, 0/17, 0/17 | 40.69 s | $0.005625 |
| Low reasoning | `glm-5.3` | 3/3 | 17/17, 17/17, 17/17 | 5.52 s | $0.000306 |
| Low reasoning | `glm-5.3-uncensored` | 3/3 | 17/17, 17/17, 17/17 | 7.19 s | $0.002411 |
| Low reasoning | `glm-5.3-abliterated` | 3/3 | 17/17, 17/17, 17/17 | 3.31 s | $0.000894 |

A 0/17 entry with no returned code was not imported or executed. The first default-effort uncensored candidate failed to import because it used `Path` without importing it. That produced 17 setup errors. These are distinct failure modes, not measured refusal rates.

Costs are estimates from returned token usage and the rates saved with each request. They are not independently verified account charges. Reasoning tokens are already included in reported completion tokens and are not added a second time.

## Reproduce

The exact prompt is in `prompt.txt`. The original application and the 17 tests were fixed before collection. All attempts used the same submitted task, temperature 0, a 4,096-token output budget and non-streaming requests. The follow-up cohort adds `reasoning_effort=low` to every model. Neither failed outputs nor successful code were manually repaired.

Raw requests, responses and candidate hashes are under `results/2026-11-01` and `results/2026-11-01-low`. Each cohort's `sandbox` folder contains the actual pytest XML, stdout, errors and container results. The authored reference passed 17/17 in the same sandbox before candidate scoring.

The container has no network, runs as a non-root user, has a read-only root filesystem and candidate mount, drops capabilities, and limits CPU, memory, process count and writable temporary storage. The native environment, inputs and image IDs are recorded in the artifacts.

[Default cohort verification](https://github.com/routerhubSI/routerhub-model-evals/actions/runs/41264901102) and [low-effort cohort verification](https://github.com/routerhubSI/routerhub-model-evals/actions/runs/41264903396) ran without API keys. Paid collection happened only on the operator's workstation.

## Limits

This is one public toy task with three attempts per configuration. It is not a held-out coding benchmark, a security audit, or proof that fewer refusals improve quality. The task is benign and does not measure harmful-request compliance.

The hosted variants have unverified upstream checkpoint and wrapper provenance. Default-cohort input counts were 713 for standard, 14,213 for uncensored and 408 for abliterated despite identical submitted text. This suggests materially different serving paths or wrappers, but does not establish their implementation. Do not attribute the observed differences solely to weight editing.

Requests were collected with up to three concurrent workers. The first low-effort abliterated diagnostic was serial. Timings include the network and complete response, not time to first token or a controlled throughput measurement. Do not turn these numbers into a general speed guarantee.

The public suite does not cover upload races, symlink attacks or production denial-of-service behavior. For example, the first low-effort abliterated candidate checks existence before writing, which is not an atomic collision defense. Passing these tests does not make emitted code safe to deploy.

## Try or inspect

Read the public artifacts before choosing a model. Current RouterHub IDs, APIs and prices are on [Models and pricing](https://routerhub.si/models). That is a first-party commercial link, not an independent endorsement.
