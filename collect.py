import argparse
import ast
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CATALOGUE_URL = "https://routerhub.si/models.json"
REQUEST_URL = "https://routerhub.si/v1/chat/completions"
USER_AGENT = "RouterHub-model-evals/0.1 (+https://github.com/routerhubSI/routerhub-model-evals)"


def candidate_source(content: str) -> str | None:
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", content, flags=re.DOTALL)
    if len(blocks) > 1:
        return None
    source = blocks[0] if blocks else content
    try:
        ast.parse(source)
    except SyntaxError:
        return None
    return source.rstrip() + "\n"


def read_json(request: Request | str, timeout: int = 60):
    prepared = (
        Request(request, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
        if isinstance(request, str)
        else request
    )
    with urlopen(prepared, timeout=timeout) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect one paid model response without executing generated code")
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--allow-paid", action="store_true")
    args = parser.parse_args()
    if not args.allow_paid:
        parser.error("No request sent. Pass --allow-paid only after approving credit use")
    if not 1 <= args.max_tokens <= 8192:
        parser.error("--max-tokens must be between 1 and 8192")
    if args.out.exists():
        parser.error("Output directory already exists. Use a new directory for each attempt")
    key = os.environ.get("ROUTERHUB_API_KEY")
    if not key:
        parser.error("Set ROUTERHUB_API_KEY privately in this terminal")
    try:
        catalogue = read_json(CATALOGUE_URL)
    except (HTTPError, URLError, TimeoutError):
        parser.error("Cannot read the public catalogue. No inference request sent")
    matches = [entry for entry in catalogue["models"] if entry["id"] == args.model]
    if len(matches) != 1 or "chat" not in matches[0]["protocols"]:
        parser.error("Choose an exact Chat Completions model ID from the current catalogue")
    instructions = (ROOT / "prompt.txt").read_text(encoding="utf-8")
    original = (ROOT / "fixtures/vulnerable/app.py").read_text(encoding="utf-8")
    body = {
        "model": args.model,
        "messages": [{"role": "user", "content": instructions + "\nOriginal app.py\n```python\n" + original + "```"}],
        "max_tokens": args.max_tokens,
        "temperature": 0,
        "stream": False,
    }
    args.out.mkdir(parents=True)
    (args.out / "request.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    request = Request(
        REQUEST_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    started = time.perf_counter()
    try:
        response = read_json(request, timeout=300)
    except (HTTPError, URLError, TimeoutError) as error:
        failure = {"status": "request-failed", "error_class": type(error).__name__, "retry_performed": False}
        (args.out / "metadata.json").write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        print("Request failed. No retry performed. Check provider usage before retrying")
        return 1
    elapsed = time.perf_counter() - started
    (args.out / "response.json").write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
    choices = response.get("choices", [])
    message = choices[0].get("message", {}) if choices else {}
    content = message.get("content")
    source = candidate_source(content) if isinstance(content, str) else None
    if source is not None:
        (args.out / "app.py").write_text(source, encoding="utf-8")
    metadata = {
        "status": "collected-not-executed",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "requested_model": args.model,
        "returned_model": response.get("model"),
        "request_elapsed_seconds": elapsed,
        "finish_reason": choices[0].get("finish_reason") if choices else None,
        "usage": response.get("usage"),
        "published_catalogue_entry": matches[0],
        "billing": "Record actual provider charges separately. Elapsed time is not tokens per second",
        "original_app_sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
        "prompt_sha256": hashlib.sha256(instructions.encode("utf-8")).hexdigest(),
        "candidate_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest() if source is not None else None,
        "candidate_executed": False,
        "tests_passed": None,
    }
    (args.out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Saved response to {args.out}. No generated code was executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
