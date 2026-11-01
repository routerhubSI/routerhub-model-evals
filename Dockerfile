FROM python:3.13.14-slim@sha256:9662417aace5ae7b8e2609cce472b72a8958e134ba372808abe9cc1a0c0125e6
WORKDIR /bench
COPY requirements.lock /bench/requirements.lock
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.lock
COPY tests /bench/tests
COPY sandbox_runner.py /bench/sandbox_runner.py
ENV PYTHONDONTWRITEBYTECODE=1
USER 65534:65534
ENTRYPOINT ["python", "/bench/sandbox_runner.py"]
