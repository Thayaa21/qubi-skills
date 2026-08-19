"""
Shared fixtures for the qubi-skills harness.

The skills live here; the validator they document lives in the separate
qcli-web repo. Everything the harness asserts is derived from that real
validator at runtime -- never from a copy, and never hardcoded -- because a
test that asserts against a stale copy of the truth asserts nothing.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.locate_qcli import REPO, resolve as _resolve_qcli

try:
    QCLI_SOURCE = _resolve_qcli()
except RuntimeError as e:
    pytest.exit(str(e), returncode=4)


def pytest_report_header(config):
    import qcli.schema as s
    return [
        f"qcli validator: {QCLI_SOURCE}",
        f"               {s.__file__}",
    ]


@pytest.fixture(scope="session")
def truth():
    """Ground truth derived from the real qcli package."""
    from tests import truth as t
    return t


def skill_dirs() -> list[Path]:
    """Every skill directory: a folder containing a SKILL.md."""
    return sorted(
        p.parent for p in REPO.glob("*/SKILL.md")
        if not p.parent.name.startswith((".", "_")) and p.parent.name != "tests"
    )


def skill_id(path: Path) -> str:
    return path.name
