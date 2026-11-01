import re
from pathlib import Path

from flask import Flask, jsonify, request

MAX_CONTENT_BYTES = 1_048_576
FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
ALLOWED_EXTENSIONS = {"txt", "csv"}
CHUNK_SIZE = 64 * 1024


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        if "file" not in request.files:
            return jsonify(error="missing file field"), 400

        file = request.files["file"]
        filename = file.filename or ""

        if not filename or not FILENAME_RE.fullmatch(filename):
            return jsonify(error="invalid filename"), 400

        extension = filename.rsplit(".", 1)[-1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            return jsonify(error="extension not allowed"), 400

        # Stream the file content only; multipart overhead is not counted.
        chunks = []
        total = 0
        while True:
            chunk = file.stream.read(CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_CONTENT_BYTES:
                return jsonify(error="file too large"), 413
            chunks.append(chunk)

        dest = upload_dir / filename
        try:
            with open(dest, "xb") as out:
                for chunk in chunks:
                    out.write(chunk)
        except FileExistsError:
            return jsonify(error="file already exists"), 409

        return jsonify(filename=filename, size=total), 201

    return app
