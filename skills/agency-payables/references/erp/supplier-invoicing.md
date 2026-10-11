# Accounts Payable › Supplier Invoicing (`Cuentas por Pagar › Facturación Proveedores`)

> **Provenance.** Functional reverse engineering of a reference agency ERP, derived from its publicly accessible help documentation (reviewed 2026-10-11). Content is paraphrased and restructured; it is not vendor documentation, source code or an endorsement. Bracketed ids such as `[mp301010]` identify the source page used as evidence. Items marked *inferred*, *assumed* or listed under gaps must be validated with your own controller, tax adviser and system owner before they drive postings or payments.

> Reverse-engineered functional specification for an open-source, agentic re-implementation of an agency ERP's supplier-invoice circuit. All text is an original paraphrase of the source help manual's behavior. Spanish UI/field names appear in backticks only as identifiers. Source references use the help-file id in square brackets (e.g. `[mp301321]`) or the user-guide slug.

---

## 1. Purpose and position in the end-to-end circuit

The Supplier Invoicing area is where an agency turns **commitments it made to third parties** (media insertion orders, production purchase orders/budgets, expense requests) into **recognised payables**. It is the "three-way match" gate between:

- **Upstream commitments**: media plans and advertising orders (`Órdenes de Publicidad`, OP), production estimates/budgets and their purchase orders (`Presupuestos de Producción`, `Órdenes de Compra`, OC), expense requests (`Solicitudes de Gastos`).
- **Downstream settlement**: payment orders and payments in Treasury (`Órdenes de Pago`), withholding certificates, tax ledgers (purchase VAT book), and the general ledger.
- **Sideways to the client**: client rebilling of differences, credits passed to clients (volume rebates, cancelled pendings), direct-billing scenarios where the supplier invoices the client directly, and supplier-commission/incentive income.

Core jobs of the module:

1. Maintain a **"pending to receive" (`pendiente de recibir`) balance** per order/budget/request line, created when the commitment is approved/issued and consumed when supplier documents are registered.
2. **Control** each incoming supplier document against that pending balance at the finest grain (spot/insertion for media, item for production, request line for expenses), recording **differences** (rate, size, quantity, discounts, reprogramming, adjustments, deficiencies) that stay open until a credit/debit note arrives or a user writes them off.
3. **Register** the document: post the accounting entry automatically, derived from the media type / production type / expense concept so the AP clerk never chooses accounts on automatic loads.
4. Capture **taxes**: VAT (`IVA`) per rate, perceptions (`percepciones`), withholdings (`retenciones` — income tax/Renta/ISR/Ganancias, VAT, ICA, IIBB) with country-specific behaviour, including fiscal-authorisation codes (Argentina CAI/CAE) and electronic support documents (Colombia).
5. Handle **special flows**: advance purchases of media and their consumption, supplier commissions (`confidencial`/overcommission) received as credit notes, volume rebates received as credit notes (agency- or client-owned, optionally passed through), full cancellation credit notes, write-off of pendings that will never be invoiced.
6. Provide **control reports**: invoices to receive, pending differences, supplier-vs-client invoice cross-reference, purchase VAT book, withholding summaries, costs by supplier, incentive reports.

Position in the E2E circuit:

```
Client brief → Estimate/Media plan → Client approval → OC / OP issued
   → [pending to receive created]
   → Supplier document received (optionally pre-received in "Recepción de Facturas")
   → CONTROL (match, differences)  → REGISTER (GL + AP subledger + taxes)
   → Differences: await NC/ND  | or write off | or rebill client
   → Retention approval (some countries) → Payment Order → Payment → Certificates
   → Client billing / direct-billing "trasladada" status → Close (pre-close / close)
```

---

## 2. Process catalogue

Conventions: **Actor** = AP clerk unless noted. Every registration process ends with the common **Save sequence** (S-SAVE) described once below. Every process that records a document header uses the common **Header capture** (S-HDR) and, in Argentina, the **Fiscal-code capture** (S-CAI).

### 2.0 Shared sub-procedures

**S-HDR — Document header capture** `[mp301321]`
- Inputs: supplier (`Proveedor`), load type (`Tipo Carga`), document type (Factura / NC / ND / Factura de crédito / Anexo in MX), letter and point-of-sale-number (`Letra`, `Punto de venta-Número`, Argentina only), regulatory document class (`Comp. RG1361`, Argentina), accounting date (`Fecha Contable`, drives the tax/GL period), document date (`Fecha del Comprobante`, issue date), payment term (`Plazo de Pago`, defaulted from supplier master; editing term recomputes due date and vice-versa), due date (`Fecha de Vencimiento`), currency of the document (`Moneda`) and exchange rate (`Cotización`, only for foreign currency in either the document or the order currency), declared grand total including taxes (`Importe Total`), non-computable amount for simplified-regime suppliers (`Importe No Computable`, Argentina monotributo / Chile), free-text remarks (`Observaciones`, later filterable in ledger enquiries).
- If the document was pre-received in the **Supplier Invoice Reception** screen (`Recepción de Facturas de Proveedores`, outside this group), header data auto-populates.
- Order currency (`Moneda Ord.`) — the currency in which the commitment was raised — is chosen in the Budget Control filter bar and represents the currency of the debt.

**S-CAI — Fiscal authorisation code (Argentina)** `[mp301321]`
- Shown for every invoice type except class "C". Fields: requires code (`Requiere C.A.I`), fiscal printer (`Controlador Fiscal`), billing type (manual / electronic / fiscal printer), active code (`C.A.I vigente`), new code + expiry (saved to the document and to the supplier master), CAE for e-invoices. Optional online validation against the tax authority with printable result.

**S-SAVE — Save and post**
1. System recomputes the detail total (net + VAT + perceptions + extra lines − withholdings where applicable) and compares it with `Importe Total`. Mismatch ⇒ blocking message, unless within the automatic rounding threshold (see R-12).
2. Optional extra lines may be added at the bottom of the summary grid: tick the line, enter work order (`OT`) which fills the `JobNumber`, choose account (tax perception or cents difference), VAT account (`0000` = not subject), amount. With configuration "automatic tax load" (from v4.6) a **Taxes** button inserts the perception line automatically against the agency's generic job/OT.
3. Colombia and Mexico: withholdings (income/Renta and VAT) are computed here; user confirms which withholdings apply.
4. Supplier fiscal-status check: warning if the agency has not validated the supplier against the tax authority (validation lives in the supplier master).
5. Final confirmation: Yes ⇒ posted to GL and AP subledger; No ⇒ stays unsaved for correction.

### 2.1 Invoice / load types (`Tipo Carga`)

When a supplier is chosen the system detects which pendings exist and enables only the matching automatic load types, plus manual types for unforeseen documents. A filter `Sólo Facturas Automáticas` must be unticked to expose manual types.

