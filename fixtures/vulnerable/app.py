from pathlib import Path

from flask import Flask, jsonify, request


def create_app(upload_dir: Path) -> Flask:
    app = Flask(__name__)
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/upload")
    def upload():
        file = request.files["file"]
        filename = file.filename or ""
        payload = file.read()
        (upload_dir / filename).write_bytes(payload)
        return jsonify(filename=filename, size=len(payload)), 201

    return app
