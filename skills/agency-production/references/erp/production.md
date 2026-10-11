# Production Module (`Producción`)

> **Provenance.** Functional reverse engineering of a reference agency ERP, derived from its publicly accessible help documentation (reviewed 2026-10-11). Content is paraphrased and restructured; it is not vendor documentation, source code or an endorsement. Bracketed ids such as `[mp301010]` identify the source page used as evidence. Items marked *inferred*, *assumed* or listed under gaps must be validated with your own controller, tax adviser and system owner before they drive postings or payments.

> Reverse-engineered functional specification of the agency-ERP "Production" module, derived from the vendor's Spanish help manual (group file `B_produccion.txt`). All prose is an original paraphrase for an MIT-licensed agentic-skills repository. Spanish field/term names appear in backticks only as identifiers. Source refs point to the help page file names.

---

## 1. Module purpose and position in the end-to-end agency circuit

**Purpose.** The Production module manages every non-media job an agency sells to a client — creative/audiovisual/digital/print production, events, talent and royalties, internal agency work — from the first price estimate through supplier selection, purchase commitment, and readiness for client billing. Its core document is the **Production Estimate** (`Presupuesto de Producción`, also called `Estimado`), a multi-line, multi-currency quotation tied to a project (`JobNumber`). Around it sit: supplier quotation/award, purchase orders (`Órdenes de Compra de Producción`), client advances (`Anticipos`), royalty contracts, supplier override-commission contracts, event-staff management, and production master data.

**Where it sits.**

| Direction | Module | Relationship |
|---|---|---|
| Upstream | **Accounts / Job tracking** (`Cuentas – Seguimiento de los Trabajos`) | Supplies the `JobNumber` (client + product + theme + billable flag + typology + billing-split code). Tasks (`Tareas`) raised in job tracking can be linked to estimate lines. Account managers drive client approval. |
| Upstream | **CxC client masters** | Billing clients (`Clientes de Facturación`), owner clients (`Clientes Titulares`), payment terms, billing-split codes (`Códigos de Apertura de Facturación`), credit limits. |
| Upstream | **Accounting masters** | Production types carry revenue/cost/discount GL accounts; observation codes classify accounts. |
| Upstream | **Fee contracts** | Estimates can be generated from a fee contract; their approval happens on the contract. |
| Lateral | **Media** | Shares suppliers, royalty contracts and entities, additional-data fields, document observations, and the override-contract numbering sequence. |
| Downstream | **CxC billing** | "Approved for billing" estimate lines become billable pending items; automatic client invoicing reads them (investment + agency service, joint or separate). |
| Downstream | **CxP supplier invoices** | Awarded/ordered lines create "pending to receive" items against which supplier invoices are matched (mandatory PO and PO approval gates optional). |
| Downstream | **Treasury** | Advances are collected like normal receivables; cost-rendering (petty-cost style) items flow through employee/cost-rendering accounts; override credits net against supplier payments. |
| Downstream | **Accounting** | Automatic journal entries at client invoicing and supplier invoice entry, using production-type accounts; month-end accrual of approved-but-unbilled work; override provisions. |
| Downstream | **Management / reporting** | Production statistics, preliminary investment (margin) report, dynamic reports, Post Buy variance. |

---

## 2. Process catalogue

Each process lists: trigger · actor · steps · inputs · outputs · state changes · approvals · source.

### P01 — Create a production estimate (`Ingresar presupuesto de producción`)
- **Trigger:** client brief/request for a non-media job; or task with cost in job tracking.
- **Actor:** estimate author (producer / account executive). Best practice: author ≠ client approver.
- **Steps:**
  1. New document; choose the period (month/year) of the estimate. System auto-assigns an `Nº Estimado` (sequence that restarts monthly) and a `Nº Presupuesto` (global, never-restarting sequence).
  2. Pick the `JobNumber` through the chain owner client → product → job. Only open/vigent jobs are offered.
  3. Enter `Tema` (subject; recommended to describe what is being quoted).
  4. Select `Tipo de Aprobación`: `A Presupuestar` (normal, requires client approval) or `Preaprobado` (skips client approval).
  5. Optional client order reference `Pedido` and client PO number `Nº OC Cliente`.
  6. `% Serv. Agencia` (agency service/commission %) and `% Bonif. Serv. Agencia` (discount on that %).
  7. `Condiciones de Pago` (defaults from client, editable any time).
  8. `Facturación` mode: `Junto` (investment + agency service on one invoice) or `General` (separate invoices).
  9. Optional client `Contacto` (must exist as agency contact); billing-split code if the job is split; optional price list, contingency % (`imprevistos`), creative idea and its % with an agency/client owner flag.
  10. Add lines (see P02–P06), confirm each line.
  11. Optional footer notes (`Notas al Pie`: model + Note 1–3) and internal agency observation (never printed).
  12. Save with confirmation.
- **Outputs:** estimate in state *Pending client approval* (or *Pre-approved*). Header shows read-only totals: sale, cost, agency service, income, margin %.
- **Source:** `mp301003.html`, `-ingresar-presupuesto-de-produccion-.html`.

### P02 — Add an indirect line (`ítem indirecto`)
- Supplier invoices the agency; agency invoices the client. `Dire` flag unchecked.
- Steps: currency → production type (`Nº`, fills description) → optional long description → supplier (`Nº Prov`, search by legal or short name) → cost net of VAT → sale price → optional discount % → optional agency-service flag (`S.Ag.`) → optional supplier commission (`Com`) → FX rate if foreign currency → confirm.
- **Source:** `-ingresar-item-indirecto-...html`.

### P03 — Add a direct line (`ítem directo`)
- Supplier invoices the client directly; `Dire` checked. Cost is copied into sale (sale = cost); agency can only earn its agency service and/or a supplier commission on it.
- **Source:** `-ingresar-item-directo-...html`.

### P04 — Add a line performed by the agency itself
- Indirect line whose supplier code is the reserved agency code `0000`. Cost and sale entered; no external PO. These lines feed the "Estimates with internal costs" report.
- **Source:** `-ingresar-item-a-realizar-por-la-agencia-...html`, `mp301357.html`.

### P05 — Add a cost-rendering line (`rendición de costos`)
- Pre-reqs: a supplier flagged as special type `Rendición de Costos`; a balance-sheet GL account (asset/liability) with observation code `84` (cost-rendering account).
- Indirect line with that special supplier as `Nº Prov`; cost, sale, discount, agency service, FX.
- Used when an employee/agency advances and later justifies costs; controlled via P27.
- **Source:** `-ingresar-item-relacionado-a-una-rendicion-...html`, `mp301547.html`.

### P06 — Add a line from a price list
- Pre-reqs: config `Lista Precios Producción = true`; choose per-client vs generic lists and per production type vs per type group.
- In the `Lista` column, pick a list item (generic list shown first, then client-specific); unit cost and unit price fill automatically; enter quantity; cost = unit cost × qty, sale = unit price × qty (× days when event staffing); optional discount, agency service, commission, FX.
- **Source:** `-ingresar-item-usando-lista-de-precios-...html`, `mp305320.html`.

