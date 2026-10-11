# Workflow catalogue

Generated from `contracts/workflows.json` by `scripts/sync_resources.py`; edit the catalogue, not this file.

Start with agency-orchestrator and agency-integrations; run only relevant stages. The circuit map is [erp-reference/e2e-circuit.md](erp-reference/e2e-circuit.md); detailed rules live in [operations-playbook.md](operations-playbook.md) and the [ERP functional reference](erp-reference/README.md). Skills accept connected tools or supplied files ([file-mode.md](file-mode.md), [integrations.md](integrations.md)). This catalogue is a routing index, not authorization.

## agency-orchestrator

Runs an agency job end to end: reads JobNumber and document state, maps the next ERP stages and routes to the right skill. Use to start, resume or triage a job. Never approves.

**Inputs:** Trusted tenant/client/job ids and JobNumber; JobNumber state and documents with revisions; period state per subledger; approval-circuit configuration; commercial scope; prior checkpoints; run ceilings; available tools.

**Outputs:** `job_state`, `dependency_graph`, `period_gate_status`, `task_assignments`, `blockers`, `approval_requests`, `checkpoints`, `next_stage`

**ERP reference:** circuit map only. **Tools:** `payload_digest`, `job_number`.

**Owner:** Account director and controller. **Next:** agency-onboarding and agency-integrations for new jobs, then dependency-ready stages.

1. Load identity, checkpoints and upstream revisions; mark stale dependents.
2. Decode the JobNumber with job_number and keep its typology and billing flags as routing constraints.
3. Route by JobNumber state and place each document in its lifecycle state with one owner skill.
4. Build the dependency graph for the actual scope and record reasons for skipped stages.
5. Check period, PO, credit, client-approval, closed-order and billing gates before dispatching mutations.
6. Dispatch read-only work concurrently, serialize shared mutations, and digest approval requests with payload_digest.
7. Assess job close readiness and the month-end period gate, then checkpoint and return.

## agency-onboarding

Onboards a client or brand: owner vs billing clients, products, attention groups, brief and contact reports. Use when a client is won or changes. No legal or tax facts from websites.

**Inputs:** Tenant id; trade name; billing-client references from trusted CxC records; product names and agreed commission percentages; provisional-master and hierarchy configuration; brief recipients and body; registered contact attendees.

**Outputs:** `intake_pack`, `owner_client_draft`, `billing_client_links`, `product_drafts`, `attention_group_plan`, `provisional_approval_requests`, `brief_draft`, `intake_gaps`

**ERP reference:** [accounts-jobs](erp-reference/accounts-jobs.md). **Tools:** `job_number`.

**Owner:** Account manager. **Next:** agency-master-data, then agency-job-lifecycle and agency-contract-po.

1. Separate the trade-name owner client from its legal billing clients and check duplicates on evidence.
2. Draft the owner client and products with codes, commission percentages, rate-card mode and hierarchy.
3. Preview the first JobNumber with job_number and report billing or typology warnings.
4. Design attention groups with one head and send approval functions for SoD review.
5. Route records through the provisional chain: requester, optional intermediate approver, final approver.
6. Draft one strategic brief per job and contact reports with registered attendees, then return the intake pack.

## agency-master-data

Maintains agency masters: clients, suppliers, media outlets, programs, dayparts, GL account tags, cost centers. Use to create, map or deactivate records. Never deletes used records.

**Inputs:** Tenant id; master type and payload; current records with usage status; legal identity evidence under restricted access; chart of accounts with observation codes; bridge-account and provisional-master configuration.

**Outputs:** `master_change_set`, `validation_report`, `duplicate_candidates`, `ledger_link_map`, `external_code_map`, `deactivation_plan`, `provisional_approval_requests`

**ERP reference:** [media-masters-ooh](erp-reference/media-masters-ooh.md), [accounts-jobs](erp-reference/accounts-jobs.md), [management-security](erp-reference/management-security.md). **Tools:** `job_number`.

**Owner:** Data steward and controller. **Next:** agency-job-lifecycle, agency-rate-cards-contracts, agency-media-planning, agency-general-ledger.

1. Read the record and its usage to decide deactivate versus delete; never delete used masters.
2. Resolve identity on stable ids and legal evidence; propose merges without deleting originals.
3. Build media masters top-down: generic type, media type, publication type, outlet with one default supplier.
4. Validate daypart 7x24 coverage, cut-off sorting and duration factors with proportional fallback.
5. Link observation-coded ledger accounts per media and production type and maintain cost centers and divisions.
6. Map external codes, route changes through the provisional chain and return the change set.

## agency-integrations

Plans which connectors each ERP stage needs (ad platforms, ledgers, e-invoicing, docs), verifies live access and falls back to files. Use when connecting tools. Never asks for secrets.

**Inputs:** Host type; stages in scope; tenant, client and platform account ids from trusted records; enabled marketplace apps and MCP servers; approved tool policy; host approval, sandbox and idempotency support; country context.

**Outputs:** `capability_inventory`, `stage_wiring_plan`, `access_matrix`, `schema_review`, `connection_requests`, `file_mode_plan`, `gaps`

**ERP reference:** [management-security](erp-reference/management-security.md). **Tools:** none.

**Owner:** Operations lead. **Next:** agency-access-governance, then the requesting stage or agency-orchestrator.

1. Inventory enabled apps and MCP tools and follow the registry selection order.
2. Map required reads and writes per stage and select candidates by role, not brand.
3. Request authentication through the host vault and verify identity with one permitted read.
4. Review output schemas and quarantine mismatches; no schema means drafts only.
5. Allowlist inner tools by least privilege and gate writes with approval, idempotency, sandbox and readback.
6. Plan file mode for gaps and report documented, configured, authenticated, read-tested and write-approved separately.

## agency-access-governance

Reviews roles, approval powers, cost visibility and segregation of duties; controls config changes and offboarding. Use when granting or auditing access. Never grants access itself.

**Inputs:** Tenant id; users, profiles, roles, specific activities and expense approval caps; agency SoD matrix; security policy; for parameter changes current and proposed values with reason; for offboarding the leaver, successor and owned open items.

**Outputs:** `access_matrix`, `capability_register`, `sod_conflicts`, `access_change_requests`, `config_change_requests`, `offboarding_plan`, `audit_evidence_pack`

**ERP reference:** [management-security](erp-reference/management-security.md). **Tools:** `payload_digest`.

**Owner:** Controller and system administrator. **Next:** agency-integrations, agency-orchestrator, or the requesting stage.

1. Build the access matrix with S/N, action levels 1-6 and cost visibility A-D per user and screen.
2. Register approval powers as capabilities and check structural user rules.
3. Run the SoD review against the agency matrix and fingerprint it with payload_digest.
4. Prepare grants on shared roles and show propagation; keep C/D fields out of model context.
5. Control parameter changes with before/after, downstream impact and a digested change request.
6. Plan offboarding by reassigning tasks, jobs and approvals before end-dating, and assemble audit evidence.

