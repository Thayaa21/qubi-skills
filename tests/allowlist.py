"""
Reviewed exceptions for the claim linter.

Kept as a file rather than an inline regex so that every addition shows up in
a diff and has to be justified in review.
"""

#: SCREAMING_SNAKE tokens that appear in skill docs but are not diagnostic codes.
NON_CODE_TOKENS = {
    # environment variables
    "QUBI_TENANT", "QUBI_USERNAME", "QUBI_PASSWORD", "QUBI_SERVER", "QCLI_WEB",
    "QUBI_SKILLS_ALLOW_VENDORED",
    # symbols exported by qcli.schema, referenced when explaining the validator
    "NODE_TYPES", "VALID_HTTP_METHODS", "VALID_CODE_LANGUAGES", "UUID_SHAPE",
    "DEFAULT_VIEWPORT", "DEFAULT_EXECUTION_MODE", "DEFAULT_AGENTHUB",
    # sentinel value for unverifiable enum fields
    "UNVERIFIED",
}

#: Skills exempted from a specific rule, with a reason. Prefer fixing the skill.
#: Format: {"skill-name": {"rule-name": "why"}}
RULE_EXEMPTIONS: dict[str, dict[str, str]] = {}

#: Things that cannot be verified without a live qubi server and are not node
#: fields, so they do not come out of the schema-extractor capture.
NON_FIELD_UNKNOWNS = [
    ("UV-RUNTIME-01", "{{variable}} interpolation semantics at runtime",
     "No local interpreter; the validator never evaluates templates",
     "Run a flow that interpolates a saved variable and read the job output"),
    ("UV-RUNTIME-02", "Whether `qubi flow run` actually executes a workflow",
     "Both REST endpoints and the SignalR hub are unreachable offline",
     "Run any saved workflow and confirm a job id comes back"),
    ("UV-HITL-01", "Whether a Hitl node contains or merely precedes HitlTask nodes",
     "The graph format has no nesting field; the designer's behaviour is unobserved",
     "Drop a Hitl node in the designer and see whether it accepts children"),
    ("UV-BRANCH-01", "The shape of Branch.conditions",
     "The field is optional, so the validator never inspects it",
     "Configure a two-way branch in the designer and download the graph"),
    ("UV-JSONPARSER-01", "The shape of JsonParser.mappings",
     "The field is optional, so the validator never inspects it",
     "Configure a mapping in the designer and download the graph"),
    ("UV-TEXTPARSER-01", "The shape of TextParser.outputMappings",
     "The field is optional, so the validator never inspects it",
     "Configure a capture-group mapping in the designer and download the graph"),
    ("UV-ASSIGN-01", "The shape of Assign.assignments",
     "The field is optional, so the validator never inspects it",
     "Configure two assignments in the designer and download the graph"),
    ("UV-ENVELOPE-01", "Whether executionMode accepts any value besides Sequential",
     "Only Sequential has ever been observed in captured payloads",
     "Check the designer for a parallel/other execution mode setting"),
]
