import re

from pathlib import Path

from flask import Flask, jsonify, request


MAX_CONTENT_LENGTH = 1_048_576
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
ALLOWED_EXTENSIONS = {".txt", ".csv"}


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH + 64 * 1024
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        if "file" not in request.files:
            return jsonify(error="missing file"), 400

        file = request.files["file"]
        filename = file.filename or ""

        if not NAME_RE.match(filename):
            return jsonify(error="invalid filename"), 400

        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            return jsonify(error="invalid extension"), 400

        payload = file.read()
        if len(payload) > MAX_CONTENT_LENGTH:
            return jsonify(error="file too large"), 413

        destination = upload_dir / filename
        try:
            with open(destination, "xb") as out:
                out.write(payload)
        except FileExistsError:
            return jsonify(error="filename already exists"), 409

        return jsonify(filename=filename, size=len(payload)), 201

    return app