## agency-job-lifecycle

Creates, moves, re-bills and closes campaign JobNumbers under typology and billing-code rules, with the two-step close. Use when a job is opened, changed or closed.

**Inputs:** Tenant ID; titular client and product codes; requested action; start year, typology, billing code and billing client for opens; job content listing with document statuses and open tasks; acting user's department type and level; inactivity-days configuration.

**Outputs:** `job_proposal`, `job_code_check`, `move_or_substitution_plan`, `close_readiness`, `inactive_job_list`, `job_audit_note`

**ERP reference:** [accounts-jobs](erp-reference/accounts-jobs.md). **Tools:** `job_number`.

**Owner:** Account director (accounts close) and finance (definitive close). **Next:** agency-fee-contracts, agency-contract-po, agency-production-estimating, agency-media-planning, agency-period-close.

1. Verify the actor is an Accounts collaborator with job-creation level and the billing client is linked.
2. Compose the 12-character code with job_number and check typology and billing-code restrictions.
3. Validate modifications, moves, substitutions and billing-client changes against invoiced locks.
4. List accounts-close blockers: unfinished tasks and documents pending approvals.
5. List definitive-close blockers: documents pending client invoicing or supplier invoice.
6. Sweep inactive jobs by configured days and return proposals pending human approval.

## agency-contract-po

Turns signed client agreements and client POs into PO limits, document links, transfers and budget reserves. Use when a client PO must govern spend. Unsigned quotes are not authority.

**Inputs:** Tenant ID; titular and billing client; signed PO or agreement with signer evidence; amount net of tax, currency and validity; documents to link with creation dates; transfer source document and POs; reserve control type and pool areas.

**Outputs:** `commercial_terms`, `po_limits`, `po_link_decisions`, `po_transfer_proposal`, `reserve_setup`, `billing_route`, `scope_exceptions`

**ERP reference:** [accounts-jobs](erp-reference/accounts-jobs.md), [receivables](erp-reference/receivables.md). **Tools:** `budget_check`, `installment_schedule`.

**Owner:** Account director and finance. **Next:** agency-budget-control, agency-fee-contracts, agency-media-planning, agency-production-estimating.

1. Verify signer, revision and entity; block unsigned quotes and unapproved increases.
2. Extract PO terms net of tax with citations and propose the PO record.
3. Link only documents created after the PO and lock the header assignment.
4. Check PO consumption with budget_check on disjoint balances.
5. Prepare transfers only between POs of the same billing client naming the source document.
6. Set up budget reserves by pool area and return proposals pending approval.

## agency-budget-control

Checks client PO, budget reserve and credit-limit headroom before client approval, keeping reservations apart from spend. Use when an estimate, plan or order needs a budget gate.

**Inputs:** Tenant ID; billing client; JobNumber; document id, revision and amount; PO or reserve authorized, spent, committed and reserved balances; credit limit, open receivables and approved unbilled work; approval circuit configuration.

**Outputs:** `budget_check`, `credit_check`, `reservation_proposal`, `balance_revision`, `blocking_exceptions`

**ERP reference:** [accounts-jobs](erp-reference/accounts-jobs.md), [media-planning](erp-reference/media-planning.md). **Tools:** `budget_check`, `credit_exposure`.

**Owner:** Finance controller. **Next:** agency-media-planning, agency-media-buying, agency-production-estimating.

1. Confirm the job is open and normalize balances to one currency and tax basis.
2. Build disjoint spent, commitment and reservation balances and run budget_check.
3. Run credit_exposure and require the credit-limit approver before client approval when exceeded.
4. Enforce credit override then client approval then order issuance.
5. Require an atomic host reservation for concurrent requests.
6. Propose reservation-to-commitment and commitment-to-spend conversions through audited transitions.

## agency-fee-contracts

Drafts fixed and hourly fee contracts: instalments, media/production split, job attachment and monthly hourly settlement. Use when the agency is paid by fee. No commission on fee jobs.

**Inputs:** Tenant ID; titular client; signed agreement; fixed or hourly kind and contract type; instalment months and amounts; single currency and rate; media/production split; jobs with percentages or pattern; approved hours and client rates for hourly contracts; open fiscal periods.

**Outputs:** `fee_contract_draft`, `instalment_schedule`, `job_allocation`, `hourly_settlement`, `approval_proposal`, `fee_exceptions`

**ERP reference:** [accounts-jobs](erp-reference/accounts-jobs.md), [expenses](erp-reference/expenses.md). **Tools:** `hourly_fee_settlement`, `installment_schedule`, `allocate`.

**Owner:** Account director and billing. **Next:** agency-client-billing, agency-accruals-revaluation, agency-profitability.

1. Verify fee accounts, fee media and fee production type and a single contract currency.
2. Build instalments with installment_schedule and split media/production with allocate.
3. Attach open jobs by percentage or pattern and enforce one-contract and invoiced locks.
4. Flag any agency commission on fee-linked estimates as a blocker.
5. Settle hourly instalments from approved hours with hourly_fee_settlement.
6. Check the fiscal period and prepare client approval then approval for billing.

## agency-tasks-timesheets

Tracks job tasks through their states and validates, approves and values timesheet hours with chargeability. Use for work requests and hour control. No self-approval of hours.

**Inputs:** Tenant ID; open non-generic JobNumber; task record, three task dates, recipient and actor role; timesheet lines in hundredths with daily total and allocation mode; approved hours with internal cost and client rates; timesheet closing date and configuration flags.

**Outputs:** `task_actions`, `task_delay_report`, `timesheet_validation`, `hour_approval_queue`, `hour_valuation`, `chargeability_report`, `timesheet_close_proposal`

**ERP reference:** [accounts-jobs](erp-reference/accounts-jobs.md), [management-security](erp-reference/management-security.md). **Tools:** `allocate`, `hourly_fee_settlement`.

**Owner:** Traffic manager and team leads. **Next:** agency-fee-contracts, agency-job-lifecycle, agency-profitability.

1. Validate task job, single recipient and date order before sending.
2. Apply task transitions only from allowed states with progress 80, 50 and 100 conventions.
3. Validate timesheet days in quarter-hour steps equal to the daily total.
4. Queue entries for the assigned approver; count only approved hours.
5. Value approved hours at internal cost and client rate and compute chargeability.
6. Preview hourly-fee burn and propose timesheet period closes.

## agency-revenue-budget

Builds the yearly revenue budget by client, product and month (investment, commission, fees, rebates) in versions vs actuals. Use for income planning. Media spend is not revenue.

