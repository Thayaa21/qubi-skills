"""
Resolve `import qcli` to the real qubi Agentic Flows validator.

Shared by tests/conftest.py (which turns failure into pytest.exit) and
tools/rollup_unverified.py (which turns failure into sys.exit) -- the
resolution logic itself has no pytest dependency so both can use it.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

INSTALL_HINT = r"""
The qubi-skills harness needs the qcli validator from the qcli-web repo.

Pick one:

  1. Editable install (preferred -- your live edits to qcli/schema.py are
     what gets tested, with no sync step):

         pip install -e ../qcli-web

  2. Point at a checkout explicitly:

         set QCLI_WEB=C:\path\to\qcli-web        (Windows)
         export QCLI_WEB=/path/to/qcli-web         (POSIX)

  3. Check qcli-web out as a sibling of this repo.
"""


def _looks_like_the_qubi_validator(mod) -> bool:
    """
    An unrelated package named `qcli` exists on PyPI (0.1.1, Python 2 era) and
    squats the same import name. Importing successfully proves nothing -- check
    that what we got is actually the qubi Agentic Flows validator.
    """
    types = getattr(mod, "NODE_TYPES", None)
    return isinstance(types, dict) and "Start" in types and "HitlTask" in types


def _purge_qcli_modules() -> None:
    for name in [n for n in sys.modules if n == "qcli" or n.startswith("qcli.")]:
        del sys.modules[name]


def _try_path(root: Path) -> bool:
    if not (root / "qcli" / "schema.py").is_file():
        return False
    _purge_qcli_modules()
    sys.path.insert(0, str(root))
    try:
        import qcli.schema as s
        if _looks_like_the_qubi_validator(s):
            return True
    except Exception:
        pass
    sys.path.pop(0)
    _purge_qcli_modules()
    return False


def resolve() -> str:
    """
    Make `import qcli` resolve to the qubi validator, and return where from.

    Raises RuntimeError with a full diagnostic on failure -- callers decide
    how to surface that (pytest.exit, sys.exit, etc).

    Explicit checkouts are tried before the installed package precisely
    because of the PyPI name collision: an installed `qcli` may not be ours.
    """
    problems = []

    env = os.environ.get("QCLI_WEB")
    if env:
        if _try_path(Path(env)):
            return f"$QCLI_WEB: {env}"
        problems.append(f"$QCLI_WEB={env} is not a qcli-web checkout")

    sibling = REPO.parent / "qcli-web"
    if _try_path(sibling):
        return f"sibling checkout: {sibling}"

    try:
        import qcli.schema as s
        if _looks_like_the_qubi_validator(s):
            return f"installed package: {Path(s.__file__).parent}"
        problems.append(
            f"an unrelated package named 'qcli' is installed at "
            f"{Path(s.__file__).parent} and shadows the real one"
        )
    except Exception as e:
        problems.append(f"import qcli failed: {e}")

    detail = "\n".join(f"  - {p}" for p in problems)
    raise RuntimeError(INSTALL_HINT + "\nWhat went wrong:\n" + detail)
