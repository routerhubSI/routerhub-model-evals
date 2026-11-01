import re
from pathlib import Path

from flask import Flask, jsonify, request

# First char: letter or digit. Rest: letters, digits, underscore, dot, hyphen.
# Total length capped at 100 (1 + 99). ASCII-only by construction, and the
# character class excludes "/" and "\", so no path components can appear.
FILENAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
ALLOWED_EXTENSIONS = (".txt", ".csv")
MAX_CONTENT_BYTES = 1_048_576  # 1 MiB file-content limit, multipart overhead excluded


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        file = request.files.get("file")
        if file is None:
            return jsonify(error="missing file field"), 400

        filename = file.filename or ""
        if FILENAME_RE.fullmatch(filename) is None:
            return jsonify(error="invalid filename"), 400

        if not filename.lower().endswith(ALLOWED_EXTENSIONS):
            return jsonify(error="unsupported extension"), 400

        # Read one byte past the limit; reads decoded file content only,
        # so multipart framing overhead is not counted against the limit.
        payload = file.stream.read(MAX_CONTENT_BYTES + 1)
        if len(payload) > MAX_CONTENT_BYTES:
            return jsonify(error="file exceeds 1 MiB limit"), 413

        # Regex forbids separators, so target stays inside upload_dir.
        # "xb" refuses to overwrite: collision raises FileExistsError -> 409.
        target = upload_dir / filename
        try:
            with open(target, "xb") as out:
                out.write(payload)
        except FileExistsError:
            return jsonify(error="file already exists"), 409

        return jsonify(filename=filename, size=len(payload)), 201

    return app
