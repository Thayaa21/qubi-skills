---
name: http-nodes
description: "Call external APIs from qubi Agentic Flows with Http nodes -- the five valid methods, headers, body, and URL interpolation. Use when a workflow makes an HTTP request."
---

# HTTP Nodes

> The designer's Method dropdown offers exactly five values. Older documentation in this repo claimed seven -- this skill pins the number that was actually captured, so it doesn't drift again.

## What this skill is

`Http` is the most-used node type in the evaluation corpus by a wide margin (253 instances, 66 of 100 workflows) -- so the gap here isn't coverage, it's **truth drift**. A prior version of this repo's schema reference documented `GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS` as valid methods. The captured designer dropdown (`schema-extractor/output/element_properties.json`, `HTTP.Method.options`) records exactly `['GET', 'POST', 'PUT', 'DELETE', 'PATCH']` -- five, not seven. `HEAD` and `OPTIONS` are not offered by the platform. This skill exists so that number stays anchored to the capture, not to whatever seemed plausible.

## When to invoke

- The user's workflow calls an external API
- `qubi flow validate` reports `INVALID_HTTP_METHOD`

## Node reference

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `method` | yes | `GET`, `POST`, `PUT`, `DELETE`, `PATCH` only -- the platform's full dropdown, no other values are valid |
| `url` | yes | Supports `{{variable}}` interpolation |
| `description` | no | |
| `input` | no | |
| `headers` | no | Object of header name → value |
| `body` | no | Request body (object, sent as JSON) |
| `saveOutputAs` | no | |

## Phase 1: GET and chain the response

The plain case -- see [fixtures/get_then_parse.json](fixtures/get_then_parse.json): `Http` GET saves its response, `JsonParser` extracts fields from it (see [json-parser-nodes](../json-parser-nodes/SKILL.md)).

## Phase 2: Headers and body for writes

`POST`/`PUT`/`PATCH` typically need both. See [fixtures/post_with_headers.json](fixtures/post_with_headers.json): `Authorization` header interpolating a stored API key, `body` interpolating a stored customer name.

```json
{
  "type": "Http",
  "name": "Create Customer",
  "method": "POST",
  "url": "https://api.example.com/customers",
  "headers": { "Content-Type": "application/json", "Authorization": "Bearer {{apiKey}}" },
  "body": { "name": "{{customerName}}" },
  "saveOutputAs": "customer"
}
```

## Phase 3: Validate

```bash
qubi flow validate <file.json>
```

`HEAD` and `OPTIONS` both fail with `INVALID_HTTP_METHOD` -- see [fixtures/invalid/http_method_head.json](fixtures/invalid/http_method_head.json). A non-string `method` value also fails with `INVALID_HTTP_METHOD` rather than crashing -- see [fixtures/invalid/http_method_not_string.json](fixtures/invalid/http_method_not_string.json).

## Operating Rules

**Always:**
- Use one of exactly five methods: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`
- Set `Content-Type` explicitly when sending a `body`
- Use `{{variable}}` interpolation in `url`/`headers`/`body` rather than hardcoding values that came from an earlier step

**Never:**
- Use `HEAD` or `OPTIONS` -- they are not in the platform's dropdown, regardless of what older documentation in this repo may say
- Hardcode a value in `url`/`body` that was already saved as a variable earlier in the flow
