import re

from pathlib import Path

from flask import Flask, jsonify, request


MAX_CONTENT_LENGTH = 1_048_576 + 4096  # file limit + multipart overhead
MAX_FILE_SIZE = 1_048_576
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        if "file" not in request.files:
            return jsonify(error="missing file"), 400

        file = request.files["file"]
        filename = file.filename or ""

        if not NAME_RE.fullmatch(filename):
            return jsonify(error="invalid filename"), 400

        dot = filename.rfind(".")
        if dot == -1:
            return jsonify(error="missing extension"), 400
        ext = filename[dot + 1 :].lower()
        if ext not in ("txt", "csv"):
            return jsonify(error="disallowed extension"), 400

        target = upload_dir / filename
        if target.exists():
            return jsonify(error="file exists"), 409

        payload = file.read()
        if len(payload) > MAX_FILE_SIZE:
            return jsonify(error="file too large"), 413

        target.write_bytes(payload)
        return jsonify(filename=filename, size=len(payload)), 201

    return app