### P07 — Supplier commission on a line (`Comisión a Proveedores` / confidential)
- Enabled when the agency uses supplier commissions and the client is configured to accept them.
- Commission window: type `Con Comisión` (or `A definir` while negotiating) → calculation `Importe Fijo` or `Porcentaje` on supplier cost → value → confirm.
- Collection mode (per agency config): supplier issues a credit note, or the agency invoices the supplier (supplier must also exist as a billing client).
- Line-level `Confidencial` flag (in `Adicionales`) prints the agency name instead of the supplier's.
- **Source:** `mp301003.html`, item guides.

### P08 — Multi-quantity supplier quotation (`Cotizar`)
- Pre-req: a production type identified as `Preproducción` (internal code 999) and a saved estimate containing the line.
- Steps: open line → `Cotizar` window → optional spec fields (width, length, depth, die-cut `Troquel`, colours, paper, desired profit %, photo-lithography `Fotocromía` amount and its supplier, item type) → add quantity columns (one per quantity to quote) → add suppliers (F2) and enter each supplier's price per quantity → optionally split each quote into `Puesta en Máquina` (make-ready) and `Impresión` (run) → confirm → save estimate.
- Output: quotation matrix (supplier × quantity).
- **Source:** `-ingresar-cotizaciones-de-proveedores-para-varias-cantidades-...html`.

### P09 — Print/e-mail received quotations
- Open line → `Cotizar` → select quotation → Print (file saved to folder) → optional e-mail with attachment.
- **Source:** `-imprimir-cotizaciones-recibidas-.html`.

