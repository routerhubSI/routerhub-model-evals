import re
from pathlib import Path

from flask import Flask, jsonify, request

MAX_CONTENT_BYTES = 1_048_576
ALLOWED_EXTENSIONS = {".txt", ".csv"}
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_BYTES + 64 * 1024  # content + multipart overhead
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify(error="file too large"), 413

    @app.post("/upload")
    def upload():
        file = request.files.get("file")
        if file is None:
            return jsonify(error="missing file"), 400

        filename = file.filename or ""

        if (
            not filename
            or "/" in filename
            or "\\" in filename
            or filename.startswith(".")
            or Path(filename).is_absolute()
            or Path(filename).name != filename
            or not NAME_RE.match(filename)
        ):
            return jsonify(error="invalid filename"), 400

        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify(error="invalid extension"), 400

        target = upload_dir / filename
        if target.exists():
            return jsonify(error="file exists"), 409

        payload = file.stream.read(MAX_CONTENT_BYTES + 1)
        if len(payload) > MAX_CONTENT_BYTES:
            return jsonify(error="file too large"), 413

        target.write_bytes(payload)
        return jsonify(filename=filename, size=len(payload)), 201

    return app
