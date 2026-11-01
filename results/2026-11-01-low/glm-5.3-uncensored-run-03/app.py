from pathlib import Path
import re

from flask import Flask, jsonify, request

MAX_CONTENT_BYTES = 1_048_576
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
ALLOWED_EXTS = {".txt", ".csv"}


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_BYTES + 64 * 1024  # content limit + multipart overhead
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        file = request.files.get("file")
        if file is None:
            return jsonify(error="missing file"), 400

        filename = file.filename or ""
        if not NAME_RE.match(filename):
            return jsonify(error="invalid filename"), 400

        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTS:
            return jsonify(error="invalid extension"), 400

        payload = file.read(MAX_CONTENT_BYTES + 1)
        if len(payload) > MAX_CONTENT_BYTES:
            return jsonify(error="file too large"), 413

        dest = (upload_dir / filename).resolve()
        if dest.parent != upload_dir.resolve():
            return jsonify(error="invalid filename"), 400
        if dest.exists():
            return jsonify(error="file exists"), 409

        dest.write_bytes(payload)
        return jsonify(filename=filename, size=len(payload)), 201

    return app