**Inputs:** Tenant ID; budget year, version name and loading method; client x product x division lines with media/supplier or production-type rows; monthly investment, commission and cost-difference bps; projected fees, rebates and refunds; actuals and last closed month; supervisor identity.

**Outputs:** `budget_version`, `budget_lines`, `income_projection`, `plan_vs_actual`, `version_lock_proposal`, `budget_exceptions`

**ERP reference:** [accounts-jobs](erp-reference/accounts-jobs.md), [management-security](erp-reference/management-security.md). **Tools:** `allocate`, `margin`.

**Owner:** Finance planning lead. **Next:** agency-management-reporting, agency-cash-forecast, agency-profitability.

1. Confirm the version is open and scoped to a specific client, product and division.
2. Open media/supplier and production rows before entering percentages.
3. Compute commission and cost-difference income per month and add fees, rebates and refunds.
4. Phase annual figures with allocate and report margin apart from managed spend.
5. Copy versions with closed months carrying actuals and build the projection.
6. Prepare supervisor lock or reopen proposals.

## agency-production-estimating

Builds production estimates: line types, price lists, supplier quotes and award, client approval with credit check, POs and Post Buy variance. Use to quote or revise non-media work.

**Inputs:** Job number state; production type catalogue; supplier master; estimate header terms; line quotes; client credit position; config flags.

**Outputs:** `estimate_draft`, `estimate_totals`, `supplier_comparison`, `client_approval_pack`, `purchase_order_drafts`, `post_buy_variance`

**ERP reference:** [production](erp-reference/production.md). **Tools:** `estimate_totals`, `allocate`, `credit_exposure`.

**Owner:** Producer and account director. **Next:** agency-production.

1. Validate the JobNumber is vigent, billable and in an open period
2. Build header and lines by kind and run estimate_totals until blockers clear
3. Collect up to three supplier quotes and a quantity matrix; draft the award
4. Run credit_exposure and prepare the whole-estimate client approval pack
5. After verified approval set chosen suppliers and draft POs split by estimate and direct/indirect
6. Prepare approval for billing from delivery evidence and the Post Buy variance

## agency-production

Runs creative delivery: asset QA, talent and royalty contracts, event staff and a rights check that blocks release. Use when delivering production work. Never publishes or assumes rights.

**Inputs:** Approved estimate lines; asset versions; deliverable specs; royalty contracts; event staff master; config flags.

**Outputs:** `production_schedule`, `asset_manifest`, `qa_findings`, `rights_check`, `staff_assignment`, `release_candidates`

**ERP reference:** [production](erp-reference/production.md). **Tools:** `payload_digest`.

**Owner:** Producer and brand/legal approver. **Next:** agency-campaign-activation.

1. Confirm client-approved estimate lines and chosen suppliers
2. QA each asset version against specs, brand and tracking
3. Register or review royalty contracts and compute expiry or remaining repetitions
4. Block any asset or plan material without valid rights
5. Draft event staff requests and record delivery and evaluation
6. Digest the release pack and route it for brand/legal approval

## agency-media-ranking

Loads a licensed rating book and builds rankings with targets, affinity, CPR and CPM. Use before TV, radio or digital planning. Never invents ratings; a ranking is not a booking.

**Inputs:** Open JobNumber and holder client (client rankings); licensed rating book export for one market and period with targets and population data; provider and market code mappings; planning and negotiation targets; time window, weekdays and outlets; rate-card settings and approved FX reference.

**Outputs:** `rating_book_manifest`, `ranking_spec`, `candidate_table`, `data_quality_exceptions`, `commercial_inheritance`, `planning_handoff`

**ERP reference:** [media-planning](erp-reference/media-planning.md). **Tools:** `audience_metrics`.

**Owner:** Media planner. **Next:** agency-tv-radio-planning, agency-media-planning, agency-digital-planning, agency-ooh-planning.

1. Confirm mode (client ranking with book, without book, or query ranking) and licence scope.
2. Validate the book: one market per import, period within four weeks, provider code mappings present; keep missing ratings missing.
3. Resolve targets and load ratings with program, weekday and overall averages; label weighted or discontinuous-market ratings as derived.
4. Filter the book into a ranking by planning and negotiation targets, outlets, hours and weekdays; never add programs or edit ratings.
5. Compute audience, CPR, CPM and affinity with audience_metrics on a declared cost basis and universe.
6. Attach the open JobNumber and the negotiations valid at that date; flag outlets without valid terms.
7. Return the ranking as a draft planning input; no booking or budget reservation results from it.

## agency-media-planning

Builds a media plan from a JobNumber: monthly schedules, spots priced per media type, agency fee, client approval and credit gates, billing release. Use for plans and approvals.

**Inputs:** Open JobNumber with billing client, product, typology, division and billing code; media type and validity; outlets with default vendors and publication types; fee settings; currency and monthly reference FX; rating criterion and targets; contracts and rate cards; approval configuration; authoritative credit limit, open AR and approved-unbilled amounts.

**Outputs:** `media_plan`, `schedule_register`, `item_pricing`, `plan_totals`, `objective_summary`, `approval_payload`, `billing_release`

**ERP reference:** [media-planning](erp-reference/media-planning.md), [media-masters-ooh](erp-reference/media-masters-ooh.md). **Tools:** `media_line_cost`, `discount_cascade`, `audience_metrics`, `credit_exposure`, `plan_diff`.

**Owner:** Media planner. **Next:** agency-budget-control, agency-media-buying, agency-client-billing; agency-production in parallel.

1. Verify the JobNumber is open and inherit its parties read-only; validate validity of at most 12 calendar months and one media type.
2. Compose the header: client PO and monthly budget numbers, division, split code, payment term, order-only and direct/indirect flags, fee and currency.
3. Add items and spots within 99 spots per day and 999 items per schedule; one duration, publication type and material per item.
4. Price items with media_line_cost and apply surcharges, discounts and agency fee with discount_cascade; set billing type, direct flag and VAT.
5. Run credit_exposure with authoritative AR figures and include a credit override in the approval request when the limit is exceeded.
6. Reject declined spots, then prepare client approval by plan or schedule bound to the payload digest; orders wait for approval.
7. After ordering, prepare approve-for-billing for selected spots and hand released spots to billing.

## agency-tv-radio-planning

Plans TV, radio and cable schedules by program or daypart: duration pricing, spot spread, materials, traffic instructions and pre/post evaluation. Use for broadcast schedules.

**Inputs:** Saved ranking linked to an open JobNumber; programs with airing days and hours; daypart set and cut-off hour; contracts or rate cards; base duration, pricing mode and coefficient tables; materials with durations and royalty contracts; spot counts or objectives; evaluation provider settings.

**Outputs:** `broadcast_schedule`, `spot_register`, `rate_basis`, `material_distribution`, `traffic_instructions`, `evaluation_report`

