import argparse
import json
import os
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
from math import isclose
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from live_api_verify import read_key


def main():
    parser = argparse.ArgumentParser(description="Verify a loopback-only LiteLLM proxy with small paid requests")
    parser.add_argument("--key-file", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--core", required=True, type=Path)
    parser.add_argument("--allow-paid", action="store_true")
    args = parser.parse_args()
    if not args.allow_paid:
        parser.error("No request sent. Explicit --allow-paid is required")
    if args.out.exists():
        parser.error("Use a new output directory")
    core = args.core.resolve()
    key = read_key(args.key_file)
    master = "sk-" + secrets.token_hex(32)
    prices = json.loads((core / "model_prices_and_context_window.json").read_text())
    models = {"routerhub-glm": "glm-5.3-abliterated", "routerhub-flash": "glm-5.3-flash-abliterated"}
    config = {
        "model_list": [
            {
                "model_name": alias,
                "litellm_params": {"model": "routerhub/" + model, "api_key": "os.environ/ROUTERHUB_API_KEY"},
            }
            for alias, model in models.items()
        ],
        "general_settings": {"master_key": "os.environ/LITELLM_MASTER_KEY"},
        "router_settings": {"num_retries": 0},
    }
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    allowed = {
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "COMSPEC",
        "USERPROFILE",
        "HOME",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMDATA",
        "PATHEXT",
    }
    environment = {name: value for name, value in os.environ.items() if name.upper() in allowed}
    environment.update(
        ROUTERHUB_API_KEY=key,
        LITELLM_MASTER_KEY=master,
        PYTHONPATH=str(core),
        LITELLM_LOCAL_MODEL_COST_MAP="True",
        PYTHON_DOTENV_DISABLED="1",
        PYTHONUTF8="1",
        PYTHONIOENCODING="utf-8",
        DO_NOT_TRACK="1",
        CUSTOM_TIKTOKEN_CACHE_DIR=os.environ.get("CUSTOM_TIKTOKEN_CACHE_DIR", ""),
    )
    args.out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="routerhub-proxy-") as temporary:
        directory = Path(temporary)
        configuration = directory / "config.yaml"
        configuration.write_text(json.dumps(config, indent=2))
        command = [
            sys.executable,
            str(core / "litellm/proxy/proxy_cli.py"),
            "--config",
            str(configuration),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--num_workers",
            "2",
            "--detailed_debug",
            "--reload",
            "--use_v2_migration_resolver",
        ]
        with (directory / "server.log").open("w", encoding="utf-8") as log:
            server = subprocess.Popen(
                command, cwd=core, env=environment, stdout=log, stderr=log, start_new_session=os.name != "nt"
            )
            try:
                ready = False
                for _ in range(120):
                    if server.poll() is not None:
                        break
                    try:
                        with urlopen(f"http://127.0.0.1:{port}/health/liveliness", timeout=1) as health:
                            ready = health.status == 200
                    except (URLError, TimeoutError):
                        pass
                    if ready:
                        break
                    time.sleep(0.25)
                if not ready:
                    raise RuntimeError("The local proxy did not start. Inspect the redacted startup log")
                results = []
                for alias, model in models.items():
                    for streaming in (False, True):
                        body = {
                            "model": alias,
                            "messages": [{"role": "user", "content": "Reply with exactly OK."}],
                            "max_tokens": 256,
                            "stream": streaming,
                        }
                        if streaming:
                            body["stream_options"] = {"include_usage": True}
                        request = Request(
                            f"http://127.0.0.1:{port}/v1/chat/completions",
                            data=json.dumps(body).encode(),
                            headers={"Authorization": "Bearer " + master, "Content-Type": "application/json"},
                        )
                        started = time.perf_counter()
                        with urlopen(request, timeout=180) as response:
                            raw = response.read().decode()
                            cost_header = response.headers.get("x-litellm-response-cost")
                        if key in raw or master in raw:
                            raise ValueError("Credential detected in response. Artifact withheld")
                        output = args.out / (alias + ("-stream" if streaming else "-normal"))
                        output.mkdir()
                        (output / "request.json").write_text(json.dumps(body, indent=2) + "\n")
                        (output / ("response.sse" if streaming else "response.json")).write_text(raw, encoding="utf-8")
                        if streaming:
                            chunks = [
                                json.loads(line[5:].strip())
                                for line in raw.splitlines()
                                if line.startswith("data:") and line[5:].strip() != "[DONE]"
                            ]
                            text = "".join(
                                (choice.get("delta") or {}).get("content") or ""
                                for chunk in chunks
                                for choice in chunk.get("choices", [])
                            )
                            usage = next(chunk["usage"] for chunk in reversed(chunks) if chunk.get("usage"))
                            measured = usage.get("cost")
                        else:
                            parsed = json.loads(raw)
                            text = parsed["choices"][0]["message"]["content"]
                            usage = parsed["usage"]
                            measured = float(cost_header) if cost_header is not None else None
                        cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
                        rate = prices["routerhub/" + model]
                        expected = (
                            (usage["prompt_tokens"] - cached) * rate["input_cost_per_token"]
                            + cached * rate["cache_read_input_token_cost"]
                            + usage["completion_tokens"] * rate["output_cost_per_token"]
                        )
                        matched = measured is not None and isclose(measured, expected, rel_tol=1e-9, abs_tol=1e-12)
                        result = {
                            "model": model,
                            "streaming": streaming,
                            "reply": text,
                            "usage": usage,
                            "elapsed_seconds": time.perf_counter() - started,
                            "proxy_cost_usd": measured,
                            "expected_token_cost_usd": expected,
                            "cost_matches": matched,
                            "actual_account_charge_verified": False,
                            "passed": text.strip() == "OK" and matched,
                        }
                        results.append(result)
                summary = {
                    "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=core, text=True).strip(),
                    "scope": "Real loopback proxy and RouterHub API",
                    "redis": "Not configured, provider routing and pricing only",
                    "worker_note": "Two workers requested with reload. Windows reload can reduce the actual worker count. No concurrency claim",
                    "results": results,
                }
                encoded = json.dumps(summary, indent=2) + "\n"
                if key in encoded or master in encoded:
                    raise ValueError("Credential detected. Summary withheld")
                (args.out / "summary.json").write_text(encoded)
                (args.out / "config.yaml").write_text(json.dumps(config, indent=2))
                print(json.dumps({"checks": len(results), "passed": sum(result["passed"] for result in results)}))
                return 0 if all(result["passed"] for result in results) else 1
            finally:
                if server.poll() is None:
                    if os.name == "nt":
                        subprocess.run(["taskkill", "/PID", str(server.pid), "/T", "/F"], capture_output=True)
                    else:
                        os.killpg(server.pid, signal.SIGTERM)
                server.wait(timeout=20)
                log.flush()
                sanitized = (
                    (directory / "server.log")
                    .read_text(encoding="utf-8", errors="replace")
                    .replace(key, "[REDACTED]")
                    .replace(master, "[REDACTED]")
                )
                (args.out / "startup-redacted.log").write_text(sanitized, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
