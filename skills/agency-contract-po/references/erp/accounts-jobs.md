# Accounts and Jobs (Cuentas) — functional spec

> **Provenance.** Functional reverse engineering of a reference agency ERP, derived from its publicly accessible help documentation (reviewed 2026-10-11). Content is paraphrased and restructured; it is not vendor documentation, source code or an endorsement. Bracketed ids such as `[mp301010]` identify the source page used as evidence. Items marked *inferred*, *assumed* or listed under gaps must be validated with your own controller, tax adviser and system owner before they drive postings or payments.

> Reverse-engineered, paraphrased specification of the "Cuentas" module of an agency ERP, written to seed an open-source agentic skills repository. It describes the business circuit, not the user interface. Spanish terms in backticks are the original field or entity names. Source references give the help-page file name in [brackets].

---

## 1. Module purpose and position in the agency E2E circuit

### 1.1 Purpose

Cuentas is the commercial and operational front office of the agency. It owns:

- **Client master data**: the trade-name client (`Cliente Titular`), its products and brands, product hierarchy, client divisions, client groups, and market categories.
- **The unit of analysis, the campaign / job** (`JobNumber`). Every downstream document (production estimate, media plan, task, timesheet hour, expense, supplier invoice, client invoice) hangs off a JobNumber, either directly or through a parent document. Profitability is measured per JobNumber.
- **Commercial agreements that replace or complement commission**: fixed-fee contracts (`Contratos de Fee Fijo`) and hour-based fee contracts (`Contratos de Fee por Horas`), including patterns for automatically attaching jobs to contracts and estimates of staff hours.
- **Client purchase-order control** (`PO Clientes`) and budget-reserve control (`Reserva Presupuestal`).
- **Workflow and collaboration**: strategic brief, contact reports (meeting minutes), internal tasks (`Tareas`), task templates, and a Gantt-based project-stage engine (`JPM`, Job Process Manager).
- **Time capture governance**: timesheet concepts, reclassification headings, timesheet closing, and last-entry control.
- **Revenue budgeting** (`Presupuesto de Ingresos`): yearly forecast of investment, commission, cost-difference and fee income per client and product, with versioning and plan-vs-actual comparison.
- **Account-side reporting**: job status and content, job P&L, investment and gross income per client (ROT), profitability per client with overhead allocation, media profitability, pending media orders and production estimates, and task statistics/KPIs.

### 1.2 Position in the circuit

```
Lead / prospect ─► Cliente Titular + Productos (master data, optionally via provisional approval)
                │
                ▼
           JobNumber (campaign)  ◄── Brief Estratégico, Informe de Contacto, Tareas, JPM
                │                         │
                │                         └─► Timesheet hours (cost & rate valuation)
                ├─► Producción: production estimates (`Presupuesto/Estimado`)
                ├─► Medios: media plans / insertion orders (`Pautas`, `Planes`)
                ├─► Fee contracts ─► monthly instalments become fee pautas / fee estimates
                ├─► PO Clientes / Reserva Presupuestal (consumption controls)
                ▼
     Client approval (`Aprobación por Cliente`) ─► Approval for billing (`Aprobación para Facturar`)
                ▼
     CxC (client billing) ─► Contabilidad (journal entries) ─► Management reports
     CxP (supplier invoices against orders) ─► Tesorería
                ▼
     Job closing: Accounts close ─► Administrative (definitive) close
```

- **Upstream**: commercial pipeline (Prospectos — only a stub in the manual), CxC master for billing clients (`Cliente de Facturación` and its assignment to a `Cliente Titular`), Contabilidad masters for collaborators, salary categories and cost-plus rates, System configuration (`Configuraciones Especiales`), Users and Security.
- **Downstream**: Producción (estimates), Medios (plans, orders, ad control), CxC (invoicing of estimates, pautas, fee instalments, differences), CxP (supplier invoice matching to orders), Gastos (expense reports charged to jobs), Contabilidad (revenue/fee accounts with observation code 22, cost centres, USGAAP 8A/8B entries), Management (profitability and KPIs).

---

## 2. Process catalogue

Each process lists: trigger, actor, steps, inputs, outputs, state transitions, approvals, sources.

### P-01 Create / maintain a trade-name client (`Cliente Titular`)
- **Trigger**: new client won, or change to an existing client.
- **Actor**: account director / master-data administrator.
- **Steps**: (1) enter description (trade name); (2) enter a 3-character alphanumeric code manually or auto-generate it from the first letters of the description; (3) optionally assign a client group and a market category; (4) set active flag; (5) optionally set web alias for client-facing web services; (6) enable or disable PO control; (7) set whether a client budget on the JobNumber is mandatory; (8) choose production rate-card mode (`Propio` own / `Negociado` shared with another titular client, selecting which one) and media rate-card mode (same two options); (9) flag whether an attachment is mandatory at approval-for-billing time; (10) optionally upload a logo and configure external-system links; (11) save.
- **Outputs**: client master record.
- **Rules**: deletion only if never used for billing.
- **Sources**: [mp301054.html].

### P-02 Provisional master-data approval workflow (Cliente Titular)
- **Trigger**: create, modify or delete a titular client while "provisional masters" mode is on.
- **Actors**: requester (role "generates provisional titular clients"), optional intermediate approver, final approver.
- **Steps (create/modify/delete)**: requester saves the change → record becomes a provisional record "pending approval" (with the operation: create/modify/delete) → optional e-mail notice on save → intermediate approver (if enabled) reviews highlighted changed fields and approves (record flagged "with intermediate approval") or rejects (record flagged "rejected") → final approver approves (change becomes definitive; for deletions, the client is physically removed after confirmation) or rejects.
- **Side processes**: requester may edit a rejected provisional record and resubmit (returns to pending), or discard a pending/rejected provisional record (the master reverts to its prior state; a provisional creation disappears). A detail view shows status, event history including attachment changes, and a field-level before/after comparison.
- **Alerts**: pending intermediate approval, pending final approval, rejected.
- **Sources**: [generar-registros-provisorios-en-el-maestro-de-clientes-titulares.html], [mp302880.html].

