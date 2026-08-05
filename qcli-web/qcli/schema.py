"""
schema.py — Workflow graph validation for qubi Agentic Flows.

Validates workflow JSON against the known node types, required fields,
and edge structure. Reports specific, actionable errors.

Severity contract:
  errors   — set valid=False, exit code 1, block `flow save`. The agent must fix these.
  warnings — do not fail the exit code, but indicate a graph that will misbehave on
             the canvas or at runtime. Treat as must-fix before saving.
"""

import difflib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Console glyphs
# ---------------------------------------------------------------------------

def _console_supports(text: str) -> bool:
    """True if stdout can encode `text`.

    Windows consoles default to cp1252, which cannot encode the check/cross/
    arrow glyphs — printing them raised UnicodeEncodeError and took down
    `qcli flow validate` entirely.
    """
    encoding = getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        text.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return False
    return True


if _console_supports("✓✗⚠→"):
    OK, BAD, WARN, ARROW = "✓", "✗", "⚠", "→"
else:
    OK, BAD, WARN, ARROW = "OK", "X", "!", "->"


# ---------------------------------------------------------------------------
# Known Node Types & Their Required Fields
# ---------------------------------------------------------------------------

# Every node type in the designer has a Description input, so it is optional
# everywhere (see schema-extractor/output/element_properties.json).
NODE_TYPES = {
    "Start": {
        "required": ["name"],
        "optional": ["description", "input", "saveOutputAs"],
    },
    "End": {
        "required": ["name"],
        "optional": ["description", "input", "saveOutputAs"],
    },
    "Agent": {
        "required": ["name", "agentId"],
        "optional": ["description", "input", "systemPrompt", "userMessage", "saveOutputAs"],
    },
    "Assign": {
        "required": ["name"],
        "optional": ["description", "assignments"],
    },
    "Branch": {
        "required": ["name"],
        "optional": ["description", "conditions", "input", "saveOutputAs"],
    },
    "Code": {
        "required": ["name", "language", "code"],
        "optional": ["description", "input", "saveOutputAs"],
    },
    "DocumentAI": {
        "required": ["name", "operation"],
        "optional": ["description", "fileVariable", "saveOutputAs", "input"],
    },
    "Http": {
        "required": ["name", "method", "url"],
        "optional": ["description", "input", "headers", "body", "saveOutputAs"],
    },
    "RPA": {
        "required": ["name", "automationId"],
        "optional": ["description", "input", "saveOutputAs"],
    },
    "Hitl": {
        "required": ["name"],
        "optional": ["description", "input", "saveOutputAs"],
    },
    "HitlTask": {
        "required": ["name", "taskName", "taskType", "assignTo"],
        "optional": ["description", "template", "saveOutputAs", "input"],
    },
    "JsonParser": {
        "required": ["name"],
        "optional": ["description", "input", "mappings"],
    },
    "TextParser": {
        "required": ["name", "regexPattern"],
        "optional": ["description", "input", "ignoreCase", "multiline", "singleline",
                     "trimOutput", "fallbackValue", "outputMappings"],
    },
}

# The designer's Method dropdown offers exactly these five.
VALID_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}
VALID_CODE_LANGUAGES = {"javascript", "python"}

# Shape-only check: 8-4-4-4-12 hex. Deliberately NOT a strict RFC-4122 v4 test —
# qubi's platform IDs (agentId, automationId, workflowId) are .NET sequential
# GUIDs whose variant nibble is not RFC-compliant, e.g.
# e9af665c-6bd1-4644-6333-08dee4aa9ecc. Applied to node ids only.
UUID_SHAPE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

DEFAULT_VIEWPORT = {"x": 0, "y": 0, "zoom": 1}
DEFAULT_EXECUTION_MODE = "Sequential"


# ---------------------------------------------------------------------------
# Validation Errors
# ---------------------------------------------------------------------------

@dataclass
class ValidationError:
    code: str
    message: str
    node_id: str | None = None
    node_name: str | None = None
    field: str | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict:
        d = {"code": self.code, "message": self.message}
        if self.node_id:
            d["node_id"] = self.node_id
        if self.node_name:
            d["node_name"] = self.node_name
        if self.field:
            d["field"] = self.field
        if self.suggestion:
            d["suggestion"] = self.suggestion
        return d

    def __str__(self) -> str:
        parts = [f"[{self.code}]"]
        if self.node_name:
            parts.append(f"({self.node_name})")
        parts.append(self.message)
        if self.suggestion:
            parts.append(f"{ARROW} {self.suggestion}")
        return " ".join(parts)


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0

    def add_error(self, error: ValidationError):
        self.errors.append(error)
        self.valid = False

    def add_warning(self, warning: ValidationError):
        self.warnings.append(warning)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }

    def print_report(self):
        if self.valid and not self.warnings:
            print(f"{OK} Valid ({self.node_count} nodes, {self.edge_count} edges)")
            return
        status = f"{BAD} INVALID" if not self.valid else f"{WARN} Valid with warnings"
        print(f"{status} ({self.node_count} nodes, {self.edge_count} edges)")
        print(f"  Errors: {len(self.errors)}, Warnings: {len(self.warnings)}")
        for err in self.errors:
            print(f"  ERROR {err}")
        for warn in self.warnings:
            print(f"  WARN  {warn}")


