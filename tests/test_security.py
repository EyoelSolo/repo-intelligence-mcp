from pathlib import Path

import pytest

from app.repository.security import (
    safe_path,
    SecurityError,
)


def test_safe_path(tmp_path):

    root = tmp_path / "repo"

    root.mkdir()

    result = safe_path(
        root,
        "src/app.ts",
    )

    assert result == (
        root / "src/app.ts"
    ).resolve()