import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent
IMAGE = "routerhub-upload-bench"


def run(arguments, **kwargs):
    return subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True, **kwargs)


def evaluate(directory, output):
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    candidate = directory / "app.py"
    result = {
        "run": directory.name,
        "requested_model": metadata["requested_model"],
        "finish_reason": metadata.get("finish_reason"),
        "passed": 0,
        "total": 17,
        "candidate_executed": False,
    }
    output.mkdir(parents=True, exist_ok=False)
    if not candidate.exists() or not candidate.read_text(encoding="utf-8").strip():
        result["status"] = "no-code-returned"
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if digest != metadata["candidate_sha256"]:
        raise ValueError("Candidate hash does not match collected metadata")
    created = run(
        [
            "docker",
            "create",
            "--network",
            "none",
            "--read-only",
            "--user",
            "65534:65534",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--cpus",
            "1",
            "--memory",
            "512m",
            "--pids-limit",
            "64",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m,mode=1777",
            "--mount",
            f"type=bind,src={candidate.resolve()},dst=/candidate/app.py,readonly",
            IMAGE,
            "--app",
            "/candidate/app.py",
            "--junitxml=/tmp/report.xml",
            "-q",
        ],
        check=True,
    )
    container = created.stdout.strip()
    try:
        try:
            completed = run(["docker", "start", "--attach", container], timeout=90)
            result["candidate_executed"] = True
            (output / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
            (output / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
        except subprocess.TimeoutExpired:
            result.update(status="sandbox-timeout", candidate_executed=True)
            return result
        copied = run(["docker", "cp", container + ":/tmp/report.xml", str(output / "report.xml")])
        if copied.returncode != 0:
            result["status"] = "missing-test-report"
            return result
        report = output / "report.xml"
        if report.stat().st_size > 1024 * 1024:
            result["status"] = "oversized-test-report"
            return result
        cases = ElementTree.parse(report).findall(".//testcase")
        state = json.loads(run(["docker", "inspect", "--format", "{{json .State}}", container], check=True).stdout)
        failed = sum(case.find("failure") is not None for case in cases)
        errors = sum(case.find("error") is not None for case in cases)
        skipped = sum(case.find("skipped") is not None for case in cases)
        result.update(
            status="evaluated",
            total=len(cases),
            failed=failed,
            errors=errors,
            skipped=skipped,
            passed=len(cases) - failed - errors - skipped,
            candidate_sha256=digest,
            container_exit_code=state["ExitCode"],
        )
        if len(cases) != 17:
            result.update(status="invalid-test-count", passed=0)
        return result
    finally:
        run(["docker", "rm", "--force", container])
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluate collected candidates only in isolated Docker containers")
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Use a new report directory")
    directories = sorted(path for path in args.inputs.iterdir() if (path / "metadata.json").is_file())
    if not directories:
        parser.error("No collected runs found")
    run(["docker", "build", "--tag", IMAGE, "."], check=True, timeout=600)
    with tempfile.TemporaryDirectory(prefix="routerhub-trusted-fixture-") as temporary:
        fixture = Path(temporary)
        source = (ROOT / "reference/app.py").read_bytes()
        (fixture / "app.py").write_bytes(source)
        (fixture / "metadata.json").write_text(
            json.dumps(
                {
                    "requested_model": "authored-reference-not-a-model",
                    "candidate_sha256": hashlib.sha256(source).hexdigest(),
                }
            )
        )
        reference = evaluate(fixture, args.out / "authored-reference")
    if reference["passed"] != 17 or reference["total"] != 17:
        raise SystemExit("Trusted reference failed in this sandbox. Candidate scores are not valid")
    results = [evaluate(directory, args.out / directory.name) for directory in directories]
    summary = {
        "sandbox": "Docker, no network, non-root, read-only, resource-limited",
        "benchmark_commit": run(["git", "rev-parse", "HEAD"], check=True).stdout.strip(),
        "image_id": run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], check=True).stdout.strip(),
        "authored_reference": reference,
        "results": results,
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
