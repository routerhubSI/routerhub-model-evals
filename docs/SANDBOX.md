# Candidate isolation

This is a proposed Docker runbook, not a claim that arbitrary code is safe inside
a container. Docker is not installed on the development workstation, so this
procedure still needs verification before model candidates are evaluated.

Use a dedicated, disposable Linux VM with an updated container runtime. Build the
test image from the trusted benchmark commit before collecting any model output.
The included Dockerfile pins Python 3.13.14 slim by the official registry's image
digest, checked on November 1, 2026. Build it with
`docker build --tag routerhub-upload-bench .` from this repository. Dependencies
are installed during the build, never at candidate runtime. The build context
excludes results, credentials and candidate implementations.

Copy only the selected generated `app.py` to an otherwise empty candidate folder.
Keep the paid inference collection outside this VM. Do not transfer API keys,
cloud credentials or private files into the sandbox.

Example invocation for Bash on the disposable VM, after building and verifying
an image named `routerhub-upload-bench` with the above contents.

```sh
docker run --rm --network none --read-only \
  --user 65534:65534 --cap-drop ALL \
  --security-opt no-new-privileges \
  --cpus 1 --memory 512m --pids-limit 64 \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m,mode=1777 \
  --mount "type=bind,src=$PWD/candidate,dst=/candidate,readonly" \
  -e PYTHONDONTWRITEBYTECODE=1 \
  routerhub-upload-bench --app /candidate/app.py -q
```

The mount exposes only the single-candidate folder, not the repository or home
directory. Use an external supervisor to impose a wall-clock timeout and kill a
stalled container. Store the test output and exit status outside the container.
Apply the same sandbox and resource limits to every candidate and reference run.
The candidate can still inspect the tests, and these are public acceptance tests,
not a held-out general coding benchmark. Do not treat passing them as proof of
security, harmlessness or general superiority.