# ---------------------------------------------------------------------------
# Validation Logic
# ---------------------------------------------------------------------------

def validate_graph(graph: dict) -> ValidationResult:
    """Validate a workflow graph dict. Returns ValidationResult."""
    result = ValidationResult()

    # Check top-level structure
    if not isinstance(graph, dict):
        result.add_error(ValidationError(
            code="INVALID_FORMAT",
            message="Graph must be a JSON object",
            suggestion="Ensure the file contains a valid JSON object with 'nodes' and 'edges'"
        ))
        return result

    nodes = graph.get("nodes")
    edges = graph.get("edges")

    if nodes is None:
        result.add_error(ValidationError(
            code="MISSING_NODES",
            message="Graph is missing 'nodes' array",
            suggestion="Add a 'nodes' array to the graph"
        ))
        return result

    if not isinstance(nodes, list):
        result.add_error(ValidationError(
            code="INVALID_NODES",
            message="'nodes' must be an array",
        ))
        return result

    if edges is None:
        result.add_error(ValidationError(
            code="MISSING_EDGES",
            message="Graph is missing 'edges' array",
            suggestion="Add an 'edges' array (can be empty [])"
        ))
        return result

    result.node_count = len(nodes)
    result.edge_count = len(edges) if isinstance(edges, list) else 0

    # Top-level canvas keys — the designer writes both on every save
    if "viewport" not in graph:
        result.add_warning(ValidationError(
            code="MISSING_VIEWPORT",
            message="Graph has no 'viewport'",
            suggestion=f"Add viewport: {json.dumps(DEFAULT_VIEWPORT)}"
        ))
    if "executionMode" not in graph:
        result.add_warning(ValidationError(
            code="MISSING_EXECUTION_MODE",
            message="Graph has no 'executionMode'",
            suggestion=f'Add executionMode: "{DEFAULT_EXECUTION_MODE}"'
        ))

    # Validate nodes
    node_ids = set()
    start_ids = []
    end_ids = []

    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            result.add_error(ValidationError(
                code="INVALID_NODE",
                message=f"Node at index {i} is not an object",
            ))
            continue

        node_id = node.get("id", "")
        node_type = node.get("type", "")

        # A non-dict 'data' used to skip every check below it, so an Agent node
        # with data:null validated clean despite agentId being required.
        # Normalize to {} so the required-field errors still fire.
        raw_data = node.get("data", {})
        if isinstance(raw_data, dict):
            data = raw_data
        else:
            data = {}
            result.add_warning(ValidationError(
                code="INVALID_NODE_DATA",
                message=f"Node at index {i} has non-object 'data' "
                        f"({type(raw_data).__name__}); treated as empty",
                node_id=node_id,
                suggestion="Set 'data' to an object with at least 'type' and 'name'"
            ))

        node_name = data.get("name", node_type)

        # Check ID
        if not node_id:
            result.add_error(ValidationError(
                code="MISSING_NODE_ID",
                message=f"Node at index {i} has no 'id'",
                node_name=node_name,
                suggestion="Add a UUID id field"
            ))
        elif node_id in node_ids:
            result.add_error(ValidationError(
                code="DUPLICATE_NODE_ID",
                message=f"Duplicate node id: {node_id}",
                node_id=node_id,
                node_name=node_name,
            ))
        else:
            node_ids.add(node_id)

        if node_id and not UUID_SHAPE.fullmatch(str(node_id)):
            result.add_warning(ValidationError(
                code="INVALID_NODE_ID_FORMAT",
                message=f"Node id is not UUID-shaped: '{node_id}'",
                node_id=node_id,
                node_name=node_name,
                suggestion="React Flow generates UUID v4 node ids; use one"
            ))

        # Check type. Without a known type there is no schema to check the rest
        # of the node against, so both branches stop here.
        if not node_type:
            result.add_error(ValidationError(
                code="MISSING_NODE_TYPE",
                message=f"Node '{node_name}' has no 'type'",
                node_id=node_id,
                node_name=node_name,
                suggestion=f"Set 'type' to one of: {', '.join(sorted(NODE_TYPES.keys()))}"
            ))
            continue
        if node_type not in NODE_TYPES:
            result.add_error(ValidationError(
                code="UNKNOWN_NODE_TYPE",
                message=f"Unknown node type: '{node_type}'",
                node_id=node_id,
                node_name=node_name,
                suggestion=f"Valid types: {', '.join(sorted(NODE_TYPES.keys()))}"
            ))
            continue

        if node_type == "Start":
            start_ids.append(node_id)
        if node_type == "End":
            end_ids.append(node_id)

        # data.type must mirror the node's type — the designer reads both
        data_type = data.get("type")
        if data_type != node_type:
            result.add_warning(ValidationError(
                code="DATA_TYPE_MISMATCH",
                message=(f"Node '{node_name}' has data.type={data_type!r} "
                         f"but type={node_type!r}"),
                node_id=node_id,
                node_name=node_name,
                field="type",
                suggestion=f'Set data.type to "{node_type}"'
            ))

        # Check position
        pos = node.get("position")
        if not pos or not isinstance(pos, dict) or "x" not in pos or "y" not in pos:
            result.add_warning(ValidationError(
                code="MISSING_POSITION",
                message=f"Node '{node_name}' has no position",
                node_id=node_id,
                node_name=node_name,
                suggestion="Add position: {x, y}"
            ))

        # Check required data fields
        schema = NODE_TYPES[node_type]
        for req_field in schema["required"]:
            if req_field not in data or not data[req_field]:
                result.add_error(ValidationError(
                    code="MISSING_REQUIRED_FIELD",
                    message=f"Node '{node_name}' missing required field: '{req_field}'",
                    node_id=node_id,
                    node_name=node_name,
                    field=req_field,
                ))

        # Unrecognised data keys — catches typos like saveOutputas
        allowed = set(schema["required"]) | set(schema["optional"]) | {"type"}
        for key in data:
            if key in allowed:
                continue
            close = difflib.get_close_matches(key, sorted(allowed), n=1, cutoff=0.7)
            result.add_warning(ValidationError(
                code="UNKNOWN_DATA_FIELD",
                message=f"Node '{node_name}' has unrecognised data field: '{key}'",
                node_id=node_id,
                node_name=node_name,
                field=key,
                suggestion=(f"Did you mean '{close[0]}'?" if close
                            else f"Known fields: {', '.join(sorted(allowed))}")
            ))

        # Type-specific validation
        if node_type == "Http":
            method = data.get("method")
            if method:
                if not isinstance(method, str):
                    result.add_error(ValidationError(
                        code="INVALID_HTTP_METHOD",
                        message=f"HTTP method must be a string, got "
                                f"{type(method).__name__}: {method!r}",
                        node_id=node_id,
                        node_name=node_name,
                        field="method",
                        suggestion=f"Use one of: {', '.join(sorted(VALID_HTTP_METHODS))}"
                    ))
                elif method.upper() not in VALID_HTTP_METHODS:
                    result.add_error(ValidationError(
                        code="INVALID_HTTP_METHOD",
                        message=f"Invalid HTTP method: '{method.upper()}'",
                        node_id=node_id,
                        node_name=node_name,
                        field="method",
                        suggestion=f"Use one of: {', '.join(sorted(VALID_HTTP_METHODS))}"
                    ))

        if node_type == "Code":
            lang = data.get("language")
            if lang:
                if not isinstance(lang, str):
                    result.add_error(ValidationError(
                        code="INVALID_CODE_LANGUAGE",
                        message=f"Code language must be a string, got "
                                f"{type(lang).__name__}: {lang!r}",
                        node_id=node_id,
                        node_name=node_name,
                        field="language",
                        suggestion=f"Use one of: {', '.join(sorted(VALID_CODE_LANGUAGES))}"
                    ))
                elif lang.lower() not in VALID_CODE_LANGUAGES:
                    result.add_error(ValidationError(
                        code="INVALID_CODE_LANGUAGE",
                        message=f"Invalid code language: '{lang.lower()}'",
                        node_id=node_id,
                        node_name=node_name,
                        field="language",
                        suggestion=f"Use one of: {', '.join(sorted(VALID_CODE_LANGUAGES))}"
                    ))

    # Check Start/End presence
    if not start_ids:
        result.add_error(ValidationError(
            code="MISSING_START",
            message="Workflow has no Start node",
            suggestion="Add a node with type 'Start'"
        ))
    elif len(start_ids) > 1:
        result.add_warning(ValidationError(
            code="DUPLICATE_START",
            message=f"Workflow has {len(start_ids)} Start nodes",
            suggestion="Keep exactly one Start node"
        ))

    if not end_ids:
        result.add_error(ValidationError(
            code="MISSING_END",
            message="Workflow has no End node",
            suggestion="Add a node with type 'End'"
        ))
    elif len(end_ids) > 1:
        result.add_warning(ValidationError(
            code="DUPLICATE_END",
            message=f"Workflow has {len(end_ids)} End nodes",
            suggestion="Keep exactly one End node"
        ))

    # Validate edges
    if isinstance(edges, list):
        for i, edge in enumerate(edges):
            if not isinstance(edge, dict):
                result.add_error(ValidationError(
                    code="INVALID_EDGE",
                    message=f"Edge at index {i} is not an object",
                ))
                continue

            source = edge.get("source", "")
            target = edge.get("target", "")

            if not source:
                result.add_error(ValidationError(
                    code="MISSING_EDGE_SOURCE",
                    message=f"Edge at index {i} has no 'source'",
                ))
            elif source not in node_ids:
                result.add_error(ValidationError(
                    code="INVALID_EDGE_SOURCE",
                    message=f"Edge references unknown source node: {source}",
                    suggestion="Ensure the source ID matches an existing node"
                ))

            if not target:
                result.add_error(ValidationError(
                    code="MISSING_EDGE_TARGET",
                    message=f"Edge at index {i} has no 'target'",
                ))
            elif target not in node_ids:
                result.add_error(ValidationError(
                    code="INVALID_EDGE_TARGET",
                    message=f"Edge references unknown target node: {target}",
                    suggestion="Ensure the target ID matches an existing node"
                ))

            if source == target:
                result.add_error(ValidationError(
                    code="SELF_LOOP",
                    message=f"Edge connects node to itself: {source}",
                ))

            # The designer derives edge ids from the endpoints
            expected_id = f"xy-edge__{source}-{target}"
            edge_id = edge.get("id")
            if not edge_id:
                result.add_warning(ValidationError(
                    code="MISSING_EDGE_ID",
                    message=f"Edge at index {i} has no 'id'",
                    suggestion=f"Use id: {expected_id}"
                ))
            elif source and target and edge_id != expected_id:
                result.add_warning(ValidationError(
                    code="EDGE_ID_MISMATCH",
                    message=f"Edge id '{edge_id}' does not match its endpoints",
                    suggestion=f"Use id: {expected_id}"
                ))

    # Connectivity — a structurally valid graph can still do nothing
    _check_connectivity(result, nodes, edges, node_ids, start_ids, end_ids)

    return result