| Code | Load type (UI name) | Pending consumed | Grain |
|---|---|---|---|
| LT-MED | Automatic control & entry — media invoices | OP pending | spot/insertion (`aviso`) |
| LT-MED-NCND | Automatic control & entry — media NC/ND | OP **difference** pending | spot |
| LT-PRD | Automatic control & entry — production invoices | budget/OC pending | budget item |
| LT-PRD-NC | Automatic control & entry — production credit notes | budget **difference** pending | item |
| LT-VOL | Automatic control & entry — volume credit notes | none (computed on orders of a period) | order/spot |
| LT-GTO | Automatic control & entry — expense invoices | expense-request pending | request line |
| LT-COM-PRD | Credit note for commission — production suppliers | agreed commission on estimate items | item |
| LT-COM-MED | Credit note for commission — media suppliers | agreed commission on orders | order |
| LT-MAN-PRD | Manual entry — production invoices | none | free lines |
| LT-MAN-MED | Manual entry — media invoices (also used for advance purchase) | none | free lines |

### 2.2 Process list

---

**P-01 Control and register a media invoice without differences** `[registrar-una-factura-de-una-orden-de-publicidad-sin-diferencias]`, `[mp301321]`
- Trigger: supplier invoice matching one or more issued OPs exactly.
- Steps: S-HDR (LT-MED) → S-CAI → Budget Control filters: period from/to (months) and optional day range 1–31 (weekly/fortnightly billing), origin = `Factura`, direct/indirect, pass-through flags (see R-20), order currency, billing client, media outlet (`Medio`, when supplier has several), option `Versión Final` → **Start** → *Order selection* window (orders colour-coded: red = controlled & closed, black = open/uncontrolled, blue = partially closed; recommendation: invoice only closed orders) → *Movements* tab: tick spots (double-click header selects all) → *Summary* tab: add perceptions if any → S-SAVE.
- Outputs: posted invoice; OP pending reduced to zero for the selected spots; tab `Control de Medios` on the invoice lists the controlled spots.
- State: OP line pending → invoiced; order locked if `Versión Final`.

**P-02 Control and register a media invoice with differences** `[registrar-una-factura-de-ordenes-de-publicidad-con-diferencias]`
- As P-01, but in Movements the clerk overwrites billed values per spot: number of spots (`Avi.`), columns (`Col.`), duration (`Dur.`), rate (`Tarifa`), and each of up to four cascaded discount percentages (`1°–4° Dto.`).
- Each override generates a **difference record** shown in tab `Diferencias`; it becomes a new pending (to receive NC or ND) from the supplier.
- Output: invoice posted at billed amount; difference pending opened (positive or negative).

**P-03 Media invoice with discounts shown as one global line** `[registrar-una-factura-de-una-orden-de-publicidad-con-los-descuentos-discriminados-en-una-linea]`
- Clicking a discount column header moves that discount from per-spot netting to a single "Discounts" line under the subtotal (percentage shown in a second column group); clicking again in the second group reverts.
- Variant: discounts arrive as separate credit notes — right-click moves the discount to a second group so the invoice is booked gross and the discount awaits an NC.

**P-04 Control a media invoice without registering it** `[controlar-una-fc-de-medios-sin-registrarla]`
- Steps as P-01/P-02 up to Movements, then **Save Control** (`Grabar Control`) and Cancel. The control (selected spots + differences) is persisted without posting.
- Purpose: separate the operational control (planner/buyer) from the accounting registration.

**P-05 Register a previously controlled media invoice** `[registrar-una-fc-de-medios-controlada-previamente]`
- S-HDR → **Recover Control** (`Recuperar Control`) loads saved movements → optional further differences → perceptions → S-SAVE.

**P-06 Re-appropriate a media invoice first entered manually** `[controlar-una-factura-de-medios-ingresada-previamente-en-forma-manual]`
- Prerequisite: invoice already posted via LT-MAN-MED (fast entry without control).
- Steps: LT-MED with option `Reapropiar Factura` → enter invoice number (header reloaded) → Start → select orders and spots, record differences → Save.
- Effect: the manual accounting entry is **reversed** and replaced by the controlled, order-linked entry. Documented as an Argentina option in the overview.

**P-07 Register an NC/ND for pending media differences** `[registrar-una-nd-o-nc-por-diferencias-pendientes]`
- LT-MED-NCND → S-HDR/S-CAI → Start → select orders with differences → Movements: tick → perceptions → S-SAVE. Consumes the difference pending. The clerk can create new differences if several credits together make up the pending.

**P-08 Control (only) a media differences document** `[controlar-un-comprobante-por-diferencias-de-medios]` and **P-09 register it later** `[registrar-un-comprobante-por-diferencias-de-medios-controlado-previamente]`
- Same split as P-04/P-05 but on LT-MED-NCND; adjustments on spots/columns/duration/rate/discounts against the pending difference.

**P-10 Control/register a document for extras not contemplated in an already-registered invoice** `[controlar-un-comprobante-por-adicionales…]`, `[registrar-un-comprobante-por-adicionales…]`
- Prerequisites: original invoice registered with no differences marked; supplier now sends an additional invoice.
- Steps: LT-MED with Budget Control origin = **`Diferencias`** → select orders (amounts appear as zero because nothing is pending) → enter billed spots/rate/discounts → Save Control or Save. Creates and consumes a brand-new difference that did not exist in the order.

**P-11 Media invoice applying an advance purchase** `[registrar-facturas-de-ordenes-de-publicidad-aplicando-anticipos]`, `[ingresar-un-comprobante-de-medios-relacionado-a-una-compra-anticipada]`
- LT-MED with `Compra Anticip.` = Yes → enter original advance-invoice number (F2 lists advance invoices of supplier + medium) → system shows remaining balance (`Saldo`) → choose order currency and medium → continue as P-01/P-02. On save the summary includes a negative "advance purchase" line; the invoice nets to zero and the advance balance decreases. If the advance has no remaining balance the system blocks the operation.

**P-12 Register an advance-purchase invoice for media** `[ingresar-una-factura-de-compra-anticipada-de-medios]`, `[compra-anticipada]`
- Trigger: annual contract with a media supplier, invoiced upfront before plans/orders exist.
- Prerequisite: a balance-sheet account (asset/liability) with observation code **89** ("account for advance purchase"), flagged for the suppliers module; default VAT account attached.
- Steps: untick `Sólo Facturas Automáticas` → LT-MAN-MED → S-HDR/S-CAI → tick `Compra Anticipada` in Budget Control → choose media outlets covered (default: all outlets of the supplier) → Start → Summary lines: JobNumber (via client→product→job lookup; generic agency job/OT allowed), OT, detail, account = code-89 account, VAT account (`0000` if exempt), net amount (VAT auto-computed) → S-SAVE.
- Accounting: Dr advance-purchase (code 89) + VAT / Cr media supplier.

