# qubi-skills

AI Skills for building qubi Agentic Flows workflows. Each skill teaches an AI agent (Claude/Kiro) a specific capability.

## Skills

| Skill | Purpose |
|-------|---------|
| **workflow-builder** | Generate workflow JSON from plain English prompts |
| **document-to-workflow** | Read PDDs, SDDs, BRDs, process docs → generate workflow JSON |
| **workflow-optimizer** | Analyze and improve existing workflows |

## How Skills Work

Each skill is a set of markdown files that an AI agent reads to understand:
- What it can do
- What schema/format to follow
- What rules to obey
- Examples to pattern-match from

## Usage

Point your AI agent (Claude Code, Kiro, etc.) at the skill folder:
- Claude Code: symlink or copy into `.claude/skills/`
- Kiro: reference in `.kiro/steering/`

## Skill Structure

```
skill-name/
├── SKILL.md              # Main entry — when to invoke, rules, phases
├── schema-reference.md   # Node types, fields, formats
├── examples.md           # Complete working examples
└── error-handling.md     # How to fix validation errors
```

## Adding a New Skill

1. Create a folder: `my-new-skill/`
2. Write `SKILL.md` with: what it does, when to invoke, phases, rules
3. Add supporting reference files as needed
4. Test it by pointing Claude at the skill and giving it a task
