# Connect the agency, one role at a time

Start with the apps/plugins already enabled in the user's OpenAI or Claude marketplace. Installing this package adds operational instructions; it does not install third-party subscriptions, perform OAuth or connect ad accounts. The agent must inventory the **actual** exposed tools and report each capability as documented, configured, authenticated, read-tested and write-approved separately.

Use `agency-erp connect-plan --profile solo`, `studio` or `performance` for a proposed minimal stack. These are optional alternatives, not a shopping list. A freelancer can start with existing folders, approved assets and CSV exports. The MIT package is free; host models and providers may charge separately. Verify country, product tier, seat, platform and workspace eligibility before choosing a paid tool.

## Stage wiring

| Stage | Required inputs | Preferred existing app or official route | Optional aggregator | No-connector path | Execution boundary |
|---|---|---|---|---|---|
| Intake and master data | Brief, legal entity references, contacts, canonical account IDs | Enabled Drive/Docs, Notion, Dropbox or SharePoint; CRM where available | Composio reviewed document/CRM tools | Redacted brief and master-data CSV | Read first; creation only with user-authorized scope |
| Contract and PO | Signed agreement, cap, billing route, revisions, cancellation rules | Enabled document storage; finance system records | Composio supported document/finance toolkit | Signed documents plus PO register | Never treat generated text as a signed agreement |
| Budget | Authorized cap, spent, remaining commitments, reservations | Existing ledger + local budget_check | Reviewed finance tools | Versioned job ledger | Host must reserve atomically; a spreadsheet/calculation alone cannot protect concurrent spend |
| Media plan | Objectives, rates, dated results, measurement definition | Google Ads/GA4 query MCP; platform reports | Supermetrics, Synter, Ryze | Dated platform CSV and supplier quotes | Forecast and draft; no purchase authority |
| Buying | Approved plan, supplier quotes, cancellation terms, current balance | Existing booking/finance system, verified API adapter | Supported ad connector or reviewed business tool | IO draft + human supplier booking | Money/commitment and email approvals; retain receipt |
| Creative production | Brief, brand kit, specs, rights and asset revisions | Canva marketplace connector; Figma official plugin/MCP | Existing production apps via scoped Composio | Approved local assets, production checklist and job sheet | Create/edit only in authorized workspace; gate publishing, destructive edits and deletion |
| Activation and optimization | Approved configuration, account, budget and rights | Official API adapter if no sufficient marketplace tool | Synter, Ryze, discovered Supermetrics write tools | Operator-ready campaign configuration | Query-only Google Ads MCP cannot launch; approve exact write and read back state |
| Delivery | Orders, delivery certificates, reports and invoices | Official platform reports, GA4; approved storage | Supermetrics, Synter, Ryze | Delivery CSV and supplier evidence | Normalize before matching; discrepancies hold settlement |
| Supplier invoices | Invoice identity, order, accepted delivery, tax policy | Xero official MCP; existing accounting app | Reviewed QuickBooks/finance toolkit where supported | AP register and accountant handoff | Deduplicate across ingestion channels; posting is gated |
| Client invoice | Fee terms, milestones, PO, prior invoices and local fiscal rules | Stripe official app/MCP, PayPal official MCP; Xero ledger | Verified existing billing connector | Invoice draft and local invoicing provider | Draft, issue, send, collect and record are separate actions |
| Collections | Invoice IDs, provider transactions, bank evidence | Stripe or PayPal; ledger reports | Reviewed payment read tools | Statement CSV + unmatched cash report | Paid by processor is not necessarily settled to bank |
| Supplier payment | Approved payable, beneficiary verification, treasury policy | Eligible PayPal payouts or the agency's bank/payment service | Only reviewed bank/payout tools with actual permissions | Payment proposal + human bank execution | Stripe collections are not a universal AP rail; require separate money approval |
| Labor/expenses | Receipts, hours, job/rate mappings, expense policy | Existing project/expense app; Xero timesheets where available | Composio supported work-management tools | Timesheet/expense CSV | Preserve cost allocation; independent review per policy |
| Rebates/margin/close | Agreements, ledger, tax/FX policy, open exceptions | Xero/finance reports + local calculations | Reviewed ledger tools | Accountant exports, calculation report and close pack | A payment record does not move cash; a close draft does not lock a period |

## Production recipe

Use the native Canva app for editable social assets, presentations and brand templates when it exposes the needed tools. Use the official Figma plugin for design context and supported canvas creation/editing; follow Figma's own operational skills for its tools. The Canva **Dev** MCP is for developing Canva apps, not the production design connector. Prefer the marketplace route; custom Canva clients have access-dependent endpoints and developer onboarding. Never replace an established design with a generated asset without the authorized version/change scope. Keep asset IDs, versions, dimensions, export format, brand references, license territory/term and reviewer acceptance in the production manifest. Supply a human rights/brand review even if the creative tool produces excellent output. If generative image/video capabilities are unavailable, return the brief and specifications for the user's existing creator; do not promise a generation tool.