**ERP reference:** [media-planning](erp-reference/media-planning.md), [media-masters-ooh](erp-reference/media-masters-ooh.md). **Tools:** `media_line_cost`, `discount_cascade`, `audience_metrics`.

**Owner:** Broadcast planner. **Next:** agency-media-planning, agency-media-buying, agency-production, agency-transmission-control.

1. Generate or append the plan from the ranking and check the broadcast-day grid against the cut-off hour and daypart coverage.
2. Create one item per program, duration, publication type, material and negotiation period; distribute spots within 99 per day.
3. Resolve duration rates (proportional or coefficient factors) and price with media_line_cost and discount_cascade.
4. Compute TRP, CPR and CPM per item with audience_metrics from ranking ratings.
5. Distribute materials so totals match exactly and block saving on royalty validity failures.
6. Prepare traffic instructions per vendor and run pre-evaluation with a same-weekday projected date; post-evaluation only after control.
7. Route re-rating and changes to ordered spots to plan changes.

## agency-ooh-planning

Plans agency-side out-of-home, DOOH and print: circuits x rate, faces, press size, month splits and evidence to request. Use for OOH and press lines. Booked faces are not exposure.

**Inputs:** Open JobNumber and plan header; supplier quotes or rate cards per circuit, face or press unit; site, circuit, screen or publication data; tariff type Normal or Package; production, installation, permit and dismantling costs; evidence policy agreed with the client.

**Outputs:** `site_plan`, `ooh_line_pricing`, `cost_schedule`, `evidence_requirements`, `booking_proposals`, `exceptions`

**ERP reference:** [media-masters-ooh](erp-reference/media-masters-ooh.md), [media-planning](erp-reference/media-planning.md). **Tools:** `media_line_cost`, `discount_cascade`, `allocate`.

**Owner:** OOH planner. **Next:** agency-media-planning, agency-media-buying, agency-production-estimating, agency-delivery-reconciliation.

1. Confirm agency-side scope and build candidates from a ranking without book by site or zone.
2. Price OOH Normal lines as circuits times rate and press lines as cm times columns times spots times rate with media_line_cost.
3. Price DOOH only on the supplier's documented basis; never convert plays to impressions by assumption.
4. Split package amounts across months equally or by purchased days with allocate so totals are conserved.
5. Apply discounts, surcharges and agency fee with discount_cascade; keep credit-note discounts and production costs as separate lines.
6. Define installation, removal, permit, proof-of-play and tear-sheet evidence per supplier and return the draft for plan approval.

## agency-digital-planning

Plans digital buys (CPM, CPC, CPV, CPA), builds naming taxonomy and UTMs, syncs planned vs actual and reprices orders from Google or Meta invoices. Use for digital plans. Never launches.

**Inputs:** Open JobNumber and linked ranking; digital masters (platforms, formats, buy types, calc types, tracking and placement types, AdServers); per-item quantities, rates, vendor, contract and currency; taxonomy templates and external codes; read-only actuals exports; platform invoices registered with taxonomy order codes.

**Outputs:** `digital_plan`, `taxonomy_strings`, `adserver_costs`, `actuals_snapshot`, `invoice_match_register`, `order_adjustment_proposal`

**ERP reference:** [media-planning](erp-reference/media-planning.md), [media-masters-ooh](erp-reference/media-masters-ooh.md), [payables-treasury](erp-reference/payables-treasury.md). **Tools:** `media_line_cost`, `discount_cascade`, `reconcile`, `invoice_check`.

**Owner:** Digital planner. **Next:** agency-media-planning, agency-media-buying, agency-campaign-activation, agency-delivery-reconciliation, agency-payables.

1. Generate the digital plan from a ranking linked to an open JobNumber and set platform, format, buy type, quantities and rate per item.
2. Price items with media_line_cost (per thousand for CPM/CPV, per action for CPC/CPA) and apply discounts and fee with discount_cascade.
3. Add ad-server costs per tracking type and render unique taxonomy and UTM strings from the client template.
4. After approval and ordering, snapshot actuals read-only and propose planned-vs-actual repricing per item.
5. Match platform invoice lines to ordered items by taxonomy and same currency; run invoice_check and reconcile per line.
6. Prepare one approval pack to switch matched items to fixed cost at the invoice line amount; never reopen billed orders.
7. After approved execution, read back order state and hand differences to reconciliation and payables.

## agency-rate-cards-contracts

Maintains media rate cards (buy and sell prices, client cards, validity) and media buy contracts (caps, installments, adjustments, balance). Use when pricing or vendor terms change.

**Inputs:** Medium or provider with media type; holder client or printed scope; currency and exponent; validity; calculation type; base or copy source with coefficient; contract consumption/control type, payment condition, cap, VAT flag, discounts, commission, assignment, rate cards by date range; installment advance % and count; authoritative contract current account for adjustments and transfers; vendor negotiation evidence.

**Outputs:** `rate_card_drafts`, `contract_drafts`, `installment_schedules`, `contract_balance_report`, `adjustment_transfer_proposals`, `pricing_exceptions`

**ERP reference:** [media-buying](erp-reference/media-buying.md), [media-masters-ooh](erp-reference/media-masters-ooh.md). **Tools:** `discount_cascade`, `media_line_cost`, `installment_schedule`, `budget_check`.

**Owner:** Media buying director. **Next:** agency-media-planning, agency-tv-radio-planning, agency-digital-planning, agency-media-buying, agency-client-billing.

1. Verify outlet, publication type, program and billing client masters exist before drafting.
2. Draft rate card headers with validity, calc type and base-card or coefficient derivation; compute buy and sell nets per line.
3. Resolve rate precedence (contract-pinned, client, printed) and report validity gaps or overlaps.
4. Validate contract combinations (free forces cash, installments need cap, child needs parent) and draft terms, share and confidential settings.
5. Generate installments that sum exactly to gross and compute contract balance and headroom from the current account.
6. Draft adjustments and transfers with billed-status and origin-not-destination guards.
7. Bind each proposal with payload_digest and return it pending approval.

## agency-media-buying

Prepares insertion orders from client-approved schedules with credit gates, versioning (cancels and replaces), sending and close/reopen rules. Use when spots must be ordered or changed.

**Inputs:** Client-approved plan and schedule revision; credit limit, open AR and approved unbilled or override approval; outlet and linked vendor per line; rate card or manual buy price; currency and exponent; VAT attributes; split criterion and cut-off; PO numbers; for changes the order number, version, sent status, reason and supplier-invoice status.

**Outputs:** `order_drafts`, `order_versions`, `send_packs`, `close_reopen_proposals`, `commitment_updates`, `supplier_exceptions`

**ERP reference:** [media-buying](erp-reference/media-buying.md). **Tools:** `discount_cascade`, `media_line_cost`, `credit_exposure`, `plan_diff`.

