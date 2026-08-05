"""qcli agents commands."""

import json
import click


@click.command("list")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def agents_list(json_output):
    """List available AI agents."""
    from qcli.client import QubiClient
    client = QubiClient()
    agents = client.list_agents()

    items = agents if isinstance(agents, list) else agents.get("items", agents.get("data", []))

    if json_output:
        click.echo(json.dumps(items, indent=2))
        return

    if not items:
        click.echo("No agents found.")
        return

    click.echo(f"Agents ({len(items)}):")
    for agent in items:
        agent_id = agent.get("id", "?")
        name = agent.get("name", "Unnamed")
        click.echo(f"  {agent_id}  {name}")


@click.command("list")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def rpa_list(json_output):
    """List available RPA automations."""
    from qcli.client import QubiClient
    client = QubiClient()
    automations = client.list_rpa_automations()

    items = automations if isinstance(automations, list) else automations.get("items", automations.get("data", []))

    if json_output:
        click.echo(json.dumps(items, indent=2))
        return

    if not items:
        click.echo("No RPA automations found.")
        return

    click.echo(f"RPA Automations ({len(items)}):")
    for auto in items:
        auto_id = auto.get("id", "?")
        name = auto.get("name", "Unnamed")
        click.echo(f"  {auto_id}  {name}")
