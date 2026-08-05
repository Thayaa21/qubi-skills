"""
auth.py — qcli Session Management for qubi Web (OAuth2 + Identity Server)

Handles login via the qubi Identity Server and stores session cookies/tokens
locally at ~/.qcli/session.json.
"""

import json
import sys
from getpass import getpass
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QCLI_DIR = Path.home() / ".qcli"
SESSION_FILE = QCLI_DIR / "session.json"

DEFAULT_IDENTITY_SERVER = "https://test.identityserver.qubi.com"
DEFAULT_AGENTHUB = "https://test.agenthub.qubi.com"

LOGIN_API = "/api/v1/account/login"


# ---------------------------------------------------------------------------
# Session Management
# ---------------------------------------------------------------------------

def _ensure_dir():
    QCLI_DIR.mkdir(parents=True, exist_ok=True)


def save_session(*, cookies: dict, server_url: str, tenant: str, username: str):
    """Save authentication session to disk."""
    _ensure_dir()
    data = {
        "cookies": cookies,
        "server_url": server_url,
        "tenant": tenant,
        "username": username,
    }
    SESSION_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        SESSION_FILE.chmod(0o600)
    except OSError:
        pass  # Windows may not support this


def load_session() -> dict | None:
    """Load existing session. Returns None if no session."""
    if not SESSION_FILE.exists():
        return None
    try:
        return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return None


def clear_session():
    """Remove stored session."""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def is_logged_in() -> bool:
    """Check if a valid session exists."""
    session = load_session()
    return session is not None and "cookies" in session


def require_login() -> dict:
    """Ensure user is logged in. Exits if not."""
    session = load_session()
    if not session or "cookies" not in session:
        print("Error: Not logged in. Run 'qcli login' first.", file=sys.stderr)
        sys.exit(1)
    return session


# ---------------------------------------------------------------------------
# Login Flow
# ---------------------------------------------------------------------------

def do_login(server_url: str, tenant: str, username: str, password: str) -> dict:
    """
    Authenticate with qubi Identity Server.

    The Identity Server uses a Blazor app with an API endpoint:
    POST /api/v1/account/login

    Returns session cookies on success.
    """
    if requests is None:
        raise ImportError("'requests' library required. pip install requests")

    identity_url = f"{server_url}{LOGIN_API}"

    # The identity server expects tenant + username + password
    payload = {
        "tenantName": tenant,
        "userNameOrEmail": username,
        "password": password,
    }

    session = requests.Session()

    try:
        resp = session.post(identity_url, json=payload, timeout=30, verify=False)
    except requests.ConnectionError:
        raise ConnectionError(f"Cannot reach identity server at {server_url}")
    except requests.Timeout:
        raise ConnectionError(f"Connection timed out to {server_url}")

    if resp.status_code == 200:
        # Extract cookies from the session
        cookies = dict(session.cookies)
        return {
            "cookies": cookies,
            "response": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {},
        }
    elif resp.status_code == 401:
        raise PermissionError("Invalid credentials")
    elif resp.status_code == 400:
        error_msg = ""
        try:
            error_msg = resp.json().get("message", resp.text)
        except Exception:
            error_msg = resp.text
        raise ValueError(f"Login failed: {error_msg}")
    else:
        raise RuntimeError(f"Login failed with status {resp.status_code}: {resp.text[:200]}")


def prompt_login() -> tuple:
    """Interactive login prompt. Returns (server_url, tenant, username, password)."""
    print("qcli login — Authenticate with qubi")
    print("-" * 40)

    server_url = input(f"Identity Server URL [{DEFAULT_IDENTITY_SERVER}]: ").strip()
    if not server_url:
        server_url = DEFAULT_IDENTITY_SERVER

    tenant = input("Tenant [default]: ").strip()
    if not tenant:
        tenant = "default"

    username = input("Email or Username: ").strip()
    password = getpass("Password: ")

    return server_url, tenant, username, password
