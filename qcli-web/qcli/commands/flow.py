"""qcli flow commands — list, validate, get, save, run."""

import json
import sys
from pathlib import Path

import click

from qcli.schema import validate_file, validate_graph, OK, BAD, WARN


@click.command("list")
@click.option("--search", "-s", default="", help="Search term")
def flow_list(search):
    """List all workflows."""
    from qcli.client import QubiClient
    client = QubiClient()
    workflows = client.list_workflows(search)

    if not workflows:
        click.echo("No workflows found.")
        return

    # Handle different response formats
    items = workflows if isinstance(workflows, list) else workflows.get("items", workflows.get("data", []))
    
    click.echo(f"Workflows ({len(items)}):")
    for wf in items:
        wf_id = wf.get("id", "?")
        name = wf.get("name", "Unnamed")
        click.echo(f"  {wf_id}  {name}")


@click.command("validate")
@click.argument("file", type=click.Path(exists=True))
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def flow_validate(file, json_output):
    """Validate a workflow JSON file.

    Checks node types, required fields, edges, and structure.
    Exit code 0 = valid, 1 = invalid.
    """
    result = validate_file(file)

    if json_output:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        result.print_report()

    sys.exit(0 if result.valid else 1)


@click.command("get")
@click.argument("workflow_id")
@click.option("--output", "-o", default=None, help="Output file path (default: stdout)")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON")
def flow_get(workflow_id, output, pretty):
    """Download a workflow graph from qubi."""
    from qcli.client import QubiClient
    client = QubiClient()
    graph = client.get_graph(workflow_id)

    indent = 2 if pretty else None
    json_str = json.dumps(graph, indent=indent)

    if output:
        Path(output).write_text(json_str, encoding="utf-8")
        click.echo(f"{OK} Saved to {output}")
        node_count = len(graph.get("nodes", []))
        edge_count = len(graph.get("edges", []))
        click.echo(f"  {node_count} nodes, {edge_count} edges")
    else:
        click.echo(json_str)


@click.command("save")
@click.argument("file", type=click.Path(exists=True))
@click.option("--workflow-id", "-w", required=True, help="Target workflow ID")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--skip-validate", is_flag=True, help="Skip validation before saving")
def flow_save(file, workflow_id, yes, skip_validate):
    """Save a workflow JSON file to qubi.

    Validates first, then pushes the graph to the specified workflow.
    """
    # Load the file
    path = Path(file)
    try:
        graph = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        click.echo(f"{BAD} Invalid JSON: {e}", err=True)
        sys.exit(1)

    # Validate
    warnings = []
    if not skip_validate:
        result = validate_file(file)
        if not result.valid:
            click.echo(f"{BAD} Validation failed with {len(result.errors)} error(s):", err=True)
            for err in result.errors:
                click.echo(f"  {err}", err=True)
            click.echo("\nFix errors or use --skip-validate to save anyway.", err=True)
            sys.exit(1)
        warnings = result.warnings
        click.echo(f"  {OK} Validation passed")

        # Warnings don't fail the exit code, but a graph with unreachable nodes
        # or a type mismatch will misbehave on the canvas. Surface them here so
        # the save decision is made with them in view.
        if warnings:
            click.echo(f"\n{WARN} {len(warnings)} warning(s) - these do not block the save, "
                       f"but should be fixed first:")
            for warn in warnings:
                click.echo(f"  {warn}")

    # Confirm
    node_count = len(graph.get("nodes", []))
    edge_count = len(graph.get("edges", []))
    if not yes:
        click.echo(f"\nAbout to save workflow to {workflow_id}")
        summary = f"  {node_count} nodes, {edge_count} edges"
        if warnings:
            summary += f", {len(warnings)} warning(s)"
        click.echo(summary)
        if not click.confirm("Proceed?"):
            click.echo("Cancelled.")
            sys.exit(0)

    # Save
    from qcli.client import QubiClient
    client = QubiClient()
    try:
        result = client.save_graph(workflow_id, graph)
        click.echo(f"{OK} Workflow saved ({node_count} nodes, {edge_count} edges)")
    except Exception as e:
        click.echo(f"{BAD} Save failed: {e}", err=True)
        sys.exit(1)


@click.command("run")
@click.argument("workflow_id")
@click.option("--input", "-i", "input_file", default=None, help="Input JSON file")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def flow_run(workflow_id, input_file, yes):
    """Execute a workflow on qubi."""
    input_data = None
    if input_file:
        try:
            input_data = json.loads(Path(input_file).read_text(encoding="utf-8"))
        except Exception as e:
            click.echo(f"{BAD} Invalid input file: {e}", err=True)
            sys.exit(1)

    if not yes:
        click.echo(f"About to run workflow: {workflow_id}")
        if not click.confirm("Proceed?"):
            click.echo("Cancelled.")
            sys.exit(0)

    from qcli.client import QubiClient
    client = QubiClient()
    try:
        result = client.run_workflow(workflow_id, input_data)
        click.echo(f"{OK} Workflow started!")
        if isinstance(result, dict):
            job_id = result.get("jobId") or result.get("id", "N/A")
            click.echo(f"  Job ID: {job_id}")
    except Exception as e:
        click.echo(f"{BAD} Run failed: {e}", err=True)
        sys.exit(1)
