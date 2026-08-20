---
name: document-ai-nodes
description: "Add DocumentAI nodes to qubi Agentic Flows for OCR, extraction, and classification of uploaded files. Use when a workflow processes PDFs, scans, invoices, or any uploaded document."
---

# DocumentAI Nodes

> `operation` is a required dropdown whose real option list has never been captured. This skill exists so nobody fills it with a guess that looks confident.

## What this skill is

`DocumentAI` runs document processing (OCR, field extraction, classification) on a file the workflow already has a reference to. It's used 15 times across the 100-workflow evaluation corpus, always fed by a variable pointing at an uploaded file and always feeding its output into a `JsonParser` or `Agent` node downstream.

## What it solves

`operation` is `DocumentAI`'s one required field beyond `name`, and it is a platform dropdown. `schema-extractor/output/element_properties.json` in qcli-web records it as `type: select, required: true, options: null` -- the designer offers a fixed list of choices, and that list was never captured during schema extraction. Despite that, the repo's own `workflow-builder/schema-reference.md` used to ship `"operation": "extract"` as if it were a confirmed value. It wasn't observed anywhere; it was a plausible-sounding guess. This skill's job is to stop that pattern from recurring.

## When to invoke

- The user's workflow processes a PDF, scanned document, image, or any uploaded file
- The user mentions OCR, document extraction, or document classification
- `qcli flow validate` reports `MISSING_REQUIRED_FIELD` on a `DocumentAI` node

## Node reference

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `operation` | yes | **Platform dropdown, options never captured. See Unverified.** |
| `description` | no | |
| `fileVariable` | no | Name of the variable holding the file reference |
| `saveOutputAs` | no | |
| `input` | no | |

## Phase 1: Get a file reference into a variable

`DocumentAI` reads from `fileVariable`, which must name a variable already set earlier in the flow -- typically via `Assign` (see [variables-and-assign](../variables-and-assign/SKILL.md)) or a prior node's `saveOutputAs`. See [fixtures/extract_from_upload.json](fixtures/extract_from_upload.json): `Assign` sets `filePath`, then `DocumentAI` reads it.

## Phase 2: Fill `operation` without inventing a value

Do not write `"operation": "extract"` or any other specific-sounding string as if it's confirmed -- it isn't. Two options:

1. Ask the human what operation the designer offers for this node (they can check by opening a DocumentAI node in the designer).
2. If unavailable, use the sentinel `"operation": "UNVERIFIED"` and tell the human this field must be set from the designer's dropdown before the workflow is saved.

```json
{
  "type": "DocumentAI",
  "name": "Extract Invoice Fields",
  "operation": "UNVERIFIED",
  "fileVariable": "filePath",
  "saveOutputAs": "extractedData"
}
```

## Phase 3: Chain the output downstream

`DocumentAI`'s output is almost always consumed by a `JsonParser` (to pull specific fields) or an `Agent` (to reason over the extracted text). See [fixtures/document_to_agent.json](fixtures/document_to_agent.json) for the DocumentAI-to-Agent shape via `saveOutputAs` / `{{extractedData}}`.

## Phase 4: Validate

```bash
qcli flow validate <file.json>
```

Leaving out `operation` produces `MISSING_REQUIRED_FIELD` -- see [fixtures/invalid/documentai_no_operation.json](fixtures/invalid/documentai_no_operation.json).

## Unverified

| ID | Claim | Why unverifiable offline | How to verify | Status |
|----|-------|---------------------------|----------------|--------|
| UV-DOCAI-01 | `operation` accepts a value like `extract`, `ocr`, or `classify` | Designer dropdown; option list not captured (`schema-extractor/output/element_properties.json` shows `options: null`) | Open a DocumentAI node in the designer and read the Operation dropdown | open |

## Operating Rules

**Always:**
- Point `fileVariable` at a variable that's actually set earlier in the flow
- Use the `UNVERIFIED` sentinel for `operation` unless a human has confirmed the real value
- Tell the human explicitly when a field needs their confirmation before saving

**Never:**
- Write a specific `operation` value ("extract", "ocr", etc.) as if it's a confirmed enum -- none has been observed
- Assume `DocumentAI` can read a file it hasn't been given a variable reference to
