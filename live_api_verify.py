import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from collect import CATALOGUE_URL, USER_AGENT, read_json

ENDPOINT = "https://routerhub.si/v1/chat/completions"
MODELS = ("glm-5.3-abliterated", "glm-5.3-flash-abliterated")


def read_key(path):
    key = path.read_text(encoding="utf-8-sig").strip()
    if key.startswith("ROUTERHUB_API_KEY="):
        key = key.split("=", 1)[1].strip().strip("\"'")
    if not key or "\n" in key or "\r" in key:
        raise ValueError("Credential file must contain one key. Contents withheld")
    return key


def token_cost(usage, model):
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    return (
        (usage["prompt_tokens"] - cached) * model["inputPrice"]
        + cached * model["cachedInputPrice"]
        + usage["completion_tokens"] * model["outputPrice"]
    ) / 1_000_000


def verify(key, model, streaming, output):
    body = {
        "model": model["id"],
        "messages": [{"role": "user", "content": "Reply with exactly OK."}],
        "max_tokens": 256,
        "stream": streaming,
    }
    if streaming:
        body["stream_options"] = {"include_usage": True}
    request = Request(
        ENDPOINT,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    started = time.perf_counter()
    with urlopen(request, timeout=180) as response:
        status = response.status
        raw = response.read().decode("utf-8")
    if key in raw:
        raise ValueError("Response contained a credential. It was not saved")
    elapsed = time.perf_counter() - started
    output.mkdir(parents=True)
    (output / "request.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    if streaming:
        (output / "response.sse").write_text(raw, encoding="utf-8")
        chunks = [
            json.loads(line[5:].strip())
            for line in raw.splitlines()
            if line.startswith("data:") and line[5:].strip() != "[DONE]"
        ]
        text = "".join(
            (choice.get("delta") or {}).get("content") or "" for chunk in chunks for choice in chunk.get("choices", [])
        )
        reported = [chunk["usage"] for chunk in chunks if chunk.get("usage")]
        usage = reported[-1] if reported else None
        finished = any(choice.get("finish_reason") == "stop" for chunk in chunks for choice in chunk.get("choices", []))
        data = {"chunks": len(chunks), "done_marker": "data: [DONE]" in raw}
    else:
        data = json.loads(raw)
        (output / "response.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        text = data["choices"][0]["message"].get("content") or ""
        usage = data.get("usage")
        finished = data["choices"][0].get("finish_reason") == "stop"
    result = {
        "model": model["id"],
        "streaming": streaming,
        "http_status": status,
        "reply": text,
        "finished": finished,
        "usage": usage,
        "elapsed_seconds": elapsed,
        "estimated_token_cost_usd": token_cost(usage, model) if usage else None,
        "billing_verified": False,
        "passed": status == 200 and text.strip() == "OK" and finished and bool(usage),
        "stream_details": data if streaming else None,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description="Small paid RouterHub API checks with redacted artifacts")
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--allow-paid", action="store_true")
    args = parser.parse_args()
    if not args.allow_paid:
        parser.error("No request sent. Explicit --allow-paid is required")
    if args.out.exists():
        parser.error("Use a new output directory")
    key = read_key(args.key_file)
    catalogue = read_json(CATALOGUE_URL)
    models = {model["id"]: model for model in catalogue["models"]}
    results = []
    for model in MODELS:
        for streaming in (False, True):
            name = model + ("-stream" if streaming else "-normal")
            try:
                result = verify(key, models[model], streaming, args.out / name)
            except (HTTPError, URLError, TimeoutError, ValueError) as error:
                result = {"model": model, "streaming": streaming, "passed": False, "error_class": type(error).__name__}
            results.append(result)
            print(json.dumps({field: result.get(field) for field in ("model", "streaming", "passed", "http_status")}))
    summary = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Direct HTTP only, not LiteLLM SDK or proxy proof",
        "credentials_published": False,
        "actual_account_charge_verified": False,
        "results": results,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
