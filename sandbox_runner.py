import json
import subprocess
import sys
from pathlib import Path


def main():
    report = Path("/tmp/report.xml")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "/bench/tests",
                "-p",
                "no:cacheprovider",
                "--basetemp",
                "/tmp/pytest",
                "--junitxml=" + str(report),
                *sys.argv[1:],
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        print(json.dumps({"status": "test-timeout", "return_code": 124}))
        return 124
    xml = report.read_text() if report.exists() and report.stat().st_size <= 1024 * 1024 else None
    print(
        json.dumps(
            {
                "status": "finished",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "report_xml": xml,
            }
        )
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