**P-13 Credit note cancelling the unconsumed advance purchase** `[mp309266]`
- Query the advance invoice (supplier list limited to those with advance invoices; F2 lookup) → enter NC number, payment term, accounting date, real date, due date, RG1361 class (AR) → confirm that the remaining balance equals what is being credited → optional attachment → fiscal-status check → confirm. Closes the advance circuit (balance = 0).
- Partial variant: button `Modificar Saldo a Anular` (on querying an NC of this kind) allows crediting less than the remaining balance.

**P-14 Register production invoice (full)** `[registrar-facturas-de-presupuestos-de-produccion]`
- Preconditions (R-30): external supplier assigned to items; budget client-approved; OC issued (and approved) if the agency enforces mandatory/approved OCs.
- Steps: LT-PRD → S-HDR (+ choice of bonus counter-account `Contra Cuenta Bonif.`) → S-CAI → Budget Control: period, direct/indirect, pass-through flags, order currency, billing client, production type filter, option `Incluir Ítems sin Costo` (not in Colombia) → Start → *Production estimates selection* → Summary: tick budgets/items, override VAT account if billed rate differs from budgeted (VAT recomputed) → perceptions → S-SAVE.

**P-15 Register a partial production invoice** `[registrar-facturas-parciales-de-presupuestos-de-produccion]`
- As P-14 but the clerk types the billed net in `Importe` (and VAT if different). On save, the remaining pending to receive is updated (stays open for later invoices).

**P-16 Register production invoice above budget** `[registrar-facturas-de-presupuestos-de-produccion-por-un-importe-mayor-al-presupuestado]`
- Clerk enters a billed amount greater than expected; on save the system creates a **pending to receive a credit note** from the supplier for the excess. (Manual example: invoice 22,000 + VAT against expected 20,000 + VAT, NC of 2,000 + VAT expected later.)

**P-17 Register production NC for budget-vs-invoice differences** `[registrar-nc-por-diferencias-entre-el-presupuesto-de-produccion-y-las-facturas-recibidas]`
- LT-PRD-NC → header → Start → select budgets with differences → tick differences, adjust VAT account/amount → save ⇒ cancels the NC pending. Entering a smaller amount creates a further residual difference.

**P-18 Register expense invoice** `[ad_cap_gus_cpp_04…]`
- Trigger: supplier has a pending expense request (`Solicitud de Gastos`) or service OC.
- Steps: LT-GTO → header/CAI → order currency → Start → *Expense requests selection* (multiple requests per invoice allowed) → Summary: tick lines, confirm/replace VAT account, optional `Deducible` flag (deductible for income tax) → perceptions → S-SAVE.
- Restriction: **no partial invoices** of a standard expense request.

**P-19 Register multiple invoices against one expense request** `[ad_cap_gus_cpp_05…]`
- Prerequisite: approved expense request configured for multiple supplier invoices.
- After selecting the request a *Distribution* window asks for invoiced net total and its split by cost centre (`Nº C.C.`), JobNumber, amount, division. On save the system **spawns a child expense request** for the invoiced amount, linked to the original, and deducts it from the original (visible in `Solicitudes Generadas`).

**P-20 Manual production invoice (no pending)** `[ingresar-comprobantes-de-produccion-sin-control-automatico]`
- Untick automatic-only → LT-MAN-PRD → header/CAI → Start → Summary: one line **per VAT rate**: JobNumber (F3 = default generic job; F2 cascade client→product→job; division if enabled), OT, detail, account, VAT account (`0000` exempt), net (VAT auto), cost centre (only for P&L accounts). Choosing a **cost account** pops a production-type selector so reporting by production type stays consistent → S-SAVE.

**P-21 Manual media invoice (no pending)** `[ingresar-comprobantes-de-medios-sin-control-automatico]`
- Same as P-20 with LT-MAN-MED; choosing a cost account pops a **medium** selector.

**P-22 Agency volume-rebate credit note** (four origin variants) `[registrar-nc-por-volumen-de-la-agencia-…]`
- LT-VOL, Budget Control `Selección` = `Volumen Agencia`, plus `Origen`:
  - `General por Mes`: all orders with the supplier/medium in a date range (whether invoiced or not).
  - `Factura`: orders included in a given supplier invoice (`Nº Factura`).
  - `Orden`: orders hand-picked in a selection window.
  - `Importe`: a fixed credit amount distributed **proportionally to order amounts** across selected orders.
- Percentages: up to four volume-discount percentages (summed) define the expected credit; optional `Transfiere al Cliente` with `% Traslado` (share of credit passed to client) and `% Cliente` (per-percentage client share, may be derived as discount% × traslado%) — or `Importe Cliente` in the amount variant.
- Counter-account (`Contra Cuenta`): cost account (reduces cost), bonus account of the media type (`Bonificaciones`), or any account (`Cuentas varias`).
- Spot-level control shows ordered amount, base for the rebate, VAT per item; editing the received amount wipes pre-entered discounts and recomputes a single effective percentage (R-15).
- Output: posted NC; if transferred, a **difference in favour of the client pending to invoice** (credit to client).

**P-23 Client volume-rebate credit note** (same four variants) `[registrar-nc-por-volumen-del-cliente-…]`
- `Selección` = `Volumen Cliente`; a billing client must be chosen; otherwise identical mechanics to P-22.

**P-24 Supplier commission credit note — production** `[registrar-nc-por-comisiones-de-proveedores-de-produccion]`
- Preconditions: special configuration "supplier commission = receives NC" with per-item collection = no, **or** "supplier commission = bills commission" with per-item collection = yes (each budget/plan item decides); bonus account defined on the production types; client-approved budgets with items flagged "receives supplier NC".
- Steps: LT-COM-PRD → header with `Contra Cuenta Bonif.` = No → Start → select estimates on which commission was agreed (`confidencial`, regardless of whether the supplier has invoiced the item) → tick commission lines, adjust VAT → perceptions → S-SAVE.

**P-25 Supplier commission credit note — media** `[registrar-nc-por-comisiones-de-proveedores-de-medios]`
- Same with media types' bonus account and OPs. Note: when the credit was computed on ordered amounts but the controlled investment turns out lower, the user can register with **initial version** and later adjust with a debit/credit via the comprobante field.

**P-26 Register in a pre-closed month** `[registrar-comprobantes-en-meses-con-pre-cierre]`
- Preconditions: suppliers pre-close done but not accounting close; user has permission `Puede Ingresar Facturas Luego del Pre-Cierre`.
- On entering an accounting date in a pre-closed month: warning → question whether to enter local-currency documents affecting **balance-sheet accounts only** → Yes. Restriction: must not hit P&L accounts.

**P-27 Automatic cents rounding** `[generar-redondeo-automatico-de-centavos]`
- Prerequisite: rounding configured with max amount and rounding account.
- On save with a difference ≤ threshold: message offers to correct the total or accept as rounding → Accept → button `Ajuste Redondeo` inserts a line to the rounding account → save.

