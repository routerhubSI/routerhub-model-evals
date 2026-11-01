import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser):
    parser.addoption("--app", default=str(ROOT / "fixtures/vulnerable/app.py"))


@pytest.fixture
def storage(tmp_path):
    return tmp_path / "uploads"


@pytest.fixture
def client(request, storage):
    source = Path(request.config.getoption("--app")).resolve()
    spec = importlib.util.spec_from_file_location("benchmark_application", source)
    if spec is None or spec.loader is None:
        pytest.fail("Cannot import the selected application")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = module.create_app(storage)
    app.config.update(TESTING=True)
    return app.test_client()
