# Management, Systems & General (cross-cutting modules)

> **Provenance.** Functional reverse engineering of a reference agency ERP, derived from its publicly accessible help documentation (reviewed 2026-10-11). Content is paraphrased and restructured; it is not vendor documentation, source code or an endorsement. Bracketed ids such as `[mp301010]` identify the source page used as evidence. Items marked *inferred*, *assumed* or listed under gaps must be validated with your own controller, tax adviser and system owner before they drive postings or payments.

Scope: Management (forward cash flow, monthly reporting & forecasting, service-center tasks), Sistemas (system parameters, users/profiles/roles, audit, print layouts), General (communications, contacts, meeting calendar, timesheet, personal debt), the main-menu home screen with alerts, and the remaining Academia index pages.
Source: the reference ERP's help documentation. Source refs are given as the original page id (e.g. `mp302007`) so implementers can trace back. All text below is an original paraphrase written for an MIT-licensed reimplementation; Spanish labels appear only as short field identifiers in backticks.

---

## 1. Purpose and role in the end-to-end circuit

The agency ERP's core circuit is: client contract / JobNumber (campaign) → estimates & media plans → client approval → purchase orders to suppliers → supplier invoices (AP) → client invoicing (AR) → collections and payments (treasury) → accounting close → management reporting. The modules in this spec do not create revenue documents themselves; they **govern, observe, and project** that circuit:

| Cross-cutting module | What it contributes to the E2E circuit |
|---|---|
| **System parameters** (`Configuraciones Especiales`) | A large feature-flag/parameter store that decides which approval gates exist (media plan approval strictness, mandatory POs, expense approval, timesheet approval), how taxes are computed (VAT rates history, withholding/perception agent flags), numbering of fiscal documents, and country behavior. Every other module reads these flags. |
| **Users, profiles, functional roles, specific activities** | Authorization layer: which screens a person can open, what CRUD level they have, whether they may see costs/margin, and which **approval powers** they hold (approve-for-billing, approve-on-behalf-of-client, approve POs, approve expenses up to a cap, approve hours, post invoices after pre-close, finalize payment lists…). This is the segregation-of-duties backbone. |
| **Audit** | Immutable trail of who did what (create/modify/delete) per entity, plus access logs, license consumption, per-user productivity, and option-usage statistics. |
| **Print layouts** (`Formatos de Impresiones`) | Coordinate-based templates that render the legally relevant outputs of the circuit: client invoices/credit/debit notes, purchase orders, payment orders & receipts, production estimates, and bank cheques. |
| **Timesheet + hour approval** | Captures labor cost per campaign (internal rate) and sale value (external rate); approved hours feed project profitability and fee billing. |
| **Communications / contacts / calendar / alerts inbox** | Internal messaging (memos, tasks, contact reports, briefs) tied to JobNumbers, a single contact registry that is the only allowed addressee source, fiscal-due-date reminders, and the alert inbox that surfaces pending approvals to each approver. |
| **Forward cash flow** (`Cash Flow Previsional`) | Treasury projection built from accounting balances, AR/AP open items, cheques, approved-but-unbilled estimates/plans/fees, payroll, capex, capital moves and manual adjustments — a planning snapshot that never posts accounting entries. |
| **Monthly reporting export** | Maps the chart of accounts and masters to a parent-company reporting system (Hyperion/HFM primarily, also Magnitude, Cartesis, a "Global Client Profitability" variant, and an "Altair" interface) and produces per-tab export files. |
| **Service-center tasks** | Ticketing between requesting areas and back-office service teams with SLA timing and requester approval. |
| **Bulk maintenance / purge** | Mass deactivation of masters and mass closing/rejection of stale transactional items (jobs, tasks, expense requests, unissued payment orders, unapproved POs, etc.). |
| **Multi-company** | Sub-companies inside one database (balance-sheet split mirroring divisions on P&L) and a separate consolidation environment that maps masters across group companies. |

---

## 2. Process catalogue

Notation: **T** trigger · **A** actor · **S** steps · **I** inputs · **O** outputs · **Ap** approvals/controls · **Ref** source page.

### 2.1 Management — Cash flow

**P-CF-01 Classify ledger groups for liquidity** (`Asignación de Liquidez de Rubros`)
- T: implementation or new account groups. A: controller/treasury lead.
- S: enter edit mode; for each account group (`rubro`) set its type (Gross Income / Compensation / Expenses) and its liquidity horizon (short- or long-term); save.
- O: classification used by the cash-flow summary. Ref: `mp302006`.

**P-CF-02 Configure chronic delay days** (customers and suppliers)
- T: before first cash flow; periodically. A: treasury.
- S: open cash-flow settings; on the Customers tab enter a default delay value, tick a set of customers, apply in bulk, then fine-tune per customer; save. Same on Suppliers tab.
- O: per-party `Días de Atraso Crónico` added to document due dates. Ref: `configurar-dias-de-atraso-de-clientes`, `...-proveedores`.

**P-CF-03 Generate a cash flow**
- T: treasury planning cycle; recommended the day after the scheduled supplier payment run. A: treasurer.
- Pre: fiscal-year holidays defined in accounting masters.
- S: New → choose type (Daily / Weekly / Strategic) → optional notes → choose whether to show active accounts with zero balance → optionally "copy from previous cash flow" (only if one exists of the same type) → Start → system asks for the VAT payment day-of-month → save setting → Start again → system builds the projection from actual data into the Summary tab → Save.
- O: numbered cash-flow snapshot (`Nº de Cash Flow`); latest one is "active", earlier ones are history. Ref: `generar-un-cash-flow`, `mp302007`.

**P-CF-04 Adjust open-item timing** (customers' current accounts, documents receivable, cheques in portfolio/values to deposit, post-dated cheques payable, obligations payable, suppliers' current accounts)
- T: after generation. A: treasurer.
- S: drill into the concept → drill into the ledger account → for each item shift its expected date left/right (`Mover`) into the desired day column → for customers/suppliers optionally configure expected withholding lines (VAT, income tax, other) either as a percentage or as manual amounts per date → Apply → Save.
- Pre: the ledger accounts must exist, be active, and carry the right observation code; post-dated cheques require the `Usa Cheques Diferidos` parameter.
- Ref: `modificar-las-estimaciones-de-cobranza-de-las-cuentas-corrientes-de-clientes`, `...documentos-a-cobrar`, `...valores-a-depositar`, `...cheques-diferidos-a-pagar`, `...obligaciones-a-pagar`, `ad_cap_gus_dir_09`.

**P-CF-05 Estimate future client billing (Gross Income — receivable side)**
- Pre: client-approved production estimates, media plans, and fixed/hourly fee contracts.
- S: under Results → Gross Income, open "Pending to bill — Media / Production / Fees". For each, assign estimated billing dates at one of four granularities: all months at once, per month, per month+client, or per individual estimate/plan line (`Fecha Fact.`). Media and production carry two dates: one for the pass-through sale (`Venta`) and one for the agency service fee (`Serv. Agencia`). Fee instalments carry dates for media and production portions. A "do not generate" action marks months with no billing expectation. Apply → Save.
- Rule: expected collection date = estimated billing date + customer's usual payment term + customer's chronic delay. Ref: `generar-las-estimaciones-de-facturacion-a-clientes`.

**P-CF-06 Estimate supplier invoices (Gross Income — payable side)**
- S: same mechanics for "Pending media costs" and "Pending production costs"; a single `Facturación` date per item, at all-months / month / month+supplier / item granularity.
- Rule: expected payment date = estimated supplier invoice date + supplier payment term + supplier chronic delay. Ref: `generar-las-estimaciones-de-facturacion-de-proveedores`.

**P-CF-07 Estimate payroll** (Compensations)
- S: one line per month in the horizon plus the following month; enter salary and social-charges amounts and payment dates; under "Other" enter concept, period, amount, supplier type (one master supplier / several / unregistered), supplier code, VAT rate (system computes VAT amount), payment date. Apply → Save. Ref: `generar-las-estimaciones-de-pago-al-personal`.

**P-CF-08 Estimate expenses, other outflows and other income**
- S: per month line, pick a P&L ledger account as concept, period, amount (positive = outflow, negative = income), supplier type/code, VAT rate, payment date. Apply → Save. Ref: `ingresar-las-estimaciones-de-gastos-egresos-y-otros-ingresos`.
- Also: "accounts and recurring expenses" configuration — manual recurring outflows (account, amount, frequency monthly/weekly/one-off, payment days, currency) because approved expense contracts are not read automatically. Ref: `mp302007`.

