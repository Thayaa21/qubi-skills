"""
browser_login.py — Browser-assisted login for qcli.

Opens a browser window, user logs in normally, then we extract the
ASP.NET Core session cookies and store them for headless CLI use.

Usage:
    python -m qcli.browser_login
    # or via: qcli login --browser

Requires: playwright (pip install playwright && playwright install chromium)
"""

import json
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from qcli.auth import save_session, QCLI_DIR, SESSION_FILE
from qcli.schema import OK, BAD

DEFAULT_AGENTHUB = "https://test.agenthub.qubi.com"
COOKIE_PREFIX = ".AspNetCore.Cookies"


def browser_login(server_url: str = DEFAULT_AGENTHUB) -> dict:
    """
    Open a browser for the user to log in, then capture session cookies.

    Returns the saved session dict.
    """
    if sync_playwright is None:
        print("Error: playwright is not installed.", file=sys.stderr)
        print("Install it with: pip install playwright && playwright install chromium", file=sys.stderr)
        sys.exit(1)

    login_url = f"{server_url}/login"

    print(f"Opening browser for login at {server_url}...")
    print("Log in normally. The window will close automatically once authenticated.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        # Navigate to login
        page.goto(login_url, wait_until="domcontentloaded", timeout=60000)

        # Wait for the user to complete login and land on the dashboard
        # The callback redirects to /dashboard after successful auth
        print("  Waiting for login to complete...")
        try:
            page.wait_for_url(
                f"{server_url}/dashboard**",
                timeout=300000,  # 5 min timeout for manual login
                wait_until="domcontentloaded",
            )
        except Exception:
            # Also accept any page on the agenthub domain after login
            current = page.url
            if server_url.rstrip("/") not in current or "login" in current:
                print(f"  {BAD} Login did not complete. Please try again.", file=sys.stderr)
                browser.close()
                sys.exit(1)

        print(f"  {OK} Login detected!")

        # Extract cookies from the browser context
        all_cookies = context.cookies(server_url)
        browser.close()

    # Filter to ASP.NET Core session cookies
    session_cookies = {}
    for cookie in all_cookies:
        if cookie["name"].startswith(COOKIE_PREFIX):
            session_cookies[cookie["name"]] = cookie["value"]

    if not session_cookies:
        print(f"  {BAD} No session cookies found. Login may have failed.", file=sys.stderr)
        sys.exit(1)

    print(f"  {OK} Captured {len(session_cookies)} session cookie(s)")

    # Save session
    save_session(
        cookies=session_cookies,
        server_url=server_url,
        tenant="default",
        username="(browser login)",
    )

    print(f"  {OK} Session saved to {SESSION_FILE}")
    print(f"\n  You can now use qcli commands without the browser.")
    print(f"  Session will last until the server expires it.")

    return session_cookies


def main():
    """CLI entry point for browser login."""
    server_url = DEFAULT_AGENTHUB

    if len(sys.argv) > 1:
        server_url = sys.argv[1]

    browser_login(server_url)


if __name__ == "__main__":
    main()
