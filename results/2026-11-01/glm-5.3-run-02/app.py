import re
from pathlib import Path

from flask import Flask, jsonify, request

MAX_CONTENT_BYTES = 1_048_576  # 1 MiB file-content limit
FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
ALLOWED_EXTENSIONS = (".txt", ".csv")


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        file = request.files.get("file")
        if file is None:
            return jsonify(error="missing file field"), 400

        filename = file.filename or ""
        if not FILENAME_RE.fullmatch(filename):
            return jsonify(error="invalid filename"), 400
        if not filename.lower().endswith(ALLOWED_EXTENSIONS):
            return jsonify(error="invalid extension"), 400

        # Read at most limit+1 bytes from the decoded file part, so
        # multipart framing overhead never counts against the limit.
        payload = file.stream.read(MAX_CONTENT_BYTES + 1)
        if len(payload) > MAX_CONTENT_BYTES:
            return jsonify(error="file too large"), 413

        # Regex forbids separators, so the target stays inside upload_dir.
        # "xb" fails atomically on collision; nothing is written before the
        # size check passes, so oversize uploads leave no file behind.
        try:
            with open(upload_dir / filename, "xb") as out:
                out.write(payload)
        except FileExistsError:
            return jsonify(error="file already exists"), 409

        return jsonify(filename=filename, size=len(payload)), 201

    return app