**P-CF-09 Estimate fixed-asset purchases and sales**
- Purchases: description, net amount, purchase date, expected supplier → system computes payment date from supplier terms + delay (overridable); VAT rate → VAT amount. Sales: description, net amount, VAT rate, sale date, optional days-to-defer collection. Ref: `ingresar-las-estimaciones-de-compra-y-venta-de-bienes-de-uso`.

**P-CF-10 Estimate capital increases/decreases**
- Increase: description, amount, expected collection date, notes. Decrease: description, amount, expected payment date, notes. Ref: `ingresar-las-estimaciones-de-aumentos-y-disminuciones-de-capital`.

**P-CF-11 Enter unexplained adjustments**
- S: type a net amount directly into the Adjustments line for a given date (positive inflow, negative outflow). No detail is kept. Ref: `ingresar-ajustes-al-cash-flow`.

**P-CF-12 Consult / delete a cash flow**
- Consult by number; view VAT day and generated estimates under settings; drill into any concept. Delete is allowed only if the snapshot has not been used as the copy source of a later one. Ref: `consultar-un-cash-flow`, `eliminar-un-cash-flow`.

### 2.2 Management — Reporting & forecasting

**P-RP-01 Configure parent-company reporting interface**
- T: implementation; new reporting accounts. A: controller with vendor support.
- S: enable the reporting-system parameter and choose the target (HFM, Cartesis, Magnitude); obtain the interface code tables (Hyperion/GCP/Magnitude/Cartesis line codes) from the vendor and load them; map each included chart-of-accounts account to an interface code; for GCP also load client codes; create new interface accounts/masters as needed (manual code, vendor category and subcategory); review the "Interface" tab listing entities lacking a mapping (unmapped = not reported) and assign them.
- Ref: `mp301523`, `mp301523_ejecutar`, `mp302817`, `mp302818`, `mp302797`.

**P-RP-02 Monthly export to reporting system**
- T: monthly close, reporting to HQ. A: controller.
- S: select fiscal period from/to; optionally exclude cost centers or cost-center groups; optionally restrict to a sub-company; Start; review data split into tabs as required by the target; export → one file per tab named after the tab (Excel; also PDF/text/HTML); print optional.
- O: import-ready files for HFM/etc. Ref: `mp301523`.

**P-RP-03 Forecast** (initial settings, create/modify, consult): pages exist but content is stub/"under construction" (`mp302025`, `mp302667`, `mp302668`, `mp302669`). See §11.

**P-RP-04 Service-center task (back-office ticket)** (`Tarea de Centro de Servicios`)
- Setup: define service sectors, the activities each sector performs, and the user profile assigned to execute each activity; enable users to release/manage service tasks.
- Request: requester clicks New → auto-incremented task number; picks sector and activity; requester auto-filled; subject; optional client/supplier; creation timestamp auto; number of transactions to process; priority; optional parent task; description, comments, attachments → Save → email sent to sector members; alert shown to users holding the executing profile.
- Execution: a sector member opens the task and via Actions either takes it or rejects it (reason required). Once taken, may release it back to the pool, reject it, or finalize with a closing comment.
- Closure: requester sees elapsed time and approves (state → approved, approval date stamped) or disapproves (returns for correction).
- Bulk: a purge action can force-finalize service tasks. Ref: `mp302889`, `mp302847`.

### 2.3 Sistemas — Configuration

**P-SY-01 Maintain special configurations** (`Configuraciones Especiales`): searchable tree of parameters grouped by circuit; edit → save → confirm. Vendor recommends consulting them before changing any flag. Changing menu ordering is restricted to top access levels. Ref: `mp301648`, `configurar-una-funcionalidad-especifica-del-sistema`.
Parameter value types (Ref same): boolean flags; enumerations; agency data values; default values proposed in transactions but editable (e.g. copies of payment orders); references to a master value with special meaning (e.g. production type used for fee contracts).

**P-SY-02 Agency identity & fiscal data**: activity type, start of activities, legal address, city, postal code, phone, VAT condition, tax ID (`C.U.I.T / NIT / RUT`), country, legal person type, group, display alias; Argentina-only registrations (gross-income number, pension registry, RAP, gross-income withholding agent number); "company is a media owner"; "uses advertisers belonging to other agencies"; place of payment. Used on all auto-generated prints. Ref: `ingresar-los-datos-filiatorios-de-la-agencia`.

**P-SY-03 Tax configuration** (see §8 list). Includes VAT rate history (new rate with effective date), differential/unregistered/provisional VAT with validity window, withholding and perception rates and minimums. Ref: `ingresar-la-informacion-fiscal-de-la-agencia`.

**P-SY-04 Fiscal document numbering & CAI**: choose shared vs. per-type numbering; enter CAI code and expiry per document type and letter (manual invoicing only). Ref: `ingresar-la-forma-de-numerar...`, `ingresar-los-codigos-de-cai...`.

**P-SY-05 Electronic invoicing web-service setup (Argentina)**: enter certificate subject data (common name, country code, email, state, serial = tax ID, organization, organizational unit), certificate folder path; vendor supplies endpoint URLs; test connection. Ref: `mp305185`.

**P-SY-06 Approval circuit configuration**: media plans, expenses, production POs, expense POs, tasks, timesheet (details §5, §8). Ref: respective `configurar-...` pages.

**P-SY-07 Email setup**: system-wide mail client type, send channel (client vs. SMTP), SMTP server, auth, credentials; per-terminal override (system default / none / MAPI / Lotus Notes / GroupWise; channel default / client / SMTP). Requires a mail bridge component installed on each terminal. Ref: `configurar-el-envio-y-recepcion-de-mails`, `ad_cap_gus_seg_62`.

**P-SY-08 Default timesheet jobs**: pick, from the built-in internal client "Agency" (code `AGC`), which internal JobNumbers appear by default in every timesheet. Ref: `mp302022`.

**P-SY-09 Accounting subcategory reassignment**: list P&L accounts by internal subcategory (Gross Income / Compensation / Other expenses) and move an account to another subcategory; unlimited changes. Ref: `mp301333`.

**P-SY-10 Mass master-data change** (`Modificación Masiva de Datos`): choose entity (suppliers, billing clients, products, owner clients, users, collaborators, ledger accounts, media over-commission refunds); filter (e.g. currently active, supplier type, payment term, linked ledger account); tick rows; Execute to flip active status. For billing clients there is also a bulk "exclude invoices" flag (so direct-investment pending items stop blocking job closure). For over-commission refunds: add (client, billing type invoice-vs-receive-credit-note, refund %) or remove per client, with a contract-period filter. Rows with a pending provisional-master change are shown flagged. Ref: `mp302860`.

**P-SY-11 Automatic purge** (`Depuración automática de registros`): choose purge type (close JobNumbers; finalize tasks naming the approving user; reject expense requests; reject expense sheets; delete unissued payment orders; production estimates pending billing; POs pending approval; POs pending generation; reject media insertions without orders; mark insertions and orders; reject media orders not billed; finalize service-center tasks) → filters → Start (list of candidates) → set approver where applicable → Confirm. Export of planned and executed actions is offered at confirmation. Ref: `mp302847`.

**P-SY-12 Multi-company**: (a) Sub-companies — create sub-company, assign divisions; description and grid editable, but not once more than one fiscal year exists; reports and financial statements filterable by sub-company. (b) Consolidation companies — register each member company (code 01 = consolidating environment; server, SQL credentials with encryption, real vs. test database); per entity type (clients, suppliers, accounts, users…) run auto-association by name, review, "show only unassigned", fix manually, save; create missing masters in the consolidation environment and link. All companies must sit on the same server. (c) Automatic-report databases — register group companies' DB connection data for cross-company reporting. Ref: `mp301519`, `mp301066`, `mp302848`, `mp302787`.

**P-SY-13 Report templates (Crystal)**: consult a predefined report code (e.g. `RPT000001` media insertion report, `RPT000002` advertising order), select version, edit, import a new template file, optionally generate a new version. Ref: `mp305321` and children.

**P-SY-14 Supplier portal configuration** (Liveranto): suppliers created in the ERP are auto-exported to the portal; apply settings to one supplier / all domestic / all foreign / all: mandatory PDF of invoice, mandatory PO approval attachment, allow manual-origin invoices (no estimate/expense/media order reference), allow partial invoicing of a PO, allow rate differences on media orders, allow different currency. Ref: `mp302923`.