**Owner:** Media buyer. **Next:** agency-transmission-control, agency-campaign-activation, agency-payables, agency-client-billing.

1. Verify client approval at the stated revision and run the credit gate before ordering.
2. Diff approved schedule lines against lines to order and split by medium, vendor and configured keys.
3. Price buy lines from the rate card (buy equals sell without a card) and enforce indirect/no-audit edit rules.
4. Draft orders and send packs; bind them with payload_digest for approval before any send.
5. Version sent orders as cancels-and-replaces; re-issue unsent orders without a version bump.
6. Warn that close auto-certifies uncontrolled spots and enforce reopen guards on supplier invoices and closed months.

## agency-transmission-control

Checks ordered TV and radio spots against monitoring data: auto and manual matching, missing or extra spots, makegoods, close readiness. Use before closing orders. An invoice is not proof.

**Inputs:** Ordered spots with station, date, window, material and order version; monitoring file or certificate with provider, timezone, cut-off and hash; default OK and deficient audit codes; code links; tolerance and match options; makegood policy; licensed ratings for post-buy.

**Outputs:** `emission_match`, `missing_or_extra_insertions`, `material_exceptions`, `makegood_register`, `close_readiness`, `postbuy_report`, `finance_handoff`

**ERP reference:** [media-buying](erp-reference/media-buying.md), [media-planning](erp-reference/media-planning.md). **Tools:** `spot_match`, `reconcile`.

**Owner:** Media buyer and traffic. **Next:** agency-media-buying, agency-plan-changes, agency-delivery-reconciliation, agency-payables.

1. Check spot-control prerequisites and import the monitoring file with hash and exclusions.
2. Queue unmapped channel, client, product and material codes for human mapping.
3. Auto match in normal or tolerance mode with one event per ordered spot and classify results.
4. Record manual and bulk controls with audit codes and controller identity.
5. Prepare the makegood register and close readiness, warning about auto-certification at close.
6. Hand ordered vs aired values to finance with reconcile.

## agency-plan-changes

Revises approved or ordered media plans as new versions: diff vs baseline, locks on ordered or billed spots, rescheduling and order versions. Use for changes after approval.

**Inputs:** Plan number with approved and latest revisions; authenticated change request with reason category and deadline; spot states and order numbers/versions (sent or unsent); authoritative PO and reserve balances; contracts, rate cards, materials and royalty validity for new dates; approval configuration.

**Outputs:** `baseline_revision`, `proposed_revision`, `line_diff`, `lock_report`, `currency_deltas`, `order_version_actions`, `approval_pack`, `verified_receipts`, `blocked_actions`

**ERP reference:** [media-planning](erp-reference/media-planning.md), [media-buying](erp-reference/media-buying.md). **Tools:** `plan_diff`, `budget_check`.

**Owner:** Media planner and account director. **Next:** agency-media-buying, agency-budget-control, agency-transmission-control, agency-client-billing, agency-delivery-reconciliation.

1. Load the approved baseline and latest revision; rebase stale requests instead of overwriting.
2. Diff lines by stable id with plan_diff and add non-financial diffs for program, duration, material, contract and dates.
3. Apply locks: billed spots untouchable, controlled spots immutable, vendor and contract fixed once ordered, no program left with zero spots.
4. Route ordered spots through unlock and order modification: new version that annuls and replaces if sent, same version if unsent.
5. Reschedule dropped spots only after control and create new items for mid-flight rate changes.
6. Check increases with budget_check and never treat unverified cancellations as released headroom.
7. Submit one approval pack bound to the payload digest, then read back revisions and order versions before marking steps executed.

## agency-campaign-activation

Prepares and, after approval, launches digital campaigns via verified tools (Meta Ads, Google Ads, Zernio) with paused staging and readback. Use when a digital plan must go live.

**Inputs:** Approved digital plan and issued order items; platform account with verified write tool; account currency and timezone; item platform, format, buy type, rates, flights and ordered net; budget snapshot and host reservation; taxonomy templates; creatives with rights; URLs and conversion events; authenticated approval reference.

**Outputs:** `activation_proposal`, `taxonomy_names`, `preflight_results`, `external_ids`, `readback_report`, `execution_receipts`, `uncertain_actions`

**ERP reference:** [media-planning](erp-reference/media-planning.md). **Tools:** `payload_digest`, `budget_check`.

**Owner:** Campaign manager. **Next:** agency-campaign-optimization, agency-delivery-reconciliation.

1. Discover reviewed write tools and read account identity, currency, timezone and existing campaigns.
2. Load only approved, ordered digital items and render taxonomy names and UTMs.
3. Check budget headroom and build the exact paused configuration; hash it for approval.
4. Execute after approval with idempotency keys and checkpoints, then read back every object.
5. Enable only verified paused objects under a separate approval and resolve uncertain writes by key or name.
6. Hand platform IDs mapped to plan items and orders downstream.

## agency-campaign-optimization

Diagnoses pacing and performance vs the approved plan and proposes bounded bid, budget, audience or creative changes. Use for in-flight reviews. Fixed commitments are not free budget.

**Inputs:** Approved plan revision with investment, TRP and reach objectives and planning target; dated actuals with source, window, attribution and lag; licensed ratings and universe; committed order and contract amounts; budget snapshot; change history.

**Outputs:** `diagnostic`, `objective_deviation`, `optimization_proposal`, `experiment_plan`, `constraint_check`, `verified_change_receipts`

**ERP reference:** [media-planning](erp-reference/media-planning.md). **Tools:** `audience_metrics`, `budget_check`, `plan_diff`.

**Owner:** Performance lead. **Next:** agency-campaign-activation, agency-plan-changes, agency-budget-control, agency-delivery-reconciliation.

1. Freeze the baseline and separate measurement gaps from performance changes.
2. Compute pacing, TRP, CPR, CPM and frequency and the objective deviation per line.
3. Classify cancellable platform budget vs committed orders and contract caps.
4. Draft bounded changes with rollback criteria and check them with plan_diff and budget_check.
5. Hash the proposal for approval and route execution to activation or plan changes.
6. Evaluate against the frozen baseline after the declared window.

## agency-ooh-inventory

Runs a media owner's billboard inventory: faces, availability, reservations to orders, posting batches and prepaid advertiser agreements. Use when selling OOH faces you own.

**Inputs:** JobNumber; billboard type and zone; salesperson; OOH rate card and item; tariff type, faces, outings, start date, rate, currency and FX; payment terms and client PO; face states and permits; motifs with shares; posting date; agreement level, validity, type, payment, billable and bonus amounts.

**Outputs:** `availability_report`, `reservations`, `ooh_orders`, `monthly_suborders`, `face_motif_assignments`, `posting_batches`, `agreement_balances`, `inventory_exceptions`

**ERP reference:** [media-masters-ooh](erp-reference/media-masters-ooh.md). **Tools:** `media_line_cost`, `discount_cascade`, `allocate`, `installment_schedule`.