**P-28 Query / modify / delete supplier documents** `[mp301075]`, `[eliminar-facturas-contabilizadas-de-proveedores]`
- Query by supplier + doc type + number (F2 = indirect list; F3 = direct invoices that do not pass through the agency, Mexico).
- Tabs: Amounts (total, unpaid balance `Saldo Impago`, balance without payment order `Saldo sin Orden de Pago`), Other data, Remarks, Claims (from supplier web portal), Concepts (GL entry summary), Divisions, Media control, Differences, Work-order movements (OT, client, account, amount, JobNumber, expense request, division, cost centre, product), Expense requests, Detail.
- Modify: only due date and remarks; accounts and amounts are immutable.
- Delete: removes the document entirely, its GL entries, and **re-opens the pending** on the plan/estimate. Not allowed if paid or if in a pre-closed month.
- Also hosts: withholdings window (CO/MX/DO/PE/GT), income-tax base window (CO accumulated monthly with deductions), attach scanned original, print voucher, export grids.
- Retention approval workflow (CL, PE, CR — see R-41).

**P-29 Full-cancellation credit note** `[mp301342]`, `[ingresar-una-nc-anulando-un-comprobante-de-un-proveedor]`
- Not available in Colombia, nor for suppliers flagged "special supplier"; applies to production or media invoices.
- Query invoice/ND (or Anexo in Mexico) → enter NC number, term, dates, RG1361 (AR) → confirm remaining balance equals invoice total → **Confirm NC** (warns if a payment order exists, which would be left without backing) → fiscal check → confirm.
- Effect: posts NC, **releases the linked OC/OP back to "pending to receive"**, allowing plan/budget edits. Generates an internal **association adjustment entry**.
- Undo: to delete such an NC, first annul the association adjustment entry, then delete the NC, then manually mark the orders as invoiced by the supplier (system cannot re-link them).
- Colombia variant: two-step provisional/definitive approval of supplier adjustment notes with notification and rejection reason sent to the supplier; alert "NC anula fc pending approval".

**P-30 Mark pendings as not invoiced by the supplier (write-off)** `[mp301345]` + four guides
- Purpose: acknowledge a pending to receive will never arrive (typical: cleansing old periods). No GL entry is generated; the effect is a margin change on the job.
- Media: LT-MED-like screen, header without document data (optionally a reference invoice number via special config) → orders → select spots → Summary → Save ⇒ difference between planned and ordered recorded on the OT and plan, with user stamp.
- Production: select budgets → set amount to cancel (total or partial) → Save ⇒ difference between budget and order, user stamp.
- Option `Transfiere al Cliente`: creates a **credit pending to invoice to the client** for the amount the supplier will not bill.
- Differences in a budget: from *Production invoices to receive* report tick the column next to `% Dif.` → `Aceptar Diferencias`.
- Media differences: from *Pending plans list* (Diferencias Pendientes de Facturar) — first decide client side (`Grabar Diferencias`), then supplier side (`Selecc.` → Grabar) which cancels the supplier pending and creates a pending to invoice the client; optionally then cancel the client pending too.

**P-31 Write off pending differences from the differences report** `[mp301373]`
- In *Pending billing differences* tick differences and Save ⇒ removed from pending with direct P&L effect (no document expected). Reversible from report `[mp302731]` via `Desmarcar`.

**P-32 Reconcile planner-approved supplier invoices** `[mp302863]`
- Screen posts supplier invoices already approved by planners (only a one-line description is available).

**P-33 Media invoices (new screen)** `[mp302941]`
- Newer media-only control/registration screen with the same automatic vs manual entry principle (portal Liveranto mentioned). Details not documented.

**P-34 Follow-up management of clients and suppliers** `[mp302789]`
- Configurable management types and actions (e.g., chasing missing certifications, tax info, documents). Criteria: next action, overdue next action, no action, finished. Comments with next-action date and contact; Finish action.

---

## 3. Entities

| Entity (ES / EN) | Key fields | Identifier | Relationships |
|---|---|---|---|
| `Proveedor` / Supplier | name, tax id (CUIT/NIT/RFC), tax condition (registered, exempt, monotributo, foreign), billing type (manual/electronic/fiscal printer), active CAI, payment term, integrating AP account (`Cuenta Contable`, obs. code 30), retention concepts, special-supplier flag, intercompany flag + code, local establishment / tax-residence cert (CR), fiscal-validation status | supplier number | has media outlets; linked billing clients; many documents |
| `Comprobante de Proveedor` / Supplier document | type (FC, NC, ND, Factura de crédito, Anexo), letter, POS-number, RG1361 class, accounting date, entry date, document date, due date, receipt date (`Fecha Contrarecibo`, MX), currency, rate, total, taxable (`Gravado`), exempt, VAT, VAT perception, IIBB perception, withholdings (Renta/IVA/Ganancias/ICA), non-computable, unpaid balance, balance without PO, load type (auto/manual), loading user, batch number, remarks, CAI/CAE, direct/indirect, `Pasa por Agencia`, `Pasa sólo el IVA`, `Trasladada`, `Versión Final`, advance-purchase link, country fields (NCF, control no., service type, resguardo no., electronic flag, annulled flag) | supplier + type + letter + number | lines; GL entry; links to OP/OC/requests; payment orders; claims; attachments |
| Document line (`Movimiento`/`Resumen`) | check, JobNumber, OT, detail, account, account description, VAT account, net, VAT, cost centre, division, deductible flag, production type / medium (for cost accounts) | doc + line no. | job, OT, account |
| `Orden de Publicidad` (OP) item / spot | month, OP no., plan no. (`Pta.`), item, client no., detail (days/dates), spots (`Avi.`), columns, duration, rate, discounts 1–4, status colour (open/partial/closed), currency, medium | OP + item + spot | plan; supplier; client; controls; differences |
| `Presupuesto de Producción` / `Orden de Compra` item | estimate no., item, description, unit cost/price, qty, cost, discount, supplier commission, production type, department, external supplier, approval status, OC status | estimate + item | job; supplier |
| `Solicitud de Gastos` / Expense request | request no., concept lines, amount, multi-invoice flag, generated child requests | request no. | supplier; job; cost centre |
| `Control de Medios` / Media control | saved selection of spots + overrides, independent of posting | doc ref | OP spots |
| `Diferencia` / Difference | origin (rate, size, quantity, discounts, reprogramming, adjustment, deficiency), amount (+/−), originating document, OP/plan/item/month, status (pending, received, written off, no-invoice), sign (NC/ND expected) | diff id | OP or budget item; supplier doc; client pending |
| `Compra Anticipada` / Advance purchase | original invoice, medium(s), original amount, pending balance, consumption docs | advance invoice | consumption invoices; cancellation NC |
| Volume rebate (`N/C por Volumen`) | selection (agency/client), origin (period, invoice, order, amount), discount % 1–4, transfer flag, % transfer, % client / client amount, counter-account type | NC | orders; client credit pending |
| Supplier commission (`Comisión a proveedores`, `confidencial`) | per item: mode (receives NC / agency bills), %/amount, status (pending assign, pending billing, billed, none) | estimate/OP item | NC; bonus account |
| Incentive scale (`Escala de Incentivos`) | supplier, medium, media type, publication type, scale size, % incentive, investment range from–to, client, billing condition (bill supplier / deduct from payment), base before/after prompt-payment discount | scale id | supplier documents; incentive report |
| Retention approval (CL/PE/CR) | state: pending assign → pending approve → approved | doc | payment order; certificate |
| Management action (`Gestión`) | type, action, entity (client/supplier/job), contact, comment, next-action date, status | action id | supplier/client/job |
| `Tipo de Medio` / `Tipo de Producción` | sales account, cost account, bonus account | code | drive automatic posting |
| `Configuraciones Especiales` | see §8 | key | system-wide |