### P-03 Maintain products and product hierarchy
- **Trigger**: new brand/product for a client.
- **Actor**: account executive / master-data admin.
- **Steps**: choose titular client → optional macro group and product group (mandatory only if a configuration forces the hierarchy) → name → 2-character code (suggested from the first two letters; must be unique within the titular client, may repeat across clients) → active flag → default agency division → attention group (or "free product") → market category / sub-category → agency commission percentages for production and media, discount-on-commission percentages for each, and an optional commission-per-media-type grid → client-side product code (printable on invoices) → time-slot restriction (e.g. tobacco after a given hour) → default target → supplier categories → logo.
- **Outputs**: product record used by every JobNumber.
- **Related masters**: `Macro Grupo de Productos` (per client) [mp305048.html]; `Grupos de Productos` (requires its macro group first) [mp301060.html]; `Categorías` / `Sub-Categorías de Productos de Mercado` (statistical, used in profitability) [mp301049.html, mp305049.html]; `Categorías de Productos por Proveedor` (category per supplier, assigned on the product's supplier tab) [mp305060.html]; `Productos de Anunciantes` for the reseller scenario in which another agency is the titular client and the advertiser owns the product [mp305050.html].
- **Sources**: [mp301050.html].

### P-04 Maintain attention groups (`Grupos de Atención`) — data-scope security
- **Trigger**: team set-up or rotation.
- **Actor**: system administrator / account director.
- **Pre-condition**: configuration "limits access by product" = true.
- **Steps**: create group (auto code, description, type `Grupo Libre` free, or `Grupo por Departamento` by department, plus the department) → active flag → select members and their functions (member, head (`Jefe`), approve on behalf of the client, approve for billing, sector approval when the strict media-approval circuit is on) → select products served → save. Assign or unassign users and products later in modify mode.
- **Sources**: [mp301013.html] and its five user guides.

### P-05 Other account masters
- `Divisiones propias de los Clientes`: client-side divisions with a client code printed on documents [mp301048.html].
- `Grupos de Clientes Titulares`: agency-defined grouping, e.g. several government ministries consolidated [mp301052.html].
- `Tipologías de Trabajo`: job typologies (seeded set, editable, new letters allowed) [mp302682.html].
- `Conceptos de Horas de TimeSheet`: per-department activity concepts, flaggable as billable [mp301620.html, -configurar-conceptos-de-time-sheet-.html].
- `Rubros de Reclasificación TimeSheet`: reclassification headings linked to country-division groups and departments, assigned in timesheet concepts [mp302873.html].
- `Actividades de Tareas` / `Etapas de Tareas`: task activities and their stages (hours, difficulty, approval type client/agency, stage type normal / check point / has alternatives / is alternative) [mp301490.html, mp301030.html].
- `Actividades de JPM` / `Etapas de JPM`: same for the JPM engine, plus parent activity, colour, staffing profiles (category, sub-category, salary category, hours), "calculate agency service" flag, alert days and order within activity [mp302779.html, mp302778.html].
- `Template para Tareas`: questionnaires (yes/no, text, date, table-backed choice; mandatory flag; internal or external use; who must complete) [mp302018.html, -ingresar-un-template-para-tareas-interno-.html].
- `Asignación de Clientes a MP-OnLine`: special client users who can see only their own campaigns, plans and estimates and approve/reject them as the client [mp302024.html].
- `Etapas de Campaña`, `Tipologías de Campaña`, `Motivos de Rechazos`: listed but not documented.

### P-06 Create a JobNumber (campaign)
- **Trigger**: client request for a campaign, an internal project, new-business pitch, or own advertising.
- **Actor**: account executive (must be a collaborator in a department typed "Cuentas"; profile at least access level 3 with cost visibility C).
- **Pre-requisites**: titular client, product, responsible user; if billable, a billing client linked to the titular client (done in CxC).
- **Steps**:
  1. Select titular client; optionally macro group and product group (they filter the product list); select product.
  2. Start year: last digit of the year (defaulted).
  3. Typology (`Tipología del Trabajo`).
  4. Billing code (`Código de Facturación`): `F` single known billing client (default; fills the default billing client, editable), `0` non-billable, `?` billing client to be defined later, `*` split / assign per document using split codes.
  5. Topic (`Tema`) — suggested to include a time reference.
  6. Responsible (`Responsable`): an Accounts-department collaborator who reports progress to the client.
  7. Other data: division (if divisions are on); hour-input mode (`Tipo de Input al Job`): normal / hours only (no estimates or pautas allowed) / no hours accepted.
  8. Hours control: assign an attention group or individual collaborators, each with estimated hours; actual hours accrue from timesheets.
  9. Estimated investment (`Inversión Estimada`): `Sin Presupuesto` (no budget), `Resumido` (media vs production, optionally monthly), or `Detallado` (by media type or media, and by production-type group or production type, optionally monthly).
  10. Save → system builds the 12-character code and stamps the entry date.
- **Output**: JobNumber in state `Vigente`.
- **Sources**: [mp301007.html], [-ingresar-un-jobnumber-facturable-.html], [-ingresar-un-jobnumber-no-facturable-.html], [-ingresar-un-jobnumber-con-un-cliente-de-facturacion-a-definir-posteriormente-.html], [-ingresar-un-jobnumber-con-apertura-de-multiples-clientes-de-facturacion-.html].

### P-07 Modify, delete, copy, reassign a JobNumber
- **Modify**: only topic, responsible, input type, hour-assignment list and investment type are editable.
- **Delete**: only if there is no movement at all; otherwise close.
- **Copy** (from the job list): select jobs → enter the target year digit → a new job is created in the current month.
- **Reassign responsible** (bulk, from the job list): e.g. when an executive leaves.
- **Sources**: [mp301007.html], [listado-de-jobnumber.html].

### P-08 Change the billing client of a JobNumber
- **Actor**: account executive.
- **Steps**: open Job Status & Content → "modify billing client" → choose new billing code (`F` single or `*` split) and, for `F`, the new billing client from those linked to the titular client → confirm.
- **Rule**: allowed only if no estimate or pauta in the job has been invoiced. Otherwise create a new job and move the documents.
- **Sources**: [mp301240.html], [-modificar-el-cliente-de-facturacion-de-un-jobnumber-.html].

### P-09 Move documents between JobNumbers
- **Steps**: in Job Status & Content, expand the document type, tick documents → Move → choose destination job → confirm.
- **Rules**: briefs and contact reports cannot be moved; invoiced estimates/pautas cannot be moved (or, per the user guide, only when billing clients match); cannot move from a billable to a non-billable job; no trace of the origin is kept.
- **Sources**: [mp301240.html], [-mover-un-documento-de-un-jobnumber-a-otro-.html].

### P-10 Substitute a JobNumber
- **Steps**: in Job Status & Content → Substitute → choose destination job → confirm. All content moves; the source job becomes `Sustituido` and can never be reused.
- **Rules**: source cannot be closed; no invoiced documents (or, per the guide, invoiced documents allowed only if the destination has the same billing clients).
- **Sources**: [mp301240.html], [-sustituir-un-jobnumber-por-otro-.html].

### P-11 Two-step JobNumber closing and reopening
| Step | Actor (department type) | Effect | Blocking conditions |
|---|---|---|---|
| Accounts close (`Cerrado por Cuentas`) | Accounts dept user (or the job responsible if configured) | No new estimates, pautas, hours, tasks, briefs | Unfinished tasks; documents pending client approval or pending approval for billing |
| Administrative / definitive close (`Cierre Definitivo`) | Administration/Finance dept user | Blocks billing, supplier invoices and expenses as well | Documents pending client invoicing or pending supplier invoice |
| Accounts reopen | Accounts | Back to `Vigente` | Not allowed if administratively closed |
| Administrative reopen | Administration/Finance | Back to `Cerrado por Cuentas` (implied) | — |

- Performed in bulk from the job list via the "close/open jobs" action. Requires access to the job list (level 1/A) and the menu-less option "Job close" (level 1/A). No accounting entry is generated.
- **Sources**: [listado-de-jobnumber.html], the four close/reopen guides, [mp301240.html].

### P-12 Automatic closing of inactive JobNumbers
- **Trigger**: periodic housekeeping or alert "jobs to close".
- **Steps**: system lists jobs with no activity for more than N days (configuration; 0 disables), oldest first → user ticks and closes.
- **Sources**: [mp301526.html], [listado-de-jobnumber.html].

### P-13 Fixed-fee contract (`Contrato de Fee Fijo`)
- **Trigger**: client negotiates a fixed amount for a period instead of commission.
- **Actor**: account director creates it; users with approval permissions approve.
- **Pre-requisites**: fee revenue GL accounts for production and media with observation code 22; a media type and a production type pointing to those accounts; a "fee" media assigned to that media type; both declared as fee media / fee production type in special configuration.
- **Steps**:
  1. Main data: titular client → auto contract number (sequential per titular client) → description (e.g. negotiation year) → contract type: fixed distribution / dynamic / dynamic with self-assignment → active flag → validity from/to → division (if sub-companies) → JobNumber pattern (dynamic types only) → billing criterion: defined billing client, or split code → instalments (monthly, from/to) → currency (single per contract) and exchange rate if foreign → production type (default from configuration; any production type whose sales account has observation code 22 is selectable) → production department (if used).
  2. Distributions: split of each instalment between Media and Production departments (default 50/50, editable, may be 100/0). For dynamic types, a profitability-distribution criterion: auto-filled from actual consumption and hours for self-assignment, otherwise entered manually.
  3. Allocation table (dynamic only): rows by product, typology, billing client, with percentage, derived from the pattern.
  4. JobNumbers tab: pick jobs (open jobs only); with fixed distribution, enter each job's percentage.
  5. Instalment detail: amount per month (not all months need an amount); system shows total; extra rows show the generated production estimate number, production invoice number, pauta number and media invoice number ("not invoiced" until billed).
  6. Save → approvals.
- **Outputs**: per instalment, a fee pauta (media share) and/or a fee production estimate (production share), locked against manual edit.
- **Sources**: [mp302001.html], [contrato-de-fee---0458.html] (video title only).

### P-14 Hour-based fee contract (`Contrato de Fee por Horas`)
- **Trigger**: client pays a monthly fee that covers a stated number of hours.
- **Additional pre-requisites**: timesheet mandatory (`Time Sheet = True`, timesheet by JobNumber); collaborators with category/sub-category and salary category (cost-plus); client rates kept current; account lead validates hours before import.
- **Creation steps**: same as P-13 with type fixed / dynamic / dynamic self-assignment; job selection for dynamic types uses filters (product, typology, start year, billing client).
- **Instalment detail**: monthly negotiated amount plus covered hours.
- **Monthly hours import** (P-14a): open contract → Modify → instalment detail → Import hours (hours of collaborators on the contract's jobs, valued at client rate) → optional adjustment coefficient → add manual rows for resources who do not use the timesheet (name, rate scale, hours) or remove rows → accept → save; instalment status = pending client approval. Import can be repeated or undone.
- **Approvals** (P-14b..e): per month: approve by client / unapprove by client (requires user flag "approves for client"); approve for billing / unapprove for billing (requires flag "approves for billing", and client approval first).
- **Sources**: [mp302008.html] and its eight user guides.

### P-15 Staff-hour estimate (`Estimación de Dedicación Horaria`)
- **Steps**: titular client → auto number per client → description → active flag → accept differences yes/no and a tolerance cap in hours → estimate type: simple (one project) or compound (several, via "configure campaigns") → rate type: agency cost rate or client sales rate, and rate month/year → application type: fee contract, JobNumber pattern, fee contract type (fixed / hourly), or a single JobNumber → add collaborators with hours (cost auto-filled) → total = Σ hours × hourly rate → save.
- **Consumer**: report "estimate vs actual hours" [mp302021.html].
- **Sources**: [mp302020.html].

### P-16 JobNumber patterns (`Patrones de JobNumber`)
- **Steps**: titular client → optional product → optional job typology → billing client → active → system generates pattern code. Levels: client; client+product; client+product+typology.
- **Sources**: [mp302003.html].

### P-17 Client purchase orders (`PO Clientes`) and transfers
- **Pre-requisite**: configuration "manage client POs"; client flagged for PO control.
- **Create**: auto code → billing client (linked to a titular client with PO control) → PO description → total amount excluding tax → currency → validity → optional contract number → balance control flag (recommended yes) → optional breakdown by product and media type → scope online/offline purchases.
- **Use**: when an estimate or pauta selects its job, the system offers to include the document under a PO (F2 lookup in the header of estimates and media plans). Only documents created after the PO's creation can be linked. Once linked, the header assignment cannot be edited manually.
- **Control points**: validation at client approval; consumption recorded when purchase/insertion orders are issued.
- **Transfer between POs** (P-17a): origin type (production estimate or pauta) → auto adjustment number → document number → origin PO (same billing client; balance shown) → destination PO → amount and reason → save.
- **Report** "Consumo PO Clientes": consumption by PO, split by estimates/pautas and by state (pending client approval, pending approval for billing, pending invoicing).
- **Sources**: [mp302794.html], [mp302903.html], [mp302795.html].

### P-18 Budget reserve (`Maestro de Reserva Presupuestal`)
- **Origin**: custom build for a Colombian telecom client.
- **Pre-requisites**: a dynamic category representing "pool areas" (`áreas de bolsa`) and its items; each user may be designated approver of pool areas.
- **Create**: auto sequential code → manual alphanumeric reserve number and year → control type: by percentage (cap 100%), by amount, or no cap → validity → per pool area, amount.
- **Use**: assignment made on the JobNumber by the job responsible, inherited by estimates and media plans (visible in their tool sidebar); first-level approval of the estimate/pauta done by the pool-area approver (analogous to client approval); at invoicing, the expense rendering shows consumption so the user picks which reserve to decrement; balance updates as consumption invoices are issued.
- **Sources**: [mp302753.html].

### P-19 Strategic brief (`Brief Estratégico`)
- **Steps**: New → select open JobNumber (client → product → job) → topic, client and product auto-filled → From (current user), To (mandatory, users), CC (users or registered external contacts) → subject (defaulted "Strategic brief job N", editable) → mandatory brief body → mail text (important for external recipients; the brief travels as attachment) → optional attachments → optional "keep in the alerts inbox" → Save → Send (internal: appears in each user's home dashboard; external: confirm addresses then e-mail).
- **Rule**: one brief per JobNumber; if one exists, the user is directed to modify it. Tracks last-modified and last-sent dates.
- **Sources**: [mp305007.html], [-ingresar-y-enviar-un-brief-estrategico-.html].

### P-20 Contact report (`Informe de Contacto`) — meeting minutes
- **Steps**: New → titular client (auto number per client) → one or more JobNumbers → optional flags quote / package (only for publisher-type companies) → exclusive flag (visible only to author, recipients, CC) → To, CC → client attendees (registered client contacts) → meeting topic, place, date → mandatory body (rich text) → mail text → attachments → Save → Send (internal + selected external addresses) → optional keep in the alerts inbox.
- **Dates**: emission, last modification, last sent (system).
- **Sources**: [mp301398.html], [-ingresar-y-enviar-un-informe-de-contacto-.html].

### P-21 Tasks (`Tareas`) — internal work requests
- **Create & send**: New → open, non-generic JobNumber → optional client contact and related contact report → dates: requested completion by Accounts, internal consensus date, date promised to client → single recipient (+ CC) → topic → description → optional template questionnaire (answer the requester's questions) → optional production estimate: create new (topic, approval type "to quote" or "pre-approved") or link existing (month/year + estimate number) → optional production types for billing → attachments → Save (`Standby`) → Send (`Pendiente`).
- **Estimate fields inherited**: management month (only open months), estimate number assigned on save, topic, billing client (from job, or chosen for `?`/`*` jobs), approval type (default from billing client), production department, client PO number, split code, division.
- **Lifecycle actions**: reassign (requester, coordinators, or users allowed to reassign in their department; only when pending or rejected); reject (recipient or coordinator; with reason; only when pending); cancel (only sent and pending); finish by recipient (progress 80%, records actual hours); approve by requester (progress 100%, delivered-to-client date, locked); requester sends back (progress 50%, back to pending with reason). Sub-tasks referencing a parent task exist in the .NET version. Change history kept.
- **Bulk closing**: an Accounts user filters the task list by JobNumber and sets progress 100% in bulk (needed before Accounts can close the job).
- **Bulk replace recipient/requester**: only for pending or standby tasks.
- **Sources**: [mp301401.html], [mp401401.html], six task user guides, [mp301399.html], [mp302689.html].

### P-22 JPM — project stage engine
- **Pre-requisite**: configuration "uses task tracking (JPM)".
- **Steps**: open JobNumber (Activities button) or Job Process Manager → add activities (right-click) → choose stages per activity → assign resources per stage (mandatory) → the client must have a contact assigned before saving → on start, the engine fires tasks to resources sequentially as stages complete; visualised as Gantt.
- **Monitoring**: per job and per resource/attention group; colours for unread, pending approval, in process; date classes Accounts / client / consensus; counts of rejections, date changes, rework by client and by management, difficulty, days taken, agency and client standard; workload saturation percentage.
- **Sources**: [mp302784.html], [mp301510.html], [mp301564.html], [mp302778.html], [mp302779.html].

### P-23 Timesheet closing and control
- **Close** (`Cierre de TimeSheet`): from the collaborator list, select people → tool "close timesheet" → cut-off date and a default JobNumber to which days without entries are assigned → locks entry and editing up to that date; can be reopened per user.
- **Control** (`Control de Horas TimeSheet`): last date each person loaded hours, by department, filtered by client and cut-off date.
- **Sources**: [mp303010.html], [mp302879.html]; Academia timesheet videos (titles only).

### P-24 Approve pending media orders from lists
- From "pending pautas" or "orders pending billing", the user filters a single state (pending client approval, pending ordering, pending approval for billing, pending billing) and approves ticked lines in bulk (digital, radio, TV and other media in one step).
- **Write-off of media differences**: list type "differences pending billing" → tick differences that will not be charged to the client → "save differences" removes the pending receivable.
- **Bulk switch of agency-commission billing mode** (`Fact. Serv. Ag`: billed together with the media vs separately/"general"): filter one mode → tick → invert. Lines with anything already invoiced are refused and reported. Requires profile permission.
- **Sources**: [mp301137.html], [mp301137_soloeditora.html], [-eliminar-pendiente-de-facturar-al-cliente-de-diferencias-de-medios-.html], [mp301063.html].

### P-25 Revenue budget (`Presupuesto de Ingresos`)
- **Pre-requisite**: choose a loading method (recommended "detailed by media and production type").
- **Steps**: New version (name; option to restrict to active clients) → save version → select client, product (and division if used) → "view data" → `Apertura` (choose media + supplier rows; production rows list all production types) → enter commission % and cost-difference % → enter monthly investment for media and production → system computes commission and cost-difference income → save. Fees, rebates and rebate refunds are entered as projected amounts.
- **Copy to new version**: optionally "include closed months" so that past months carry actual values instead of the old plan.
- **Lock**: supervisor can close a version to modifications and reopen it.
- **Queries**: plan vs actual (or version vs version) per year, by media or client; projected view (actual for closed months, plan for open months; actual = booked or ordered).
- **Sources**: [mp301019.html], [mp301015.html], [mp301021.html].

### P-26 Expense report (`Rendición de gastos`)
- Listed in Academia as common to all profiles (video only). Details belong to the Gastos module; Cuentas users charge expenses to JobNumbers. [rendicion-de-gastos---0527.html].

---

## 3. Entities and master data

Legend: **R** required, O optional, A auto-generated.

### 3.1 `ClienteTitular` (trade-name client)
| Field | Meaning | Req |
|---|---|---|
| `Código` | 3-char alphanumeric code (manual or generated from description) | R/A |
| `Descripción` | Trade name (not the legal entity) | R |
| `Grupo de Clientes` | FK client group | O |
| `Categoría Prod. Mercado` | Market segment | O |
| `Vigente` | Active | R |
| `Alias Web` | Alias for web services | O |
| `Control de PO` | Enables PO control | O |
| `Presupuesto obligatorio en Job` | Client budget mandatory on JobNumber | O |
| `Tarifario Producción` | `Propio` / `Negociado` (+ titular client whose rate card is shared) | O (default Propio) |
| `Tarifario Medios` | Same for media | O (default Propio) |
| `Adjunto obligatorio` | Document must be attached at approval for billing | O |
| Logo, external-system links | — | O |
Relationships: 1..n `ClienteFacturacion` (legal billing entities, CxC master) via assignment; 1..n `Producto`; 1..n `DivisionCliente`; 1..n `MacroGrupoProducto`; 1..n `FeeContract`; 1..n `JobNumber`.

### 3.2 `Producto`
| Field | Meaning | Req |
|---|---|---|
| `Cliente Titular` | Owner | R |
| `Macro Grupo` / `Grupo de Producto` | Hierarchy | O (R if configured) |
| `Producto` | Name | R |
| `Código` | 2-char, unique per titular client | R |
| `Vigente` | Hidden for new jobs when inactive | R |
| `División (agencia)` | Default agency division | O |
| `Grupo de Atención` / `Producto Libre` | Data-scope | O |
| `Categoría/SubCategoría de Mercado` | Statistics | O |
| `% Servicio de Agencia Producción` | Commission on production estimates | O |
| `% Bonificación Serv. Ag. Producción` | Discount applied over that commission | O |
| `% Servicio de Agencia Medios` | Commission on media plans | O |
| `% Bonificación Serv. Ag. Medios` | Discount over media commission | O |
| `Serv. Ag. por Tipo de Medio` | Grid media type → % | O |
| `Código en el Cliente` | Client's own code, printable on invoices | O |
| `Restricción Franja Horaria` | Restricted airtime window | O |
| `Target` | Default audience | O |
| Supplier categories, logo | — | O |

### 3.3 `JobNumber` (campaign)
| Field | Meaning | Req |
|---|---|---|
| `Código JobNumber` | 12 chars: client(3) + product(2) + start-year digit(1) + typology(1) + billing code(1) + sequence(4) | A |
| `Cliente Titular`, `Producto` | — | R |
| `Macro Grupo`, `Grupo` | Filters | O |
| `Año Inicio Trabajo` | Last digit of year | R (defaulted) |
| `Tipología del Trabajo` | A/C/P/R/G/M/I/N/S/W | R |
| `Código de Facturación` | F / 0 / ? / * | R (default F) |
| `Cliente de Facturación` | Only when F | R if F |
| `Tema` | Campaign name | R |
| `Responsable` | Accounts-dept collaborator | R |
| `División` | If divisions on | O/R |
| `Tipo de Input al Job` | Normal / hours only / no hours | R |
| Hours control rows | collaborator or attention group + estimated hours; actual hours accrue | O |
| `Inversión Estimada` | none / summarised (opt. monthly) / detailed (opt. monthly) | R (type) |
| `Reserva Presupuestal` | Assigned reserve | O |
| `Estado` | Vigente / Cerrado por Cuentas / Cierre Definitivo / Sustituido | A |
| `Fecha de Ingreso` | Entry date | A |
Special: a generic JobNumber per client with product "Sin Producto" is auto-created, used for client expenses not tied to a project; tasks cannot be linked to generic jobs. Agency-level generic jobs hold structural expenses.

### 3.4 Job typologies (`Tipologías de Trabajo`)
| Code | Meaning | Behaviour |
|---|---|---|
| A | Advertising | Media and production, unrestricted |
| C | Collateral | Creative/production only; media plans blocked |
| P | Promotions | — |
| R | Public relations | — |
| G | General | Administration-only; expense jobs |
| M | Direct marketing | — |
| I | Research | — |
| N | New business | No sales value allowed on linked documents; agency absorbs cost |
| S | Presentations | No sales value allowed |
| W | Own advertising | No sales value allowed |

### 3.5 `FeeContract` (fixed or hourly)
| Field | Meaning | Req |
|---|---|---|
| `Tipo` | Fixed fee / hourly fee | R |
| `Cliente Titular` | — | R |
| `Nº Contrato` | Sequential per titular client | A |
| `Descripción` | — | R |
| `Tipo de Contrato` | Fixed distribution / dynamic / dynamic self-assignment | R |
| `Vigente`, `Vigencia Desde/Hasta` | Validity | R |
| `División` | If sub-companies | O |
| `Patrón de JobNumber` | Dynamic only | R if dynamic |
| `Criterio de Facturación` | Defined billing client / split code | R |
| `Cliente de Facturación` or `Código de Apertura` | — | R (one) |
| `Cuotas Desde/Hasta` | Monthly instalment range | R |
| `Moneda`, `Cotización` | Single currency; rate if foreign | R |
| `Total Contrato` | Σ instalments | A |
| `Estado` | Not client-approved / client-approved / approved for billing / partially invoiced / fully invoiced | A |
| `Tipo de Producción` | Fee production type (observation-22 account) | R |
| `Departamento` | Production dept | O |
| Distribution % media / production | Default 50/50 | R |
| Profitability distribution % | Dynamic only | A/R |
| Allocation table rows | product, typology, billing client, % | dynamic |
| JobNumber rows | job (+ % for fixed) | R |
| Instalment rows | month, amount, (hourly: covered hours, imported hours, adjustments, manual resources), generated estimate #, pauta #, invoice #s, per-instalment approval state | R |
| `Observaciones` | — | O |

### 3.6 `HourEstimate` (`Estimación de Dedicación Horaria`)
Titular client, number (A, per client), description, active, accept differences, tolerance hours, type simple/compound, rate type agency/client, rate month-year, application type (fee contract / pattern / contract type / JobNumber) and target, lines (collaborator, hours, unit rate, line total), total.

### 3.7 `JobPattern`
Titular client (R), product (O), typology (O), billing client (R), active, code (A).

### 3.8 `ClientPO`
Code (A), billing client (R), PO reference/description (R), amount ex-tax (R), currency (R), validity (R), contract number (O), balance (A), control balance flag, product and media-type breakdown (O), scope online/offline. Child: consumption lines (document, amount, state) and transfers (origin doc, origin PO, destination PO, amount, reason, adjustment number).

### 3.9 `BudgetReserve`
Code (A), reserve number (R, alphanumeric), year (R), control type (percentage / amount / none), cap, validity, pool-area lines (area, amount, balance).

### 3.10 `AttentionGroup`
Code (A), description, type (free / by department) + department, active, members (user + roles: member, head, approve-for-client, approve-for-billing, sector approval), products. One head per group; user may belong to many groups.

### 3.11 Documents
- `BriefEstrategico`: JobNumber (unique), topic, from, to (R), cc, subject, body (R), mail text, attachments, last modified, last sent.
- `InformeContacto`: number (A per client), titular client, JobNumbers (1..n), exclusive, quote/package flags, to, cc, client attendees, meeting topic/place/date, body (R), mail text, attachments, emission/modified/sent dates.
- `Tarea`: number, JobNumber, contact, related contact report, requester (A), single recipient, CC, topic, description, dates (requested by Accounts, internal consensus, promised to client, delivered to client), estimated and actual hours, progress %, state, template answers, linked production estimate (0..1), production types, attachments, history, parent task.
- `TaskTemplate`: code, description, completed-by, internal/external, active, questions (text, type, options table, mandatory).
- `RevenueBudgetVersion`: name, year, open/closed, lines per client × product × division × (media+supplier | production type) × month: investment, commission %, cost-difference %, fees, rebates, rebate refunds; computed commission and cost-difference.
- `TimesheetConcept`: department, code (A), description, billable flag, reclassification heading.
- `TimesheetReclassHeading`: name, visible name, active, country-division group, department group.

---

## 4. Document lifecycles

### 4.1 JobNumber
```
(new) ─save─► Vigente ─Accounts close─► Cerrado por Cuentas ─Admin close─► Cierre Definitivo
                ▲             │                     ▲                         │
                └─Accounts reopen┘                  └──────Admin reopen───────┘
Vigente ─substitute─► Sustituido (terminal, never reusable)
Vigente (no movements) ─delete─► (removed)
```
Triggers: Accounts-type department users (or the responsible, if configured) for the accounts close/reopen; Finance-type department users for the definitive close/reopen; automatic-close tool lists candidates but a user confirms.

### 4.2 Fee contract (header and per instalment)
```
Sin Aprobar por Cliente ─approve by client─► Aprobado por Cliente ─approve for billing─► Aprobado para Facturar
        ▲                       │                       ▲                     │
        └──unapprove by client──┘                       └─unapprove for billing┘
Aprobado para Facturar ─some instalments invoiced─► Facturado Parcialmente ─all invoiced─► Facturado Total
```
- Approvals can be applied to all instalments or month by month.
- Approval is impossible if the accounting period of the instalment does not exist yet.
- Deletion only while no instalment is invoiced.
- Hourly contracts: each monthly instalment is saved "pending client approval" after the hours import.

### 4.3 Task
```
Standby ─send─► Pendiente ─finish (recipient, 80%)─► Finalizada por Destinatario ─approve (requester, 100%)─► Finalizada/Aprobada (locked)
   │              │  │  │                                     │
   │              │  │  └─reject (recipient/coordinator)─► Rechazada ─reassign─► Pendiente
   │              │  └─reassign─► Pendiente (new recipient)  └─send back (requester, 50%)─► Pendiente
   │              └─cancel─► Cancelada
Also reported: Vencida (overdue) as a list filter.
```

### 4.4 Provisional master record
```
Pending (create|modify|delete) ─intermediate approve─► Pending + IntermediateApproved ─final approve─► Definitive (or Deleted)
            │                                  │
            └─reject─► Rejected ◄──reject──────┘
Rejected ─edit & resubmit─► Pending ;  Pending|Rejected ─discard─► previous state
```

### 4.5 Media pauta / production estimate (as seen from Cuentas)
`Sin aprobar por cliente` → `Aprobado por cliente` → (media: `Ordenado`) → `Aprobado para facturar` → `Facturado`. Estimates may also be `Pre-aprobado` (allowed when the job has no client budget; lets supplier invoices be attached), `A presupuestar`, `Rechazado`, `Anulado y sustituido`. Media items also carry ad-control status (OK / deficient or dropped / not controlled) and "closed order" after ad control.

### 4.6 Revenue-budget version
`Abierto` ⇄ `Cerrado a modificaciones` (supervisor only).

### 4.7 Timesheet period per collaborator
`Open` → `Closed up to date D` (blank days auto-assigned to a chosen job) → reopen per user.

---

## 5. Business rules and validations

**Master data**
1. Titular client code: 3 alphanumeric characters; auto-generation requires a description first.
2. A titular client may be deleted only if never used in billing.
3. Product code: 2 alphanumeric characters, unique within a titular client, reusable across clients.
4. An inactive product is hidden for new jobs but remains on existing ones.
5. If the product-hierarchy configuration is on, a product cannot be saved without macro group and group. A product group requires an existing macro group.
6. Masters such as concepts, macro groups, reclassification headings can only be deleted if unused; otherwise deactivate.
7. A task activity cannot be deleted while a stage references it; a stage cannot be deleted while a task references it.
8. Rate-card resolution: `Propio` → look first for the client's own rate card for the media/production item; `Negociado` → use the rate card of the designated titular client.

**Data-scope security**
9. A user in no attention group sees all products; a user in one or more groups sees only those groups' products, plus any "free" products.
10. Each attention group has at most one head. When "copy group heads in tasks" is on, the head is copied on every task addressed to group members.
11. Group roles (approve for client / approve for billing / sector approval) apply only to documents of the group's products and are independent from collaborator activities.

**JobNumber**
12. The creator must be a collaborator of a department typed Accounts, with profile level ≥ 3C. The responsible must also be an Accounts collaborator.
13. Code composition is deterministic (see 3.3); the 4-digit sequence distinguishes jobs sharing the same 8-character root.
14. Best practice: a campaign should not live more than a year; long-running products get one job per year.
15. Billing code `0`: linked documents accept costs only, never sales value, and can never be invoiced.
16. Billing code `?`: documents can be created but cannot be approved by the client (nor invoiced) until a billing client is assigned.
17. Billing code `*`: each estimate/pauta must carry its own billing client or split code linked to the titular client.
18. Typologies N, S, W forbid sales values; typology C forbids media plans; typology G is reserved to Administration.
19. Input type "hours only" forbids estimates and pautas; "no hours" forbids timesheet entries.
20. Investment type "no budget" lets estimates be created as pre-approved, which allows supplier invoices to be attached; the other investment types do not allow costs to be entered on that basis (as stated by the manual).
21. Only open jobs appear in lookups for briefs, tasks, fee contracts.
22. Billing-client change only if nothing in the job is invoiced.
23. Documents cannot move from billable to non-billable jobs; invoiced documents cannot move (or only between jobs with the same billing clients); briefs and contact reports never move; moves leave no audit trail of origin.
24. Substitution: source not closed; no invoiced content unless billing clients match; source becomes permanently unusable.
25. Accounts close blocked by unfinished tasks or by documents pending client approval or pending approval for billing.
26. Administrative close blocked by documents pending client invoicing or pending supplier invoices.
27. Accounts cannot reopen an administratively closed job.
28. Auto-close threshold = configured inactivity days; 0 disables; 30–60 days suggested.
29. A job may be deleted only if it has no movement.

**Fee contracts**
30. Contract currency is unique; different currencies require separate contracts; a foreign currency requires an exchange rate.
31. Contract total = Σ instalment amounts (system computed).
32. Each instalment is split by the media/production distribution percentage; when both are non-zero, two billable items per month are generated (one fee pauta, one fee production estimate) and they must be invoiced separately.
33. Fixed distribution: each linked job gets a percentage of each instalment. Dynamic: jobs matching the pattern are included without a percentage and the system distributes fees proportionally across all included jobs. Self-assignment: on JobNumber creation, if an active contract's pattern matches, the system asks the user whether to include the job.
34. Jobs created after the contract may be added manually.
35. Fixed-distribution contracts cannot receive new jobs once the first instalment is invoiced.
36. A JobNumber may belong to only one fee contract unless the special configuration allowing multiple contracts is true.
37. No agency commission may be charged on any estimate linked to a fixed or hourly fee contract.
38. Fee-generated pautas and estimates are read-only (owned by the contract).
39. A contract may be deleted only if no instalment has been invoiced.
40. A contract cannot be approved for a period whose fiscal year is not yet open in accounting.
41. Client approval precedes approval for billing; each requires the corresponding user permission flag.

**Hourly-fee calculation (tool-worthy)**
42. Implicit hourly price `p = instalment_amount / covered_hours`.
43. If imported hours `h ≤ covered_hours`: reference base value = `h × p` (instalment billed is the agreed amount). Example pattern: amount 50,000 for 100 hours → p = 500; 50.5 hours → reference 25,250.
44. If `h > covered_hours`: the excess hours are valued at the collaborator's client sales rate (from the internal client-rate table by salary category, which can differ by client), and the excess is billed automatically on top of the agreed fee: `billable = instalment_amount + Σ_excess (hours_i × client_rate_i)`. The exact allocation of which person's hours count as "excess" is not specified.
45. An optional adjustment coefficient per line modifies imported hours; manual resource lines (name, rate scale, hours) cover people who do not use the timesheet.
46. Hours accumulate: late-loaded hours fall into the next month's import.
47. If the agency uses supervisor approval of timesheets, only approved hours are imported.
48. Import is repeatable and reversible until approval.

**Staff-hour estimate**
49. Estimate total = Σ(collaborator hours × hourly rate of the chosen rate type and month). Differences vs actual may be accepted up to the configured hour tolerance.

**Tasks**
50. Exactly one recipient per task (CC unlimited); recipients must be system users.
51. Date order: requested-by-Accounts ≤ internal consensus ≤ promised-to-client.
52. At most one production estimate per task; the estimate's management month must be open.
53. Tasks cannot reference generic jobs.
54. Reassign: only when pending or rejected; by requester, coordinators or department reassigners. Reject: only when pending; by recipient or coordinator. Cancel: only when sent and pending.
55. Progress conventions: finished by recipient = 80%; sent back by requester = 50% and pending; approved by requester = 100% and immutable.
56. Configurable: automatic copies to team heads and coordinators; e-mails to creatives and Accounts staff; CCs and Accounts staff may edit others' tasks; tasks to creatives cannot be printed; templates mandatory.

**Brief / contact report**
57. One strategic brief per JobNumber; To and body mandatory.
58. Contact report body mandatory; exclusive reports visible only to author, recipients and CC; client attendees must be registered contacts.

**PO and reserves**
59. PO amounts are net of tax; POs apply prospectively only (documents created before the PO cannot be linked).
60. PO check at client approval; consumption at order issuance; header PO assignment locked once set.
61. PO transfers are between POs of the same billing client and must name the source document.
62. Reserve control: percentage (cap 100%), amount, or none; balance reduced by consumption invoices; pool-area approver gives first-level approval.

**Media lists**
63. Bulk approval from pending lists works on one state at a time.
64. Agency-commission billing mode can be switched only for lines with nothing invoiced; refusals are reported line by line; requires permission.
65. Writing off a media difference removes it from receivables pending billing.

**Timesheet**
66. Concepts are per department and optionally billable (used to distinguish billable hours in hourly-fee contracts); enabled only with "uses JobNumber concepts in timesheet".
67. Closed timesheet periods block entry and edit; unfilled days are assigned to a chosen job at closing.
68. Weighted hours option normalises hours to an 8-hour day.

**Revenue budget**
69. Budget lines are per product (and per division when divisions are used).
70. Commission income = investment × commission %; cost-difference income = investment × cost-difference %; total income = investment-derived items + fees + rebates − rebate refunds (the manual lists rebate refunds as a line; sign treatment inferred).
71. Percentages entered before the media/supplier opening are wiped; open first, then enter percentages.
72. Copying with "include closed months" substitutes actuals for past months.
73. Only supervisors can close/reopen a version; modify requires a specific client, product and division (not "all").

**Profitability formulas**
74. Media profitability, method "net investment plus commission": `(sale + commission − cost) / sale`.
75. Method "net investment only": `(sale + commission − cost) / (sale + commission)`. (Worked pattern: sale 100, cost 90, commission 15 → 25% and 21.74%.) Note the manual's labels for the two methods appear swapped relative to the formulas.
76. Gross income (ROT) = revenue − direct costs + agency commission + fees.
77. Client result (ROT) = gross income − other expenses (non-billable, new business, own advertising) + miscellaneous income − miscellaneous expenses.
78. Client profitability: income = billing − supplier costs; direct costs = valued hours + unplanned direct expenses; contribution margin = income − direct costs; structural expenses (everything booked to the agency's generic job in expense accounts) are allocated to clients in proportion to each client's share of contribution margin; net result = contribution margin − allocated structural expenses.
79. Indirect-cost driver options: valued hours, hour count, or 50/50 blend (valued hours recommended).
80. Hour valuation: internal cost = hours × internal hourly cost of the collaborator; client value = hours × client hourly rate.

---

## 6. Accounting and financial impacts

- **Fee revenue accounts**: two GL accounts (media fees, production fees) flagged with observation code 22 ("fee/honorarium account"); linked through a fee media type + fee media, and a fee production type, declared in special configuration. Fee instalments post revenue to these accounts when invoiced (through CxC).
- **Commission** (`Servicio de Agencia`) and its discount are computed on estimates and media plans from product (or media-type) percentages; may be billed together with the media or separately.
- **Job closing** has no accounting effect; it only blocks postings.
- **Job P&L views** (Job Status & Content, Fee Contract Content) show an income statement by GL account, split into booked-to-date (three columns) and pending (three columns).
- **Cost centres**: profitability reports can exclude a cost centre; the agency's generic JobNumber collects structural expenses.
- **USGAAP reporting entries**: a special entry type posts movement code 8A and its automatic reversal 8B, so local balances are unchanged while headquarters reporting can include 8A only, or exclude both.
- **Provisions**: in some countries, direct (pass-through) and reimbursement amounts pending client invoicing must be shown separately to support accrual provisions.
- **Work in progress**: "Pending direct billing control" lists, per work order, supplier documents not yet passed to the client — a WIP account reconciliation.
- **Accounting period gate**: fee contracts cannot be approved for periods whose fiscal year is not yet open; production-estimate months closed for loading cannot be chosen.

---

## 7. Cross-module handoffs

| Counterpart | Cuentas sends | Cuentas receives |
|---|---|---|
| Producción | JobNumber, task-linked production estimates (topic, approval type, billing client/split, department, client PO no.), fee production estimates per instalment, PO/reserve assignment | Estimate status (approved, invoiced), item control on tasks |
| Medios | JobNumber, fee pautas per instalment, PO/reserve assignment, commission % by product/media type, rate-card mode, time-slot restriction, target | Pauta status, ordered amounts, ad-control status, differences |
| Gastos | JobNumber (incl. generic jobs) for expense charging; reserve consumption choice at invoicing | Direct expenses per job (shown in P&L and profitability) |
| CxC (billing) | Approved-for-billing estimates, pautas, fee instalments; billing client / split code; mandatory attachment rule; differences write-off; commission billing mode | Client invoice numbers back onto contract instalment rows; invoiced status that locks moves, substitution, billing-client change, contract deletion; collection dates and collection days for KPIs |
| CxP | Orders linked to jobs; PO consumption at order issuance | Supplier invoices matched to orders (pending supplier invoice blocks definitive close) |
| Tesorería | — (indirect) | Collection dates (shown in estimate lists) |
| Contabilidad | Observation-22 accounts usage; division; USGAAP 8A/8B | Fiscal periods (gate approvals), booked amounts for "accounted" views and closed months |
| Management | Job P&L, ROT, profitability per client, media profitability, revenue budget vs actual, task KPIs | Same screens are also published under the Management menu |
| Users & Security / Config | — | Approval flags, department types, access levels, special configurations |
| Contabilidad masters | — | Collaborators (category, sub-category, internal cost, client rates per client), cost-plus salary categories |

---

## 8. Configuration parameters and country-specific behaviour

### 8.1 Special configurations referenced
| Parameter | Effect |
|---|---|
| `Time Sheet` (initial configs) | Enables timesheet; mandatory for hourly fees |
| `Time Sheet por Cliente = x JobNumber` | Hours captured by JobNumber |
| `Tipo de Producción Fee` (Production) | Fee production type |
| `Medio Fee` (Media) | Fee media |
| Allow a JobNumber in more than one fee contract | Lifts rule 36 |
| `Usa Conceptos de JobNumber en TimeSheet` | Enables timesheet concepts |
| `Usa Seguimiento de Tareas (JPM)` | Enables JPM masters, projects and reports |
| `Usa Workflow` | Enables complementary tasks / stage time measurement |
| `Limita acceso a producto` | Enables attention-group scoping |
| `Copia Jefes Grupos en Tareas` | Auto-copy group heads on tasks |
| Task process options | auto copies, e-mails, edit rights, print restriction, mandatory templates |
| `Administrar PO de Clientes` | Enables client POs |
| Product hierarchy mandatory | Rule 5 |
| `Con Divisiones` / sub-companies | Division fields on jobs, contracts, reports, budget |
| `Usa Departamentos de Producción` | Production department on estimates/contracts |
| Strict media approval circuit | Enables sector approval role |
| `Límite de días de inactividad de Job` | Auto-close threshold |
| `Responsable puede cerrar Job` | Job responsible may close |
| `Sugerir cierre de Jobs sin Movimientos` | Alert for jobs to close |
| `Usa Maestros/Movimientos Provisorios`, `Genera Clientes Titulares Provisorios`, `Usa Aprobación Intermedia`, mail on save / on approval and their address lists | Provisional master workflow |
| Revenue-budget loading method | Granularity of budget entry |

### 8.2 User-level flags
`Aprueba por Cliente`, `Aprueba para Facturar`, pool-area approver, provisional-master roles (generate / intermediate approval / final approval), reassign within department, supervisor level (budget lock), profile entries (job list 1/A, job close 1/A, 3C for job creation, commission-mode switch).

### 8.3 Country notes
- **Colombia**: the budget-reserve feature was built for a Colombian telecom client.
- **"Certain countries"** (unspecified): need separation of direct/reimbursable amounts pending billing for provisions.
- **Headquarters reporting**: USGAAP 8A/8B entries for multinational agencies.
- Tax: reports can include/exclude VAT (`IVA`) and VAT on commission; PO amounts are net of tax. No country-specific tax rules are described in this module. Argentina/Mexico specifics are not mentioned here.

---

## 9. Reports and queries

| Report | Purpose / KPIs | Source |
|---|---|---|
| Estimate vs actual hours | Hour burn vs estimate per client/estimate | [mp302021.html] |
| Accrued fee contracts list | Instalments invoiced vs not, by period, client, currency, optional jobs | [mp302735.html] |
| Fee contract content | Instalment documents and status, hours (cost & client value), billed/pending/total income, GL statement | [mp302878.html] |
| Job status & content | Documents by type with status, hours by day/department with internal and client value, P&L billed/pending/total, GL view; actions: new doc, move, substitute, change billing client, close/open | [mp301240.html] |
| JobNumber list | Filter by dates, approval state, titular/billing clients, generic jobs, job state; actions copy, reassign, close/open | [listado-de-jobnumber.html] |
| Investment & gross income per client (ROT) | Revenue, costs, commission, fees, gross income, other costs, misc income/expenses, result; date criteria: work-order month, client-invoice date, accounting date, booked only; include direct, pending, in-process; hours option; charts | [mp301428.html] |
| Investment & gross income of non-clients | Supplier-side income: cost differences, discounts, supplier commissions per work order/supplier | [mp302724.html] (stub) |
| Profitability per client | Billing, income, direct hours, direct expenses, contribution margin, allocated structural expenses, net result; drivers; division/sub-company/rubro breakdowns; USGAAP option | [mp301430.html] |
| Media profitability | % profitability by client/product with two formulas; ad audit filter | [mp301116.html] |
| Pauta list | All pautas; filters by fees, prepayments, rejected, currency (multi-currency vs consolidated), ad control; flowchart weekly export; pre/post evaluation; commission-mode switch | [mp301063.html] |
| Pending pautas / orders pending billing | Pending client approval, ordering, approval for billing, billing; differences; bulk approve | [mp301137.html], [mp301137_soloeditora.html] |
| Production estimate list | Filters by many dimensions, direct/indirect supplier invoice, fees, cost status; columns client invoice, approval dates, collection date, VAT on commission, discounts, approver; editable client PO no.; copy, cancel-and-replace, print | [mp301173_ejecutar.html] |
| Pending direct billing control | WIP: supplier documents not yet billed to client by work order; detail and summaries by client, WO, supplier | [mp301226.html] |
| PO consumption | Consumption by state | [mp302795.html] |
| Task list (task / agenda / graphic agenda) | Status, delay = today − consensus date, filters by many criteria; bulk close; replace recipient | [mp301399.html] |
| Task statistics | Tasks received vs delivered by department and client | [mp301365.html] |
| KPI reports | Summary (actions and average times) and detailed per client (estimate status, invoiced or not, average collection days) | [mp301565.html] |
| JPM by job / by resource | Gantt, rejections, date changes, rework, difficulty, days, standards, saturation % | [mp301510.html], [mp301564.html] |
| Timesheet dynamic report | Hours by job valued at internal and external rate; pivot fields | [mp302030_horas_base.html] |
| Timesheet hour control | Last loading date per person | [mp302879.html] |
| Provisional masters report | Creation, approvals, rejections, reasons, responsible, lead times | [mp302880.html] |
| Dynamic reports hub | Cost/expense/petty-cash renderings, timesheet, equivalent units, order modifications, publication types, job list | [mp302005.html] |
| Revenue budget queries | Plan vs actual / version vs version; projected (actual closed months + plan open months); scope "media billing" vs "complete" | [mp301015.html], [mp301021.html] |

---

## 10. Agentic-skill implications

### 10.1 Atomic agent jobs
| # | Job | Inputs | Deterministic tool | Controls | Exceptions to flag |
|---|---|---|---|---|---|
| J1 | Onboard titular client | trade name, group, category, rate-card modes, PO flag | `generate_client_code(desc)` with uniqueness check | Provisional approval chain if enabled | Duplicate names/codes; missing billing-client linkage |
| J2 | Create product | client, name, hierarchy, commission %s | `generate_product_code(name, client)` | Hierarchy-mandatory config | Code collision; commission % outside policy |
| J3 | Open JobNumber | client, product, year, typology, billing code, topic, responsible, investment | `build_jobnumber_code(...)`, `validate_job_rules(...)` | Creator/responsible must be Accounts collaborators | `?` jobs aging without billing client; typology/billing contradictions (e.g. N with F); missing topic year reference |
| J4 | Fee-contract matcher | new JobNumber, active contracts & patterns | `match_patterns(job, patterns)` | Ask human on self-assignment contracts | Job already in another contract; contract fixed-distribution already invoiced |
| J5 | Draft fee contract | client, period, amount schedule, split %, jobs or pattern, currency/rate | `build_instalments(from,to,amounts)`, `split_media_production(amount, pct)`, `validate_percentages_sum_100(jobs)` | Two-step approval with permission flags | Fiscal period not open; foreign currency w/o rate; % not summing to 100 |
| J6 | Monthly hourly-fee close | contract, month, approved timesheet hours, client rates, manual resources | `compute_hourly_instalment(amount, covered_hours, hours_by_person, client_rates, coeffs)` | Hours approved by supervisor; account lead validation; client approval then billing approval | Overrun > tolerance; unapproved hours; late hours carried; missing rate for a category/client |
| J7 | Staff-hour estimate & burn tracking | collaborators, hours, rate type/month | `estimate_total(lines, rates)`, `burn_vs_estimate(actual, est, tolerance)` | — | Burn above tolerance |
| J8 | PO guard | billing client, PO, document amount, document creation date | `po_available_balance(po)`, `check_po_eligibility(doc_date, po_created)` | Check at client approval | Insufficient balance; document predates PO; transfer without source document |
| J9 | Reserve guard | job reserve, document, area | `reserve_balance(reserve, area, control_type)` | Pool-area approver | Cap exceeded |
| J10 | Brief/contact-report writer | job(s), meeting notes, attendees | template rendering | Human review before send; external address confirmation | Second brief on same job; non-registered attendees; exclusive flag handling |
| J11 | Task dispatcher | request, job, dates, recipient, template, estimate | `validate_task_dates(req, consensus, promised)` | State-machine enforcement | Generic job; multiple recipients; closed month for estimate |
| J12 | Task follow-up | task list | `task_delay(consensus_date, today)` | — | Overdue, rejected, standby tasks blocking job close |
| J13 | Job closer | job list, config threshold | `job_close_readiness(job)` (open tasks, pending approvals, pending billing, pending supplier invoices), `inactive_jobs(days)` | Accounts vs Finance role separation | Blocking items; attempt to reopen definitive close from Accounts |
| J14 | Move/substitute/re-bill | source job, docs, target job | `validate_move(doc, src, dst)`, `validate_substitute(src, dst)`, `validate_billing_change(job)` | Human confirmation (no audit trail in legacy — the skill should log origin) | Invoiced docs; billable→non-billable |
| J15 | Pending-billing sweeper | pending lists | filters by single state | Approval permissions | Differences to write off need explicit decision |
| J16 | Profitability analyst | billing, costs, hours, expenses | `rot(...)`, `client_profitability(..., driver)`, `media_profitability(sale, cost, commission, method)` | — | Negative contribution, jobs with costs but no revenue, sales on N/S/W jobs |
| J17 | Revenue-budget planner | client×product×month investment, %s, fees, rebates | `revenue_budget_line(inv, comm_pct, costdiff_pct, fees, rebates, refunds)`, `copy_version(include_closed_months)`, `projection(actuals, plan, close_month)` | Supervisor lock | Editing a closed version; percentages entered before opening |
| J18 | Timesheet governance | collaborators, last entry dates | `timesheet_gaps(today)`, `close_timesheet(cutoff, default_job)` | — | Staff not loading hours; hours on inactive clients hidden by filters |
| J19 | Access-scope auditor | attention groups, products | `visibility(user)` | — | Free products used on confidential jobs; groups with >1 head; products with no group while others are grouped |

### 10.2 Cross-cutting controls an agent must respect
- Segregation: Accounts close vs Finance close; client approval vs billing approval; provisional master requester vs approvers.
- Never invent sales value on non-billable jobs or typologies N/S/W; never add commission on fee-linked estimates.
- Treat invoiced status as a hard lock for moves, substitution, billing-client change, contract deletion and fixed-contract job additions.
- Always record an audit log for document moves (the legacy system does not).

---

## 11. Gaps and ambiguities in the manual

1. All Academia pages (timesheet, tasks, expense reports, campaign concepts, brief, contact report, job approval, fee contract, campaign analysis, additional lists) contain only video titles; no content.
2. Stubs with no content: `Etapas de Campaña`, `Tipologías de Campaña`, `Motivos de Rechazos`, `Listados Genéricos`, `Prospectos`, `Tareas Complementarias`, `Inversión y Gross Income de No Clientes` (introduction only).
3. Hourly-fee overrun: unclear whether the excess is computed per person or in aggregate, which person's hours are deemed excess, and whether "billable concepts" filter the import.
4. Fixed-fee "dynamic" distribution: the proportional allocation basis (hours? consumption? investment?) is not defined except for self-assignment ("actual consumption and hours").
5. Instalment states vs contract-level state: how the header state derives from mixed instalment states before invoicing is not described.
6. Media profitability method labels appear inverted relative to their formulas.
7. Move rules conflict: overview says invoiced estimates/pautas can never move; the guide permits it when billing clients match. Same for substitution.
8. Investment type "no budget" vs others: the statement that only "no budget" allows cost entry is ambiguous (likely refers to pre-approved estimates only).
9. Administrative reopen target state (back to Accounts-closed or to Vigente) is not stated.
10. Rebate refunds sign in revenue-budget total is not explicit.
11. Profitability "structural expenses" allocation uses contribution-margin share; behaviour with negative contribution margins is undefined.
12. "Approved" vs "Finished by requester" task states are described inconsistently across pages.
13. The manual mixes `JobNumber`, campaign, project and work order (`OT`) loosely; the OT-to-JobNumber cardinality is not defined here.
14. No explicit journal-entry templates are given for fee instalments; only account-flag prerequisites.
15. Country-specific behaviour for Argentina/Mexico is not described in this module.
16. Task template "internal vs external" usage and how external parties answer are not explained.
17. PO "online/offline" scope and the product/media-type breakdown enforcement rules are not detailed.
18. JobNumber copy action: the meaning of entering "2" for year is unclear (likely the target year digit).