**Owner:** OOH sales manager (media-owner vertical). **Next:** agency-client-billing, agency-collections, agency-profitability.

1. Check face availability by state, dates and permit, or circuit quantity for bulk types.
2. Create one reservation per billboard type and zone and convert it to an order when the PO arrives.
3. Price lines (normal or package), apply cumulative and credit-note discounts and check the agreement.
4. Slice orders into calendar-month sub-orders with exact conservation.
5. Assign faces and motifs (shares sum to 100%) under role restrictions.
6. Build, close and issue posting batches; record face state changes.
7. Hash proposals for approval and hand monthly slices to billing.

## agency-delivery-reconciliation

Matches supplier invoices to closed orders, production items or expense requests and classifies differences by origin. Use when an invoice must be checked. Never edits supplier figures.

**Inputs:** Supplier document header and declared total; pendings per spot/item/request line with expected net; order close and certification status; estimate approval and PO status; tolerance policy.

**Outputs:** `match_result`, `discrepancies`, `evidence_links`, `payable_candidate`, `writeoff_proposals`

**ERP reference:** [supplier-invoicing](erp-reference/supplier-invoicing.md), [media-buying](erp-reference/media-buying.md). **Tools:** `reconcile`, `invoice_check`, `spot_match`.

**Owner:** Media/finance analyst. **Next:** agency-payables, agency-client-billing, agency-accruals-revaluation.

1. List the supplier's pendings by category and enforce currency homogeneity.
2. Match only closed orders; flag open orders and auto-certification on close.
3. Verify spots with spot_match and select pendings at spot, item or request-line grain.
4. Recompute billed values and compare with reconcile and invoice_check.
5. Record differences by origin and open NC pendings for production excess.
6. Prepare write-off proposals with margin effect for controller approval.
7. Digest the control and hand off to registration.

## agency-payables

Logs supplier invoices, checks duplicates and math, picks the load type and prepares registration with derived accounts. Use when supplier documents arrive. Never posts or pays itself.

**Inputs:** Supplier document with type, letter, number, dates, currency, declared total and source hash; saved control; VAT accounts and perceptions; payment term; accounts on media/production/expense types; period status.

**Outputs:** `reception_log`, `duplicate_check`, `normalized_invoice`, `registration_proposal`, `holds`, `posting_receipt`

**ERP reference:** [supplier-invoicing](erp-reference/supplier-invoicing.md), [payables-treasury](erp-reference/payables-treasury.md). **Tools:** `invoice_check`, `reconcile`, `payment_terms`, `tiered_commission`.

**Owner:** AP lead. **Next:** agency-payment-run, agency-tax-compliance, agency-accruals-revaluation.

1. Log the document in the reception register with a traffic number and responsible checker.
2. Deduplicate by supplier, type, letter and number and return defective documents with a reason.
3. Capture the header, due date via payment_terms, and choose the load type from pendings.
4. Recover the control and check totals and VAT with invoice_check.
5. Derive accounts automatically and compute volume or commission credits with tiered_commission.
6. Apply advance-purchase, full-cancellation and period rules.
7. Gate with reconcile, digest and submit the registration for approval.

## agency-payment-run

Proposes supplier payment lists, payment orders, withholdings and release instruments for two-person approval. Use for a payment run or bank file. Never approves or releases payments.

**Inputs:** Payment date, due window, currency, method and bank account; open items with balances and locks; client-collection evidence; supplier tax profiles, overrides and host rates; availability and checkbook state; FX rates.

**Outputs:** `payment_list_proposal`, `payment_orders_draft`, `withholding_schedule`, `release_proposal`, `bank_file_request`, `approval_requests`

**ERP reference:** [payables-treasury](erp-reference/payables-treasury.md). **Tools:** `withholding`, `payment_terms`, `aging`, `fx_revaluation`.

**Owner:** Treasury lead (preparer) and finance approver. **Next:** agency-cash-settlement, agency-tax-compliance, agency-cash-forecast.

1. Build unlocked candidates in the due window with aging and payment_terms.
2. Attach client-collected evidence and save a provisional list that locks items.
3. Compute withholdings at the configured moment with host-supplied rates.
4. Route the list to a different approver and generate one OP per supplier from the definitive list.
5. Propose release instruments within availability and preview FX with fx_revaluation.
6. Prepare bank files and undo flows only under period and approval guards.
7. Digest every list, OP and release proposal and hand off pending approval.

## agency-cash-settlement

Prepares deposits, transfers, bank charges, bank reconciliation, cheque lifecycle and card statements. Use when treasury must record or reconcile cash. Never moves money.

**Inputs:** Bank account and statement balances and lines; last definitive reconciliation; treasury movements; portfolio cheques; bank charge details; checkbook and cheque status; card statements; rejection details.

**Outputs:** `deposit_proposals`, `bank_charge_entries`, `reconciliation_report`, `cheque_actions`, `card_statement_match`, `availability_snapshot`, `unapplied_cash`

**ERP reference:** [payables-treasury](erp-reference/payables-treasury.md), [receivables](erp-reference/receivables.md). **Tools:** `reconcile`, `allocate`, `journal_check`.

**Owner:** Treasury lead. **Next:** agency-period-close, agency-cash-forecast, agency-collections, agency-payment-run.

1. Prepare deposits and bank charges in the account currency and validate with journal_check.
2. Split charges across dimensions with allocate.
3. Match treasury movements to statement lines and compare pairs with reconcile.
4. Propose a definitive reconciliation only when the balance proof closes exactly.
5. Manage own and third-party cheque lifecycle and rejections with replacement instruments.
6. Match card statements per currency and report availability per funding source.
7. Digest proposals and hand off without claiming postings.

## agency-client-billing

Prepares client invoices and credit/debit notes from plans, estimates and fees approved for billing: fee, VAT, partial and split billing. Use to turn pending-to-bill into invoices.

**Inputs:** Billing client master; pending to bill extract; billing readiness; tax tables; split codes; advance sale balances.

**Outputs:** `billing_selection`, `invoice_drafts`, `credit_debit_note_drafts`, `fee_calculation`, `split_allocation`, `billing_exceptions`

**ERP reference:** [receivables](erp-reference/receivables.md), [production](erp-reference/production.md), [media-planning](erp-reference/media-planning.md). **Tools:** `discount_cascade`, `estimate_totals`, `payment_terms`, `allocate`, `invoice_check`.

**Owner:** Billing lead. **Next:** agency-tax-compliance.

1. Confirm billing code, client status and billing readiness
2. Select approved-for-billing lines by single source, currency, due date and product
3. Compute net, agency fee and production totals with deterministic tools
4. Apply partial billing, advance-sale draw and split-code allocation
5. Compute VAT, perceptions and due date and verify totals
6. Propose credit or debit notes for corrections and differences
7. Digest the draft pack and return it pending approval