---

## 4. Document lifecycles

### 4.1 Commitment line ("pending to receive")
```
Created (OP issued / budget approved [+OC issued/approved] / expense request approved)
  → Pending to receive (amount = expected cost)
  → [Controlled-not-posted] (P-04/P-08)
  → Partially received (partial invoice, P-15) ─┐
  → Fully received (P-01/P-14/P-18)            ├→ Difference pending (if billed ≠ expected)
  → Written off as not invoiced (P-30)         ┘
  → Re-opened (on document deletion P-28 or full-cancellation NC P-29)
```
Media order status visible by colour: black (open, not controlled), blue (partially closed), red (controlled and closed). `Versión Final` locks the order and plan; an "initial" load keeps them editable until a closing document or "mark as invoiced".

### 4.2 Supplier document
```
Received (optionally pre-received in Reception screen; supplier portal claims attach later)
 → Header captured (+ fiscal code validated, AR)
 → Controlled (spot/item match; differences computed)   [may persist as "control" only]
 → Taxes added (VAT per rate, perceptions; withholdings computed CO/MX)
 → Total reconciled (exact or within rounding threshold)
 → Fiscal-status warning acknowledged
 → Posted (GL + AP subledger; Unpaid = Without-PO = Total)
 → [Retention: pending assign → pending approve → approved]  (CL/PE/CR foreign suppliers)
 → [Colombia adjustment notes: provisional → definitive approval]
 → Payment order issued (Without-PO balance decreases; Unpaid unchanged until paid)
 → Partially paid (Unpaid = Without-PO < Total) → Paid (both 0)
 → Optional: Annulled by NC (P-29) | Deleted (only if unpaid and period open)
 → Direct billing: `Trasladada` flag once included in client invoice
```

### 4.3 Difference
```
Opened by override in control (P-02/P-08/P-10/P-16) or by credit computed lower than ordered (P-25)
 → Pending NC/ND from supplier
 → Closed by NC/ND (P-07/P-09/P-17)  | Written off (P-31, P&L effect) | Not-invoice with client transfer (P-30)
 → Optionally rebilled/credited to client (pending to invoice client)
 → Reversible write-off (Desmarcar in [mp302731])
```

### 4.4 Advance purchase
```
Advance invoice (code-89 asset) → Initial balance = Original
 → Consumption docs (zero-total invoices that net an "advance" line) → Balance decreases
 → Balance 0 ⇒ further consumption blocked
 → Unconsumed remainder: Cancellation NC (total or reduced via "Modificar Saldo a Anular") ⇒ closed
```

---

## 5. Business rules and calculations

**Matching and control**

- **R-01 (Pending-driven load types)**: available automatic load types depend on what the supplier has pending (OP, OP differences, budgets, budget differences, expense requests, commissions). Manual types require unticking the automatic-only filter.
- **R-02 (Three-way match grain)**: media = commitment (OP) × execution evidence (spot control / closed order) × supplier invoice; production = budget/OC × approval × invoice; expenses = request × invoice. The recommendation is to invoice only orders already controlled and closed; otherwise invoicing itself closes the order on the supplier's word.
- **R-03 (Total equality)**: the sum of controlled detail plus taxes and extra lines must equal the declared `Importe Total`; otherwise saving is blocked (except R-12).
- **R-04 (Sum-of-documents principle)**: suppliers may split billing any way their systems allow; the system checks that the **sum of all documents equals the order total**; residuals become differences.
- **R-05 (Spot-level variables)**: billed value per spot = f(spots, columns, duration, rate, discounts 1–4). Proposed formula (cascaded discounts, to be confirmed — see §11):
  `gross = spots × size × rate` where `size = columns × duration` (print: columns × cm; broadcast: duration in seconds/units),
  `net = gross × Π_{k=1..4}(1 − d_k)`.
  `difference = net_billed − net_ordered`, attributed to origin codes {rate, size, quantity, discount, reprogramming, adjustment, deficiency}.
- **R-06 (Discount presentation)**: discounts may be (a) per item in the invoice, (b) totalled as one line, (c) issued as separate NCs; the control must support all three without changing the net expected cost.
- **R-07 (Differences origin filter)**: `Origen = Diferencias` allows registering a document for amounts not present in any pending (extras); amounts start at zero.
- **R-08 (Final vs initial version)**: final version locks OPs/plan; initial allows later order/plan edits; closing an initial version requires an invoice/NC for the difference or "mark as invoiced".
- **R-09 (Production partial and over-budget)**: billed < expected ⇒ remaining pending stays open; billed > expected ⇒ pending to receive NC created for the excess.
- **R-10 (Expense requests)**: standard requests cannot be partially invoiced; multi-invoice requests spawn a child request per invoice and reduce the parent.
- **R-11 (Mandatory OC)**: if `OC obligatoria` is on, no production invoice can be registered before the OC exists; if `Aprobación OC obligatoria` is on, the OC must also be approved.
- **R-12 (Rounding)**: if |declared total − computed total| ≤ configured max, user may accept a rounding line posted to the configured rounding account.
- **R-13 (Currency homogeneity)**: one document cannot mix orders/budgets/requests of different currencies; a foreign-currency document cannot carry commitments issued in another foreign currency. (Local-currency document over foreign-currency orders is allowed with an exchange rate.)
- **R-14 (Exchange rate)**: rate field enabled when either the document currency or the order currency is foreign; it converts between debt currency (order) and document currency.

**Volume rebates, commissions, incentives**

