import re
from pathlib import Path

from flask import Flask, jsonify, request

MAX_FILE_BYTES = 1024 * 1024
FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z")
EXTENSIONS = frozenset({".txt", ".csv"})


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_BYTES + 64 * 1024
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        file = request.files.get("file")
        if file is None:
            return jsonify(error="missing file"), 400
        filename = file.filename or ""
        if FILENAME.fullmatch(filename) is None:
            return jsonify(error="invalid filename"), 400
        if Path(filename).suffix.lower() not in EXTENSIONS:
            return jsonify(error="unsupported extension"), 400
        payload = file.stream.read(MAX_FILE_BYTES + 1)
        if len(payload) > MAX_FILE_BYTES:
            return jsonify(error="file too large"), 413
        try:
            with (upload_dir / filename).open("xb") as destination:
                destination.write(payload)
        except FileExistsError:
            return jsonify(error="file already exists"), 409
        return jsonify(filename=filename, size=len(payload)), 201

    return app