def _check_connectivity(result, nodes, edges, node_ids, start_ids, end_ids):
    """Warn about nodes unreachable from Start or with no path to End."""
    if not node_ids or not isinstance(edges, list):
        return

    forward = {nid: set() for nid in node_ids}
    backward = {nid: set() for nid in node_ids}
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        src, tgt = edge.get("source"), edge.get("target")
        if src in node_ids and tgt in node_ids:
            forward[src].add(tgt)
            backward[tgt].add(src)

    def reach(seeds, adjacency):
        seen, stack = set(seeds), list(seeds)
        while stack:
            for nxt in adjacency[stack.pop()]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    from_start = reach([s for s in start_ids if s in node_ids], forward)
    to_end = reach([e for e in end_ids if e in node_ids], backward)

    for node in nodes:
        if not isinstance(node, dict):
            continue
        nid = node.get("id")
        if nid not in node_ids:
            continue
        data = node.get("data")
        name = data.get("name", node.get("type", "")) if isinstance(data, dict) else node.get("type", "")

        if start_ids and nid not in from_start:
            result.add_warning(ValidationError(
                code="UNREACHABLE_NODE",
                message=f"Node '{name}' is not reachable from Start",
                node_id=nid,
                node_name=name,
                suggestion="Add an edge connecting it to the flow, or remove it"
            ))
        elif end_ids and nid not in to_end:
            result.add_warning(ValidationError(
                code="NO_PATH_TO_END",
                message=f"Node '{name}' has no path to the End node",
                node_id=nid,
                node_name=name,
                suggestion="Add an outgoing edge so the flow can terminate"
            ))


def validate_file(file_path: str) -> ValidationResult:
    """Validate a workflow JSON file."""
    path = Path(file_path) if not isinstance(file_path, Path) else file_path

    if not path.exists():
        result = ValidationResult()
        result.add_error(ValidationError(
            code="FILE_NOT_FOUND",
            message=f"File not found: {file_path}",
        ))
        return result

    try:
        text = path.read_text(encoding="utf-8")
        graph = json.loads(text)
    except json.JSONDecodeError as e:
        result = ValidationResult()
        result.add_error(ValidationError(
            code="INVALID_JSON",
            message=f"File is not valid JSON: {e}",
            suggestion="Check for syntax errors in the JSON file"
        ))
        return result

    return validate_graph(graph)