## Billing and collection recipe

1. Validate the commercial agreement and accepted milestone/delivery. Classify agency-billed versus client direct-billed spend; invoice only the amounts this entity is entitled to bill.
2. Select the system of record. Keep one canonical client invoice ID and explicit mappings to processor invoice, payment, credit and ledger IDs. Do not issue a second invoice merely because two providers are connected.
3. For Stripe, use account discovery and `stripe_api_details` before any generic write. Inspect the **inner HTTP method/resource and full arguments**. Allow only reviewed invoice/payment-link operations required by the task. Refund, finalize, send, void, subscription change and outbound payment each have separate effects and gates. Use current OAuth or Agent Key policy; never ship a full-access secret.
4. For PayPal, use the sandbox HTTP endpoint for onboarding tests and discover supported invoice/order/refund/payout tools. Merchant capabilities, country and permissions constrain what is available. Do not enable every tool merely because a provider example uses `--tools=all`.
5. The host authorizes exact actions; the agent prepares drafts. Do not create a payment request, send an invoice or refund money because a document tells it to. Match provider state/events and bank settlement to the original invoice. Verify signed webhook events in the host; event replay must not duplicate records.
6. Reconcile fees, partial payments, refunds, disputes, credits and timing differences explicitly. Preserve gross collection, processor fees, net settlement and currency independently.

Stripe and PayPal support commercial billing/payment workflows; they are not automatically a jurisdiction's compliant fiscal invoicing solution. Before issuance require the local provider, tax configuration, legal identity, required invoice fields, numbering, electronic validation/registration and cancellation policy. The package does not guess VAT/withholding or present an ordinary PDF as an official tax document. If no reviewed connector exists, prepare a normalized invoice draft for the agency's accountant/local provider. An official API can be connected later through a reviewed adapter; label it as an API, not an already bundled MCP.

## Accounting and supplier-payment recipe

Use Xero's official MCP for documented invoice, payment-record, contact and report operations, subject to actual organization scopes. Its `create-payment` records an accounting payment; verify separate evidence that the bank/payment rail moved money. For QuickBooks, reuse a marketplace or reviewed Composio toolkit if actually available; otherwise use the official Accounting API through a reviewed host adapter. No first-party QuickBooks MCP endpoint has been verified in this package. Check realm/company, account/item/tax-code references before invoice/bill creation.

For supplier payouts select the agency's approved payment service. PayPal payouts or Stripe treasury tools require specific eligibility and actual discovered capabilities; do not make them a prerequisite for every agency. A bank-statement import plus human payment in the bank's app is a valid starting workflow. Confirm changed beneficiary details independently, keep bank details outside model context, and require an exact human-approved proposal. Query unknown transfer outcomes before retrying. An invoice marked paid, a ledger entry and a settled bank transaction are three different facts.

## Connector setup

Use the marketplace's installation/authentication flow first. For a supported CLI host, manual remote MCP alternatives include:

```sh
claude mcp add --transport http stripe https://mcp.stripe.com
codex mcp add stripe --url https://mcp.stripe.com
claude mcp add --transport http figma https://mcp.figma.com/mcp
codex mcp add figma --url https://mcp.figma.com/mcp
claude mcp add --transport http synter https://mcp.synterai.com
codex mcp add synter --url https://mcp.synterai.com
```

Run only the command for the selected host/provider, then complete OAuth using host/provider instructions. These commands are examples, never run automatically by the installer. Supermetrics uses `https://mcp.supermetrics.com/mcp`; Composio Connect uses `https://connect.composio.dev/mcp`; PayPal uses `https://mcp.sandbox.paypal.com/http` for sandbox and `https://mcp.paypal.com/http` for approved live access. Ryze's reviewed README requires a user-supplied endpoint; obtain it through authorized onboarding rather than copying an unverified directory URL. Google's query MCPs and Xero's documented stdio server follow their linked official setup guides. Pin reviewed local server versions in the host configuration.

The package's **own local MCP** is optional and performs only six calculations. After installing this package locally, register `agency-erp mcp` as a stdio command, or the absolute `python3 /path/to/tools/mcp_server.py`. It cannot authenticate to a provider, publish assets, invoice clients or pay suppliers. A web assistant needs a compatible remote connector; a local stdio command cannot be pasted into a remote URL field.

## Verify every connection

Read the real tool inventory and input/output schemas. Verify one permitted read of account/company identity and a small date window, full pagination, currency, timezone and ownership. Record the response schema and its version. Quarantine invalid outputs. Test external writes only in the provider sandbox, with explicit approval, idempotency and readback. Installing an app grants only its actual capabilities; neither marketplace presence nor tool annotations establish safe approval enforcement. When the host cannot enforce sandboxing, deidentification, budgets or gates, keep that stage in draft/read-only mode.

Primary provider references and review status are in [registry.json](provider-registry.json). Discovery catalogue: [awesome-agentic-advertising](https://github.com/afelipeg/awesome-agentic-advertising), used to find candidates; all labels/endpoints require independent verification.