- **R-15 (Volume expected credit)**: `expected_credit = Σ_orders(order_amount) × Σ_{k}(p_k)` (the manual says the percentage can be a sum of up to four discounts). When the user overrides the received amount, pre-entered discounts are cleared and `p_effective = received_amount / order_amount × 100` is placed in the first discount slot.
- **R-16 (Transfer to client)**: `client_share = credit × %Traslado` (or `% Cliente_k = p_k × %Traslado`, or a fixed `Importe Cliente`); the client share becomes a pending credit to invoice to the client; the agency keeps the rest.
- **R-17 (Amount-origin distribution)**: `alloc_i = credit × order_i / Σ order`.
- **R-18 (Counter-account choice)**: rebate posts against cost (reducing cost), the media type's bonus account, or a user-chosen account.
- **R-19 (Supplier commission mode)**: global configuration "receives NC" vs "agency bills commission"; with per-item mode each estimate/plan item chooses. Only items marked "receives supplier NC" appear in LT-COM-*; bonus account must exist on the production/media type.

**Direct billing and pass-through**

- **R-20 (Direct vs indirect)**: indirect = supplier bills the agency, the agency rebills the client. Direct = supplier bills the client. For MX, CO, PE, GT, HN, SV, EC, PA, CR the agency can receive the supplier's invoice for direct items before billing the client.
- **R-21 (`Factura pasa por Agencia`)**: when unticked, the document does not touch GL or supplier current account (agency not liable); it is only verified and passed to the client. `Pasa sólo el IVA` (enabled only when the former is off): debt does not pass, but VAT does and is taken as input VAT (typical Mexico).
- **R-22 (`Trasladada`)**: in direct-billing countries the document carries a status showing whether it has been included in the client invoice.

**Taxes**

- **R-23 (VAT by account)**: VAT is computed from the VAT account (which encodes the rate) on each line; `0000` = not subject. One line per VAT rate on manual loads. If billed rate differs from budgeted, change the VAT account and VAT is recomputed; VAT amount can be overtyped on partial/over-budget loads.
- **R-24 (Difference lines and VAT)**: adding a difference line without VAT causes it to appear as exempt in the purchase VAT book; recommended to attach a VAT value.
- **R-25 (Perceptions)**: entered as extra lines with JobNumber, OT, perception account (with proper observation code) and VAT `0000`; or auto-inserted against generic job/OT with automatic tax-load config.
- **R-26 (Withholdings CO/MX)**: computed at confirmation (Renta/ISR and IVA; plus ICA in CO); user confirms applicable retentions; retention window lists supplier's retention types with editable taxable base, per client.
- **R-27 (CO accumulated income-tax base)**: for retention type "monthly accumulated with deductions", base = gross − (health + pension + AFP + voluntary contributions + fixed % deduction) per the base window.
- **R-28 (Non-computable amount)**: for AR monotributo (and CL) suppliers, an amount that is excluded from retention computation / VAT credit.
- **R-29 (Fiscal status check)**: warn if supplier not validated with the tax authority; validation lives on the supplier master.

**Pre-conditions, periods, immutability**

- **R-30 (Production receivability)**: external supplier on item + client approval + OC (if mandatory/approved).
- **R-31 (Account completeness)**: media and production types must have accounts assigned or the system refuses both client billing approval and supplier invoice registration.
- **R-32 (Accounting date)**: must fall in an open month of the selected fiscal year; pre-closed month allowed only with permission, local currency, balance-sheet accounts only.
- **R-33 (Immutability)**: posted documents cannot change accounts or amounts; only due date and remarks.
- **R-34 (Deletion)**: allowed only if unpaid and period not pre-closed; deletion removes GL entry and reopens pendings.
- **R-35 (Full-cancellation NC)**: only for total cancellation of a FC/ND; not CO; not special suppliers; warns on existing PO; releases OP/OC to pending; requires association-adjustment removal before NC deletion.
- **R-36 (Write-off)**: "not invoiced by supplier" generates no GL entry; it changes the job margin and is stamped with the user.
- **R-37 (Advance purchase)**: consumption blocked when balance is 0; consumption invoices net to zero via an advance line.
- **R-38 (Balances)**: `Saldo Impago = Total − payments`; `Saldo sin OP = Total − amounts covered by issued payment orders`; at registration both equal Total.
- **R-39 (Automatic posting)**: on automatic loads the clerk never chooses accounts; cost account derives from the media/production type of the plan/budget, or from the expense concept.
- **R-40 (Cost-account dimension)**: on manual loads, choosing a cost account forces selection of production type (production) or medium (media); cost centre required for P&L accounts.
- **R-41 (Retention approval CL/PE/CR)**: with the special config on, foreign-supplier invoices go Pending assign → Pending approve → Approved (disapprove returns to Pending assign); only approved invoices can be paid; the PO uses approved retentions unchanged; certificates from PO or mass from the detailed payments list; alerts and a pending-retentions view. CR: lists retention concepts with/without tax treaty when the supplier has no local establishment and holds a residence certificate.

---

## 6. Accounting impacts

| Event | Debit | Credit | Notes |
|---|---|---|---|
| Media invoice (indirect, passes through agency) | Media cost account (from media type) by OT/Job; input VAT | Supplier integrating account (obs. 30) | Differences posted at billed value |
| Production invoice | Production cost account (from production type); input VAT | Supplier | Over-budget excess posted, NC pending opened |
| Expense invoice | Expense account (from concept), cost centre; input VAT | Supplier | Deductible flag for income tax |
| Perception line | Perception receivable/credit account (obs. code) | (part of supplier total) | VAT `0000` |
| Withholding (CO/MX at registration) | Supplier | Withholding payable | |
| Rounding | Rounding adjustment account (Dr or Cr) | — | Within threshold |
| Advance purchase invoice | Advance-purchase account (obs. 89); VAT | Media supplier | Generic job/OT allowed |
| Consumption invoice | Media cost (actual job/OT) | Advance-purchase account | Net total 0 |
| Advance cancellation NC | Supplier | Advance-purchase account (± VAT) | Balance → 0 |
| Volume NC (agency) | Supplier | Cost / Bonus account / chosen account | Client share → pending client credit |
| Commission NC | Supplier | Bonus account of media/production type | |
| Production/media NC for differences | Supplier | Cost account; VAT | |
| Full-cancellation NC | Supplier | Original cost/VAT accounts | + association adjustment entry |
| Direct, not passing agency | — | — | No GL, no AP |
| Direct, VAT only (MX) | Input VAT | Clearing/third-party (assumed) | Exact counterpart not documented |
| Write-off pending (not invoiced) | — | — | No GL; margin effect on OT/plan |
| Difference write-off | P&L (result) | — | Manual says "direct result"; posting mechanism unclear |
| Re-appropriation | Reverse manual entry; post controlled entry | | |
| Division split | Per division amounts | | When `Usa Divisiones de Empresa` |

Extra-accounting (management) tracking: every line carries OT, JobNumber, client, product, division, cost centre, expense request — the "Work-order movements" tab exists to verify imputation outside the GL.

---

## 7. Cross-module handoffs