**P-SY-15 Software maintenance**: check/install updates (only users with special main-menu permission; optionally block new sessions and force-disconnect users; version upgrades auto-backup); script administration across environments; view license, technical info, error screenshots. Ref: `ad_cap_gus_seg_57`, `mp302657`, `ad_cap_gus_seg_60/61/58`.

### 2.4 Sistemas — Users & security

**P-US-01 Create user**
- Pre: security policy, media approval policy, non-billable estimate approval policy, production PO policy, expense policy, expense PO policy, and standard profiles reviewed.
- S: New → link to existing contact or let the system create one (a user is always a contact) → name → login code (≤8 alphanumeric) → password (≤8) → type (pure / collaborator / client) → not blocked → unique email (unless the other holder is inactive) → start date (defaults today) → blank end date → department → Profiles tab: base profile either a standard (by department) or copied from another user, then fine-tune; special main-menu accesses (month-close control routines, script admin, license info) → Settings tab: language, regional setting, Mac user + daemon for mandatory timesheet, max simultaneous instances per option; specific activities checkboxes → Save → Modify → set expense control/approval relationships (whom this user controls `Ctrl` / approves `Apr`, max amount) → Save.
- Rules: user must be saved before expense relationships are set; approver needs access level 1 or 2 on the relevant screen; Mac users can only use the web portal for hours and tasks. Ref: `mp301236_usuarios`, `ingresar-un-usuario`.

**P-US-02 Modify profile** (per screen/branch S/N, access level, visibility level) — ideally via the shared profile so all holders update. Ref: `modificar-el-perfil-de-acceso-de-un-usuario`, `mp302016`.

**P-US-03 Modify specific activities** — same list as creation. Ref: `ad_cap_gus_seg_14`.

**P-US-04 Deactivate user**: set end date → becomes inactive; recommended to first reassign. Delete is only allowed if the user has no specific activities/history. Ref: `dar-de-baja-a-un-usuario`.

**P-US-05 Reassign responsibilities**: "Replace" → choose successor for open tasks → choose successor as responsible for open JobNumbers. Successor must hold sufficient permissions. Ref: `pasar-la-responsabilidad...`.

**P-US-06 Password reset**: set provisional password; valid for one login; user must set a new one. Ref: `ad_cap_gus_seg_18`.

**P-US-07 Restricted user maintenance**: a helpdesk-type screen that only allows changing password, email, unblocking, and reactivating (resetting last-access date when inactivity lockout is on). Ref: `mp302728`.

**P-US-08 Unlock stuck departed user**: inactive users may still own pending items (e.g. unapproved expense sheets); a dedicated action releases a "locked" user record so approvals can proceed. Ref: `mp301236_usuarios`.

**P-US-09 Profiles**: create/copy/delete (delete only if unassigned)/export-import to Excel (two sheets: modules and menu options with permissions) to move profiles from test to production. Ref: `mp302016`, `generar-un-nuevo-perfil-de-usuario`.

**P-US-10 Functional roles**: define role name/code, base profile (standard or copied from another role), specific activities, provisional-master permissions; changing a role propagates to all users holding it. A report lists options enabled per role with access/visibility levels. Ref: `mp301236_maestro_funciones`, `mp302829`. (Role rules, role-allowed activities, SoD control screens are stubs: `mp302827`, `mp302828`, `mp302826`.)

**P-US-11 External system credentials**: map ERP users to credentials in a contracted third-party service. Ref: `mp309236`.

### 2.5 Sistemas — Audit

**P-AU-01 Movement audit trail**: filter by date range, criterion (user or department), users/departments, entity/operation type, optional key (document number or period code like `202011`), "show from key", include deleted users → list of Date, Time, User, Action, Entity type, Entity number, Notes. Some screens expose context audits in their Tools tab (e.g. estimate header changes vs. item-level changes and approvals). Sequencer value viewable. Ref: `mp301188`, `obtener-las-pistas-de-auditoria...`.
**P-AU-02 Open transactions**: list currently open transactions. Ref: `ad_cap_gus_seg_35`.
**P-AU-03 License consumption**: per period, licenses used and excess attempts. Ref: `mp302802`.
**P-AU-04 Access control report**: per-user access detail, selectable across group databases. Ref: `mp302859`.
**P-AU-05 Efficiency report**: per user/department counts of supplier docs entered/cancelled, client docs entered/cancelled, payments, collections, journal entries, cancelled payments/collections. Ref: `mp301619`.
**P-AU-06 System usage report**: option-access counts per user/department and record counts per audited entity. Ref: `mp302768`.
**P-AU-07 Access-by-user report**: human-readable listing of each option with visibility level + description and action rights (create, delete, modify, special, per specific activities), optional tabs for specific activities and provisional-master rights; filters by user, department, profile, visibility level. Ref: `mp302935`.
**P-AU-08 Dynamic permissions report**: pivot/grid builder over user-permission data. Ref: `mp402832_8`.

### 2.6 Sistemas — Print layouts

**P-PF-01 Cheque layout**: per (cheque type normal/post-dated, bank) — one layout per bank — set X/Y coordinates and max lengths for amount in figures (with currency sign option, asterisk fill before/after, bold), amount in words (+ continuation line, ~60 chars typical), payee (+ continuation), PO notes, separation (cheque height), date / day / month / year (2-digit option, "DE" legend), legend + complementary text, postal code, signature (agency name), place (agency city); page height/width, font; post-dated cheques add a due-date block. Copy, export as SQL script. Ref: `mp301328` + children.

**P-PF-02 Invoice layout**: define document types (invoice/CN/DN), billing type (generic; direct vs indirect; manual; CN-cancels-invoice; media-hub commission; fee billing; over-commission billing; withholding certificate), origin (general/media/production), detail mode (by day; summarized by item; summarized to free text; summarized by supplier invoice), description, active flag, parent/child inheritance, default printer, paper size, proforma allowed, copies same/different sheet; tick-box coordinates for doc type and client tax condition; colors, background image; header (letter, number, doc type with strike-through, date formats, print time, no leading zeros), client and agency fields, client order number / client PO number, payment condition and due date; fiscal identification code (footer); body region start/end (page break), box, PDF margins, supplier/invoice reference for commission invoices; detail fields; agency-service line inline or in totals; "on behalf of client" legends; amounts (net, gross+discounts, unit price×qty); totals, amount in words, CAI + QR (Argentina); footnotes per currency/foreign type; up to 60 lines, 90 body + 90 footer variables, logos per division, generating/approving user; agency, division and promissory-note data. Assign layout to billing client × document type × branch × letter; barcode per (doc, letter, branch). Copy, export SQL, preview, test print, import from legacy MediaPlus. Ref: `mp301327`.

**P-PF-03 Purchase-order layout**: type production or expenses; all clients or a specific one; unit of measure; header (agency, tax data, printing/creating user, PO number, estimate number, subject, JobNumber, product), supplier, invoice-to (client for direct, agency for indirect), body region, description, unit price, qty, days (requires price-list and per-day costing parameters), totals net of tax, place and payment terms, special notes, cancellation block, logo, signatures (image path on network), up to 20+20 lines, 30+30 variables, PO type title (Direct / Indirect / Mixed), notes by type (e.g. "does not pass through agency"). Ref: `mp301439`.

**P-PF-04 Payment-order & receipt layout**: one layout each; orientation and size; agency and counterparty data, document number/date, body header (cancelled documents and funds used: currency, bank, cheque/operation number, amount), optional accounting entry columns (account, sub-account, JobNumber, OT), totals in figures and words, number of cheques, exchange rate, signatures, up to 50 variables and 50 lines, logo. Ref: `mp301329`.

**P-PF-05 Production estimate layout**: multiple named layouts (per client, currency, language); orientation; currency sign; grouped notes; grouping of items (e.g. by supplier); header, body, unit price/qty, sale or cost amount; **alternatives** mode (up to 3 supplier quotes per item, each with agency fee, optional supplier observations, optional anonymization "supplier 1/2/3", no grand total); totals (net, words), payment place/terms, notes, agency and client logos, signatures. Reprint required after layout change. Ref: `mp301331`.

### 2.7 General — Communication, contacts, organization

**P-GN-01 Agency contact registry**: New → name, organization, title, address, phones, fax, mobile, two emails, access type (who may see it), active flag, notes → related entities tab (tick entity type and pick code — mandatory per intro, e.g. media vendor, bank) → Save. Copy action clones a contact. Ref: `mp302014`, `-ingresar-un-contacto-de-la-agencia-`.

