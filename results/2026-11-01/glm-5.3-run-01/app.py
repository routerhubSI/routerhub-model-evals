import re
from pathlib import Path

from flask import Flask, jsonify, request

MAX_FILENAME_LENGTH = 100
MAX_CONTENT_BYTES = 1_048_576  # 1 MiB of file content; multipart framing excluded
ALLOWED_EXTENSIONS = {".txt", ".csv"}
FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        file = request.files.get("file")
        if file is None:
            return jsonify(error="missing file part named 'file'"), 400

        filename = file.filename or ""

        if not filename:
            return jsonify(error="filename must not be empty"), 400
        if len(filename) > MAX_FILENAME_LENGTH:
            return jsonify(error="filename exceeds 100 characters"), 400
        if not FILENAME_PATTERN.fullmatch(filename):
            return jsonify(
                error="filename must be ASCII, start with a letter or digit, "
                "and contain only letters, digits, underscores, dots or hyphens"
            ), 400

        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if f".{extension}" not in ALLOWED_EXTENSIONS:
            return jsonify(error="only .txt and .csv files are allowed"), 400

        chunks = []
        total = 0
        while True:
            chunk = file.stream.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_CONTENT_BYTES:
                return jsonify(
                    error=f"file exceeds {MAX_CONTENT_BYTES} byte limit"
                ), 413
            chunks.append(chunk)
        payload = b"".join(chunks)

        # upload_dir is a Path and filename contains no separators or "..",
        # so the resolved target cannot escape upload_dir.
        target = upload_dir / filename
        try:
            with open(target, "xb") as destination:
                destination.write(payload)
        except FileExistsError:
            return jsonify(error="filename already exists"), 409

        return jsonify(filename=filename, size=total), 201

    return app
