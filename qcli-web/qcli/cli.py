"""
cli.py — qcli Entry Point (Web Version)

Registers all commands for qubi Agentic Flows CLI.

Usage:
    qcli login
    qcli logout
    qcli status
    qcli flow list
    qcli flow validate <file>
    qcli flow get <workflow-id>
    qcli flow save <file> --workflow-id <id>
    qcli flow run <workflow-id>
    qcli agents list
    qcli rpa list
"""

import click

from qcli.commands.login import login, logout, login_status
from qcli.commands.flow import flow_list, flow_validate, flow_get, flow_save, flow_run
from qcli.commands.agents import agents_list, rpa_list


# ---------------------------------------------------------------------------
# Top-level group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(version="0.2.0", prog_name="qcli")
def cli():
    """qcli — qubi Agentic Flows CLI.

    Validate, save, and deploy workflows to qubi's web platform.
    """
    pass


# ---------------------------------------------------------------------------
# Subgroups
# ---------------------------------------------------------------------------

@cli.group()
def flow():
    """Workflow commands (list, validate, get, save, run)."""
    pass


@cli.group()
def agents():
    """Agent commands."""
    pass


@cli.group()
def rpa():
    """RPA automation commands."""
    pass


# ---------------------------------------------------------------------------
# Register commands
# ---------------------------------------------------------------------------

# Top-level
cli.add_command(login)
cli.add_command(logout)
cli.add_command(login_status, name="status")

# Flow commands
flow.add_command(flow_list, name="list")
flow.add_command(flow_validate, name="validate")
flow.add_command(flow_get, name="get")
flow.add_command(flow_save, name="save")
flow.add_command(flow_run, name="run")

# Agent commands
agents.add_command(agents_list, name="list")

# RPA commands
rpa.add_command(rpa_list, name="list")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    cli()


if __name__ == "__main__":
    main()
