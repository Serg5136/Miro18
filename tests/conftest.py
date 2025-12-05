import sys
from pathlib import Path

import pytest


# Ensure project root is on sys.path for imports when running pytest directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_state():
    return {"cards": [1], "connections": [], "frames": []}


@pytest.fixture
def autosave_service(tmp_path):
    from src.autosave import AutoSaveService

    return AutoSaveService(filename=tmp_path / "autosave.json")
