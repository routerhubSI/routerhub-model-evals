import io

import pytest

MAX_FILE_BYTES = 1024 * 1024


def send(client, filename, payload=b"example\n"):
    return client.post("/upload", data={"file": (io.BytesIO(payload), filename)})


@pytest.mark.parametrize("filename", ("notes.txt", "report.csv", "REPORT.CSV"))
def test_valid_upload_preserves_content(client, storage, filename):
    payload = b"name,value\nexample,42\n"
    response = send(client, filename, payload)
    assert response.status_code == 201
    assert response.get_json() == {"filename": filename, "size": len(payload)}
    assert (storage / filename).read_bytes() == payload


def test_missing_file_is_rejected(client, storage):
    response = client.post("/upload", data={})
    assert response.status_code == 400
    assert tuple(storage.iterdir()) == ()


def test_empty_filename_is_rejected(client, storage):
    response = send(client, "")
    assert response.status_code == 400
    assert tuple(storage.iterdir()) == ()


@pytest.mark.parametrize("filename", ("../escaped.txt", "..\\escaped.txt", "nested/escaped.txt"))
def test_unsafe_filename_cannot_write_outside_storage(client, storage, filename):
    sentinel = storage.parent / "escaped.txt"
    sentinel.write_bytes(b"unchanged")
    response = send(client, filename, b"overwrite")
    assert response.status_code == 400
    assert sentinel.read_bytes() == b"unchanged"
    assert tuple(storage.iterdir()) == ()


def test_absolute_path_cannot_overwrite_existing_file(client, storage):
    sentinel = storage.parent / "absolute.txt"
    sentinel.write_bytes(b"unchanged")
    response = send(client, str(sentinel), b"overwrite")
    assert response.status_code == 400
    assert sentinel.read_bytes() == b"unchanged"
    assert tuple(storage.iterdir()) == ()


@pytest.mark.parametrize("filename", ("payload.py", "payload.html", "payload.exe", "noextension", ".hidden.txt"))
def test_disallowed_names_create_no_files(client, storage, filename):
    response = send(client, filename)
    assert response.status_code == 400
    assert tuple(storage.iterdir()) == ()


def test_oversized_file_is_rejected_before_persistence(client, storage):
    response = send(client, "large.txt", b"x" * (MAX_FILE_BYTES + 1))
    assert response.status_code == 413
    assert tuple(storage.iterdir()) == ()


def test_exact_size_limit_remains_usable(client, storage):
    payload = b"x" * MAX_FILE_BYTES
    response = send(client, "boundary.txt", payload)
    assert response.status_code == 201
    assert (storage / "boundary.txt").read_bytes() == payload


def test_collision_preserves_original_file(client, storage):
    assert send(client, "existing.txt", b"original").status_code == 201
    response = send(client, "existing.txt", b"replacement")
    assert response.status_code == 409
    assert (storage / "existing.txt").read_bytes() == b"original"
