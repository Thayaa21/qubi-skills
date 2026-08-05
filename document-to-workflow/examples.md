# Document-to-Workflow Examples

## Example 1: Invoice Processing PDD

**Document says:**
> 1. Receive invoice PDF via email
> 2. Extract invoice number, vendor, amount, and line items using OCR
> 3. Validate amount against PO in the ERP system
> 4. If amount matches (±5%), auto-approve
> 5. If amount doesn't match, route to AP manager for review
> 6. Once approved, post to ERP

**Generated workflow:**

```
Start → DocumentAI (extract invoice) → Http (lookup PO in ERP) → JsonParser (get PO amount)
  → Code (compare amounts) → Branch (within tolerance?)
    → Yes: Http (post to ERP) → End
    → No: HitlTask (AP manager review) → Http (post to ERP) → End
```

---

## Example 2: Employee Onboarding SOP

**Document says:**
> 1. HR creates employee record in HRIS
> 2. IT provisions email account
> 3. IT provisions laptop
> 4. Manager assigns onboarding buddy
> 5. System sends welcome email to new hire
> 6. Schedule orientation meeting

**Generated workflow:**

```
Start → Http (create HRIS record) → Http (provision email)
  → Http (provision laptop) → HitlTask (assign buddy)
  → Agent (compose welcome email) → Http (send email)
  → Http (schedule orientation) → End
```

---

## Example 3: Customer Support Ticket Routing (BRD)

**Document says:**
> Requirements:
> - Tickets arrive via API webhook
> - Classify ticket: billing, technical, general
> - Billing → route to billing team
> - Technical → check if known issue (search KB), if yes auto-reply, if no escalate
> - General → AI auto-respond

**Generated workflow:**

```
Start → JsonParser (extract ticket fields)
  → Agent (classify: billing/technical/general) → Branch (category?)
    → billing: Assign (team=billing) → Http (route to billing queue) → End
    → technical: Http (search KB) → Branch (found?)
        → yes: Agent (compose KB reply) → Http (send reply) → End
        → no: HitlTask (escalate to eng) → End
    → general: Agent (auto-respond) → Http (send reply) → End
```

---

## Example 4: Data Pipeline (Spreadsheet)

**Spreadsheet has columns: Step | Source | Action | Destination**

| Step | Source | Action | Destination |
|------|--------|--------|-------------|
| 1 | Salesforce API | Fetch new leads | Variable: leads |
| 2 | leads | Filter score > 80 | Variable: hotLeads |
| 3 | hotLeads | Enrich with Clearbit | Variable: enriched |
| 4 | enriched | Format for CRM | Variable: formatted |
| 5 | formatted | Push to HubSpot | HubSpot API |

**Generated workflow:**

```
Start → Http (GET Salesforce leads) → Code (filter score > 80)
  → Http (Clearbit enrich) → Code (format for CRM)
  → Http (POST to HubSpot) → End
```

---

## Mapping Patterns

| Document Phrase | Node Type | Rationale |
|----------------|-----------|-----------|
| "Extract from PDF/image" | DocumentAI | Document processing |
| "Call [system] API" | Http | External integration |
| "If [condition] then..." | Branch | Decision point |
| "Summarize / Classify / Generate" | Agent | AI/LLM task |
| "Calculate / Filter / Transform" | Code | Deterministic logic |
| "Manager approves" | HitlTask | Human decision |
| "Set [variable] to [value]" | Assign | Variable assignment |
| "Parse the response" | JsonParser | Structured extraction |
| "Extract [pattern] from text" | TextParser | Regex extraction |
| "Run desktop automation" | RPA | UI automation |
