import ast
import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from collect import USER_AGENT, candidate_source, read_json

ROOT = Path(__file__).resolve().parent


def test_single_python_block_is_saved_without_executing():
    source = "raise RuntimeError('must never run')\n"
    assert candidate_source("Explanation\n```python\n" + source + "```\n") == source


def test_multiple_blocks_are_not_silently_combined():
    assert candidate_source("```python\nx = 1\n```\n```python\nx = 2\n```") is None


def test_refusal_text_does_not_become_a_candidate():
    assert candidate_source("I cannot provide that implementation.") is None


def test_empty_completion_is_not_a_python_candidate():
    assert candidate_source("") is None
    assert candidate_source("```python\n\n```") is None


def test_plain_valid_python_remains_unexecuted():
    source = candidate_source("import os\nos.remove('DO_NOT_RUN')\n")
    assert source is not None
    assert isinstance(ast.parse(source), ast.Module)


def test_paid_opt_in_is_required_before_network_or_output(tmp_path):
    output = tmp_path / "run"
    result = subprocess.run(
        [sys.executable, str(ROOT / "collect.py"), "--model", "glm-5.3-abliterated", "--out", str(output)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert "No request sent" in result.stderr
    assert not output.exists()


def test_public_catalogue_request_identifies_client_without_credentials():
    with patch("collect.urlopen") as transport:
        transport.return_value.__enter__.return_value = io.StringIO('{"models": []}')
        assert read_json("https://routerhub.si/models.json") == {"models": []}
    request = transport.call_args.args[0]
    assert request.get_header("User-agent") == USER_AGENT
    assert request.get_header("Accept") == "application/json"
    assert request.get_header("Authorization") is None