### P10 — Award a line to a quotation (`Adjudicar`)
- Pre-reqs: quotations entered; estimate approved by client.
- Steps: open line → `Cotizar` → `Adjudicar` → choose quantity to award → `Calcular Valor` (highlights each supplier's price for that quantity) → pick winning supplier/price → accept → confirm → save.
- Effect: line cost/supplier set to awarded values. If the type is Preproduction and a `Fotocromía` value was quoted, after approval the system spawns a separate photo-lithography line.
- **Source:** `-adjudicar-el-item-a-una-cotizacion-.html`, `mp301036.html`.

### P11 — Alternative suppliers and chosen supplier (`Otros proveedores`)
- Up to three suppliers per line with estimated cost and observations (e.g., reliability notes). Supplier #1's cost comes from the line itself.
- After client approval: modify line → choose `Proveedor elegido` → confirm.
- **Rule:** until a chosen supplier is set, no "pending to receive" exists and no supplier invoice can be entered — even if the chosen supplier equals the one already on the line.
- **Source:** `mp301003.html`.

### P12 — Modify a line
- Edit main data, description, `Adicionales` (division — defaults from campaign; activity/stage when estimate came from a costed task; confidential supplier flag), and link `Tareas Asociadas` (tick tasks).
- Locks: see rules R20–R22.
- **Source:** `-modificar-un-item-...html`.

### P13 — Delete / recover a line
- Delete line → save. Recover is possible only before saving (undo of the deletion in the open edit session).
- Locks: cannot delete invoiced lines (client or supplier side), lines of closed estimates, or the first line.
- **Source:** `-eliminar-un-item-...html`, `-recuperar-un-item-eliminado-...html`.

### P14 — Modify header (`Modificar Encabezado`)
- Editable post-save: subject, client order, client PO, agency service %, its discount, payment terms, billing mode, contact, footer notes. Typical trigger: client sends its PO number to be quoted on the invoice.
- **Source:** `-modificar-el-encabezado-...html`.

### P15 — Estimate billable to several clients
- Pre-reqs: a `JobNumber` whose billing code is the "split / assign in plan or estimate" type; billing clients linked to the owner client; billing-split code with percentages.
- Steps as P01 plus: select one of the billing clients and the `Código de Apertura` that defines each client's %.
- **Source:** `-ingresar-presupuesto-de-produccion-facturable-a-varios-clientes-.html`.

### P16 — Print / export the estimate
- Choose print format(s) and copies; `Resumida` (show only first line's text with the sum of all lines' sale) vs detailed; options: logo, omit VAT, VAT-inclusive prices, export Word/PDF, only internal indirect lines, only lines with supplier. Argentina: may include estimated gross-income (IIBB) perception.
- **Source:** `-imprimir-el-presupuesto-...html`, `mp301003.html`.

### P17 — Client approval (`Aprobar por Cliente`)
- Pre-reqs: approval type `A Presupuestar`; user flagged `Aprueba por Cliente`.
- Whole-estimate approval only (reject unneeded lines first). Validates credit limit when the agency uses credit limits. If config `Genera Versión Inicial Automática` is on, the *initial version* snapshot for Post Buy is taken now.
- Fee-contract estimates are approved from the fee contract instead.
- Bulk variant from pending report (P24).
- **Source:** `-aprobar-presupuesto-...-por-cliente-.html`, `-aprobar-masivamente-por-cliente-...html`.

### P18 — Client disapproval (`Desaprobar por Cliente`)
- Reverts to pending client approval. Same role. Not allowed if any part is approved for billing.
- **Source:** `-desaprobar-un-presupuesto-...-por-cliente-.html`, `-desaprobar-masivamente-por-cliente-...html`.

### P19 — Approve for billing (total or per line) (`Aprobar para Facturar`)
- Pre-reqs: estimate client-approved or pre-approved; user flagged `Aprueba para Facturar`.
- `Aprobar Total` (all lines) or `Aprobar ítem` (partial delivery). Marks work as finished/delivered and releases it to client invoicing.
- **Source:** `-aprobar-presupuesto-...-para-facturar-.html`, `ad_cap_gus_pro_04-...html`, `-aprobar-masivamente-para-facturar-...html`.

### P20 — Disapprove for billing (total or per line)
- Reverts lines to client-approved. Not allowed on lines already invoiced to the client.
- **Source:** `-desaprobar-presupuesto-...-para-facturar-.html`, `-desaprobar-un-item-...-para-facturar-.html`, `-desaprobar-masivamente-para-facturar-...html`.

### P21 — Client rejection and recovery (`Rechazos`)
- `Rechazar Total` / `Rechazar Ítem`: cancels the request while preserving content (preferred over deletion). `Recuperar Total` / `Recuperar Ítem` removes the rejection.
- **Source:** four rejection/recovery guides.

### P22 — Close / reopen estimate (`Cerrar` / `Abrir`)
- Close freezes the estimate (no edits, no line deletions). Reopen re-enables changes.
- **Source:** `cerrar-un-presupuesto-...html`, `-abrir-un-presupuesto-...cerrado-.html`.

### P23 — Copy; Void-and-replace (`Copiar`; `Anula y Sustituye`)
- Copy: from a consulted estimate, choose new period (new number auto-assigned) and target `JobNumber` (same or other client; must be vigent); confirm; save.
- Void-and-replace: same, but the source estimate is automatically rejected (kept as history). Vendor recommends Copy + manual reject instead.
- Both available also from the complete estimate list.
- **Source:** `-ingresar-un-presupuesto-...-copiandolo-de-otro-.html`, `-anular-un-presupuesto-...-sustituyendolo-...html`, `mp301173_ejecutar_completo.html`.

### P24 — Pending-approval workbench (multi-state report with actions)
- One report, three entry points: *Pending client approval*, *Pending approval for billing*, *Pending billing*; or `Completo` (all three together). Accessible also from Accounts and CxC billing menus.
- Filters: month range; list type (classic / complete / ageing by production-type group); criterion (client, product, job; or client-state / state-client); user (all, creator, task requester) and ordering; direct/indirect; department; with/without cost; with/without sale; type group; no supplier; includes agency service; exclude direct-without-commission; exclude zero balances; exclude discounted lines; show/hide fee contract instalments; client type and range; division; currency.
- Views: summarised by estimate / by client, grouped by product, include VAT, show supplier, show billing client, show split state, show task.
- Actions (with rights): bulk approve by client, bulk disapprove by client, bulk approve for billing (line level), bulk disapprove for billing. Drill-down to the estimate.
- **Source:** `mp301130.html` + four bulk guides.

### P25 — Purchase order from estimate (`Orden de Compra de Producción`)
- **Trigger:** line client-approved and supplier chosen/awarded. PO may be optional or mandatory per config.
- **Paths:** (a) bulk `Ordenar` from the estimate — generates POs for all lines in one step (auto-splits direct vs indirect into separate POs); (b) `Emitir Orden de Compra` for one supplier/selected lines with extra detail; (c) standalone PO screen: New → period → type `Estimado` → estimate number → supplier → secondary data (payment term, print currency, FX if not local, print client detail Y/N) → footer notes (model + text) → tick lines (totals and VAT computed) → save → optionally print.
- **Outputs:** PO with auto number, due date, client, campaign, lines, taxes. Commitment lock on supplier and cost of included lines.
- **Approval:** if `Aprobación Obligatoria de Compra en Producción = true`, a user flagged `Aprueba Ordenes de Compra de Producción` must approve (state → Approved).
- **Print/send:** copies, logo, omit VAT, Word/PDF export; e-mail with supplier address auto-filled from master; signature blocks (issuer, producer, executive).
- **Change:** PO must be free of supplier invoices (delete the invoice if month not pre-closed, or enter a supplier credit note); then **Anular** (void, supplier is informed, state Annulled) or **Eliminar** (delete; number released for reuse). Then edit estimate and reissue.
- **Source:** `mp301005.html`, `ad_cap_gus_pro_32/33/34-...html`, `mp302743.html`.

### P26 — Client advance request (`Anticipos`)
- Advance requests to the client linked to production estimates; they follow the normal receivable collection process. States: *Pending legalisation*, *Pending collection*, *Legalised*. Monitored by P31.
- **Source:** `anticipos.html`, `mp302694.html`.

### P27 — Control of cost renderings
- Report of renderings and advances whose operational circuit is not closed, filtered by an observation-code-84 account (all employee sub-accounts or one), production type, period, state (all / pending / not pending); optional payment-order, bank account, cheque number/state columns.
- **Source:** `mp301547.html`.

### P28 — Royalty contracts (`Contratos de Regalías`)
- Pre-reqs: `Control de Regalías = true`; royalty entities exist; for estimates, a production type identified `Regalías`.
- Create: owner client; supplier (must be flagged Production and/or Media); manual contract number; name; signing date; start date; modality `Por Meses` or `Por Repeticiones`; quantity (months or repetitions); amount; responsible user; comment; entities grid (type: voice-over `Locutor`, model, music, production house + entity name).
- Extend (`Extensión de Contrato`): allowed when the contract is no longer vigent, repetitions exhausted, or assigned to material, and not previously extended; creates a new contract (new number) copying the old one; modality cannot change.
- Delete only if not invoiced.
- Link to estimate: on a royalty-type line, modify → `Contratos de Regalías` action → tick contract of the line's supplier → approve. One contract per estimate. Unlink by deleting the line.
- Link to media plan: plan on a vehicle linked to the contract's supplier; assign a material tied to the contract; system computes the intersection of validities of contracts assigned to materials; out-of-validity materials block assignment with an error reasons window.
- Expiry alerts on the home dashboard for month-based contracts only.
- **Source:** `mp301486.html`, `-generar-nuevo-contrato-de-regalias-.html`, `-extender-contrato-de-regalias-.html`.

### P29 — Royalty entities master
- Auto-numbered code; type (model, voice-over, production house, music); description; vigent/non-vigent. Delete only if unused.
- **Source:** `mp309258.html`.

### P30 — Supplier override-commission contracts (`Contratos de Overcomisiones de Producción`)
- **Purpose:** retroactive volume commission negotiated confidentially with a supplier, optionally partly refunded to clients.
- **Three stages:** (1) contract definition; (2) monthly pending-generation run by administration — scans qualifying estimates, computes commission, leaves a pending to invoice the supplier or to receive its credit note (or provisions income in non-billing months); (3) billing via a special invoicing option, or credit entry via automatic supplier-invoice entry.
- Pre-reqs: supplier exists as billing client; a contract type exists (defines income / client-refund GL accounts; eligible accounts have observation codes 23, U4 or 20).
- Fields: supplier; auto code (sequence shared with media contracts → gaps); description (suggest period); validity start/end (max one year); eligible production types (e.g., exclude Fee); base `neta` or `bruta` investment; contract currency (informational, does not filter estimates); `% de reducción` of investment; contract type; calculation method; cap `monto límite`; client/product include/exclude lists; billing type (agency invoices supplier / supplier issues credit notes, paid or netted against payments); `Orden Generación Pendiente` (precedence among multiple contracts with same supplier; later contracts subtract earlier ones); `Período de Corte` (months in which pendings are generated; other months still calculated and provisioned); client refund (whether/how part returns to clients); division.
- Actions: new, query, copy, modify, delete (no trace), annul (cancels pendings, keeps conditions visible).
- **Source:** `mp302849.html`.

### P31–P40 — Reports (detailed in §9)
Advances list, production statistics, preliminary investment list, estimates with internal costs, pending workbench, dynamic production report, consolidated timesheet dynamic report, estimate list (complete), PO list, POs pending generation, royalty contracts list, supplier list.

### P41 — Event staff (three-stage process)
- Pre-reqs: `Usa Gestión de Eventos = true`; special supplier of type "eventual"; production types flagged `Requiere asignación personal` (and `Solicita Período`, Colombia); promotion staff registered.
- **Stage 1 — Staff master** (`Personal para Promociones`, P42).
- **Stage 2 — Request & assignment on the estimate:** line with a staffing-type production type and the eventual supplier; `Cantidad` = people per day; `Total Días` = event days (may differ from calendar span); `Desde/Hasta` event dates; save. `Solicitar Personal`: per day mark requested slots, pick persons (F2), mark `Elegido` (default) or `Reserva` (substitute), choose self-invoicing vs representative supplier, daily cost; confirm; `Enviar Solicitud`. `Asignar Personal` re-opens request to confirm/modify and send.
- **Stage 3 — Delivery & evaluation** (`Entrega y Evaluación de Personal para Eventos`): filter by job or estimate (period + number); grid per activity date/person: ID, chosen/reserve, state, replaced-by, total cost, supplier cost, temporary administration, own-account cost, arrival time, punctuality/presentation, objective fulfilment, customer service, total evaluation %, end time, equivalent control document, signature, notes. Modify → `Agregar Reserva` (estimate, line, person, supplier, cost components) → save.
- **Source:** `mp302772.html`, `mp301352.html`.

### P42 — Masters maintenance
Suppliers, production types, type groups, price-list items, price lists, text models, document/client observations, additional data fields, supplier articles (Mexico), payment terms, production templates, promotion staff (see §3).

---

## 3. Entities and master data

### E1 Production Estimate header (`Presupuesto de Producción`)
| Field | Meaning | Req |
|---|---|---|
| `Fecha / Nº Estimado` | Period (month/year, ±36 months bounded by closed periods) + monthly sequence | Auto/Req |
| `Nº Presupuesto` | Global never-resetting number | Auto |
| `JobNumber` | Project (implies owner client, product, theme, billable flag, typology, division, billing code) | Req |
| `Cliente` | Billing client (for split jobs) | Cond |
| `Código de Apertura` | Billing split % code | Cond |
| `Tema` | Subject | Req |
| `Tipo de Aprobación` | `A Presupuestar` / `Preaprobado` | Req |
| `Pedido`, `Nº OC Cliente` | Client order / PO ref (printed on invoice) | Opt |
| `% Serv. Agencia`, `% Bonif. Serv. Agencia` | Agency service % and discount on it | Req/Opt |
| `Condiciones de Pago` | Payment terms | Req (defaulted) |
| `Facturación` | `Junto` / `General` | Req |
| `Contacto` | Client contact | Opt |
| Price list, `% imprevistos`, creative idea + %, owner (agency/client) | Header pricing extras | Opt |
| `Notas al Pie` (model, Note 1–3) | Printed footer | Opt |
| `Observación agencia` | Internal note | Opt |
| Other data: creator, created date, delivery note (`remito`) issued, state | Audit | Auto |
| Totals: sale, cost, agency service, income, margin % | Display | Calc |
| Open/closed flag; initial version snapshot | Control | Auto |
| Attachments | Permission-tiered | Opt |
| Additional data (`Datos Adicionales`) | Custom fields | Opt |

### E2 Estimate line (`ítem`)
| Field | Meaning |
|---|---|
| `Moneda`, `Cotización` | Line currency, reference FX (re-asked at invoicing) |
| `Dire` | Direct (supplier → client) vs indirect |
| `Nº` | Production type |
| `Descripción` (+ optional additional description) | Long text used on invoice |
| `Lista` | Price-list item |
| `Nº Prov` / `Proveedor` | Supplier (code `0000` = agency; special cost-rendering supplier; eventual supplier) |
| `Costo Unit.`, `Precio Unit.`, `Cantidad`, `Días` | Unit economics |
| `Costo`, `Venta` | Totals (net of VAT) |
| `Dto.` | Discount % |
| `% utilidad` | Margin % (display or driver if cost-plus config) |
| `S.Ag.` | Agency service applies |
| `Com` + commission window | Supplier commission: type (with / to define), fixed or %, value |
| `Confidencial` | Hide supplier on print |
| Group, division, activity, stage | `Adicionales` |
| Other suppliers (≤3) + `Proveedor elegido` | Sourcing |
| Quotation matrix (spec fields, qty columns, supplier prices, make-ready/run split) | `Cotizar` |
| Linked tasks | Traceability |
| Royalty contract | Royalty-type lines |
| Event fields: people/day, total days, from/to, staff request | Event lines |
| Billing tab | Auto invoices to client (investment vs agency service), supplier invoices/credit notes, commission documents, user who manually marked as invoiced |
| Line states | client approval / billing approval / rejected / invoiced client / invoiced supplier / ordered |

### E3 Production Purchase Order
Number (auto), period, type (`Estimado`), estimate ref, supplier, due date, client, campaign, payment term, print currency + FX, print-client-detail flag, footer notes, selected lines with descriptions, net, VAT (possibly reduced rate), state (draft/issued, approved, annulled), creator, creation date, invoiced-by-supplier and invoiced-to-client flags.

### E4 Client Advance (`Anticipo`)
Request number, advance date, month/year, estimate, line number + description, estimate subject, amount, state (pending legalisation / pending collection / legalised), job, product, days overdue, due date, receipt number.

### E5 Royalty Contract
Owner client, supplier, contract number (manual), name, contract date, start date, modality (months/repetitions), quantity, amount, responsible user, comment, entities[], extended-from link, derived expiry.

### E6 Royalty Entity
Code (auto), type (model / voice-over / production house / music), description, vigent.

### E7 Override-commission Contract
See P30 fields; plus scale table rows (from, to, value or %), cap, client/product inclusion rules, refund rules, cut-off months, precedence, division, state (active / annulled).

### E8 Supplier (`Proveedor`)
Code (auto, immutable), legal name, short/trade name, cheque payee name, vigent, fiscal responsibility type, tax ID (up to 20 chars for foreign), indirect GL account (obs. code 30), supplier type flags (Production, Media, Expenses, Traffic), payment term (+ days; 0 = cash), person type (natural / legal / RESICO natural / moral), invoicing type (manual / electronic / fiscal printer), in-conflict flag (e.g., from apocryphal-invoice lists), owners/shareholders, associated client, Hyperion code, excluded from credit-invoice, activity, intercompany + code, media contact; taxes (country-specific: AR VAT/income/social-security/IIBB withholdings, reduction %, jurisdiction, ARCA concept, reduction periods by tax; CO national VAT computation); multiple payable accounts (obs. 30); CAI history (print authorisation & expiry); IIBB registration; early-payment scale; address/e-mail; special type (Normal, Petty-cash rendering, Expense rendering, Cost rendering, Bank debits, Accounting movement; each special type usable once), enabled, intermediary; bank data; external-system codes; attachments; logo.

### E9 Production Type (`Tipo de Producción`)
Code (auto), description, group, identification (`Normal`, `Bonificada` 996, `Impuesto al Cheque` 997, `Orden de Contratación` 998, `Preproducción` 999, `Regalías`), vigent, commissionable default, print grouping (grouped / not), print colour, requests period (CO events), requires staff (CO events), client account codes (free text for invoice and estimate), accounting tab (only via Accounting branch): accounting type (bridge vs result accounts), sale account (obs 01 bridge / 20–23 no bridge), cost account normal & job-advertising (02 / 39), cost non-rebillable (35), cost new business (37), cost own advertising (36), discounts account (23), optional split taxed/untaxed, VAT condition and rate (reduced rates), CO foreign-supplier national VAT rate, PR IVU applicability.

### E10 Production Type Group
Code (auto), description. Used as department/area (digital, audiovisual, art). Assigned from the type.

### E11 Price-list Item
List type (by production type or by type group), linked type/group, code (auto), description, unit of measure, client-specific nomenclature codes for printing.

### E12 Price List
Owner client (generic or specific), code (auto), description, version (auto per client/code), valid from/to (open-ended until superseded), currency, show-only-priced flag, rows (item, sale price, cost). Copy with % uplift for sale and cost (zero allowed).

### E13 Estimate Text Model
Code, short description, free text.

### E14 Document/Client Observation
Client type (owner / billing; specific or all), document (media plan + ad orders, media plan, ad order, production estimate, production order), subtype (media type / production type), type (specific or all), notes with keywords replaced at print (billing client name/tax ID/address/phone/contact; agency name/tax ID/address/phone; printing user, department, campaign responsible, group head; FX rate, VAT amount, invoice total, local & foreign totals, estimate contact).

### E15 Additional Data Field
Code (auto), description, type (numeric / alphanumeric / date), length, special category (billing prerequisites: required actions for owner/billing clients, mandatory attachments), vigent, scope (estimates / media plans / both) and owner-client list (empty = all). Referential only; not in standard reports.

### E16 Supplier Article (Mexico only)
Manual code (supplier's), description, single supplier, auto article number. Used as `Código SAP` in media plans.

### E17 Payment Term
Code (auto), description, days, vigent. Applies to billing clients.

### E18 Production Template
Name; grid of type groups/departments and production types. On an estimate, each type in the template becomes a separate line.

### E19 Promotion Staff (`Personal para Promociones`)
Contact code (new or existing contact), name, HR file number, birth date, payment branch, supplier (self-invoicing or representative supplier), notes; contact data; tax data (ID, responsibility, person type, income/VAT withholdings — only document type/number when invoicing via representative); bank data (Colombia).

### E20 Staff Request / Assignment
Estimate line, days, requested slots per day, person, chosen/reserve, self-invoice vs supplier, daily cost; evaluation fields per P41 stage 3.

**Key relationships:** JobNumber 1–N Estimates; Estimate 1–N Lines; Line N–1 Production Type N–1 Group; Line N–1 Supplier; Line 0–1 Royalty Contract (≤1 per estimate); Line 0–N quotations; Estimate 1–N POs; PO N–1 Supplier, PO lines ⊂ one estimate; Line 0–N Tasks; Estimate 0–N Advances; Supplier 0–1 associated Client; Override contract N–1 Supplier(as client).

---

## 4. Document lifecycles

### 4.1 Estimate (header) / line approval state machine
```
            [Draft/Saved]
         ┌──────┴────────┐
 A Presupuestar      Preaprobado
         │                 │
 PENDING_CLIENT_APPROVAL   │
         │ approve_by_client (role: Aprueba por Cliente; credit-limit check; snapshot initial version if auto)
         ▼                 ▼
     CLIENT_APPROVED  <────┘
         │ approve_for_billing (total or per line; role: Aprueba para Facturar)
         ▼
  APPROVED_FOR_BILLING (per line)  ──► INVOICED_TO_CLIENT (CxC)
```
- `disapprove_by_client`: CLIENT_APPROVED → PENDING_CLIENT_APPROVAL; blocked if any line approved for billing.
- `disapprove_for_billing` (total/line): APPROVED_FOR_BILLING → CLIENT_APPROVED; blocked for invoiced lines.
- `reject` (total/line) from any non-invoiced state → REJECTED; `recover` → previous state.
- `close` → CLOSED overlay (no edits); `open` → removes overlay.
- `void_and_replace` → source REJECTED + new estimate created.
- Supplier side per line: CHOSEN_SUPPLIER (needed if alternatives exist) → ORDERED (PO) → PO APPROVED (if mandatory) → INVOICED_BY_SUPPLIER.
- Manual "mark as invoiced" (client or supplier) can cancel pendings; user name recorded on the line billing tab.
- Pending reports expose three queues: pending client approval, pending billing approval, pending billing.

### 4.2 Purchase order
`NEW → SAVED/ISSUED → (APPROVED if mandatory)`; `→ ANNULLED` (only if no supplier invoice; supplier informed); `→ DELETED` (only if no supplier invoice; number reusable). Invoicing by supplier locks it until the invoice is removed or reversed by a credit note.

### 4.3 Advance
`PENDING_LEGALISATION → PENDING_COLLECTION → LEGALISED` (exact triggers not described; collection follows standard receivable).

### 4.4 Royalty contract
`ACTIVE (vigent) → EXPIRED / REPETITIONS_EXHAUSTED → EXTENDED (new contract created, old flagged as extended)`; delete only if not invoiced.

### 4.5 Override contract
`ACTIVE → monthly PENDING generated → INVOICED / CREDIT_RECEIVED / PROVISIONED`; `ANNULLED` cancels pendings (conditions retained); `DELETED` removes trace.

### 4.6 Masters
Most masters have a vigent/non-vigent flag; deletion only when unused.

---

## 5. Business rules and validations

**Header & numbering**
1. Estimate period may be moved within ±36 months of the current month, constrained by closed periods.
2. `Nº Estimado` resets monthly; `Nº Presupuesto` is a global monotonic number. Natural key = (period, estimate number) or presupuesto number.
3. Only open/vigent jobs can be assigned (on create and on copy).
4. A billable job allows cost and sale; a generic (non-billable) job allows cost only.
5. Payment terms default from the client and may be changed at any time.
6. Billing mode `Junto` puts investment and agency service on one invoice; `General` issues separate invoices.
7. Split-billing estimates require a split-type job, linked billing clients, and a split code with percentages.

**Line economics**
8. Cost and sale are entered net of VAT.
9. `Costo = Costo Unit. × Cantidad × Días`; `Venta = Precio Unit. × Cantidad × Días` (days only when relevant).
10. Line discount `Dto.` is a %; net sale = Venta × (1 − Dto/100). A production type identified as `Bonificada` (code 996) makes printing show final post-discount prices automatically.
11. Direct line: `Venta := Costo`; agency revenue comes only from agency service and/or supplier commission.
12. Agency service = Σ(eligible line sale) × `% Serv. Agencia` × (1 − `% Bonif`/100), where a line is eligible if `S.Ag.` is checked (default from the production type's `Comisionable` flag). Config can move the % to line level.
13. Optional cost-plus config: user sets cost and margin %; sale is computed (`Venta = Costo × (1 + %utilidad/100)` — exact formula not stated; markup-on-cost assumed).
14. Header income summary: income = (sale − cost) + agency service (+ supplier commission); margin % displayed.
15. Supplier commission: fixed amount or % of supplier cost; type "to define" allowed while negotiating; requires agency feature + client acceptance; collected via supplier credit note or agency invoice to supplier (supplier must be a billing client).
16. Each line has its own currency; foreign currency needs a controlled currency and reference FX; FX is re-entered at invoicing. One invoice holds one currency only → mixed-currency estimates produce multiple invoices.
17. Agency-performed lines use supplier `0000`.
18. Preproduction-type lines with a `Fotocromía` value spawn a separate photo-lithography line upon approval.
19. Cheque-tax production type (997, Argentina, when parameter on) auto-adds a line passing that tax cost to the job.

**Locks**
20. Lines invoiced to the client: sale price, discount, agency service and supplier commission are immutable.
21. Lines invoiced by the supplier: supplier and cost are immutable.
22. Closed estimate: no line may be modified or deleted.
23. First line of an estimate cannot be deleted (only modified).
24. Once a PO is issued, the supplier and cost of its lines are locked; changes require voiding/deleting the PO first.
25. A PO tied to a supplier invoice cannot be annulled/deleted until the invoice is deleted (month not pre-closed) or reversed by credit note.
26. Deleted line recovery is only possible before saving.

**Approvals & segregation of duties**
27. Client approval requires `Aprueba por Cliente` permission; billing approval requires `Aprueba para Facturar`; PO approval requires `Aprueba Ordenes de Compra de Producción`.
28. Vendor recommends that the creator not approve (internal audit); a special config enforces it (name not given).
29. Client approval is whole-estimate; reject lines not proceeding beforehand.
30. Billing approval can be total or per line (partial delivery).
31. Client approval is validated against the client's credit limit when credit limits are used.
32. Cannot disapprove by client if approved for billing; cannot disapprove for billing if invoiced.
33. Estimates pending billing approval cannot be invoiced.
34. Fee-contract-originated estimates are approved via the fee contract.

**Sourcing & purchasing**
35. Up to three alternative suppliers per line; until a chosen supplier is confirmed, no pending-to-receive exists and supplier invoices cannot be entered.
36. Award requires client approval.
37. PO cannot mix lines of different estimates.
38. PO cannot mix direct and indirect lines; bulk ordering auto-splits them.
39. PO in foreign currency only for currencies with system-managed daily FX.
40. If PO is mandatory, supplier invoices require an existing PO; if PO approval is mandatory, the PO must be approved first.
41. Reduced-VAT production types: the reduced rate flows to the client-side VAT on the estimate, to the PO, to supplier invoice booking and to client invoicing.
42. Production department users cannot see unit sale price or sale column; creative/normal departments can.
43. Attachments: levels 1–2 delete, 1–4 attach, 1–6 open.

**Royalties**
44. Requires `Control de Regalías`; royalty production type for estimates; supplier must be Production/Media type.
45. One royalty contract per estimate.
46. Extension only when not vigent / repetitions exhausted / assigned to material, and never extended before; modality immutable on extension; new number required.
47. Contract delete only if not invoiced.
48. Media plans reject materials whose contract validity does not cover the plan (validity intersection computed across contracts).
49. Expiry alerts only for month-based contracts.

**Override commissions** (deterministic engine, base = qualifying net or gross investment after `% de reducción`)
50. *Fixed %*: C = I × p.
51. *Value scale*: C = fixed amount of the bracket containing I.
52. *Absolute-% scale*: C = I × p(bracket of I).
53. *Marginal scale*: C = Σ over brackets of (portion of I in bracket × bracket %). Note: manual examples treat the first bracket as starting from 0 for the marginal portion (e.g., I = 3,000 → 2,000×5% + 1,000×3% = 130).
54. *Stepped scale*: C = I × p₁ + Σₖ≥₂ (I − lowerₖ) × (pₖ − pₖ₋₁) for each reached bracket k (e.g., 5,500 → 110 + 35 + 10 = 155).
55. Cap: cumulative C over the contract ≤ `monto límite`.
56. Validity ≤ 1 year; retroactive calculation allowed.
57. Eligible production types and client/product include/exclude lists filter estimates; contract currency does not filter.
58. Multiple contracts with one supplier are processed in `Orden Generación Pendiente`; later contracts subtract amounts from earlier ones.
59. Non-cut-off months: computed and provisioned, not billed.
60. Supplier must exist as billing client; contract type maps to GL accounts with obs. codes 23/U4/20.

**Masters**
61. Unique special identifications: only one production type each for 996, 997, 998, 999.
62. Supplier special types (other than Normal) can each be assigned once.
63. Supplier payable account change only if no movements; payments settle per payable account (two accounts with balance → two payment orders).
64. Supplier payment term with 0 days = cash.
65. Masters deletable only if unused (types: no estimates; payment terms: not on a billing client; suppliers: no movements; articles: not on a plan; entities: unused).
66. Price-list version auto-increments per client/code; no end date = valid until superseded; copy applies independent % uplifts to sale and cost.
67. Price-list lookup on a line: generic list shown first, then client list.
68. Additional-data fields are referential only (not in standard reports).
69. Observations are printed automatically and cannot be edited per document.
70. Ageing scales in reports must be built in descending positive day values; otherwise ageing fails.

---

## 6. Accounting and financial impacts

- **Client invoicing** of approved-for-billing lines posts revenue to the production type's sale account (obs 01 if bridge-account scheme, 20–23 if direct result accounts); agency service and investment may be separate invoices.
- **Supplier invoice entry** against estimate lines posts cost to the type's cost account, selected by job typology: normal/job-advertising (02 bridge / 39), non-rebillable (35), new business (37), own advertising (36). Payable goes to the supplier's indirect account (obs 30) or another assigned obs-30 account.
- **Discounts/bonuses** post to obs-23 account.
- Optional taxed/untaxed account split per production type.
- **Supplier commissions** (confidential): supplier credit note or agency invoice to supplier; shown on the line billing tab.
- **Override commissions:** income to contract-type account (23/U4/20); client refunds to defined account; provisions in non-cut-off months; credit notes may be netted in supplier payments.
- **Cost renderings:** balance-sheet obs-84 account (with per-user sub-accounts).
- **Advances:** treated as receivables; "cut-off date" mode reconciles against the GL account for *values to deposit*.
- **Month-end:** accounting uses the estimate state to accrue approved but unbilled work.
- **Event staff (CO/GT):** VAT withholdings to obs-19 account; equivalent document (`Documento Equivalente`) for unbilled eventual providers with sequential numbering.
- Direct lines: supplier invoices the client; agency books only its service/commission.

---

## 7. Cross-module handoffs

| To/From | Handoff |
|---|---|
| **Cuentas (Accounts)** | Job selection; tasks without cost linked to lines; account team handles client approval; pending reports also in Accounts menu. |
| **Medios** | Shared suppliers (type flags), royalty contracts/entities (media plan materials), additional data, observations, override numbering; supplier articles (MX) used in media plans. |
| **Gastos** | Supplier type `Gastos`; special suppliers for expense/petty-cash renderings. |
| **CxC billing** | Approved-for-billing queue; billing mode; client PO number; split codes; one currency per invoice; FX re-entry; reduced VAT; IIBB perception (AR); advances collected as receivables; "mark as invoiced to client". |
| **CxP** | Pending-to-receive after supplier choice/award; mandatory PO & PO-approval gates; supplier credit notes for commissions; "mark as invoiced by supplier"; reduced VAT booking. |
| **Tesorería** | Advances collection; cost-rendering settlement (payment order, bank account, cheque columns); override credit netting; supplier bank data for payment files. |
| **Contabilidad** | Production-type GL mapping (only editable from Accounting branch); automatic entries; month-end accrual; observation-code-driven account lists. |
| **Management** | Statistics, preliminary investment margin, Post Buy, dynamic reports, consolidated timesheet. |
| **Fee contracts** | Fee-originated estimates, fee instalments visible in pending reports (no cost). |
| **Home dashboard** | Royalty expiry alerts. |

---

## 8. Configuration parameters and country-specific behaviour

**Special configurations (Production group unless noted)**
- `Control de Regalías` / "Utiliza Regalías" — enables royalties.
- `Lista Precios Producción`; `Lista de Precios por Cliente` (true per client / false generic); `Lista de Precios por Tipo de Producción` (true per type / false per group).
- `Orden de Compra Obligatoria en Producción`.
- `Aprobación Obligatoria de Compra en Producción`.
- `Copias de Ordenes de Compra`.
- General › logo printing › `Orden de Compra = true`.
- Print formats for POs and estimates (Systems › print formats).
- `Genera Versión Inicial Automática` (Post Buy snapshot at client approval).
- `Usa Gestión de Eventos`.
- `Usa Módulo de Promoción` (enables type 998).
- `Impuesto al Cheque` (AR, enables type 997).
- Unnamed configs: line-level agency service %; additional description field; cost + margin → sale; creator ≠ approver enforcement; supplier commission collection mode.
- General › `Usa Documento Equivalente RS`, `Ultimo Código Emitido` (CO, GT).
- Cash & Banks › `Retención IVA Múltiple` (CO, GT).
- Bridge-account accounting scheme; taxed/untaxed account split; typology-based accounts (implementation-time).
- Sub-companies/divisions toggles filters.
- User permissions: `Aprueba por Cliente`, `Aprueba para Facturar`, `Aprueba Ordenes de Compra de Producción`; department type (Production / Creative / Normal) controls sale visibility; access levels 1–6 for attachments.

**Country behaviour**
- **Argentina:** IIBB perception on printed estimate (release 5.0+); supplier tax data (VAT withholding agent, income tax, SUSS social security, IIBB jurisdiction, multilateral agreement %, high-risk register, simplified regime, ARCA concept, CAI); CABA register import order (high-risk → exceeded magnitudes → general regime → reduced rates); apocryphal-invoice register sets supplier in conflict; cheque tax type 997.
- **Colombia:** event management (period request, staff assignment); equivalent document for unbilled providers; multiple VAT withholding accounts (obs 19); supplier bank data for payment interfaces; national VAT on foreign supplier invoices at production-type rate.
- **Guatemala:** equivalent document, multiple VAT withholding.
- **Mexico:** supplier articles (`Código SAP`); person types including RESICO and moral persons.
- **Chile:** multiple supplier bank accounts from a bank list file for supplier payment lists.
- **Puerto Rico:** IVU applicability per production type.
- Foreign suppliers: tax ID up to 20 characters.

---

## 9. Reports, queries and KPIs

| Report | Purpose / key filters | Output columns / KPIs | Source |
|---|---|---|---|
| Advances list | General or by client (billing/owner, range), dates, together/separate, current vs cut-off date (GL reconciliation), state, currency mode (single / consolidated with revalued amount), currency filter, ageing breakdown (by due, accounting or real date; custom descending buckets) | Request no., date, month/year, estimate, line, description, subject, amount, state, job, product, days overdue, due date, receipt, ageing buckets | `mp302694.html` |
| Production statistics | 12 grouping modes (by type, group, client×product, types×client, total investment by client, supplier×client, type×estimate, type×supplier, group×estimate, macro-group×product-group, type×product); client type; group/type; direct/indirect; department; with agency service; month range; state options (include/only pending client approval, pending billing approval, agency costs, only ordered); currency mode; division; chart | Type, detail, cost, sale, result, agency service, task date → profitability by service | `mp301254.html` |
| Preliminary investment list | Date criterion (creation / client approval / billing approval), invoice type, estimate state, department, scope (supplier, billing client, product, all, owner, product group, client group, macro group), currency, division | Margin from cost difference, agency commission, fee; cycle times creation→client approval→billing | `mp301650.html` |
| Estimates with internal costs | Month range, owner clients, together/separate, groups/types, currency mode | Estimate, type, cost, sale, margin for agency-performed lines | `mp301357.html` |
| Pending workbench | See P24 | Queues + ageing by type group; bulk actions | `mp301130.html` |
| Dynamic production report | Field picker (data & calculated: estimate, line, amounts), templates, filters (months, owner & billing client, include discounted), pivot; online vs offline dataset; weekly scheduled generation at 00:00; use consolidated fields for multi-currency (e.g., consolidated net billable) | User-defined | `mp402832_2.html` |
| Consolidated timesheet dynamic report | Hours by collaborator across group companies; filters (dates, owner client, collaborator, category, currency); pivot vs grid; templates; scheduling | Hours, cost by collaborator/client | `mp302855.html` |
| Estimate list (complete) | Date or creation date; criterion (supplier, billing client, product, owner, product group, client group, macro group, type group, job); direct/indirect; fee include/exclude/only; rejected include/exclude/only; cost (with/without/no value); department, production department, responsible; open/closed; options (only pending client approval, exclude, only non-billable, amount ≠ 0); currency (single with FX columns / consolidated at estimate FX); division | Client invoice (red if manually marked), approval & collection dates, last modified, observations, VAT on agency service, discounts, job theme, approver; per-line breakdown with editable client PO; actions: print selected, export, pivot, copy, void-and-replace | `mp301173*.html` |
| PO list | Date criterion (issue month, estimate creation, PO creation), estimate state, invoiced to client, invoiced by supplier, PO state; entity filters | PO grid, creator, type group, type, supplier invoice details | `mp302743.html` |
| POs pending generation | Criterion (user/supplier/all), direct/indirect, dates, exclude zero, client-approved only (default), only invoiced, non-billable job, include event suppliers, billing client, division | Lines without PO | `mp301358.html` |
| Cost-rendering control | See P27 | Pending renderings and advances | `mp301547.html` |
| Royalty contract list | Start/end validity, contract date, responsible, supplier, client | Contracts | `mp301524.html` |
| Post Buy | Initial vs current version; cost or sale variance | Negotiation variance per line | `mp301003.html` |
| Supplier list | Grouping, custom views, auto-filters | Supplier master | `listado-de-proveedores.html` |

**KPIs derivable:** gross margin by production type/client/supplier; agency service income; supplier commission income; cycle time (create → client approval → billing approval → invoice); backlog of approved-unbilled (accrual); POs pending generation; ageing of pending approvals; Post Buy savings; override commission earned vs cap; advance ageing; staff evaluation score.

---

## 10. Agentic-skill implications

### 10.1 Atomic agent jobs (candidate skills)
1. `estimate.create` — build header from job + client defaults; validate job vigent/billable; set approval type.
2. `estimate.add_line` (variants: indirect, direct, agency-internal, cost-rendering, price-list, royalty, event-staff).
3. `estimate.apply_template` — expand production template to lines.
4. `estimate.price_from_list` — resolve generic vs client list, version and validity.
5. `estimate.compute_totals` — deterministic totals/margin (tool).
6. `sourcing.request_quotes` — build quotation matrix, generate supplier RFQ documents/e-mails.
7. `sourcing.award` — choose quantity/supplier (cheapest by default, explain trade-offs from observations).
8. `sourcing.choose_supplier` — set `Proveedor elegido` among ≤3 alternatives.
9. `approval.client` / `approval.client_revert` — with credit-limit check and Post Buy snapshot.
10. `approval.billing` (total/line) / revert.
11. `estimate.reject` / `recover`, `close` / `open`, `copy`, `void_and_replace`, `update_header` (client PO).
12. `po.generate` — split by estimate, supplier, direct/indirect; compute VAT (reduced rates).
13. `po.approve`, `po.send` (PDF + e-mail), `po.void` / `delete` with invoice-link check.
14. `advance.request` and `advance.monitor`.
15. `royalty.create` / `extend` / `link_to_line` / `expiry_watch`.
16. `override.define_contract`, `override.run_monthly` (pending/provision), `override.bill_or_credit`.
17. `events.request_staff`, `events.assign`, `events.evaluate`, `events.replace`.
18. `reports.pending_queues`, `reports.margin`, `reports.post_buy`, `reports.po_pending`, `reports.renderings`.
19. `masters.*` maintenance with unused-before-delete checks.

### 10.2 Required inputs (minimum)
Job (client, product, billable flag, typology, division, split code), production type catalogue with flags and GL mapping, supplier master (type flags, payment terms, tax data, e-mail), client master (payment terms, credit limit, accepts supplier commission), currency table with daily FX, user permission matrix, config flags (§8), price lists, contracts.

### 10.3 Deterministic calculations worth a tool
- Line totals (unit × qty × days, discount), direct-line sale=cost.
- Agency service with bonus discount and line eligibility.
- Margin/income summary; cost-plus sale computation.
- Supplier commission (fixed / %).
- Multi-currency conversion and "one currency per invoice" grouping.
- Billing split across clients by split code %.
- PO grouping (estimate × supplier × direct/indirect) and VAT (incl. reduced rates).
- Override engine: five scale methods, reduction %, net/gross base, cap, precedence, cut-off/provision.
- Royalty validity: month-based expiry date, repetition counter, validity intersection across materials.
- Ageing buckets (descending scale validation).
- Post Buy variance (initial vs current per line, cost and sale).
- Event cost: people/day × days × daily cost; evaluation % aggregation.

### 10.4 Controls and approvals (human-in-the-loop)
- Enforce maker ≠ checker for client approval, billing approval, PO approval.
- Credit-limit check before client approval.
- Hard locks (R20–R26) as preconditions to every mutating tool.
- PO-mandatory / PO-approval-mandatory gates before supplier invoice entry.
- Confidential commission visibility restricted; production-department users never see sale values.
- Royalty validity check before media/estimate assignment.

### 10.5 Exceptions to flag
- Lines with multiple alternative suppliers but no chosen supplier (blocks CxP).
- Client-approved lines without PO when PO is mandatory; POs unapproved.
- Commission type "to define" lingering (periodic review recommended).
- Estimates on generic jobs carrying sale values; jobs closed while estimates open.
- Mixed currencies → multiple invoices.
- Approved-for-billing but not invoiced past threshold (accrual).
- Post Buy negative variance (sale down / cost up) beyond tolerance.
- Royalty contracts near expiry or repetitions exhausted; materials out of validity.
- Override cumulative commission near cap; months provisioned but not billed.
- Supplier in conflict (apocryphal list) or expired CAI/register.
- Cost renderings and advances pending closure; overdue advances.
- Manually "marked as invoiced" lines (bypass of automatic flow).
- Tasks not linked to any estimate (unquoted/unbilled work leakage).
- Event staff no-shows / low evaluation, reserves activated.

---

## 11. Gaps and ambiguities

1. **Academia pages** (concepts, how to create an estimate, loading example, approval circuit, cost rendering, estimate analysis, tips) contain only video titles; no content available.
2. **Post Buy de Producción**, **Reporte Dinámico de Medios** (listed under Presupuestación), **Plan de Producción** (empty page) and **Listado de Presupuestos (Básico)** have no help content here.
3. Exact formula for cost-plus pricing (markup on cost vs margin on sale) not stated.
4. Whether agency service is computed on sale before or after line discount, and how `% imprevistos` (contingency) and creative idea % enter totals, is unspecified.
5. Advance lifecycle triggers (what "legalised" means — matched to invoice?) and how an advance is created from an estimate are not described in this group.
6. The configuration that enforces creator ≠ approver, line-level agency %, additional description field and cost-plus mode are referenced but unnamed.
7. Activities/stages on lines are "not in use"; linkage semantics with costed tasks unclear.
8. Line-level state model (vs header) is implied by per-line billing approval and rejection; precise aggregation rules for header status not given.
9. Marginal-scale examples imply the first bracket starts at 0 although the table says 1,000; edge handling of bracket boundaries ("1,999" vs "2,000") and amounts below the first bracket are undefined.
10. Override "client refund" mechanics (proportional to which investment, document type) not detailed.
11. Credit-limit validation rule (exposure formula) not described here.
12. Whether PO amounts must equal line cost, and tolerance between PO and supplier invoice, is not stated (only "detect differences").
13. The relationship of `Entrega y Evaluación` (called "third stage") with the staff master page (also called "third stage") is inconsistent in the manual; stage 1/2 boundaries are inferred.
14. Rounding rules and decimal precision for currency and taxes are not mentioned.
15. Month-end accrual mechanics (journal entry, reversal) are only mentioned as a use of the estimate data.
16. Royalty contract usage counting for repetition-based contracts (where repetitions are decremented — media plan spots?) is not specified.
17. Duplicate menu path: royalty contracts are accessed under Presupuestación in this file but guides cite Compras; treat as the same screen.
