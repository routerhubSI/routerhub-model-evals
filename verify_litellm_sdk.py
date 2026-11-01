import argparse
import hashlib
import json
import os
import subprocess
import time
from math import isclose
from pathlib import Path

from live_api_verify import read_key


def main():
    parser = argparse.ArgumentParser(description="Verify the checked-out LiteLLM provider with small paid requests")
    parser.add_argument("--key-file", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--allow-paid", action="store_true")
    args = parser.parse_args()
    if not args.allow_paid:
        parser.error("No request sent. Explicit --allow-paid is required")
    if args.out.exists():
        parser.error("Use a new output directory")
    key = read_key(args.key_file)
    os.environ["ROUTERHUB_API_KEY"] = key
    os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    import litellm

    source = Path(litellm.__file__).resolve().parents[1]
    prices = json.loads((source / "model_prices_and_context_window.json").read_text())
    results = []
    for model in ("glm-5.3-abliterated", "glm-5.3-flash-abliterated"):
        for streaming in (False, True):
            messages = [{"role": "user", "content": "Reply with exactly OK."}]
            options = {"stream_options": {"include_usage": True}} if streaming else {}
            started = time.perf_counter()
            response = litellm.completion(
                model="routerhub/" + model,
                messages=messages,
                max_tokens=256,
                stream=streaming,
                num_retries=0,
                timeout=180,
                **options,
            )
            if streaming:
                chunks = list(response)
                final = litellm.stream_chunk_builder(chunks, messages=messages)
            else:
                final = response
            elapsed = time.perf_counter() - started
            usage = final.usage.model_dump(exclude_none=True)
            rates = prices["routerhub/" + model]
            cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
            expected = (
                (usage["prompt_tokens"] - cached) * rates["input_cost_per_token"]
                + cached * rates["cache_read_input_token_cost"]
                + usage["completion_tokens"] * rates["output_cost_per_token"]
            )
            cost = litellm.completion_cost(completion_response=final)
            text = final.choices[0].message.content or ""
            result = {
                "model": model,
                "streaming": streaming,
                "reply": text,
                "finish_reason": final.choices[0].finish_reason,
                "usage": usage,
                "request_elapsed_seconds": elapsed,
                "litellm_calculated_cost_usd": cost,
                "expected_token_cost_usd": expected,
                "cost_matches": isclose(cost, expected, rel_tol=1e-9, abs_tol=1e-12),
                "actual_account_charge_verified": False,
            }
            result["passed"] = text.strip() == "OK" and result["cost_matches"] and result["finish_reason"] == "stop"
            results.append(result)
    native = next(path for path in (source / "litellm/rust_bridge").glob("_native.*") if path.suffix in {".pyd", ".so"})
    summary = {
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip(),
        "native_sha256": hashlib.sha256(native.read_bytes()).hexdigest(),
        "scope": "Actual checked-out LiteLLM SDK and RouterHub API, not mocks",
        "results": results,
    }
    encoded = json.dumps(summary, indent=2) + "\n"
    if key in encoded:
        raise ValueError("Credential detected. Artifact was not saved")
    args.out.mkdir(parents=True)
    (args.out / "summary.json").write_text(encoded, encoding="utf-8")
    print(json.dumps({"checks": len(results), "passed": sum(result["passed"] for result in results)}))
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
