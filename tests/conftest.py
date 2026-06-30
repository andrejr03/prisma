from __future__ import annotations

from pathlib import Path

import pytest
from app.config import PrismaSettings, load_settings


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def phase1_settings(tmp_path: Path) -> PrismaSettings:
    return load_settings().with_overrides(
        index_path=str(tmp_path / "qdrant"),
        manifest_path=str(tmp_path / "manifest.json"),
    )
