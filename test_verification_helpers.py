import json
import subprocess
import sys
from pathlib import Path

import pytest

from live_api_verify import read_key, token_cost

ROOT = Path(__file__).resolve().parent


def test_reported_reasoning_tokens_are_not_billed_twice():
    usage = {
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "prompt_tokens_details": {"cached_tokens": 80},
        "completion_tokens_details": {"reasoning_tokens": 15},
    }
    prices = {"inputPrice": 2, "cachedInputPrice": 0.5, "outputPrice": 3}
    assert token_cost(usage, prices) == (20 * 2 + 80 * 0.5 + 20 * 3) / 1_000_000


def test_key_file_assignment_is_not_treated_as_the_key(tmp_path):
    source = tmp_path / "key.txt"
    source.write_text('ROUTERHUB_API_KEY="fake-example-key"\n', encoding="utf-8-sig")
    assert read_key(source) == "fake-example-key"


@pytest.mark.parametrize("script", ("live_api_verify.py", "verify_litellm_sdk.py", "verify_litellm_proxy.py"))
def test_verifiers_reject_paid_calls_before_reading_the_key(script, tmp_path):
    output = tmp_path / "output"
    arguments = [
        sys.executable,
        str(ROOT / script),
        "--key-file",
        str(tmp_path / "does-not-exist"),
        "--out",
        str(output),
    ]
    if script == "verify_litellm_proxy.py":
        arguments.extend(["--core", str(ROOT)])
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert "No request sent" in result.stderr
    assert not output.exists()


def test_low_effort_report_contains_all_three_attempts_per_model():
    summary = json.loads((ROOT / "results/2026-11-01-low/sandbox/summary.json").read_text())
    assert len(summary["results"]) == 9
    assert summary["authored_reference"]["passed"] == summary["authored_reference"]["total"] == 17
    for model in ("glm-5.3", "glm-5.3-uncensored", "glm-5.3-abliterated"):
        runs = [row for row in summary["results"] if row["requested_model"] == model]
        assert len(runs) == 3
        assert all(row["passed"] == row["total"] == 17 for row in runs)
