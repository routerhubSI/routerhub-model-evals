import json
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent


def fixture_check(app: str, report: Path):
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "--app", app, "-q", "--tb=no", f"--junitxml={report}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if not report.exists():
        raise RuntimeError("Test collection did not produce a report\n" + result.stdout + result.stderr)
    cases = ElementTree.parse(report).findall(".//testcase")
    failures = sum(case.find("failure") is not None for case in cases)
    errors = sum(case.find("error") is not None for case in cases)
    skipped = sum(case.find("skipped") is not None for case in cases)
    return {
        "total": len(cases),
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
        "exit_code": result.returncode,
    }


def main():
    with tempfile.TemporaryDirectory(prefix="routerhub-fixture-check-") as temporary:
        directory = Path(temporary)
        baseline = fixture_check("fixtures/vulnerable/app.py", directory / "baseline.xml")
        reference = fixture_check("reference/app.py", directory / "reference.xml")
    expected_baseline = {"total": 17, "failed": 12, "errors": 0, "skipped": 0, "exit_code": 1}
    expected_reference = {"total": 17, "failed": 0, "errors": 0, "skipped": 0, "exit_code": 0}
    collector = subprocess.run(
        [sys.executable, "-m", "pytest", "test_collector.py", "test_verification_helpers.py", "-q"],
        cwd=ROOT,
        check=False,
    )
    print(json.dumps({"authored_fixtures_only": True, "baseline": baseline, "reference": reference}, indent=2))
    return 0 if baseline == expected_baseline and reference == expected_reference and collector.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