**P-GN-02 Inbox & communications**: integrates with the terminal's mail client via a MAPI bridge; grid of communications (origin: contact report/task/memo/brief; read/unread; attachment; subject; date; time; JobNumber); Send/Receive; Generate new contact report / memo / task / brief from a selected email; save external email as internal email linked to a JobNumber (then visible in the JobNumber status screen under document type "E-mail"); export; auto-filters. Ref: `mp301435`, `asignar-un-jobnumber-a-un-mail-externo`.

**P-GN-03 Send email**: New → To and CC chosen only from contacts → subject → JobNumber via cascading lookup (owner client → product → JobNumber) → attachments → body → Send → confirm → internal recipients get it in their alerts inbox; for external recipients a confirmation dialog lists external addresses to keep/remove → sent. Ref: `mp306401`, children.

**P-GN-04 Memo (internal communication)**: New → JobNumber via cascade (only open jobs listed; memo auto-numbered and inherits job subject) → From auto = author → To exactly one person → CC and client-side attendees → subject → rich body → Save (requires all main fields) → Send → appears in recipients' alerts inbox "Memos" box. Memos are informational (no due dates or budgets, unlike tasks). Ref: `mp305401`, `enviar-una-comunicacion-interna`.

**P-GN-05 Meeting calendar**: views daily / work-week / week / month; create event (subject, location, color, notes, reminder & frequency, all-day, start/end, show-as, "meeting" flag + invitees from contacts, recurrence: start time, duration, recurrence type and parameters, recurrence start/end) → Save sends invitations; create fiscal due date (subject, notes, reminder, recurrence, single date or recurring pattern). Optional sync with Outlook per user (sync email, interval minutes, days before/after window). Ref: `mp301392` + children.

**P-GN-06 Timesheet entry** (detailed in §5): via menu or forced at login. Ref: `mp301387` + children.

**P-GN-07 Approve hours**: approver selects collaborator (`Horas De`), Start, ticks Approve or Reject per entry, Save. Variant: approval at login. Ref: `mp301527`, `aprobar-la-asignacion...`.

**P-GN-08 Modify past hours**: Consult → responsible, fiscal year, month → Modify → click day → confirm → edit → Save. Requires `Permite Modif. Horas Día Anterior`. Ref: `-modificar-la-asignacion-de-horas-trabajadas-`.

**P-GN-09 Personal debt inquiry**: as-of date, pick self or (for managers) subordinates, active/inactive filter → balance per sub-account of the collaborator (loans, unsettled expense/cost sheets, reimbursements). Ref: `mp301098`, child.

**P-GN-10 Timesheet reports**: static report (filters dates, owner client, active clients only, collaborators, active status, category; real hours with cost and weighted hours capped at 8/day; internal and external rate valuations) and dynamic pivot report (field picker, templates, filters date/client/collaborator/category/currency, pivot vs grid, scheduled weekly generation at 00:00, online vs offline source). Ref: `mp302874`, `mp402832_5`.

### 2.8 Home screen (alerts dashboard) and navigation

- Three zones: Communications (tasks, memos, contact reports, strategic briefs), Calendar (fiscal calendar, appointments, invitations), Other (alerts, 10 most-used and 10 most-recent options per user).
- Per-user settings: show fiscal due dates; show holidays; refresh interval (minutes); retention days for unread notices; choice of alerts from a system-defined list filtered by the user's access. Clicking an alert opens the underlying process; the alert disappears once the work is done. Ref: `menuprincipal`, `ad_cap_gus_gen_23..29`.
- Navigation aids: menu tree, screen search, favorites folder, personalized icon view (per-user), contextual help tab, per-user printer settings (printer, paper size, source, orientation). Ref: `ad_cap_gus_gen_08/11/18/22`, `mp302649`.

### 2.9 Academia (training index)

Video curricula organized by function and role: Accounts (common topics, account executive, account director); Production (concepts, building an estimate, worked example, approval circuit, cost settlement, estimate analysis, tips); Offline media planning (concepts, system planning, TV, radio/cable, press/OOH, rescheduling, reports); Offline media buying (concepts, buying, press/OOH, radio/TV/cable, ad verification, pre/post evaluation, changes, reports); Digital planning (concepts, steps, masters, process, buying, taxonomy); Expenses (concepts, masters, approval, requests, petty cash, expense settlement, cost settlement, expense budget); AR (concepts, controls, billing types, indirect media billing, production billing, manual/fixed-asset/advance billing, e-invoicing); AP (common topics, AP analyst); Treasury (concepts, masters, payment orders, cash flow, "libranza", collections, bank reconciliation, reports); Accounting (fundamentals, closing process); Systems (users/collaborators, audit/formats). Value for the repo: it confirms the canonical **personas** (account executive, account director, production, media planner, media buyer, digital planner, AP analyst, AR, treasurer, accountant, sysadmin) that skills should be organized around. Ref: `academia`, `*2.html`.

---

## 3. Entities

| Entity | Spanish | Key fields (Spanish → English) |
|---|---|---|
| Company / environment | Empresa | `Alias del Nombre`, `Tipo de Actividad` (agency/advertiser/producer), `Inicio de Actividades`, `Domicilio`, `Localidad`, `Código Postal`, `Teléfono`, `Tipo de IVA`/`Condición IVA`, `C.U.I.T/NIT/RUT` tax id, `País`, `Tipo de Persona`, `Grupo al que Pertenece`, `Empresa es un Medio`, `Usa Anunciantes`, `Lugar de Pago`, logo, real/test DB flag |
| Consolidation member | Empresa del Consolidado | code (01 = consolidator), name, server, SQL user/password (encrypted), DB type real/test, master associations per entity type |
| Sub-company | Sub-Empresa | auto code, `Descripción`, set of divisions (code, name, active) |
| Branch / point of sale | Sucursal | referenced by invoice layout assignment and barcode (doc × letter × branch); e-invoicing points of sale always number per type |
| Division / cost center | División / Centro de Costos | user default division & cost center; logo per division for invoices |
| Department | Departamento | type (incl. coordination type used by task copy rules); standard profiles are offered per department |
| Attention group | Grupo de Atención | restricts which clients/products/contacts a user sees |
| Contact | Contacto | `Nombre y Apellido`, `Organización`, `Cargo`, `Domicilio`, `Teléfono 1/2`, `Fax`, `Móvil`, `E Mail 1/2`, `Tipo de Acceso`, `Vigente`, `Observaciones`, related entities (type + code) |
| User | Usuario | contact link, `Código de Usuario` (≤8), `Clave de acceso` (≤8), `Tipo de Usuario` (puro / colaborador / cliente), email (unique among active), `Usuario Vigente`, `Fecha de Alta`, `Fecha de Baja`, reactivation date, `Usuario Bloqueado` + last block/unblock dates, department, attention group, cost center, division, base profile & type, special main-menu accesses, language, regionalization, Mac flag & Mac short name, `Cant. Máx. Opciones Simult.`, specific activities, expense control/approve map with `Monto Máximo Permitido`, provisional-master rights, Outlook sync settings, AD domain/user, digital signature (client users), client-user scope (owner client, billing clients, products) |
| Collaborator | Colaborador | department, pay level/category (junior/senior/expert), daily hours, timesheet obligation, timesheet approver, internal rate (cost/hour) and external rate (sale/hour), default division, responsible-for-entry relationships; may exist without a user |
| Profile | Perfil | code, description, tree of menu branches/options each with `S/N` access, `N/A` access level 1–6, `N/V` visibility A–D ("Multiple" at branch level when children differ) |
| Functional role | Rol Funcional | code, name, base profile, specific activities, provisional-master rights; propagates to users |
| Specific activity (permission) | Actividad Específica | boolean or parametrized power (see §5 R-SEC) |
| External system credential | Usuario Sistema Externo | provider, user, external username, password |
| System parameter | Configuración Especial | group (General, Billing, Accounting, Security, Cash&Bank, Production, Media, Media Hub, Interface, Company Data, Initial Settings, Users, Taxes, System, Time Sheet, E-mail, Accounts, Tasks, Expenses), key, type (bool/enum/value/default/master-ref), value, help text |
| VAT rate history | Historial IVA | effective date, rate |
| CAI | CAI | doc type, letter, number, expiry |
| Alert | Alerta | system-defined id, name, visibility tied to access; per-user `Ver` flag; opens target process |
| Communication | Comunicación | origin (contact report/task/memo/brief/e-mail), read status, attachment, subject, date, time, JobNumber |
| Memo | Memo | auto number, JobNumber, subject, sent date, last-modified date, from, to (single), CC, client attendees, body |
| Calendar item | Evento / Cita / Invitación / Vencimiento Fiscal | subject, location, color, notes, reminder & frequency, all-day, start, end, show-as, meeting flag, invitees, recurrence (start time, duration, type, pattern, from, to) |
| Holiday | Feriado del Ejercicio | date (used by cash flow and timesheet) |
| Timesheet day | TimeSheet | responsible, fiscal year, month/year, date, total hours, entered hours, lines (owner client, JobNumber, subject, product, division, concept or task, hours in 0.25 steps), approval state, audit |
| Cash-flow snapshot | Cash Flow | number, type (daily/weekly/strategic), notes, show zero-balance accounts, copied-from, VAT pay day, per-concept item list with expected dates, `Posterior` bucket, adjustments, generated estimates |
| Delay profile | Días de Atraso Crónico | party (customer/supplier), days |
| Account group liquidity | Rubro | type (Gross Income/Compensation/Expenses), liquidity (short/long) |
| Reporting mapping | Código de interfaz | target system, interface code, account mapping, category/subcategory, client codes (GCP) |
| Service-center task | Tarea de Centro de Servicios | number, sector, activity, requester, responsible, subject, client, supplier, created at, transaction count, priority, parent task, description, comments, attachments, state, finish comment, approval date |
| Audit record | Auditoría | date, time, user, action, entity type, entity number, notes, sequencer |
| Print layout | Formato | type, scope (client/doc type/branch/letter), coordinates map, fonts, lines, variables, images, notes, parent layout, active |
| Report template | Reporte Crystal | code, name, subreport, autostart, version, file |
| Supplier-portal setting | Config. Proveedor Liveranto | scope, 6 booleans (§2.3 P-SY-14) |