| From / To | Handoff |
|---|---|
| Media buying (OP, plans) → AP | OP spots create pendings; controls can lock orders/plans; differences flow back to plan/OT (margin). |
| Production (estimates, OC, approvals) → AP | Approved budget items with external supplier (+OC) create pendings; differences reflect on budget/OT; commission flags per item. |
| Expense requests → AP | Approved requests create pendings; multi-invoice spawns child requests. |
| AP → Client billing (AR) | Pending to invoice client for: transferred volume rebates, transferred write-offs, media differences to rebill/credit; direct-billing `Trasladada`; cross report supplier vs client invoices; advance-sale linkage (pay supplier only when client advance collected). |
| AP → Treasury | Unpaid / without-PO balances; approved retentions only; PO warnings on cancellation NCs; certificates from PO or mass list. |
| AP → Tax | Purchase VAT book (with AR SIRED/CITI exports), retention summaries (MX ISR/IVA, EC Renta/IVA), CO DIAN XML equivalent/support documents, CO certificate export to the supplier portal. |
| AP → GL / Close | Automatic entries; pre-close permission; account master codes 30, 89, 20–23, 39 etc. |
| Supplier master | Payment term, CAI, tax condition, retentions, fiscal validation, intercompany. |
| Supplier web portal (Liveranto) | Claims shown on invoices; e-documents; certificates; user who posted via portal shown in VAT book. |
| Image base / attachments | Scan and attach originals; bulk download of related documents (estimate, plan, OC/OP, approvals, invoice image). |
| Alerts | Retentions pending assign/approve; CO cancellation NCs pending approval. |

---

## 8. Configuration and country-specific behaviour

**Special configurations / parameters referenced**
- `Carga Automática de Impuestos` (≥ v4.6): Taxes button inserts perceptions on generic job/OT.
- Rounding: enable automatic rounding, max amount, rounding account.
- `Comisión Proveedores` = Recibe N/C | Factura Comisión; `Forma de Cobro por Ítem` yes/no.
- OC mandatory; OC approval mandatory.
- `Usa Divisiones de Empresa` (sub-companies).
- `Imprime Voucher Factura Proveedores`, `Usa Numeración de Lote de Facturas`.
- `Usa Contrarecibo` (MX receipt date).
- Retention approval for foreign suppliers (CL, PE, CR).
- Include invoice number when writing off differences.
- `Imprime comprobantes relacionados` + `Permite adjuntar múltiples archivos`.
- `Usa Incentivos por Cliente`.
- `Usa Web Proveedores` (CO certificate export).
- Colombia NC-annul approval + notification contact.
- User permission: `Puede Ingresar Facturas Luego del Pre-Cierre`; two user activities for retention assign/approve.
- Account master: obs. code 30 (supplier integrating), 89 (advance purchase), perception codes, bonus account on media/production types.

**Country matrix**

| Country | Behaviour |
|---|---|
| Argentina | Letter + POS; RG1361 class; CAI/CAE/fiscal printer; online AFIP validation; monotributo non-computable amount; VAT and IIBB perceptions; provisional VAT (obsolete); re-appropriate manual invoice; SIRED/CITI exports; "Facturación por Proveedor" fiscal listing. |
| Mexico | Direct billing; `Pasa sólo el IVA`; F3 lookup for direct invoices; withholding computation ISR/IVA; Anexo document type; `Fecha Contrarecibo`; retention summary; VAT book reconciled with creditable VAT auxiliary and used for SAT informative return; `Pasa por Agencia` column in cross report. |
| Colombia | Withholdings (Renta, ICA, IVA) split on amounts; accumulated monthly income-tax base with deductions; regime order number; annulled flag; equivalent-document XML (not for debit notes) for non-responsible/foreign suppliers; support-document listing and XML; no full-cancellation NC screen (adjustment-note approval instead); excludes "items without cost"; production-items invoice detail report; expense & sales audit report; certificate export to portal. |
| Chile | Annulled flag; electronic-invoice flag; non-computable VAT; retention approval for foreign suppliers. |
| Peru | Withholdings window; retention approval for foreign suppliers. |
| Costa Rica | Retention approval with tax-treaty concepts for non-established foreign suppliers. |
| Dominican Republic | NCF variable / fixed; service type 01–11; withholdings window. |
| Guatemala | Service type; withholdings window. |
| Venezuela | Control number; retention print on NC screen. |
| Uruguay | Withholding receipt number (`Resguardo`). |
| Ecuador | Retention summary (Renta/IVA); retention print. |
| Puerto Rico | Income-tax base window on NC screen. |
| Direct billing countries | MX, CO, PE, GT, HN, SV, EC, PA, CR. |

---

## 9. Reports and KPIs

| Report | Purpose / key filters | KPI potential |
|---|---|---|
| Media invoices to receive `[mp301105]` | Pending OP spots; Normal vs cut-off date; by client/supplier; local/foreign; media type; direct/indirect; currency; installments; prepaid; client billed status; gross/net; customer PO no. | Uninvoiced media accrual; aging of pendings |
| Production invoices to receive `[mp301103]` | Pending budgets/OCs; by client/supplier; division; department; production type group/type; with/without OC; multi-currency vs accounting format; client billed; balance below; negatives; foreign | Production accrual; differences accept |
| Pending billing differences `[mp301373]` | By supplier/client/document/OP; origin type; cut-off date; directs; saved-without-invoice; negatives; write-off action | Open differences value; differences by origin; write-off rate |
| Non-billable marked estimates/plans/differences `[mp302731]` | Items marked not billable to client or not invoiced by supplier; Desmarcar | Leakage audit |
| Supplier invoices vs client invoices `[mp301362]` | Cross-reference, difference column, "unbilled" pendings, paid/unpaid, PO exists, commission filter, advance-sale status, consolidated multi-company | Rebill completeness; pay-when-paid control; margin per job |
| Invoices by supplier `[mp301354]` | Per account line; by contable/entry/doc date; media/production; VAT type; direct; concept; difference status; responsible; division; account range; ranking; bulk attachment download | Spend ranking; manual-entry ratio |
| Billing by supplier `[mp301579]` (AR) | Net totals by supplier/period with tax ids | Fiscal |
| Purchase VAT book `[mp301351]` | Totals by type, by tax condition, by supplier; FF/expense-report filters; direct/indirect; exclusions; FX diff; SIRED/CITI | VAT reconciliation |
| Retentions summary `[mp301577]` (MX/EC) | ISR/IVA or Renta/IVA by supplier/period | Retention compliance |
| Supplier commissions list `[mp301516]` | Status: pending assign, pending billing, billed, none | Commission capture rate |
| Costs by supplier `[mp309257]` | Media vs production cost, documents vs provisions, manual entries, intercompany | Supplier concentration |
| Production items invoice detail `[mp309254]` (CO) | Item-level cost/price/qty/discount/commission per supplier doc | Item margin |
| Incentive scales `[mp302783]` / Incentive report `[mp302782]` | Scales by supplier/medium/publication; incentives computed from scales, bill-to-supplier vs deduct-from-payment, pending/billed, prompt payment | Incentive accrual |
| Advance purchase consumption `[mp301375]` + dynamic report `[mp402832_7]` | Original vs consumed vs pending; pivot/grid; scheduled offline generation | Advance utilisation |
| Expenses & sales `[mp302690]` (CO) | Revenue/cost/provision movements by observation codes | Audit |
| Support documents list `[mp302931]` (CO) | DIAN support docs; print/XML | Compliance |
| Follow-up management `[mp302789]` | Next/overdue actions | Collection of missing docs |

