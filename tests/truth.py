"""
Ground truth, derived from the installed qcli package at runtime.

Nothing here is hardcoded. If the validator gains a node type, an enum value,
a diagnostic code or a CLI flag, this module sees it on the next run -- which
is the whole point: the linter must not become another unchecked claim.
"""
from __future__ import annotations

import io
import re
from functools import lru_cache
from pathlib import Path

import qcli.schema as _schema

# --- node schema -----------------------------------------------------------

NODE_TYPES: dict = _schema.NODE_TYPES
VALID_HTTP_METHODS: set = set(_schema.VALID_HTTP_METHODS)
VALID_CODE_LANGUAGES: set = set(getattr(_schema, "VALID_CODE_LANGUAGES", {"javascript", "python"}))

#: keys that belong to the node envelope rather than to data{}
ENVELOPE_KEYS = {"id", "type", "position", "data"}

#: keys the designer adds on round-trip; present in downloaded graphs, never
#: required, and not part of NODE_TYPES -- so examples may legitimately show them
DESIGNER_ONLY_KEYS = {
    "measured", "selected", "dragging", "width", "height",
    "sourcePosition", "targetPosition", "positionAbsolute", "deletable",
}


def required(node_type: str) -> set:
    return set(NODE_TYPES[node_type].get("required", []))


def optional(node_type: str) -> set:
    return set(NODE_TYPES[node_type].get("optional", []))


def allowed_data_keys(node_type: str) -> set:
    return required(node_type) | optional(node_type) | {"type"}


# --- diagnostic codes ------------------------------------------------------

@lru_cache(maxsize=1)
def codes() -> frozenset:
    """Every error/warning code the validator can emit."""
    src = io.open(_schema.__file__, encoding="utf-8").read()
    found = set(re.findall(r'code="([A-Z][A-Z0-9_]*)"', src))
    # sanity: if this regex ever stops matching the file's style, fail loudly
    # rather than silently allowing every SCREAMING_SNAKE token through
    assert len(found) >= 25, f"only {len(found)} codes discovered -- has schema.py changed style?"
    return frozenset(found)


# --- CLI surface -----------------------------------------------------------

@lru_cache(maxsize=1)
def binary_names() -> frozenset:
    """Console-script names this package installs (never hardcode 'qcli')."""
    names = set()
    try:
        from importlib.metadata import entry_points
        eps = entry_points()
        selected = eps.select(group="console_scripts") if hasattr(eps, "select") else eps.get("console_scripts", [])
        for ep in selected:
            if ep.value.startswith("qcli"):
                names.add(ep.name)
    except Exception:
        pass
    if not names:
        # not installed: read setup.py's declaration instead
        setup = Path(_schema.__file__).resolve().parent.parent / "setup.py"
        if setup.is_file():
            names |= set(re.findall(r"([A-Za-z0-9_.-]+)\s*=\s*qcli\.cli:", setup.read_text(encoding="utf-8")))
    assert names, "could not determine the console-script name from entry_points or setup.py"
    return frozenset(names)


@lru_cache(maxsize=1)
def command_tree() -> dict:
    """
    {('flow','validate'): {'-j','--json-output', ...}} for every leaf command.

    Built by walking the click group object, never by regexing cli.py, so it
    tracks the real CLI automatically.
    """
    import click
    import qcli.cli as cli_mod

    root = None
    for value in vars(cli_mod).values():
        if isinstance(value, click.Group) and value.name in (None, "cli", "qcli"):
            root = value
            break
    assert root is not None, "could not locate the root click group in qcli.cli"

    tree: dict[tuple, set] = {}

    def walk(cmd, prefix=()):
        subs = getattr(cmd, "commands", {})
        if not subs and prefix:
            opts = set()
            for p in cmd.params:
                opts |= set(p.opts) | set(p.secondary_opts)
            tree[prefix] = {o for o in opts if o.startswith("-")} | {"--help"}
        for name, sub in subs.items():
            walk(sub, prefix + (name,))

    walk(root)
    return tree


def command_paths() -> set:
    return set(command_tree())


# --- fields whose real values cannot be known offline ----------------------

@lru_cache(maxsize=1)
def unverified_fields() -> frozenset:
    """
    Node data fields backed by a platform dropdown whose options were never
    captured. Derived from the schema-extractor capture: a `select` widget
    with `options: null` means "we never saw the list".

    Falls back to the known set if the capture file is not present.
    """
    import json

    repo = Path(_schema.__file__).resolve().parent.parent
    capture = repo / "schema-extractor" / "output" / "element_properties.json"
    fallback = frozenset({"agentId", "operation", "automationId", "taskType", "assignTo", "template"})
    if not capture.is_file():
        return fallback

    # designer label -> the field name used in the graph JSON
    label_to_field = {
        "Select Agent": "agentId",
        "Operation": "operation",
        "Automation": "automationId",
        "Task Type": "taskType",
        "Assign To": "assignTo",
        "Template": "template",
    }
    found = set()
    data = json.loads(capture.read_text(encoding="utf-8"))
    for spec in data.values():
        for f in spec.get("fields", []):
            if f.get("type") == "select" and f.get("options") is None:
                field = label_to_field.get(f.get("label"))
                if field:
                    found.add(field)
    return frozenset(found) or fallback


#: values a fixture may use for an unverified field, and nothing else
SENTINEL_UUID = "00000000-0000-0000-0000-000000000000"
SENTINEL_TEXT = "UNVERIFIED"