## agency-billing-requirements

Checks client-specific prerequisites (client PO, service entry, attachments, custom fields) before an invoice is issued. Use when procurement paperwork gates billing.

**Inputs:** Requirement catalogue; source documents; client po records; attachments; issued invoices.

**Outputs:** `requirement_matrix`, `evidence_matches`, `missing_requirements`, `issuance_ready`, `locked_field_changes`, `owner_requests`

**ERP reference:** [receivables](erp-reference/receivables.md), [accounts-jobs](erp-reference/accounts-jobs.md). **Tools:** none.

**Owner:** Billing lead and account manager. **Next:** agency-client-billing.

1. Read the trusted client requirement catalogue
2. Expand requirements to job, plan, schedule, order and estimate level
3. Check billing code, client PO link, validity and balance
4. Check mandatory attachments, custom fields and invoice data
5. Apply locks on invoiced sources and propose credit and reissue
6. Return readiness per source with evidence and owners

## agency-collections

Prepares customer receipts applying cash, cheques, transfers and withholding certificates, plus advances, aging, credit exposure and follow-up lists. Use for collections and overdue chasing.

**Inputs:** Open items; remittance evidence; withholding certificates; credit limits; tax tables; fx rates; client contacts.

**Outputs:** `receipt_proposal`, `application_plan`, `withholding_certificates`, `advance_applications`, `aging_report`, `credit_exposure`, `followup_worklist`

**ERP reference:** [receivables](erp-reference/receivables.md). **Tools:** `aging`, `credit_exposure`, `allocate`, `withholding`, `payment_terms`.

**Owner:** Credit and collections lead. **Next:** agency-cash-settlement.

1. Validate one debt currency and one integrator account per receipt
2. Match remittances to open items and propose applications
3. Capture certificate-accurate withholdings and compare expected amounts
4. Propose instruments, advances and advance re-application
5. Compute aging, delay and credit exposure
6. Build the follow-up worklist and digest the receipt pack for approval

## agency-rebates

Calculates supplier overcommissions, volume rebates, incentives and finder fees with five scale engines, monthly provision vs bill and client shares. Use for rebate proposals.

**Inputs:** Rebate contracts; qualifying orders; registered supplier invoices; prior pendings; fx rates; supplier settlements.

**Outputs:** `eligible_base`, `rebate_calculation`, `pending_register`, `provision_proposal`, `client_rebates`, `rebate_exceptions`

**ERP reference:** [media-buying](erp-reference/media-buying.md), [production](erp-reference/production.md), [receivables](erp-reference/receivables.md), [supplier-invoicing](erp-reference/supplier-invoicing.md). **Tools:** `tiered_commission`, `flat_rebate`, `allocate`.

**Owner:** Controller and media director. **Next:** agency-accruals-revaluation.

1. Read contract terms, scope and holder from the trusted master
2. Build the base with reduction, vendor commission and sequencing
3. Run the scale engine on cumulative base with cap
4. Distribute commission across orders and net or credit negatives
5. Flag provision or bill months and handle retroactivity
6. Compute client rebates and digest the pending register for approval

## agency-expenses

Controls agency overhead: expense contracts and requests, employee expense sheets, cost sheets vs estimates, petty cash and expense budget. Use for non-media spend. No self-approval.

**Inputs:** Requester or claimant pseudonym; concept, net amount, currency and allocation; configuration flags and approver matrix; contract schedule; sheet lines and receipts; estimate item; fund balance; budget balances.

**Outputs:** `expense_request_drafts`, `contract_schedule`, `sheet_review`, `settlement_proposal`, `deferral_schedule`, `budget_check_result`, `approval_requests`

**ERP reference:** [expenses](erp-reference/expenses.md). **Tools:** `allocate`, `installment_schedule`, `invoice_check`, `budget_check`.

**Owner:** Office manager and controller. **Next:** agency-payables, agency-payment-run, agency-cash-settlement, agency-profitability.

1. Validate currency, work order and allocation eligibility and check budget with budget_check.
2. Build contract schedules and deferrals with installment_schedule and allocations with allocate.
3. Route approvals by limit with creator different from approver and enforce the PO gate.
4. Review sheets and check taxed receipts with invoice_check.
5. Prepare settlements with employee or agency balance and cost-sheet caps.
6. Track petty cash availability and propose replenishment.
7. Digest proposals and hand off pending independent approval.

## agency-tax-compliance

Prepares e-invoice authorization (Mexico CFDI, Argentina CAE), VAT books, withholdings, certificates and tax positions from your tax tables. Use for tax steps. Never stamps or files itself.

**Inputs:** Approved document drafts; country tax tables; numbering series; ledger tax balances; sub journals; withholding records.

**Outputs:** `authorization_requests`, `numbering_report`, `vat_books_reconciliation`, `withholding_perception_schedule`, `certificate_register`, `tax_positions`, `statutory_exports`

**ERP reference:** [receivables](erp-reference/receivables.md), [supplier-invoicing](erp-reference/supplier-invoicing.md), [accounting](erp-reference/accounting.md). **Tools:** `invoice_check`, `withholding`.

**Owner:** Tax lead. **Next:** agency-period-close.

1. Confirm period status, country tables and numbering series
2. Recompute document VAT and totals and check numbering
3. Prepare consecutive CAE batches or PAC stamping requests
4. Compute and reconcile withholdings, perceptions and certificates
5. Reconcile VAT books and present VAT and IIBB positions
6. Prepare statutory exports and digest the pack for approval

## agency-general-ledger

Drafts and validates chart of accounts, account tags, voucher types and manual journal entries, templates and opening balances. Use when an account or entry needs checking.

**Inputs:** Fiscal year; period subledger states; locked periods; chart of accounts; voucher types; entry lines; supporting attachment; opening subledger detail.

**Outputs:** `journal_entry_proposal`, `journal_check_report`, `coa_change_proposal`, `opening_balance_reconciliation`, `integration_difference_report`

**ERP reference:** [accounting](erp-reference/accounting.md). **Tools:** `journal_check`, `allocate`.

**Owner:** Chief accountant. **Next:** agency-accruals-revaluation.

1. Classify the request and load every referenced account master and voucher type
2. Validate rubro, account and subaccount changes against hierarchy, immutability and observation-code rules
3. Gate the entry on period x subledger state and voucher-type allowances
4. Check dimensions, entry type, manual-movement restrictions and foreign-currency consistency per line
5. Run journal_check in total and per division slice; use allocate for distribution codes
6. Route provisional entries through attachment, intermediate and final approval bound to a payload digest
7. Reconcile opening balances and integrator breakdowns to the GL and report differences

## agency-accruals-revaluation