---

## 4. Lifecycles

- **User**: draft → active (start date reached, not blocked) ⇄ blocked (manual, wrong-password limit, inactivity limit) → inactive (end date set) → reactivated (reactivation date) ; delete only if no activity. Password: provisional (one-time) → personal; forced change every N days.
- **Profile/Role**: created → assigned (cannot be deleted) → edited (propagates to holders) → unassigned → deletable.
- **Timesheet day**: pending → entered (total = expected) → [if approval on] pending approval → approved (counts in reports) | rejected → re-entered by collaborator → pending approval. Locks: cannot edit prior days unless parameter allows; self-reactivation within N days.
- **Hours for login**: if mandatory, login blocked until every pending day for every collaborator the user is responsible for is entered.
- **Memo**: new → saved → sent (in recipients' alerts inbox) → read → expires from the alerts inbox after retention days.
- **Service-center task**: created → (rejected by sector) | taken → (released → back to pool) | (rejected) | finalized → approved | disapproved → back to executor.
- **Cash-flow snapshot**: generated → adjusted (modified/saved repeatedly) → superseded by a newer snapshot (copy-forward keeps unchanged planned items) → historical; deletable only if never copied.
- **Print layout**: created → generated (tabs populated) → configured → assigned → (inactive) → deleted. Changes require reprint of existing documents.
- **Provisional master change** (3-stage): proposed by operator → validated by manager (approve/reject) → registered by accounting. Same for provisional journal entries, except designated users may post definitive entries directly.
- **Alert**: raised by a pending condition → visible to users with access who opted in → user opens and completes process → disappears.

---

## 5. Business rules and calculations

### Cash flow (R-CF)
1. Horizons: daily = 20 calendar days per overview text but 15 business days per the generation guide (conflict, see §11); weekly = 15 weeks, each column dated on Monday; strategic = 15 months from generation date.
2. Opening position = book balance of all bank and cash accounts in the selected currency (`Disponibilidades líquidas`).
3. Only active ledger accounts tagged with the relevant observation code feed each concept.
4. Customer open item expected date = document due date + customer chronic delay. Supplier open item expected date = due date + supplier chronic delay.
5. Estimated-billing items: expected collection = estimated billing date + customer usual payment term + chronic delay; supplier side analogous with supplier term + delay. Payroll "other" lines use the supplier delay.
6. Fixed-asset purchase payment date = purchase date + supplier terms + delay (overridable); sale collection date = sale date + optional defer days.
7. Any expected date falling on a holiday or weekend shifts to the next business day.
8. Items dated after the horizon go to a `Posterior` column; items before/after the window for cheques in portfolio are shown in a trailing column and can be moved.
9. Only client-approved estimates, media plans and fee contracts are included; pending-approval or rejected ones are excluded; approved items without an estimated billing date are excluded from the summary (all listed items should be dated).
10. Expected withholdings per party may be set as a percentage of the item or as manual amounts and reduce the net cash expected.
11. VAT position is read-only (computed from recorded sales/purchases to date) and placed on the configured VAT payment day.
12. Adjustments are net amounts only (positive inflow, negative outflow); expenses estimates use positive = outflow, negative = income.
13. A snapshot never posts accounting entries, never alters source transactions, and is not refreshed by later real transactions; refresh = generate a new snapshot with copy-from-previous (copies the last snapshot of the same type; planned items that didn't change keep their dates).
14. Projected balance per column = previous balance + inflows − outflows across all concepts (Disponibilidades, values to deposit, customers, documents receivable, suppliers, post-dated cheques, obligations, VAT position, fixed-asset buys/sells, capital moves, Gross Income estimates, compensation, expenses/other, recurring configured outflows, adjustments).
15. Generating after the planned payment run is recommended, because pending supplier debt is drawn from AP and would otherwise understate future bank balance.
16. Multiple integrating (control) accounts for customers or suppliers are shown separately.
17. Approved expense contracts are not auto-read; recurring outflows must be configured manually (frequency monthly/weekly/one-off, payment days, currency).

### Reporting (R-RP)
18. An entity or account without an interface code is not reported; the interface tab lists such gaps.
19. Export files are produced one per tab, named after the tab.
20. Cost centers / cost-center groups can be excluded; sub-company filter scopes the export.

### Timesheet (R-TS)
21. Allocation mode (`Time Sheet por Cliente`): by client (posts to the client's generic job), by JobNumber, or by task (tasks in progress proposed; manual extra lines for the remainder).
22. Hours in quarter-hour increments only (0.25, 0.50, 0.75, 1).
23. A day can only be saved when entered hours equal the collaborator's configured daily total.
24. Non-client time goes to internal client `AGC` jobs: generic, maternity, sickness, vacation, holidays, "time and cost not assignable to client" (also recommended for general overheads in other modules), new business; additional generic jobs can be created per client.
25. Rows with hours stay visible for 7 days; jobs stay in lookup for `Duración Jobs en Carga de Horas` (days per one page, weeks per another).
26. Business-days-only flag: when off, weekend/holiday days must be filled (0 allowed).
27. Hour cap flag limits entry to profile hours.
28. Previous-day edit flag; self-reactivation window (`Cant. Máx. Días a auto-reactivar` > 0 enables a reactivate button).
29. Approval flag: only approved hours count in management reports; rejected hours must be re-entered. Approver alert "hours pending approval" in the alerts inbox. Optional approval at login (approver must enter own hours then approve subordinates sequentially).
30. Concepts flag: hours per JobNumber are split by JobNumber concepts.
31. Audit flag: logs user, date, JobNumber, approvals and rejections.
32. Generic-job restriction flag (job-mode only).
33. Division default: if `Filtrar división default por JobNumber` true use job division, else collaborator division; generic jobs require manual division.
34. Fiscal year, month and date are system-driven from the last entry (sequential entry; not editable).
35. Traffic lights for last week / last 4 weeks compare share of hours charged to clients versus management target (e.g. ~90% for executives) with tolerance: amber when deviating, red when excessive.
36. "Replicate hours" copies the first day's allocation to subsequent days (e.g. vacation) retroactively; should be used on return.
37. Reporting: hours above 8/day are weighted down to 8 in the weighted section; valuation uses internal rate (cost) and external rate (sale).
38. "Active clients only" filter hides hours of now-inactive clients — known pitfall.

### Security & access (R-SEC)
39. Every operator must be a registered user; every user is a contact; collaborator can exist without user and vice versa.
40. Login code and password max 8 characters; email unique among active users.
41. Access levels: 1 full CRUD + special actions (e.g. posting to control accounts); 2 create/delete/modify/query; 3 create/modify/query; 4 create/query; 5 query (one page lists "query with special actions" as 5 and "query only" as 6). Visibility: A supervisor/unrestricted; B profitability and costs; C costs; D no costs. Branch-level assignment cascades to children; differing children display "Multiple".
42. Hiding costs (level D) is an explicit anti-collusion control so buyers/planners can't favor suppliers.
43. Expense approvers need access level 1 or 2 on the expense screen; approval cap per approver (blank = unlimited); self-approval blocked if `No Permite Autoaprobar Gastos` = true.
44. Specific activities (powers): approve others' hours; control/approve others' expenses (+cap); requires control/approval (inverse view); approve for billing; approve on behalf of client; approve non-billable estimates; approve production POs; approve expense POs; must enter FX rates at login (blocking dialog if today's rate missing); post supplier invoices after pre-close; finalize payment lists; view supplier commissions; view exclusive contacts; reassign tasks in own department / other departments / any task from list; view fee instalments in listings; close insertions (media); close estimates; reject expense sheets; web-only hours & tasks (no license consumed); external (client) user; view all expense requests; audit adjustments administration; create package items; recipient may set internal date beyond promised date; administer / view USGAAP-only entries; approve supplier contacts from supplier portal. Costa Rica / Panama: separate calculator and approver of withholdings — unpaid until approved.
45. Approve-for-billing on media requires the media circuit to be Restricted/Strict or approval-for-billing enabled; approve-by-client on media applies when circuit ≠ None.
46. Security policy parameters: fingerprint, min password length, password history count, max password age (days), inactivity lockout days, max failed attempts, password encryption, single password across multi-company, terminal binding, audit login/logout, audit system access, idle auto-logout minutes (0 = never), secure password (uppercase + digit), case-sensitive.
47. Active Directory SSO optional (special configuration + domain/user on profile).
48. Deleting a user with history is forbidden; use end date. Departed users with pending items must be unlocked and replaced.
49. Updates require special main-menu permission.
50. Max simultaneous instances per option per user.
51. A user without department can be saved but cannot create campaigns or incur costs.

### Approval circuit rules governed here (R-AP)
52. Media plan circuit: None (approve-for-billing + final version), Restricted (initial version, client approval, approve-for-billing, final version), Strict (plan enablement, senior approval, initial version, client approval, approve-for-billing, final version). Additional flags: budget control on save, approve-for-billing required, ad-verification implies approve-for-billing, client approval per insertion vs whole plan, may order to vendor without client approval, attachment allowed/mandatory on client approval, credit limit control for media/production (Restricted/Strict only).
53. Production POs: mandatory PO → supplier invoices for production estimates only accepted with a generated PO; mandatory PO approval → only with approved PO; only users with the activity may approve.
54. Expense POs: same two rules for expense requests.
55. Expenses: control by client vs JobNumber; campaign owners approve cost sheets (JobNumber mode); advances linkable to expense sheets; circuit covers requests, cost sheets, expense sheets, petty cash, expense contracts.
56. Supplier commission: none / agency invoices supplier / receives credit notes (in development); provisioning; per-item who bills; restrict visibility to account department; default %; result account either fee income (observation code 22, part of Gross Income) or supplier commissions (code U4, other income); mandatory entry. Only invoiceable if billing client accepts supplier commissions.
57. Penny rounding: max amount auto-booked as rounding difference on supplier invoices to an account in category Results / subcategory Other expenses / observation code C1 flagged for AP and expenses modules.
58. Tasks: days-to-due tolerance for overdue alert; assigned/overdue alerts; auto-copy coordination department; auto-copy attention-group heads; email tasks to creatives / account users; copied users may edit; no printing for creatives; account users may edit; JPM tracking and templates; auto-finish task when related production estimate is billed; forbid generic jobs; workflow timer start/stop; suppress final-completion notification; email on billing a costed task; cancellation/modification notice; per-question responder in task forms.

### Numbering & documents (R-DOC)
59. Fiscal numbering: shared across doc types or independent per type; always independent per letter; e-invoicing points of sale always independent per type.
60. CAI used only for manual (non fiscal-printer, non-electronic) invoices; expiry tracked.
61. Invoice letter (Argentina): A, B, C, E, M by issuer/recipient tax status.
62. Print layouts: coordinate value −1 means "not printed"; one cheque layout per bank; one payment-order and one receipt layout; changes require reprinting.

### Communications (R-COM)
63. Recipients only from the contact registry; internal contacts receive via the alerts inbox, external via email (with confirmation of external addresses).
64. Memo has exactly one To recipient; only open JobNumbers selectable.
65. Unread notices remain in the alerts inbox for the configured retention days.
66. Home alerts are system-defined; users may only choose among those allowed by their access.

### Audit (R-AUD)
67. Audit records capture date, time, user, action, entity type, entity number, notes; filterable by user/department/entity/key; deleted users' records retrievable.
68. Mass changes and purges offer export of planned and executed actions at confirmation.
69. Dynamic reports: expensive online queries are blocked and must run offline (on a nightly frozen copy); scheduled reports run weekly at 00:00 and stamp generation time and filters.

---

## 6. Financial impacts

- Cash flow: zero accounting impact (planning only), but drives treasury decisions: payment-run sizing, financing needs, collection follow-up.
- Reporting export: no postings; determines HQ consolidated P&L/GCP figures — mapping errors silently drop amounts (unmapped = unreported).
- Subcategory reassignment (Gross Income / Compensation / Other expenses) changes management P&L presentation and the cash-flow Gross Income/Compensation blocks.
- Timesheet: approved hours × internal rate = labor cost per JobNumber; × external rate = billable value (fee-by-hours contracts, profitability). Unapproved hours are invisible to profitability.
- Approval flags directly gate revenue recognition and AP: no approval-for-billing → no client invoice; mandatory PO approval → supplier invoice cannot be booked.
- Tax parameters determine invoice VAT, withholdings, perceptions, and VAT position timing (registration date vs payment date for input VAT, post-close input VAT registration, retention-date basis).
- Penny rounding auto-books small differences to an expense account.
- Supplier commission configuration decides whether commission revenue lands in Gross Income or Other income.
- Over-commission refund configuration creates obligations to return part of media rebates to clients (invoice vs credit note).
- Purge actions can close jobs and reject orders/estimates, removing them from pending-to-bill — affects revenue pipeline and cash-flow inputs.
- Bulk "exclude invoices" on billing clients removes direct-investment pending items from job closure checks.
- USGAAP-only entries exist for HQ reporting and are visible only to authorized users.
- Personal debt: employee loans and unsettled expense/cost sheets are receivables from staff.

---

## 7. Cross-module handoffs

| From | To | Handoff |
|---|---|---|
| Accounting (balances, observation codes, holidays) | Cash flow | opening liquidity, concept mapping, business-day calendar |
| AR open items / documents / cheques in portfolio | Cash flow | expected collections |
| AP open items / post-dated cheques / obligations | Cash flow | expected payments (best after payment-list run) |
| Production estimates, media plans, fee contracts (client-approved) | Cash flow | pending-to-bill and pending-cost estimates |
| Expenses (approved requests without invoice) | Cash flow | manual expense estimates |
| Accounting (chart of accounts, cost centers, sub-companies) | Reporting export | monthly HFM/Magnitude/Cartesis files |
| Timesheet (approved) | Accounts/Production/Fees/Profitability | labor cost & sale value per JobNumber |
| Tasks module | Timesheet (task mode), alerts inbox, Purge, Billing (auto-finish on billing) | |
| Users/Roles | Every module | approval powers and visibility |
| Collaborators master (Accounting masters) | Timesheet, Hour approval, Personal debt | daily hours, approver, rates |
| Special configurations | Media, Production, Expenses, AR, AP, Treasury, Tasks, Timesheet | circuit behavior |
| Print layouts | AR (invoices), Production (estimates, POs), Expenses (POs), Treasury (payment orders, receipts, cheques), Media (Crystal insertion report and advertising order) | rendering |
| Contacts | Email, memos, meetings, vendor/bank entities on documents | addressee source |
| Communications | JobNumber status screen | email filed as document type "E-mail" |
| Supplier creation | Supplier portal | auto export + portal behavior settings |
| Consolidation | Group reporting | master associations |
| Home alerts | Hour approval, task status, approvals generally, service-center tasks | work queue |
| Users with FX-rate activity | Treasury/AR/AP | daily currency rates captured at login |

---

## 8. Configuration and country-specific behavior

**Parameter groups**: General; Billing (`Facturación`); Accounting; Security; Cash & Bank; Production; Media; Media Hub (`Central de Medios`); Interface; Company Data; Initial Settings; Users; Taxes; System (.NET environment); Time Sheet; E-mail; Accounts (e.g. alerts to close inactive projects); Tasks; Expenses.

**Notable parameters that change behavior** (name → effect):

General / initial
- `Tipo de Actividad` — agency vs advertiser vs producer mode.
- `Empresa es un Medio` — company acts as a media owner.
- `Usa Anunciantes` — handles advertisers that are clients of other agencies.
- `País`, `Condición IVA`, `Tipo de Persona de Agencia`, `Grupo al que Pertenece`, `Lugar de Pago`.
- `Archivo de Contactos` — contacts managed per billing client vs per owner client.
- `Aprueba JobNumber por Cliente` — example boolean requiring client approval of jobs.
- `Adjunta Documento en Aprobación por Cliente`, `Adjunto Obligatorio`, `Límite de Crédito en Medios/Producción`.
- `Controla IVA Incluido en Clientes del Exterior`, `Criterio de IVA por Fecha Factura` (estimate rate vs rate at invoice date).
- Logo printing per layout + `Logo de la Empresa`.
- `Tipo de Producción Fee` — production type used for fee contracts.
- `Copias de Ordenes de Pago` — default copies.

Billing
- `Ajuste Automático por Diferencia de Redondeo` (max auto-rounding amount).
- `Comisión Proveedores` (No / Invoice / Receive CN), `Provisiona Comisión Proveedores`, `Forma de Cobro por Ítem`, `Restringe Visualización a Cuentas`, `Usa Porc Comisión a Proveedores por Default`, `Cuenta Contable de Imputación`, `Carga Obligatoria de Comisión Prov.`
- `Factura IVA propio en medios` (agency's vs media's VAT rate), `Redondeo IVA X OT`, `Redondeo IVA X Factura Total`, `Factura IVA Cliente del Exterior`, `Usa Traslado Percepción IVA`.
- `Control de Numeración por Tipo de Comprobante`; CAI number/expiry per type & letter; letter used for foreign billing; free-text invoice allowed.

Accounting
- `Controla Crédito Fiscal IVA` + `Control Desde` (input VAT by payment date vs registration date), `Registra Crédito Fiscal Post Cierre`, `Armar Posición IVA por la fecha real de las retenciones`; depreciation method; secondary account group; reporting system choice (HFM/Cartesis/Magnitude, GCP on request).

Cash & bank
- `Usa Cheques Diferidos`; IIBB withholding certificate numbering per fiscal year vs indefinite; `Traslada Retención IVA`; `Es Autorretenedor`; `Difiere IVA Proveedor de Persona Física`, `Difiere Retención IVA del Proveedor del Exterior`, `Usa Tabla de Ret. Rentas` (Argentina, set false); `Correlatividad Conjunta Ret IVA y Ganancias`; supplier web portal; max numbering gaps in payment orders/receipts; early-payment discounts.

Taxes
- `Retiene Ingresos Brutos` + `Jurisdicción Sede`; `Porcentaje de IVA` with history; `IVA Diferencial`; `IVA No Inscrip.`; `IVA Provisorio` + validity; `Retiene IVA`, `Porcentaje Retención IVA`, `Monto Mínimo para Retener IVA`; `Porcentaje de Percepción IVA`, `Monto Mínimo para Percibir IVA`; `Percibe Ingresos Brutos` (no / investment + agency service / agency service only) + minimum; `Porc Ret Ganancias`, `Porc Ret Ganancias No Inscr.`; SUSS withholdings (cleaning, social security, security services); `Usa Múltiples Tasas de IVA` (Argentina false); `Retiene Contribución Publicitaria` + start date + rate + copies; `Monto mínimo para retener IIBB a proveedores`.

Production
- `Orden de Compra Obligatoria en Producción`, `Aprobación Obligatoria Órdenes de Compra`, `Aprobación No Facturables`, central production / production departments, `Lista Precios Producción`, `Calcular Costos por Día`.

Media
- `Circuito de Aprobación Medios` (None/Restricted/Strict), `Controla Presupuesto`, `Aprueba para Facturar`, `Aprueba para Facturar al Controlar Avisos`, `Período de Aprobación por Cliente` (per insertion vs per plan), `Puede Ordenar sin Aprobar x Cliente`; media hub flags.

Expenses
- `Control Gastos por JobNumber`, `No Permite Autoaprobar Gastos`, `Aprob. De Rend. De Costos por Responsable`, `Asocia Anticipos a Planillas de Gastos`, `Orden de Compra Obligatoria en Gastos`, `Aprobación Ordenes de Gastos`.

Tasks — the 18 flags in §5 rule 58 (`Días por Vencer para Estado de Tareas`, `Alerta de Estado de Tareas`, `Copia Coordinador en Tarea`, `Copia Jefes Grupos en Tareas`, `Envía Tareas por EMail a Creativos`, `...a Cuentas`, `Tarea Modificable por los Copiados`, `No Imprimir Tareas Creativos`, `Tareas Modificables por Cuentas`, `Usa Seguimiento de Tareas (JPM)`, `Usa JPM en Seguimiento de Tareas`, `Finaliza Tarea al Facturar`, `Impedir Relacionar Tareas a Job Genéricos`, `Usa Workflow`, `Sin Notificación de Finalización Definitiva`, `Envía e mail al facturar tarea con costo`, `Aviso de Cancelación de Tarea`, `Quien Responde a Cada Pregunta en Form Asociado`).

Time Sheet / Initial — `Time Sheet` (on) + `Desde el`; `Duración Jobs en Carga de Horas`; `Ingreso Time Sheet Sólo Días Hábiles`; `Limita Horas Ingreso Time Sheet`; `Permite modif. Horas Día Anterior`; `Time Sheet por Cliente` (client/JobNumber/task); `Limita Job Genéricos del Cliente`; `Usa Aprobación de Time Sheet`; `Aprobación de TimeSheet al Inicio`; `Usa Conceptos de JobNumber en Time Sheet`; `Audita Carga Time Sheet`; `Cant. Máx. Días a auto-reactivar`; `Filtrar división default por JobNumber`.

Security — §5 rule 46 list. E-mail — client, channel, SMTP server, auth, user, password. Users — Active Directory, lockout method, timesheet obligation. Interface — reporting/planning system integrations. Sub-company enablement (vendor-enabled). Provisional masters circuit.

**Country-specific**
- Argentina: AFIP e-invoicing web service (certificate-based, test connection), CAI for manual invoices, invoice letters A/B/C/E/M with QR and identification code, gross-income (IIBB) registration/withholding/perception by jurisdiction, ANSES and RAP numbers, SUSS withholdings, income-tax withholding (registered/non-registered), advertising contribution withholding, several flags that must be set false.
- Costa Rica & Panama: two-person withholding workflow (calculator + approver); unapproved withholding blocks payment.
- Tax ID label varies (`CUIT/NIT/RUT`); language and regionalization per user.
- Multinational group features: HFM/GCP/Magnitude/Cartesis/Altair exports, USGAAP-only entries, consolidation environment.

---

## 9. Reports and KPIs

- Cash-flow summary (per day/week/month): opening liquidity, inflows/outflows by concept, projected closing balance, `Posterior` bucket; exports to Excel/print.
- Parent-company reporting files per tab.
- Timesheet report: real hours & cost, weighted hours (8h cap), internal vs external valuation by campaign/client/collaborator/category. KPIs: chargeability % (hours to clients / total) vs target with traffic light, month completion %, hours pending approval.
- Dynamic timesheet and permissions pivots (scheduled, online/offline).
- Personal debt per collaborator sub-account.
- Service-center: elapsed time request→finish→approval, by sector/activity/priority (SLA KPI).
- Audit: movement trail; open transactions; license consumption (used vs excess attempts); access control; efficiency (documents per user per type — productivity KPI); system usage (option hits, records per entity — adoption KPI); access-by-user (auditor-friendly SoD evidence); options by role.
- Accounting subcategory listing (export/print).
- Unit-equivalents report (hours-based units per user; purpose not fully described).

---

## 10. Agentic-skill implications

### 10.1 Atomic jobs (candidate skills/tools)

| Skill | Inputs | Output | Deterministic core |
|---|---|---|---|
| `cashflow.generate_snapshot` | type, currency, as-of date, include-zero flag, previous snapshot id, VAT day, holiday calendar | snapshot with dated items per concept | yes — horizon builder, date-shift, bucketing |
| `cashflow.expected_date` | doc due date or estimated billing date, payment-term days, chronic delay, holiday calendar | expected date | pure function (tool) |
| `cashflow.apply_withholding_estimate` | items, mode (% or manual), rates | net expected cash | pure function |
| `cashflow.estimate_pipeline` | approved estimates/plans/fees + billing-date assignments (all/month/month-party/item) | dated sale & agency-fee inflows, dated supplier cost outflows | yes |
| `cashflow.add_manual_lines` | payroll, expenses/other income, capex, capital, recurring outflows, adjustments | lines with VAT computed | yes (VAT = net × rate) |
| `cashflow.roll_forward` | previous snapshot + fresh actuals | new snapshot, preserving unchanged planned dates | yes, with diff report |
| `cashflow.balance_projection` | snapshot | running balance per column, min-balance alert | yes |
| `reporting.validate_mapping` | chart of accounts, entities, interface code table | list of unmapped items + coverage % | yes |
| `reporting.export_period` | period, exclusions, sub-company, target | per-tab files | yes |
| `timesheet.validate_day` | lines, collaborator daily total, flags | pass/fail with reasons (quarter steps, total match, business day, cap, generic job, division) | yes |
| `timesheet.replicate_days` | first-day allocation, date range, calendar | lines for each day | yes |
| `timesheet.approve` | approver, entries, decisions | state changes + audit | gated by permission |
| `timesheet.valuation` | approved hours, rates | cost, sale, weighted hours (8h cap), chargeability vs target, light | yes |
| `access.check` | user, action, screen, field class | allow/deny, visibility mask | yes — mirror levels 1–6, A–D, specific activities |
| `access.sod_review` | users × activities | conflicts (e.g. creates & approves same expense; enters & approves invoice; enters supplier invoice & finalizes payment list) | rule engine |
| `users.offboard` | user, successor, end date | reassigned tasks/jobs, unlock pending items, deactivate | orchestrated |
| `config.get/set` | key, value, actor | change + audit + impact notes | gated, human confirm |
| `audit.query` | filters | trail rows | yes |
| `purge.plan/execute` | purge type, filters, approver | candidate list → confirmed actions + export | plan is deterministic; execute needs approval |
| `masters.bulk_deactivate` | entity, filters, ids | status flips + pending-provisional warnings | yes |
| `comms.send_memo/email` | JobNumber, recipients from contacts, body | message, inbox notice or email | validation deterministic |
| `calendar.add_fiscal_due` | subject, recurrence | events + reminders | recurrence expansion tool |
| `today.alerts_for(user)` | user | list of pending work items per enabled alert | query |
| `service_task.*` | create/take/release/reject/finish/approve | state machine transitions + timing | yes |
| `render.document` | doc data, layout | PDF | layout engine (prefer modern templates; keep coordinate model optional) |
| `tax.config_resolve` | date, country, parties | applicable VAT rate (history), withholding/perception rates & minimums | yes |

### 10.2 Deterministic calculations worth a tool
- Business-day calendar and holiday shift; horizon column generation (20/15 days, 15 Mondays, 15 months).
- Expected date = base date + term + delay → shift to next business day → bucket (in horizon or `Posterior`).
- Running cash balance and minimum-balance detection.
- VAT computation with rate history by effective date.
- Timesheet validation (quarter-hour, total equality, flags) and weighted hours.
- Chargeability % and traffic-light classification against target/tolerance.
- Mapping coverage for reporting exports.
- Access evaluation (S/N + level + visibility + activities + amount caps).
- Recurrence expansion for calendar items and recurring cash outflows.
- Service-task elapsed time.

### 10.3 Control model the agent runtime should mirror
1. **Identity**: every agent action runs as a named user (or a service user of type "pure") — never anonymous. Agent sessions must respect `Cant. Máx. Opciones Simult.` style concurrency limits and idle timeouts.
2. **Screen/action authorization**: map each tool to a "screen" and required access level (create ≥4, modify ≥3, delete ≥2, special ≥1, read ≤5/6). Deny if S/N not granted.
3. **Field-level visibility**: strip cost and margin fields from tool outputs when visibility is C/D (D: no costs; C: costs but not profitability; B: both; A: all). This matters for LLM context: never load hidden fields into the model's context for such users.
4. **Approval powers as capabilities**: approve-for-billing, approve-by-client, approve POs, approve expenses (with per-approver amount cap and no self-approval), approve hours (only for assigned collaborators), post after pre-close, finalize payment list, close insertions/estimates, approve supplier-portal contacts, approve withholdings (CR/PA). An agent may **prepare** but should require a human holding the capability to **commit**, unless the deployment explicitly delegates.
5. **Segregation of duties**: enforce the preparer ≠ approver rule for expenses, provisional masters (operator → manager → accounting), withholdings (calculator ≠ approver), service tasks (executor ≠ requester-approver), and timesheets (collaborator ≠ approver). Run `access.sod_review` on role changes.
6. **Configuration changes** are high-risk: require confirmation, record before/after, and surface downstream impact (e.g. switching media circuit to Strict blocks orders lacking approvals).
7. **Audit**: every tool write emits an audit row (date, time, user, action, entity type, entity id, notes, agent run id). Bulk operations export planned vs executed lists.
8. **Gates from parameters**: tools must read the parameter store at runtime (mandatory PO, PO approval, approval-for-billing, timesheet approval) rather than hard-code circuits.
9. **Login gates**: mandatory timesheet and FX-rate entry block other work for that user; agents acting for a user must either complete or surface these blockers first.
10. **Communications**: agents may only address registered contacts; external sends require explicit confirmation of external addresses.

### 10.4 Exceptions to handle
- No previous snapshot of the same type → copy-forward unavailable.
- Approved estimates without billing dates → excluded; agent should list them as "undated pipeline".
- Ledger accounts missing observation codes → concept silently empty; validation step needed.
- Holidays not configured → wrong date shifting.
- Unmapped reporting entities → under-reported HQ numbers.
- Timesheet day totals not matching → cannot save; rejected hours → rework loop; inactive client filter hiding hours.
- Departed user still owning approvals/tasks/jobs → offboarding flow.
- Deleting a snapshot that was copied, a profile that is assigned, or a user with activity → refuse.
- Supplier commission invoice to a billing client that does not accept commissions → refuse.
- Purge of items with downstream links (e.g. jobs pending direct investment) → warn; use exclude-invoices flag.
- Pending provisional-master change on an entity in a bulk update → flag/skip.
- Expensive online report → force offline mode.
- Layout change after documents issued → reprint needed.

---

## 11. Gaps and ambiguities

1. **Forecast**: initial settings, create/modify, consult and main forecast pages are stubs or "under construction"; no data model, drivers, or approval flow documented. Must be designed from scratch (likely revenue/gross-income forecast by client/product/month vs actuals).
2. **Daily cash-flow horizon**: overview says 20 calendar days; generation guide says 15 business days. Make it configurable.
3. **Access level numbering** inconsistency: profile page lists six levels (5 = query with special actions, 6 = query only); profile-creation guide lists five. Adopt six.
4. **Duration of jobs in timesheet lookup**: described in days on one page and in weeks on another.
5. **Functional-role rules, role-allowed activities, SoD control** screens are stubs — SoD conflict matrix must be defined by the implementer.
6. **Multi-company masters**, UT/consortium composition, consortium members, "Sform", Altair interface, maintenance of reporting masters/interfaces: one-line placeholders only.
7. **Unit-equivalents report**: semantics of "equivalent units" not explained.
8. **Weekly/strategic cash flow** differences beyond horizon are minimal; how payroll lines map to weeks/days is not explicit.
9. **Liquidity classification** (short/long) usage in calculations is not described beyond grouping.
10. **Contact "related entity" mandatory** in intro but marked optional in the step guide.
11. **Chargeability target/tolerance** values and where they are configured are not specified.
12. **Personal debt** sources (which ledger sub-accounts) not enumerated.
13. **Alert catalogue** (names/conditions) is not listed — only examples ("hours pending approval", task status). Needs to be reconstructed from other module specs.
14. **"Supplier receives credit note" commission** mode is marked as in development.
15. **Branches (`sucursales`)** appear only as layout/barcode assignment keys; no master definition in this group.
16. **Fee pending-to-bill** fields refer to media/production portions of fee instalments; the fee contract structure lives in another module.
17. **Liveranto portal** behavior beyond the six flags is out of scope here.
18. **Security**: passwords limited to 8 characters is a legacy constraint; a reimplementation should exceed it while preserving the policy knobs.
