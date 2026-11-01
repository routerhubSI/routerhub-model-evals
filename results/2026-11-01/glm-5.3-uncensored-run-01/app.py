import re

from flask import Flask, jsonify, request

MAX_CONTENT_BYTES = 1_048_576  # 1 MiB, exact size allowed
MAX_FILENAME_LEN = 100
ALLOWED_EXTENSIONS = {".txt", ".csv"}

# Simple ASCII names only: start with letter/digit, then letters, digits,
# underscore, dot or hyphen. No separators, no absolute paths, no leading dot.
FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _bad_request(message: str):
    return jsonify(error=message), 400


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        file = request.files.get("file")
        if file is None:
            return _bad_request("missing file field")

        filename = file.filename or ""
        if not filename:
            return _bad_request("empty filename")
        if len(filename) > MAX_FILENAME_LEN:
            return _bad_request("filename too long")
        if not FILENAME_RE.match(filename):
            return _bad_request(
                "invalid filename: must be simple ASCII "
                "(letters, digits, underscore, dot, hyphen), "
                "starting with a letter or digit"
            )

        if "." not in filename or Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
            return _bad_request("only .txt and .csv files are accepted")

        # Read at most one byte past the limit to detect overflow without
        # buffering unbounded data. Multipart framing overhead is consumed
        # by the parser and never counted against this content limit.
        data = file.stream.read(MAX_CONTENT_BYTES + 1)
        if len(data) > MAX_CONTENT_BYTES:
            return jsonify(error="file too large"), 413

        dest = upload_dir / filename
        # Defense in depth: regex already forbids separators, but assert the
        # destination stays inside upload_dir.
        if dest.resolve().parent != upload_dir.resolve():
            return _bad_request("invalid destination")

        # Exclusive create: never overwrite an existing file.
        try:
            with open(dest, "xb") as out:
                out.write(data)
        except FileExistsError:
            return jsonify(error="file already exists"), 409

        return jsonify(filename=filename, size=len(data)), 201

    return app