Prepares month-end jobs: unbilled revenue and cost provisions, WIP, overcommission provision, FX revaluation and work-order closing with day-1 reversals. Use after pre-close.

**Inputs:** Period subledger states; month end buy sell rates; open foreign currency items; pending billing and supplier items; expense requests without invoice; overcommission pendings; bridge balances by ot; intercompany flags.

**Outputs:** `fx_revaluation_proposal`, `gross_income_provision_proposal`, `wip_reclass_proposal`, `expense_provision_proposal`, `overcommission_provision_proposal`, `ot_close_proposal`, `ic_reclass_proposal`, `close_job_checklist`

**ERP reference:** [accounting](erp-reference/accounting.md), [production](erp-reference/production.md), [media-buying](erp-reference/media-buying.md). **Tools:** `fx_revaluation`, `journal_check`, `tiered_commission`, `allocate`.

**Owner:** Chief accountant. **Next:** agency-period-close.

1. Confirm the relevant subledgers are pre-closed and operational pendings are validated
2. Prepare the three FX runs with buy rates for receivables and sell rates for payables using fx_revaluation
3. Prepare one Gross Income provision per month and the WIP, expense and overcommission provisions with day-1 reversals
4. Prepare OT closing with bridge accounts, downgrading definitive to provisional when items are pending
5. Prepare intercompany reclass while the month is pre-closed and not closed
6. Validate each entry and reversal with journal_check and split amounts with allocate
7. Hand the job checklist with digests and verified statuses to period close

## agency-fixed-assets

Prepares the fixed-asset register, monthly depreciation, disposals and annex from capital expense requests. Use when capitalising, depreciating or retiring assets.

**Inputs:** Asset concepts; expense request and invoice; purchase value and dates; depreciation method and criterion; cost center mode; period state; disposal details.

**Outputs:** `asset_register_changes`, `depreciation_run_proposal`, `disposal_proposal`, `fixed_asset_annex`

**ERP reference:** [accounting](erp-reference/accounting.md), [expenses](erp-reference/expenses.md). **Tools:** `depreciation_schedule`, `journal_check`.

**Owner:** Chief accountant. **Next:** agency-period-close.

1. Confirm the asset came from an expense request on a B1 concept and validate the record
2. Check the asset is still editable and set first-month rule from the criterion
3. Compute straight-line schedules with depreciation_schedule and label any P, M or inflation amounts as outside the tool
4. Build the voucher type 94 run by division and cost center and validate it with journal_check
5. Prepare disuse or sale disposals after annulling any posted run for that month
6. Produce the annex roll-forward and tie it to B1 and B2 balances

## agency-period-close

Sequences the monthly and year-end close: subledger pre-close, ordered close jobs, mandatory gates, reconciliations and reopen rules. Use to close or reopen a period.

**Inputs:** Period subledger states; month end rate; close job receipts; trial balance with integrators; unpaid invoices at cutoff; bank reconciliations; reopen or year close request.

**Outputs:** `close_checklist`, `close_job_status`, `post_close_reconciliations`, `unresolved_balances`, `lock_proposal`, `reopen_plan`, `adjustment_plan`

**ERP reference:** [accounting](erp-reference/accounting.md), [payables-treasury](erp-reference/payables-treasury.md). **Tools:** `journal_check`, `fx_revaluation`, `aging`.

**Owner:** Controller. **Next:** agency-management-reporting.

1. Confirm pre-close readiness and the last-day rate, then request subledger pre-close
2. Sequence the close jobs in vendor order and record each verified status
3. Enforce mandatory gates: FX when foreign balances exist and OT close with bridge accounts
4. Run the post-close reconciliations, aging at cut-off and journal_check on late adjustments
5. Prepare the lock proposal with evidence and a payload digest for controller approval
6. Assess reopen cascades, deleted automatic entries and the audit re-close sequence before any reopen

## agency-profitability

Analyzes job, client and media profitability: gross income, valued hours, expenses, contribution and overhead allocation, with media spend kept apart. Use for margin reviews.

**Inputs:** Ledger results by job; approved hours and rates; direct expenses; structural expense pool; managed spend; pending items.

**Outputs:** `job_pnl`, `client_profitability`, `overhead_allocation`, `margin_bridge`, `managed_spend`, `completeness_gaps`

**ERP reference:** [accounts-jobs](erp-reference/accounts-jobs.md), [accounting](erp-reference/accounting.md). **Tools:** `margin`, `allocate`.

**Owner:** Finance controller. **Next:** agency-management-reporting.

1. Fix period, basis, date criterion and currency
2. Compute gross income per job and client with managed spend apart
3. Value approved hours at internal cost and client rate
4. Compute contribution margin per client with the margin tool
5. Allocate structural overhead by contribution share with the allocate tool
6. Reconcile posted gross income to the P&L heading and draft corrective proposals

## agency-cash-forecast

Projects agency cash by day, week or month from balances, receivables, payables, approved unbilled work and payroll, with expected payment dates. Use for liquidity planning.

**Inputs:** Opening liquidity; ar open items; ap open items; chronic delays; approved unbilled pipeline; payroll capex recurring; holiday calendar.

**Outputs:** `cash_forecast`, `currency_buckets`, `undated_pipeline`, `collection_scenarios`, `supplier_exposure`, `liquidity_gaps`

**ERP reference:** [management-security](erp-reference/management-security.md), [payables-treasury](erp-reference/payables-treasury.md). **Tools:** `cash_projection`, `payment_terms`, `aging`.

**Owner:** CFO / treasury. **Next:** agency-payment-run.

1. Fix snapshot type, horizon, currencies and holidays
2. Load opening liquidity and AR/AP items with due date plus chronic delay
3. Date the client-approved pipeline with billing date plus terms plus delay
4. Add payroll, recurring outflows, capex, capital moves and adjustments
5. Run cash_projection and find the minimum closing balance
6. Stress-test scenarios and draft actions for their own approvals

## agency-management-reporting

Prepares the monthly management pack and HQ reporting exports, checks account mapping coverage and computes KPIs (gross income, DSO, chargeability, WIP aging). Use after month close.

**Inputs:** Closed period state; trial balance; interface code table; account mapping; ar open items; approved hours; wip items.

**Outputs:** `management_pack`, `mapping_coverage`, `export_files`, `kpi_summary`, `variance_commentary`

**ERP reference:** [management-security](erp-reference/management-security.md), [accounting](erp-reference/accounting.md). **Tools:** `margin`, `aging`, `allocate`.

**Owner:** Controller and CFO. **Next:** agency-period-close.

1. Verify the period is closed and post-close controls pass
2. Validate interface-code mapping coverage and list unmapped items
3. Assemble per-tab export files with scope and 8A/8B policy
4. Compute gross income, DSO, chargeability and WIP aging
5. Write variance commentary and digest the pack for CFO sign-off