---

## 10. Agentic-skill implications

### 10.1 Atomic jobs (candidate skills/tools)

1. `detect_load_types(supplier)` → list of pendings by category.
2. `capture_header(doc_image|xml)` → normalised header (dates, currency, rate, total, fiscal codes); validate due date = doc date + term.
3. `validate_fiscal_code(country, supplier, code)` (AR CAI/CAE, DO NCF, CO CUFE/XML) and `check_supplier_tax_status`.
4. `list_pendings(supplier, filters)` (period, day range, currency, client, medium, production type, direct/indirect, origin=invoice|differences).
5. `match_media_invoice(invoice_lines, op_spots)` → selected spots, overrides, differences by origin.
6. `match_production_invoice(invoice_lines, budget_items)` → full/partial/over.
7. `match_expense_invoice(invoice_lines, requests)` incl. multi-invoice distribution.
8. `compute_taxes(lines, country, supplier)` → VAT by rate, perceptions, withholdings.
9. `reconcile_total(declared, computed, rounding_cfg)` → ok | rounding line | error.
10. `build_journal_entry(doc, account_maps)`.
11. `post_document` (idempotent by supplier+type+letter+number).
12. `save_control` / `recover_control` (separate control from posting).
13. `register_difference_note(nc|nd, differences)`.
14. `compute_volume_rebate(orders, percentages|amount, transfer)`.
15. `register_commission_note(items)`.
16. `advance_purchase_open/consume/close`.
17. `cancel_document_full(doc)` (release pendings, association adjustment).
18. `write_off_pending(lines, transfer_to_client)` and `write_off_difference`.
19. `retention_assign/approve` (CL/PE/CR).
20. Reporting tools: pendings to receive, differences, supplier-vs-client cross, VAT book, retention summary.
21. Follow-up: `create_followup_action` for missing invoices/certifications.

### 10.2 Deterministic calculations worth a tool

- Due date: `due = doc_date + term_days`; inverse `term = due − doc_date`.
- Spot net: `net = spots × columns × duration × rate × Π(1−d_k)` (confirm size semantics per media type).
- Difference: `Δ = net_billed − net_ordered` per spot with origin attribution order (quantity → size → rate → discount).
- Production: `remaining = expected − Σ billed`; if `< 0` ⇒ NC pending `= −remaining`.
- VAT per line: `vat = net × rate(vat_account)`; `0000` ⇒ 0.
- Total check: `Σ(net + vat) + Σ perceptions + Σ extra − withholdings(where netted) == declared ± rounding_max`.
- Volume: `expected = Σ order × Σp_k`; `p_eff = received / Σ order`; `client_share = credit × %traslado`; proportional allocation.
- Advance: `balance = original − Σ consumption − cancellation`.
- Balances: `unpaid = total − paid`; `without_po = total − Σ PO amounts`.
- FX: `amount_local = amount_doc × rate`; enforce currency-homogeneity rule R-13.
- CO income base: `base = gross − Σ deductions − gross × fixed%`.

### 10.3 Controls (guardrails for agents)

- Never post without a pending unless the load type is manual and the user/agent records justification in remarks.
- Block mixed currencies; block accounting dates in closed months; pre-close only with permission and balance-sheet accounts.
- Require OC/approval when configured; require accounts on media/production types.
- Duplicate detection on supplier+type+letter+number.
- Human approval checkpoints: differences above tolerance, write-offs, full-cancellation NCs (esp. when PO exists), retention approval, transfer-to-client percentages, manual entries hitting P&L.
- Audit stamp on write-offs and controls; preserve control separately from posting.
- Recommend controlling only closed (red) orders; flag invoicing of open orders as "closing on supplier's word".

### 10.4 Exceptions to handle

- Supplier splits invoice + NC for same item; discounts billed via separate NCs.
- Extras billed after a clean invoice (origin = differences).
- Commission credit computed on ordered amount larger than actual investment.
- Advance consumption billed as invoice + NC pair (enter both manually, plus a fictitious automatic consumption document).
- NC deletion after full cancellation (manual re-marking).
- Direct invoices that do not pass through the agency (verification only) and VAT-only pass-through.
- Foreign suppliers with treaty retentions; monotributo non-computable.
- Missing VAT on difference lines (exempt distortion in VAT book).

---

## 11. Gaps and ambiguities

1. **Tolerances**: no percentage/amount tolerance for matching is documented beyond the rounding threshold; matching is user-driven. A re-implementation must define tolerances.
2. **Spot pricing formula**: the meaning of columns × duration and whether discounts are cascaded or additive is not stated (volume NC suggests additive "sum of up to 4 discounts"; media discounts are likely cascaded). Needs confirmation.
3. **Difference origin attribution** when several variables change at once is unspecified.
4. **Difference write-off posting**: described as producing a "direct result", but the GL entry (if any) is not described; "mark as not invoiced" explicitly has no GL entry, implying the result arises through accrual/provision reversal elsewhere.
5. **Accrual model**: costs-by-supplier mentions provisions, but how pendings are accrued at month end (and reversed at registration) is outside this group.
6. **VAT-only pass-through** counterpart account (MX) not documented.
7. **Withholding computation tables** (rates, thresholds, bases) per country are not described; only where they are triggered.
8. **Perception accounts and observation codes** values not listed (only "corresponding observation code").
9. **Re-appropriation** is described for Argentina in the overview but the guide is generic; country scope unclear.
10. **Commission on media with initial version**: the exact mechanism to adjust via "comprobante" field is vague.
11. **Reconciliation of planner-approved invoices** `[mp302863]` and **new media screen** `[mp302941]` have one-paragraph descriptions only; approval workflow by planners is undocumented.
12. **Supplier invoice reception** screen (pre-reception) is referenced but not in this group.
13. **Incentives**: computation from scales (prompt-payment base, billing vs payment deduction) not specified beyond report fields.
14. **Retentions in NC full-cancellation**: whether withholdings of the original are reversed is not stated.
15. **Multi-company/division split rules** (how amounts are apportioned to divisions) not described.
16. **Approval for payment**: outside CL/PE/CR retention approval and CO adjustment notes, there is no explicit "approved for payment" state in this group; payment readiness seems implied by registration (plus optional pay-when-paid check in the cross report).
17. Expense request "service OC" optionality depends on agency configuration that is not named.
