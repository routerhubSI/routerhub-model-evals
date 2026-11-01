import re
from pathlib import Path

from flask import Flask, jsonify, request

MAX_CONTENT = 1_048_576
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
ALLOWED_EXTS = {".txt", ".csv"}


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT + 64 * 1024  # overhead margin
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        if "file" not in request.files:
            return jsonify(error="missing file"), 400

        file = request.files["file"]
        filename = file.filename or ""

        if not NAME_RE.fullmatch(filename):
            return jsonify(error="invalid filename"), 400

        if Path(filename).suffix.lower() not in ALLOWED_EXTS:
            return jsonify(error="invalid extension"), 400

        dest = upload_dir / filename
        if dest.exists():
            return jsonify(error="file exists"), 409

        payload = file.stream.read(MAX_CONTENT + 1)
        if len(payload) > MAX_CONTENT:
            return jsonify(error="file too large"), 413

        dest.write_bytes(payload)
        return jsonify(filename=filename, size=len(payload)), 201

    @app.errorhandler(413)
    def too_large(e):
        return jsonify(error="file too large"), 413

    return app
