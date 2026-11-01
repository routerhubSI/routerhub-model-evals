import re
from pathlib import Path

from flask import Flask, jsonify, request

FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
ALLOWED_EXTENSIONS = {".txt", ".csv"}
MAX_CONTENT_BYTES = 1_048_576


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        file = request.files.get("file")
        if file is None:
            return jsonify(error="missing file"), 400

        filename = file.filename or ""

        if not filename:
            return jsonify(error="empty filename"), 400
        if "/" in filename or "\\" in filename:
            return jsonify(error="paths not allowed"), 400
        if filename.startswith("."):
            return jsonify(error="leading dot not allowed"), 400
        if Path(filename).is_absolute():
            return jsonify(error="absolute path not allowed"), 400
        if not FILENAME_RE.match(filename):
            return jsonify(error="invalid filename"), 400

        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            return jsonify(error="extension not allowed"), 400

        payload = file.read(MAX_CONTENT_BYTES + 1)
        if len(payload) > MAX_CONTENT_BYTES:
            return jsonify(error="file too large"), 413

        destination = upload_dir / filename
        if destination.exists():
            return jsonify(error="file already exists"), 409

        destination.write_bytes(payload)
        return jsonify(filename=filename, size=len(payload)), 201

    return app
