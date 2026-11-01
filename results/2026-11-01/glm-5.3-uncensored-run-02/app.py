import re
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request

FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
ALLOWED_EXTENSIONS = {".txt", ".csv"}
MAX_CONTENT_BYTES = 1_048_576
CHUNK = 64 * 1024


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        if "file" not in request.files:
            return jsonify(error="missing file"), 400

        file = request.files["file"]
        filename = (file.filename or "").strip()

        if not filename:
            return jsonify(error="empty filename"), 400
        if not filename.isascii():
            return jsonify(error="filename must be ASCII"), 400
        if len(filename) > 100:
            return jsonify(error="filename too long"), 400
        if "/" in filename or "\\" in filename or Path(filename).name != filename:
            return jsonify(error="path separators not allowed"), 400
        if not FILENAME_RE.fullmatch(filename):
            return jsonify(error="invalid filename"), 400
        if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
            return jsonify(error="only .txt and .csv allowed"), 400

        target = upload_dir / filename
        size = 0
        try:
            with tempfile.SpooledTemporaryFile(max_size=MAX_CONTENT_BYTES) as buf:
                while True:
                    chunk = file.stream.read(CHUNK)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_CONTENT_BYTES:
                        return jsonify(error="file too large"), 413
                    buf.write(chunk)
                buf.seek(0)
                # "xb" fails if the file exists -> no overwrite
                with open(target, "xb") as out:
                    while True:
                        chunk = buf.read(CHUNK)
                        if not chunk:
                            break
                        out.write(chunk)
        except FileExistsError:
            return jsonify(error="filename already exists"), 409

        return jsonify(filename=filename, size=size), 201

    return app
