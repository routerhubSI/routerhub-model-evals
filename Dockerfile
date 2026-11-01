FROM python:3.13.14-slim@sha256:9662417aace5ae7b8e2609cce472b72a8958e134ba372808abe9cc1a0c0125e6
WORKDIR /bench
COPY requirements.txt /bench/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY tests /bench/tests
ENV PYTHONDONTWRITEBYTECODE=1
USER 65534:65534
ENTRYPOINT ["python", "-m", "pytest", "/bench/tests", "-p", "no:cacheprovider", "--basetemp", "/tmp/pytest"]
