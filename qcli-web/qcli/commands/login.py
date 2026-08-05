"""qcli login/logout/status commands."""

import sys
import click

from qcli.auth import (
    do_login, save_session, clear_session, load_session,
    prompt_login, DEFAULT_AGENTHUB,
)
from qcli.schema import OK, BAD


@click.command("login")
@click.option("--server", default=None, help="Identity Server URL")
@click.option("--agenthub", default=None, help="AgentHub URL")
@click.option("--tenant", "-t", default=None, help="Tenant name")
@click.option("--username", "-u", default=None, help="Email or username")
@click.option("--password", "-p", default=None, help="Password")
@click.option("--browser", "-b", is_flag=True, help="Login via browser (recommended)")
def login(server, agenthub, tenant, username, password, browser):
    """Authenticate with qubi Identity Server."""
    if browser:
        from qcli.browser_login import browser_login
        hub_url = agenthub or DEFAULT_AGENTHUB
        browser_login(hub_url)
        return

    if server and tenant and username and password:
        server_url = server
        t = tenant
        u = username
        pwd = password
    else:
        server_url, t, u, pwd = prompt_login()

    hub_url = agenthub or DEFAULT_AGENTHUB

    click.echo(f"Connecting to {server_url}...")
    try:
        result = do_login(server_url, t, u, pwd)
        save_session(
            cookies=result["cookies"],
            server_url=hub_url,
            tenant=t,
            username=u,
        )
        click.echo(f"{OK} Logged in as {u} (tenant: {t})")
    except ConnectionError as e:
        click.echo(f"{BAD} Connection failed: {e}", err=True)
        sys.exit(1)
    except PermissionError as e:
        click.echo(f"{BAD} Auth failed: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"{BAD} {e}", err=True)
        sys.exit(1)


@click.command("logout")
def logout():
    """Clear stored session."""
    clear_session()
    click.echo("Logged out. Session cleared.")


@click.command("status")
def login_status():
    """Show current login status."""
    session = load_session()
    if session:
        click.echo(f"Logged in as: {session.get('username', '?')}")
        click.echo(f"Tenant: {session.get('tenant', '?')}")
        click.echo(f"Server: {session.get('server_url', '?')}")
    else:
        click.echo("Not logged in. Run 'qcli login' to authenticate.")
