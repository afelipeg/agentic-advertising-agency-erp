# Expenses (Gastos): overhead, expense reports and petty cash

> **Provenance.** Functional reverse engineering of a reference agency ERP, derived from its publicly accessible help documentation (reviewed 2026-10-11). Content is paraphrased and restructured; it is not vendor documentation, source code or an endorsement. Bracketed ids such as `[mp301010]` identify the source page used as evidence. Items marked *inferred*, *assumed* or listed under gaps must be validated with your own controller, tax adviser and system owner before they drive postings or payments.

> Reverse-engineered functional spec for an open-source agentic skills repo, fully paraphrased. Spanish labels appear in backticks only as field or menu identifiers. Points marked **[inferred]** are reasoned from context and are not stated explicitly in the source; check them before implementation.

Source file: `groups/F_gastos.txt` (~3.1k lines, 96 sections). Source refs below use the page filename, e.g. `[mp301114]`.

---

## 1. Purpose & position in the E2E circuit

The Gastos module governs **agency-side spending that is not media buying or client production purchasing**. It handles four flows:

1. **Purchase-to-pay for overhead and indirect spend.** Recurring supplier agreements (`Contratos de Gastos`) and one-off spend requests (`Solicitudes de Gastos`) can optionally go through expense purchase orders (`Órdenes de Compra de Gastos`). They end in a supplier invoice that is booked in Accounts Payable (CxP) and paid by Treasury.
2. **Employee out-of-pocket reporting.** An employee lists what they spent on an expense sheet (`Planilla de Gastos`). After approval, accounting turns the sheet into an expense settlement (`Rendición de Gastos`) that books the receipts, reimburses the employee or nets an advance, and records any refund of unused cash.
3. **Production cost reporting against client-approved estimates.** A cost sheet (`Planilla de Costos`) and its cost settlement (`Rendición de Costos`) record costs paid by staff on behalf of a production estimate (`Presupuesto de Producción`) that the client has approved. The cost lands on the estimate item and therefore on the job.
4. **Imprest / petty cash.** A petty cash sheet (`Planilla de Fondo Fijo`) and its settlement (`Rendición de Fondo Fijo`) record what a custodian spent from a fixed fund. The fund is then topped back up to its fixed amount (`Reponer`).

The module also covers **expense budgeting** (`Presupuesto de Gastos`), budget-vs-actual analysis, and the **analytic master data** shared with Accounting: cost centers, cost-center groups, divisions, division groups, country division groups, allocation codes, and expense concepts.

**Position in the circuit:**

```
Masters (CC, Divisions, Concepts, Allocation codes, Occasional suppliers)
        │
        ▼
Expense Contract ──approve──► auto Expense Requests (approved)
Expense Request ──approve──► [Expense PO ──approve?──] ──► Supplier invoice (CxP) ──► Payment (Tesorería)
                     └─(optional) Accrue/defer over N months (Contabilidad)
Expense Sheet / Cost Sheet / Petty-cash Sheet ──send──► authorize ──► Settlement (Rendición)
        ──► GL + VAT purchase subledger ──► Pay / Refund / Replenish (Tesorería)
Cost Sheet ◄── requires client-approved Production Estimate item (Producción/Cuentas)
All lines carry: Cost Center, Division, Client, Job/OT (JobNumber) ──► Job profitability & analytic P&L
Expense Budget (CC × account × month) ◄── compared to all GL postings
```

Several spend types are absorbed into the job or client: overhead charged to a client's generic OT, staff expenses charged to a specific OT, and production costs charged against an estimate item. This is how Gastos feeds **job and client profitability**. An internal supplier type also lets a "spend" be booked as a reduction of an income account, which creates a loss on the OT.

---

## 2. Process catalogue

Each process gives the trigger, actor, steps, inputs, outputs, state change, approvals and source.

### P1. Set up the expense regime (one-time configuration)
- **Trigger:** go-live, or a policy change.
- **Actor:** System administrator / controller.
- **Steps:** (1) Choose the control granularity with `Control de Gastos por JobNumber`. ON means spend is tracked per campaign/JobNumber. OFF means it is tracked per client only, so lines can go only to product-generic OTs. (2) Set self-approval policy with `No Permite Autoaprobar Gastos` (some pages call it "Permite autoaprobar gastos"). (3) For each user, set the flags that say whether they control and/or approve other users' spend, plus their approvers and amount limits (`Controla/Aprueba Gastos de otros Usuarios`). (4) Decide whether POs are mandatory (`Orden de compra obligatoria en Gastos`) and whether POs need approval (`Aprobación Ordenes de Gastos`). (5) Optionally enable line-item breakdown on requests (`Apertura ítems en Solicitudes de Gastos`), occasional suppliers (`Usa proveedores eventuales`), linking advances to sheets (`Asocia Anticipos a Planillas de gastos`), job-owner approval of cost reports (`Aprob. Rend. de Costos por Responsable del Job`), voiding of sheets/settlements (`Anulación de Planillas y Rendiciones`), and second approval by concept. (6) Give each user a default cost center for agency spend.
- **Outputs:** Configuration flags that drive every later process.
- **Refs:** `[mp302002]`, `[mp301114]`, `[mp301110]`, `[mp303009]`, `[mp301096]`.

### P2. Maintain analytic masters
- **Trigger:** organization change.
- **Actor:** Controller.
- **Steps:** Create cost-center groups, then cost centers that point to a group. Create division groups and country division groups, then divisions. Create allocation codes: cost-center percentages that must total 100%, then a division split per cost center that must also total 100%. Create concepts linked to GL accounts. Create occasional suppliers.
- **Rules:** Codes are auto-sequenced. A record can be deleted only if it has never been used. An inactive (`Vigente`=off) record cannot be selected in new transactions.
- **Refs:** `[mp301097]`, `[mp305097]`, `[mp306097]`, `[mp307097]`, `[mp302871]`, `[mp301092]`, `[mp301096]`, `[mp301611]`.

### P3. Register an expense contract (recurring supplier agreement)
- **Trigger:** A recurring, known-in-advance cost such as rent, parking or insurance. It may be prepaid at a frozen price.
- **Actor:** Requester (any user with access), entering on their own behalf or for a selected `Solicitante`.
- **Inputs:** supplier (active and enabled for Gastos), contract type (`Normal`, or `Especial` in Colombia only), requester, concept (must be flagged periodic), description, currency and rate, validity from/to, contract total, auto-renewal option (yes, no, or renew until a cancellation deadline), and a monthly grid with three rows: amount to invoice, number of invoices expected that month, and amount to accrue in each month. The distribution can be entered manually (CC, JobNumber, OT, %, division) or derived automatically (`Con Apertura`=Sí with a CC allocation code plus JobNumber mode `Único` with one campaign, or `Apertura` with a JobNumber allocation code).
- **Steps:** New → fill the main data → fill the monthly grid and distribution → save. The contract is created as **Pending approval**. Creation date and number are assigned automatically.
- **Outputs:** Contract record.
- **Refs:** `[mp302002]`, the two "Ingresar un contrato…" guides.

### P4. Approve / disapprove / reject / recover an expense contract
- **Actor:** A user flagged as approving other users' spend. If self-approval is disabled, the creator cannot approve their own contract.
- **Transitions:**
  - `Pendiente de aprobar` → **Approve** → `Aprobado`. The approver is stamped, and the system **auto-creates one Expense Request per expected invoice for every month loaded**, already in Approved state and linked back to the contract.
  - `Aprobado` → **Disapprove** → `Pendiente de aprobar`.
  - `Pendiente de aprobar` → **Reject** → `Rechazado`. **Recover rejection** returns it to `Pendiente de aprobar`.
  - **Delete** removes the contract and frees its number for reuse.
- **Guards:** A contract whose months fall in a fiscal year not yet opened by accounting cannot be approved. POs and supplier invoices can be raised only on requests from approved contracts.
- **Refs:** `[mp302002]`, `[aprobar-un-contrato-de-gastos]`.

### P5. Create an expense request (one-off spend)
- **Trigger:** Need to buy a good or service.
- **Actor:** Requester. The requester and date are stamped automatically.
- **Inputs:**
  - Concept, which determines the GL account.
  - Description.
  - Net amount (excluding VAT). Entered by hand, or calculated from item lines (qty × unit price, with a per-division price) when item breakdown is ON.
  - Currency and rate.
  - Type: `Débito` for an invoice or `Crédito` for a credit note or refund.
  - Subaccount division.
  - Supplier type: `Externo` with a supplier, or `Interno` with an income GL account carrying observation code 21/22.
  - Allocation: either manual detail lines (CC, JobNumber, OT, amount, division), or `Con Apertura` (CC allocation code + JobNumber `Único`/`Apertura`), or a subaccount breakdown (account + subaccount + amount).
  - Optional deferral months and deferral start date.
  - Useful life, for fixed-asset concepts.
  - Country stamp-tax fields.
  - Attachments.
- **Initial state:** set by the requester's approval level (see §4.2).
- **Variants (each a separate user guide):**
  - **Multi-invoice request.** The concept is flagged `Facturación Múltiple`. Only one detail line is allowed. It is auto-filled with the user's default CC and the agency's generic JobNumber, and the final distribution is set when each invoice is entered. A partial invoice spawns a child request for the invoiced amount and reduces the parent by that amount.
  - **Credit in favor of the agency.** Type = `Crédito`. The refund is allocated to an AGENCY-client JobNumber, can be deferred, and goes to an external supplier.
  - **Reimbursement request (`por reintegro`).** Type = `Débito`. Uses the subaccount breakdown to charge the amount to an employee's subaccount, for spend made on the employee's behalf and later recovered (for example through payroll). Requires a balance-sheet bridge account with observation code `S1` assigned to the Treasury and Expense functions. `Con Apertura`=No and no deferral.
  - **Fixed-asset purchase.** The concept's account carries observation code `B1` (original value of fixed assets). Useful life is captured. When the supplier invoice is entered, a fixed-asset record is **created automatically** in the Fixed Assets master.
  - **Automatic allocation** (allocation codes) and **manual allocation** (detail lines).
- **Refs:** `[mp301114]` and the nine guides under it.

### P6. Approve / reject / disapprove an expense request
- **Actor:** A user with `Controla/Aprueba gastos de otros usuarios`, or Supervisor level. Mass approval is available from the request list (`[aprobar-solicitudes-de-gastos-masivamente]`).
- **Transitions:**
  - Pending → **Approve** → `Aprobada`, with the approver stamped.
  - Pending → **Reject** → `Rechazada`. A rejection reason (`Descripción de rechazo`) must be entered and saved.
  - Approved → **Disapprove** → Pending. This is **blocked if a PO exists**; the request must first be removed from the PO.
  - **Delete** removes the request and reuses its number.
- **Optional second approval:** for concepts flagged for audit double approval, a second approver with the extra user permission is needed.
- **Refs:** `[aprobar-una-solicitud-de-gastos]`, `[rechazar-una-solicitud-de-gastos]`, `[mp301096]`.

### P7. Copy periodic requests
- **Actor:** A user with level 1 on the request list.
- **Steps:** List requests → select those with periodic concepts → Copy → enter a new delivery date → review the "to generate" tab → Generate. The new request numbers are shown.
- **Rule:** Only requests that use periodic concepts can be copied.
- **Ref:** `[ingresar-solicitudes-de-gastos-copiandolas-de-otras]`.

### P8. Accrue (defer) a request over several months
- **Trigger:** A spend consumed over several months, such as a quarterly or annual bill.
- **Actor:** Accounting or the requester, on an approved request that has deferral months.
- **Steps:** Query the request → **Devengar**. Entries are generated for (deferral months + 1) periods, starting at the deferral start date and using the distribution percentages. They are posted whether or not the invoice has arrived. **Anular Dev.** voids the accrual with a void date. **Elimina Dev.** erases it as if it never happened.
- **State:** → `Devengada`, and later `Contabilizada` when the invoice is entered.
- **Rule:** The accrual is **not** auto-reversed on day 1 of the next month. The supplier invoice is posted to the "expenses to accrue" account linked to the expense account. Agencies that use expense provisioning usually do not use this feature.
- **Ref:** `[devengar-una-solicitud-de-gastos-en-varios-meses]`, `[mp301114]`.

### P9. Issue / approve / print an expense purchase order
- **Trigger:** An approved request that must be formalized with the supplier. This is mandatory when the PO-mandatory flag is ON.
- **Actor:** Purchasing or the requester. If PO approval is ON, a PO approver must approve.
- **Modes:**
  - (a) **From a request.** Choose one approved request, then tick its items.
  - (b) **By supplier.** Choose a supplier, tick several of its approved requests that have no PO yet, click `Cargar Orden`, then tick items.
- **Fields:** PO number (auto), date (today, cannot be edited), currency (controlled currencies only), payment terms (days or a predefined condition), editable item descriptions, and the PO total (sum of ticked items).
- **Effects:** Once a PO exists, the source request items **cannot be modified, deleted or rejected**. The PO can be printed: number of copies, signatures (issuer, producer, account executive), logo on by default, VAT omitted by default, Word/PDF export, and email to the supplier's master-file address (release 4.8i and later).
- **Guards:** If POs are mandatory, the supplier invoice is blocked until the PO exists. If PO approval is mandatory, it is blocked until the PO is approved.
- **Refs:** `[mp301139]` and its four guides.

### P10. Supplier invoice against request → `Contabilizada` (handoff to CxP)
- Entering the supplier invoice in CxP against an approved request (or an approved PO when required) moves the request to `Contabilizada`. The request stores the invoice number, invoice date, posting date and PO number. When the payment order is issued, the payment date is stored too. Requests that came from contracts are marked as invoiced.
- **Refs:** `[mp301114]`, `[mp302002]`.

### P11. Prepare and submit an employee expense sheet
- **Trigger:** An employee incurred spend, with or without a prior advance.
- **Actor:** The employee, or a delegate entering for users whose spend they control. Sheets are numbered per user.
- **Inputs (header):** who incurred the spend, expense type (local, or **travel**, which adds city and hotel columns), description, reporting currency and rate, and free-text observations.
- **Inputs (line):** date, city (travel only), detail, concept, currency (uncontrolled foreign currencies are allowed), gross amount including taxes split across category columns (food, transport/parking, hotel, other), rate, total (auto = amount × rate), client (a real client or the AGENCY client), OT (specific or client-generic), cost center, and division.
- **Totals:** total spent, advance delivered, balance owed to the agency or to the employee, and the cash returned (`Devolución`, entered by right-clicking).
- **Steps:** New → save. Lines can be added over time with Modify. Then **Enviar**, which locks the sheet and sets it to "sent for approval". Attachments can be linked per line, including photos from the mobile app.
- **Refs:** `[mp301110]`, `[ad_cap_gus_gto_01…]`.

### P12. Authorize / bounce / de-authorize an expense sheet
- **Actor:** A Supervisor on the sheet screen (can approve anyone), or an assigned approver within their amount limit. The approving user must have level < 3 on the screen. Self-approval is allowed only when the agency permits it **and** the user is classed as an "Expense Approver User".
- **Transitions:**
  - Sent → **No Enviar** → Pending. The sheet is unlocked so the employee can fix it.
  - Sent → **Autorizar** → Authorized. The sheet now waits for accounting.
  - Authorized → **Desaprobar/Desautorizar** → Sent. This is blocked once the settlement is posted.
  - **Eliminar fila** removes a disallowed line during review.
  - **Eliminar** removes the whole sheet and is allowed only in Pending state.
- **Refs:** `[ad_cap_gus_gto_02…]`, `[ad_cap_gus_gto_03…]`, `[ad_cap_gus_gen_16…]`.

### P13. Post an expense settlement (`Rendición de Gastos`)
- **Trigger:** An authorized expense sheet.
- **Actor:** Accounting.
- **Steps:**
  1. New. Pick an open fiscal year and an approved sheet. The settlement number is sequential. The subaccount is the employee.
  2. For each line that has a taxed receipt, tick it to open the receipt tab and enter:
     - supplier name;
     - VAT condition;
     - tax ID;
     - document type (invoice or credit note);
     - letter, point of sale and number;
     - date and currency;
     - net amount. VAT is derived as the reported gross minus the net.
  3. In Argentina, also enter the CAI (pre-printed forms), CAE (electronic invoice) or fiscal-controller code. Other countries add their own fields (see §8).
  4. For each line, confirm or change the account and concept (F2 help on accounts, then concepts), the VAT rate or VAT account (`0000` if no VAT is shown), the cost center and the deductible flag.
  5. Click **Grabar provisorio** to save partial work. This posts nothing.
  6. Click **Grabar**. This is final: it posts the entries and blocks further edits.
- **After posting:** **Pagar** reimburses the unpaid balance. **Contab. Devol.** records cash returned by the employee. **Reponer** auto-issues a payment order. **Rechazar** sends the sheet back to its creator with reasons. **Eliminar** deletes the settlement and leaves no posting trace.
- **Refs:** `[mp301269]` and its three guides.

### P14. Reimburse the employee from the settlement
- Query the settlement → **Pagar**, enabled when there is an unpaid balance → in the `Pagar Con` window enter payment currency, rate, date and method (cash, using a cash GL account; other methods are allowed) → confirm → print the payment order (copies, logo, PDF).
- Only users allowed to enter payments can do this. The same payment can also be made from the Treasury Payments screen.
- **Ref:** `[reintegrar-los-gastos-al-responsable-desde-la-rendicion-de-gastos]`.

### P15. Record the refund of an unused advance
- Query the settlement → **Contab. Devol.**, enabled when a refund amount was reported → enter the refund date → save → choose the division → in the `Cobrar Con` window enter the date and method (cash GL account or another method) → confirm → print the receipt.
- Only users allowed to enter collections can do this. It can also be done from the Collections screen.
- **Refs:** `[devolver-el-sobrante-del-anticipo-en-la-rendicion-de-gastos-en-efectivo]`, `[devolver-el-sobrante-del-anticipo-en-la-rendicion-de-costos-en-efectivo]`.

### P16. Prepare / authorize a production cost sheet
- **Trigger:** Staff paid production costs that belong to a client-approved production estimate.
- **Actor:** The person responsible for the costs, or a delegate. If `Aprob. Rend. de Costos por Responsable del Job` is ON, the job owner approves.
- **Inputs (header):** who incurred the costs, description, reporting currency (**must equal the estimate item's currency**), rate, estimate month/year, estimate (`Estimado`), and an estimate item assigned to the special supplier "Rendición de costos".
- **Inputs (line):** date, detail, currency, gross amount, rate, total, cost center, division. There is **no concept column**; the account comes from the service type on the estimate item.
- **Guards:** The estimate must be client-approved. The sheet total must not exceed the item amount.
- **Transitions:** Same as P12 (Send / No Enviar / Authorize / De-authorize). De-authorization is blocked once the settlement is posted.
- **Refs:** `[mp301100]` and its three guides.

### P17. Post a cost settlement (`Rendición de Costos`)
- Same mechanics as P13, with three differences:
  - (a) The GL account **cannot be changed**, because it is tied to the estimate's service type. Fix the estimate instead.
  - (b) The Budget section shows the estimate item and the payment order number and state.
  - (c) **Balance adjustment on the estimate:** the estimate holds costs net of tax. After a settlement that splits out tax, the estimate item would keep waiting for the tax portion from the supplier. The user must reduce the item's pending balance by that tax amount. This is allowed only once the item shows as supplier-invoiced. Example: an item of 5,000 with 457.62 of split-out tax is adjusted to 4,542.38.
- A consolidated view is available in "Detalle de Anticipos y Rendiciones de Costo".
- **Refs:** `[mp301113]` and its two guides.

### P18. Petty cash lifecycle
1. **Create the fund.** Administration issues a payment order that funds a dedicated GL account (observation code `51`, usable in Treasury), one per custodian or fund, for example "Petty cash – Production". Any number of funds can exist. **[Treasury]**
2. **Record spending.** The custodian keeps a petty-cash sheet for a period of roughly one to two weeks, such as the first half of July. Header: description, reporting currency (must equal the fund account's currency), rate, fund account. The "Datos contables" panel shows the account balance, the total of sheets not yet posted, and the current balance (account balance minus unposted sheets). Line: date, collaborator who spent, approver of the spend, detail, concept, currency, gross amount, rate, total, client or AGENCY, OT, cost center, division.
3. **Send.** The custodian sends the sheet before the fund runs out.
4. **Authorize.** Same rules as P12. If `Anulación de Planillas y Rendiciones` is ON, **Anular** moves the sheet to `Rechazada`.
5. **Post the settlement** (`Rendición de Fondo Fijo`). Same mechanics as P13. Accounts can be changed by F2.
6. **Replenish** (`Reponer`). Query the settlement → Reponer → enter date, currency, rate and beneficiary → `Pagar Con` (cash account or another method) → print the payment order. The fund goes back to its fixed amount, which works as a control.
- **Refs:** `[mp303009]`, `[mp301262]`, `[reponer-el-fondo-fijo]` and the related guides. These screens are also reachable under Treasury → Deposits and Other Operations.

### P19. Budget expenses and compare with actuals
- **Actor:** Controller or budget owner.
- **Steps:** Pick the year, CC group, cost center (mandatory to enter values; division is mandatory when divisions are used), whether to show account groupings or inactive accounts, the grouping scheme (`Principal` or `Hyperion`), and the presentation (`Detallado` per account or `Resumido` per grouping). Then type amounts per account per open month. Each cell saves when you leave it.
- **Tabs:** *Budgeted* (data entry), *Actual* (all GL postings to those accounts from any source, including manual adjustments), and *Projected* (actuals for closed months plus budget for open months; read-only, used with CC = All). Click a month to get a budget-vs-actual variance comparison.
- **Refs:** `[mp301134]` and its two guides; `[mp301136]` for control.

### P20. Fee contracts (cross-module content filed under Planilla de Gastos)
The manual places seven guides about **client fee contracts** (`Contratos de Fee Fijo`, a Cuentas function) under the expense-sheet page. Their content:
- **Contract types:** fixed distribution, dynamic distribution, and dynamic with auto-assignment.
- **Billing criterion:** a defined client, or a client allocation code.
- **Installments and splits:** monthly installment amounts. Distribution percentages split each installment between media and production; a profitability split covers investment versus hours.
- **Job assignment:** JobNumbers are assigned either manually or through a JobNumber pattern. Dynamic contracts use an allocation table.
- **Approvals:** two separate approval tracks, *by client* and *for billing*, each controlled by its own user permission.
- **Restrictions:**
  - Fixed-distribution contracts cannot take new campaigns once the first installment is billed.
  - Media and production installments are generated and billed separately.
  - Estimates linked to fee or hourly contracts cannot carry an agency commission.
  - With auto-assignment, the system prompts when a new JobNumber matches the pattern.
- **Refs:** `[ad_cap_gus_cta_01…07]`. This belongs in the Cuentas spec; it is listed here only as a cross-reference.

---

## 3. Entities

| Entity (ES / EN) | Identifier | Key fields | Relationships |
|---|---|---|---|
| `Contrato de Gastos` / Expense Contract | `N° de Contrato` (auto, reusable on delete) | supplier, `Tipo` (Normal/Especial-CO), `Solicitante`, `Concepto`, `Detalle`, `Moneda`, `Cotización`, `Desde/Hasta`, `Total del Contrato`, `Renovación automática` (+ `Vto. para Cancelar Renovación Automática`), `Estado`, `Fecha de Creación`, `Aprobador`, `Con Apertura`, `Apertura C. Costos`, JobNumber mode (`Único`/`Apertura`), `Apertura por JobNumber` | 1→N Expense Requests (one per invoice per month); N→1 Supplier, Concept |
| Contract month line / Monthly schedule | (contract, month) | `Importe a Facturar`, `Cant. de Facturas`, `Devengamiento` per month | generates requests |
| Distribution line / Allocation line | row | `Nº CC`, `JobNumber`, `Nº O.T.`, `Porcentaje` or `Importe`, `División` | on contracts and requests |
| `Solicitud de Gastos` / Expense Request | `N° Solicitud` (auto sequential, reusable on delete) | `Fecha`, `Solicitante`, `Concepto`, `Cuenta Contable` (derived), `Detalle`, `Importe` (net), `Moneda`, `Cotización`, `Tipo` (Débito/Crédito), `División de subcuenta`, `Bienes de uso`, `Tipo Proveedor` (Externo/Interno), `Proveedor` or `Cuenta`, `N° Orden de Compra`, `N° Factura`, `Fecha Factura`, `Impuesto al Timbre` (CO), `Timbre`/`Impuesto sin Timbre` (GT), `Estado`, `Aprobado por`, `Rechazado por`, `Descripción de rechazo`, `Contrato`, `Fecha Contabilización`, `Fecha Pago`, `Con Apertura`, `Meses de Diferimiento`, `Inicio Diferimiento`, `Vida útil` | N→1 Contract (optional); parent/child via "Solicitudes Generadas" (multi-invoice); 1→N items; N→1 PO; 1→1 supplier invoice (CxP); → Fixed Asset |
| Request item / Line item | row | `Cantidad`, `Precio Unitario`, `Subtotal`, price per division | when item breakdown is ON |
| Subaccount breakdown line | row | `N° Cuenta`, `Cuenta Contable`, `N° Subcuenta`, `SubCuenta`, `Importe` | cannot be combined with allocation codes |
| `Orden de Compra de Gastos` / Expense PO | `Nº Orden de Compra` (auto) | `Tipo` (by Solicitud / by Proveedor), `Fecha` (today), `Moneda`, `Plazo de Pago`, items (`Selecc.`, `Descripción`, amount), `Total Orden`, approval state | N→N Requests (by-supplier mode); N→1 Supplier |
| `Presupuesto de Gastos` / Expense Budget cell | (year, CC, [division], GL account or grouping, month) | budgeted amount | compared to GL actuals |
| `Planilla de Gastos` / Expense Sheet | `Nº de Planilla` (sequence per user) | `Gastos Efectuados Por`, `Tipo de Gastos` (Local/Viaje), `Descripción`, `Moneda de Rendición`, `Cotización`, `Observaciones`, state, totals (`Total`, `Anticipo Entregado`, `Saldos a favor de la Agencia`, `Saldos a favor del Empleado`, `Devolución`) | 1→N lines; 1→1 Settlement; N→1 user (employee subaccount) |
| Expense sheet line | row | `Fecha`, `Ciudad`, `Detalle`, `Concepto`, `Moneda`, amount columns (`Alimentación`, `Transporte/Estacionamiento`, `Hotel`, `Otros`), `Cotización`, `Total`, `N° Cli.`, `N° O.T.`, `Centro de Costo`, `División`, attachment | → Client, OT, CC, Division |
| `Planilla de Costos` / Cost Sheet | `Nº de Planilla` (per user) | `Costos Efectuados Por`, `Descripción`, `Moneda de Rendición`, `Cotización`, `Mes/Año`, `Estimado`, `Ítem`, totals (`Total`, `Anticipos`, `Devolución`) | N→1 Production Estimate item |
| Cost sheet line | row | `Fecha`, `Detalle`, `Moneda`, `Importe`, `Cotización`, `Total`, `Centro de Costo`, `División` | |
| `Planilla de Fondo Fijo` / Petty-cash Sheet | `Nº de Planilla` (global sequence) | `Descripción`, `Moneda de Rendición`, `Cotización`, `Cuenta` (fund GL account, obs 51), `Saldo de la cuenta`, `Planillas no Contabilizadas`, `Saldo Actual Fondo Fijo`, state | 1→N lines; N→1 fund account |
| Petty-cash line | row | `Fecha`, `Colaborador`, `Aprobado por`, `Detalle`, `Concepto`, `Moneda`, `Importe`, `Cotización`, `Total`, `N° Cli.`, `N° O.T.`, `Centro de Costo`, `División` | |
| `Rendición` (Gastos / Costos / Fondo Fijo) / Settlement | `Ejercicio` + `N° Rendición` (sequential) | `Planilla`, `Sub-cuenta` (employee) or fund account, `Moneda Rendición`, receipts, per-line account/concept/VAT/CC/`Deducible`/`Apl IVA`, state (provisional/posted/paid/void), totals, unpaid balance, refund, payment order ref | 1→1 Sheet; 1→N Receipts; → payment order / collection |
| Supporting receipt (`Comprobante`) | supplier + doc number | `Proveedor` (name), `Tipo IVA`, tax ID (`CUIT/NIT/RUT/RFC`), `Tipo Comprobante` (Factura/NC), `Factura N°`, `Fecha`, `Moneda`, `Cotización`, `Importe Neto`, tax amounts (manual), CAI/CAE/fiscal controller, country fields | N→1 Occasional supplier (optional) |
| `Proveedor para Rendiciones y Fondos Fijos` / Occasional Supplier | auto code | `Nombre`, `Nombre Abreviado`, `Orden del cheque`, `Vigente`, `Tipo de responsable`, tax ID, `Plazo de pago`, `Tipo de persona` (legal entity or individual), `Jurisdicción`, uses NIT, VAT withholding %, address/phones/email | no current account; used only to prefill receipts |
| `Centro de Costos` / Cost Center | auto code | `Descripción`, `Grupo de Centro Costos`, `Vigente` | N→1 CC Group |
| `Grupo de Centros de Costos` | auto code | `Descripción`, `Vigente` | 1→N CC |
| `Código de Apertura por Centro de Costo` / CC Allocation Code | auto code | `Descripción`, lines (CC, %), each with sub-lines (Division, %) | used on requests and contracts |
| JobNumber Allocation Code | (maintained in Accounting masters) | JobNumbers with % | used on requests and contracts |
| `Concepto` / Expense Concept | auto code | `Descripción`, `Cuenta Contable`, `Periódico (Mensual)`, `Facturación Múltiple`, `Apertura Ítems en Sol. de Gtos.`, `Vigente`, second-approval flag, external interface code | N→1 GL account (result account, Gastos grouping) |
| `División` / Division (business unit) | auto code | `Descripción`, `Grupo de División`, `Vigente`, `Ingresos Compartidos (C. Medios / Agencia)` + intercompany accounts, address, tax ID | N→1 Division Group; N→N Country Division Group |
| `Grupo de Divisiones` | auto code | `Descripción`, `Vigente` | |
| `Grupo de Divisiones País` | auto code | `Descripción`, `Sigla`, `Vigente`, applicable group companies | |
| Special suppliers | master records | "Rendición de Gastos", "Rendición de Costos", "Fondo Fijo" | flagged as special petty-cash suppliers |
| Special GL accounts | obs codes | `83` expense-report account, `84` cost-report account, `51` petty-cash account, `S1` subaccount bridge, `B1` fixed-asset original value, `21/22` income accounts for internal supplier | |

---

## 4. Document lifecycles

### 4.1 Expense Contract
`Pendiente de aprobar` ⇄ (`Aprobar` / `Desaprobar`) `Aprobado`; `Pendiente de aprobar` ⇄ (`Rechazar` / `Recuperar rechazo`) `Rechazado`. **Delete** is possible and frees the number. Approval generates the child requests. Auto-renewal can extend validity unless the contract is cancelled before the cancellation deadline. **[inferred]** Disapproving after child requests have been invoiced is not covered by the manual.

### 4.2 Expense Request
Initial state depends on the requester's level:
- `Normal`: created pending approval.
- `Auto-aprobada`: requester has Supervisor level.
- `Pendiente de Aprobar`: an exception where some user approves the supervisor.

Then:
- → `Aprobada` (Approve)
- → `Rechazada` (Reject + reason)
- → `Devengada` (accrual run, no invoice yet)
- → `Contabilizada` (supplier invoice entered)
- Payment date is stamped when the payment order is issued.

Back-transitions: `Aprobada` → pending via Disapprove (blocked if a PO exists); `Devengada` → `Aprobada` via Anular/Elimina Dev. **[inferred]**
Multi-invoice: a partial invoice creates a child request for the invoiced amount, and the parent's remaining amount drops by the same figure.

### 4.3 Expense PO
Created → (if approval is enabled) pending approval → approved → consumed by the supplier invoice. Can be deleted with no trace. Voided POs can be listed (`incluir anuladas`), so a void state exists **[ambiguity]**. While a PO exists, its source request items are frozen.

### 4.4 Sheets (Expense, Cost, Petty cash)
`Pendiente` (being edited; delete allowed) → `Enviado` (locked) → either `No Enviar` back to `Pendiente`, or `Autorizado` → `Cont. provisoria` (settlement saved provisionally) → `Contabilizado` (settlement posted).
- `Autorizado` → `Enviado` via De-authorize, unless the settlement is posted.
- `Anulado/Anulada`: an approved sheet sent back for revalidation, for example via settlement **Rechazar**.
- Petty cash only: `Rechazada` via **Anular**, when the voiding configuration is ON.
- The dynamic report lists a longer set: created, pending, sent, approved, disapproved, posted, plus provisional and intermediate approval when the provisional circuit is enabled.

### 4.5 Settlement (Rendición)
New (from an authorized sheet) → `Provisoria` (Grabar provisorio; no GL) → `Contabilizada` (Grabar; GL + VAT subledger; immutable) → `Pagada` (reimbursement or replenishment payment order issued) or `Anulada`. **Rechazar** returns the sheet to its creator with reasons. **Eliminar** removes the settlement and its posting with no audit trail.

### 4.6 Reimbursement / advance netting / refund
`Saldo` = sum of line totals − advance delivered.
- Positive (owed to the employee): **Pagar** → payment order.
- Negative (owed to the agency): the employee returns cash → `Devolución` field on the sheet → **Contab. Devol.** on the settlement → collection receipt.
- Zero: closed with no cash movement.

### 4.7 Rebilling to clients
The manual describes **no explicit rebilling document** in this module. Client impact happens through allocation:
- Spend charged to a client's **specific OT** reduces that job's margin ("lower profit").
- Spend charged to a client's **generic OT** shows as client-servicing cost.
- **Production costs** reported through cost sheets land on an item of a *client-approved* production estimate. That estimate is the vehicle that gets billed to the client in Production/Cuentas. **[inferred]**
- Internal-supplier requests turn a spend into a reduction of OT income.
See §11.

---

## 5. Business rules & calculations

1. **Currency eligibility.** Contracts, requests, POs and expense sheets can use only the local currency or foreign currencies whose daily rate the system maintains. Sheet *lines* can use uncontrolled foreign currencies with a rate typed by hand.
2. **Line conversion.** For sheet lines, `Total = Importe × Cotización`, converted to the sheet's reporting currency. When the reporting currency is foreign, a header rate converts it to local currency.
3. **Cost-sheet currency** must equal the currency of the production estimate item. **Petty-cash sheet currency** must equal the currency of the fund account.
4. **Cost-sheet cap.** Total reported costs ≤ the amount of the estimate item, and the estimate must be client-approved.
5. **Request amount** is net of VAT. With item breakdown ON, `Importe = Σ(Cantidad × Precio Unitario)`.
6. **Detail-sum equality.** On manual allocation, the detail lines must add up to the header `Importe`.
7. **Allocation code integrity.** Cost-center percentages total 100%. Within each cost center, the division percentages total 100%. JobNumber allocation codes apply percentages across campaigns. **[inferred]** They also total 100%.
8. **Allocation split.** Line amount = request net × CC% × division% × JobNumber% when codes are combined. **[inferred]** The manual says only that the system fills the detail automatically.
9. **Exclusivity.** A subaccount breakdown cannot be combined with CC or JobNumber allocation codes.
10. **OT eligibility.** Spend can go only to OTs that are open or provisionally/partially closed.
11. **Control granularity.** With JobNumber control OFF, spend goes only to product-generic OTs, or client-generic JobNumbers in some guides. With it ON, any JobNumber is allowed, including generic ones when the spend covers several jobs and won't be split.
12. **Agency overhead** goes to the special client AGENCY and its generic project.
13. **Approval authority.**
    - (a) A Supervisor on the screen can approve anyone.
    - (b) An assigned approver can approve the users they control. One user may have several approvers, **each with its own amount limit**.
    - (c) Sheet approvers need level < 3 on the screen.
    - (d) Self-approval needs both the agency setting and the "Expense Approver User" class.
    - (e) With self-approval disabled, creator ≠ approver.
    - (f) Requests on flagged concepts need a second approval.
    - (g) Requests can be copied only by level-1 users. A user without Supervisor level sees only their own requests in lists.
14. **Contract approval guard.** A contract cannot be approved while any of its months belongs to a fiscal year that does not yet exist.
15. **Contract to request generation.** For each month m with `Cant. de Facturas` = k_m > 0, the system creates k_m requests in Approved state. **[inferred]** Each gets `Importe a Facturar_m / k_m`.
16. **Periodic concept prerequisite.** A contract needs a concept flagged periodic. Without one, only plain requests are possible. Copying requests also needs periodic concepts.
17. **Deferral.** Number of periods accrued = `Meses de Diferimiento` + 1 (the current month plus N more). Each period's entry is (net / (N+1)) split by the distribution percentages **[inferred: equal installments]**. Accrual entries are not auto-reversed. The invoice is posted against the "expenses to accrue" account.
18. **PO guards.** A PO can be raised only on approved requests. If POs are mandatory, the invoice is blocked without one. If PO approval is mandatory, the invoice is blocked until the PO is approved. A request that has a PO cannot be edited, deleted, rejected or disapproved.
19. **Multi-invoice.** Partial invoice amount I against a request of amount A creates a child request of amount I and leaves A − I outstanding on the parent. Only one detail line is allowed before invoicing.
20. **Fixed asset trigger.** If the concept's account has obs `B1`, the fixed asset is created when the supplier invoice is entered, with the useful life captured on the request.
21. **Internal supplier.** The posting goes to an income account with obs 21/22 and turns into a loss on the OT.
22. **Credit type.** `Crédito` requests represent supplier credit notes or refunds in the agency's favor.
23. **Taxes on sheets.** Sheet lines carry gross amounts. Each taxed receipt issued in the agency's name gets its own line. Untaxed tickets may be added together on one line. A receipt covering several services is split across lines by concept, pro rata.
24. **VAT derivation in a settlement.** `VAT = reported gross − net entered`. Other tax amounts are typed by hand; **the system does not compute VAT rates**. If no VAT is shown, use VAT code `0000`.
25. **VAT account default.** If the expense or cost account has a linked VAT-credit account, `Apl IVA` defaults on. Otherwise the user must pick the VAT account. Linking every expense account to a VAT account is recommended so requests can show a VAT estimate.
26. **Deductible flag.** On by default for each line (income-tax deductibility in Argentina). Can be cleared. It feeds the deductible/non-deductible filters in reports.
27. **Non-split receipts** are combined into **one exempt entry** in the VAT purchase subledger, under the settlement or fund number.
28. **Closed periods.** A settlement cannot be posted into a closed fiscal year. Budget cannot be entered for closed months, which are shown in orange.
29. **Budget scope.** Only result accounts in subcategory *Otros Gastos* can be budgeted. Actuals include every posting to those accounts, whatever the source. The budget ignores contracts and requests that are still awaiting approval.
30. **Projected.** For each month: closed → actual; open → budget.
31. **Petty-cash available balance** = GL balance of the fund account − Σ(sheets sent or authorized but not yet posted).
32. **Sheet balance.**
    - `Saldo a favor Agencia` = advance − total, when positive.
    - `Saldo a favor Empleado` = total − advance, when positive. With no advance, this equals the total.
    - The returned cash brings the agency-side balance to zero.
33. **Cost-estimate tax adjustment.** After a cost settlement splits out tax T, reduce the estimate item's pending amount by T. This is allowed only once the item shows as supplier-invoiced.
34. **Settlement account edits.** In expense and petty-cash settlements, accounting can change the account or concept by F2 without bouncing the sheet. In cost settlements it cannot, because the account follows the estimate's service type.
35. **Deletion semantics.** Contracts, requests, POs, pending sheets and settlements are hard-deleted, and their numbers are freed for contracts, requests and sheets. Master records can be deleted only if they were never used.
36. **Fee contracts.** Not part of this module; see P20.

---

## 6. Accounting impacts

The manual names the accounts but rarely the full entries. Rows marked **[inferred]** were reconstructed from standard practice and the account roles described.

| Event | Debit | Credit | Notes |
|---|---|---|---|
| Expense request invoiced (CxP) | Concept's expense account, split by CC / division / JobNumber / OT; VAT credit | Supplier current account | Request → `Contabilizada` **[inferred structure]** |
| Fixed-asset request invoiced | Fixed-asset account (obs B1); VAT | Supplier | Creates a fixed-asset record with useful life |
| Internal-supplier request | (allocation to OT) | Income account obs 21/22 (reduction) | Shows as a loss on the OT **[inferred side]** |
| Subaccount breakdown (reimbursement) | Employee subaccount on the S1 bridge account | — | Amount to be recovered from the employee **[inferred]** |
| Deferral run (`Devengar`), each month | Expense account (by distribution) | "Expenses to accrue" account | N+1 entries, not auto-reversed |
| Invoice on a deferred request | "Expenses to accrue" account | Supplier | Clears the accrual |
| Void accrual (`Anular Dev.`) | Reversal on the void date | | **[inferred]** |
| Advance to employee (Treasury) | Employee subaccount on account obs 83 (expenses) or 84 (costs) | Cash/Bank | **[inferred]** from "Asocia Anticipos" and the netting logic |
| Expense settlement posted | Expense accounts (per line: CC, client/OT, division), VAT credit for split-out receipts | Employee subaccount on account obs 83 | Discriminated receipts go to the VAT purchase subledger individually; the rest go as one exempt entry |
| Cost settlement posted | Cost account from the estimate item's service type (job-linked), VAT credit | Employee subaccount on account obs 84 | Then adjust the estimate item for the tax portion |
| Reimbursement payment (`Pagar`) | Employee subaccount (83/84) | Cash/Bank | Payment order |
| Refund of unused advance (`Contab. Devol.`) | Cash/Bank | Employee subaccount (83/84) | Collection receipt, with division chosen |
| Petty-cash creation | Fund account (obs 51) | Cash/Bank | Payment order **[Treasury]** |
| Petty-cash settlement posted | Expense accounts + VAT | Fund account (obs 51) | **[inferred]**; consistent with the available balance falling only after posting |
| Petty-cash replenishment | Fund account (obs 51) | Cash/Bank | Payment order to the beneficiary/custodian |
| Provisional save of any settlement | — | — | No GL impact |

**Analytic dimensions** on each expense posting: cost center (expense accounts only), division (all result accounts), client, JobNumber/OT, concept (subclassification of the account), deductible flag.

---

## 7. Cross-module handoffs

| Counterpart | Direction | Object / trigger |
|---|---|---|
| **Cuentas (jobs/JobNumbers, OTs, clients)** | in | OT and JobNumber status (open or provisionally closed), client list, AGENCY client and its generic project, generic OTs per client/product; JobNumber allocation codes |
| **Cuentas (fee contracts)** | n/a | Fee contract guides are filed here but belong to Cuentas (P20) |
| **Producción (production estimates)** | in/out | Cost sheets need a client-approved estimate and an item assigned to "Rendición de costos"; the settlement consumes the item, and a tax adjustment on the item follows; "Detalle de Anticipos y Rendiciones de Costo" view |
| **CxP (Accounts Payable)** | out | Approved request (or approved PO) → supplier invoice entry → request `Contabilizada`; partial invoices spawn child requests; special suppliers live in the CxP supplier master |
| **Tesorería (Treasury)** | out/in | Payment orders for supplier invoices (pay date stamped back on the request), employee reimbursements (`Pagar`), petty-cash creation and replenishment (`Reponer`), collections for advance refunds (`Contab. Devol.`); advances to employees; accounts 83/84/51/S1 must be enabled for Treasury postings |
| **Contabilidad (GL, analytic)** | out | Settlement and accrual entries; VAT purchase subledger; fiscal year and period open/close; account observation codes; *Otros Gastos* subcategory for budgeting; account groupings (Principal/Hyperion); CC and division analytics for the P&L by division or division group |
| **Bienes de Uso (Fixed Assets)** | out | Auto-created asset from a B1 request on invoice entry; useful life from the asset-concept master |
| **Usuarios y Seguridad** | in | Approver/controller assignments, amount limits, screen levels (Supervisor, level 1, level < 3), approve-by-client / approve-for-billing flags, default CC per user |
| **CxC (rebilling)** | — | No direct handoff documented (see §11) |
| **Mobile app** | in | Receipt photos linked to sheet lines (`Relacionar adjuntos`) |
| **Email service** | out | PO PDF emailed to the supplier |

---

## 8. Configuration & country-specific behavior

### 8.1 Special configurations (`Configuraciones Especiales – Gastos` and related)
- `Control de Gastos por JobNumber`: allocation by campaign (ON) or by client only (OFF).
- `No Permite Autoaprobar Gastos` / `Permite autoaprobar gastos`: self-approval policy.
- `Orden de compra obligatoria en Gastos`: PO required before the supplier invoice.
- `Aprobación Ordenes de Gastos`: PO approval step.
- `Apertura ítems en Solicitudes de Gastos`: quantity × price item lines on requests; turns on the fixed-asset field.
- `Usa proveedores eventuales`: lightweight occasional-supplier master with no current account.
- `Asocia Anticipos a Planillas de gastos`: links advances to sheets for netting.
- `Aprob. Rend. de Costos por Responsable del Job`: the job owner approves cost sheets.
- `Anulación de Planillas y Rendiciones`: enables Anular on sheets.
- `Usa Planilla Unificada de Gastos y Costos`: unified sheet and settlement (the manual says this was dropped or is unavailable).
- Second approval of requests per concept (name of the flag not given).
- Division usage (`SubEmpresas`): enables division columns and filters, and makes division a mandatory filter in the budget.
- Expense provisioning in use: deferral normally not used.
- Logo printing on POs (`General – Impresión de logo`, Orden de Compra = true); PO print formats.
- `Usa Comp. RG 1361` (Argentina); `Usa Documento Equivalente Régimen Simplificado` (Colombia).

### 8.2 Country specifics
- **Argentina:** CAI (pre-printed), CAE (electronic) or fiscal-controller code on receipts; invoice letter and point of sale; RG 1361 document type; deductible flag tied to income tax; CUIT as the tax ID.
- **Colombia:** contract type `Especial`; stamp tax (`Impuesto al Timbre`) on requests; equivalent document for simplified-regime suppliers (`Nro de Orden`, a notional document number); division shared income includes incentives; NIT.
- **Guatemala:** `Timbre` yes/no and `Impuesto sin Timbre` on requests.
- **Chile:** receipt attributes `Electrónica` and `Boleta de Honorarios`; RUT.
- **Venezuela & Dominican Republic:** `N° Control` (alphanumeric folio number) and invoice type loaded from a `TIPFACT.TXT` file.
- **Dominican Republic:** expense service classification codes 01–11 (personnel; work/supplies/services; leases; fixed-asset expenses; representation; other allowed deductions; financial; extraordinary; cost-of-sales purchases; asset acquisitions; insurance).
- **Mexico:** RFC as the tax ID.
- The occasional-supplier VAT-withholding field is relabeled per country. Taxpayer type and jurisdiction lists vary by country.

---

## 9. Reports & KPIs

| Report | Purpose / filters | KPI it supports |
|---|---|---|
| `Informe Comparativo Final` `[mp301136]` | Budget vs actual for a fiscal year and month range; monthly detail (v4.6+); view by CC or account (with CC, division, concept, optional grouping column); state (all/unassigned/unposted/posted); deductible; responsible; expense accounts only; drill from CC to account, split into direct and indirect | Budget variance per CC/account; direct vs indirect cost mix |
| `Informes de Gastos Totales` `[mp301133]` | Variation analysis; criteria: CC group, CC, client, requester, authorizer, account, supplier, concept; detail by account/concept; state; deductible; monthly breakdown and cumulative; currency; division; drill-down; charts | Spend trend per dimension; month-on-month growth |
| `Informes de Solicitudes de Gastos` `[mp301132]` | Requests grouped by supplier/requester/authorizer/account/concept/client/product/department; state (unapproved/unposted/posted); drill to request | Approval backlog; spend by requester |
| `Listado de Solicitudes de Gastos` `[mp301131]` | Criteria: supplier, account, concept, CC, authorizer, requester, client, amount range, accrual control, entry date; state; deferral (with cut-off date); with/without PO; divisions; include deleted; invoice detail; deferral months; **estimated VAT** (net/VAT/total for cash flow); origin and generated request columns; mass approve; copy | Cash-flow forecast of committed spend; PO compliance rate; deferred balance at cut-off |
| `Listado de Contratos de Gastos Devengados` `[mp309259]` | By supplier/month/contract; installment invoiced or not; date range on creation; supplier, division, currency | Uninvoiced contract installments (accrual exposure) |
| `Listado de Órdenes de Compra de Gastos` `[mp301140]` | General or by supplier; date range; include voided; generation and invoice posting dates; batch print/PDF | PO-to-invoice cycle time |
| `Listado de Facturas de Proveedores Eventuales` `[mp302704]` | Receipts captured in settlements; date; settlement type; state (posted/provisional); supplier range; sort; payment order column | Spend with occasional suppliers |
| `Listado de Planilla de Gastos / Costos / Fondo Fijo` | Date, users (own plus those they approve), sheet state, settlement state; click to open; shows employee subaccount balance | Sheets awaiting approval; aging; employee balances |
| `Listado de Rendiciones de Gastos / Costos / Fondo Fijo` | By posting date; grouping, column chooser, autofilter, expand/collapse | Posted settlement volume |
| `Rendiciones de Costos Deducibles` `[mp302766]` | Cost settlements filtered by deductible flag | Deductible vs non-deductible split (income tax) |
| `Reporte Dinámico de Rendición de Gastos` `[mp302030_rengtos]` | Settlement analysis by campaign per collaborator; filters on date, users, state; field picker | Staff spend per campaign |
| `Reporte dinámico de Gastos` `[mp402832_6]` | User-built pivot/grid; saved templates; filters on date, sheet state, settlement state, collaborator; Excel export; **weekly scheduled generation at 00:00**; online vs offline (snapshot DB) source; costly online queries are forced offline | Self-service analytics |
| `Presupuesto de Gastos` tabs | Budgeted / Actual / Projected; per-month comparison | Full-year forecast (actual + remaining budget) |
| Petty-cash "Datos contables" panel | Fund balance, unposted sheets, available | Fund utilization; when to replenish |

Suggested KPIs for the repo: approval cycle time (request created → approved; sheet sent → authorized → posted); share of spend with a PO; budget variance % by CC; deferred-expense balance; uninvoiced contract installments; open employee advances and aging; petty-cash utilization %; share of spend charged to client OTs vs AGENCY; deductible ratio.

---

## 10. Agentic-skill implications

### 10.1 Candidate atomic skills (jobs)
1. `expense-config-advisor`: reads the agency's policy and outputs the configuration flags (P1), the approver matrix and the limits.
2. `expense-master-maintainer`: creates or validates CCs, groups, divisions, concepts and allocation codes (enforcing 100% totals and the "never used" rule for deletion).
3. `expense-contract-builder`: turns a lease or subscription agreement (PDF) into a contract with a monthly schedule, invoice counts, accrual rows and distribution.
4. `expense-contract-approver`: checks the fiscal year exists and approver ≠ creator, then approves and emits the generated requests.
5. `expense-request-intake`: turns natural language, an email or a quote into a request. Picks the concept (and therefore the account), the net amount, currency/rate, type, supplier and allocation. Detects the fixed-asset, multi-invoice, refund and reimbursement variants.
6. `expense-request-approver`: routes to the right approver by limit and concept second-approval flag; handles approve, reject-with-reason and disapprove (PO guard).
7. `expense-po-issuer`: groups approved requests by supplier, drafts the PO, renders the PDF and emails it.
8. `expense-accrual-scheduler`: produces the deferral schedule and entries; handles void/erase.
9. `expense-sheet-assistant` (employee-facing): turns receipt photos into sheet lines. Classifies concept and category column, splits multi-service receipts, flags taxed receipts that need their own line, picks client/OT/CC/division, computes totals and balance against the advance, then submits.
10. `cost-sheet-assistant`: same, but validates against the client-approved estimate item (currency, remaining amount).
11. `petty-cash-custodian`: keeps the sheet up to date, watches the available balance, triggers submission before depletion.
12. `sheet-reviewer` (approver-facing): checks policy (limits, category caps, duplicates, missing receipts, closed or invalid OTs) and recommends authorize, bounce (with reasons per line) or line deletion.
13. `settlement-poster` (accounting-facing): OCR and tax-ID lookup of receipts; VAT = gross − net; country fiscal fields (CAI/CAE, folio, DR service code); VAT account defaulting; deductible flag; provisional save; final post.
14. `settlement-cash-closer`: decides between reimburse, refund and zero; prepares payment-order or receipt drafts for Treasury; replenishes petty cash.
15. `estimate-tax-adjuster`: after a cost settlement, proposes the reduction of the estimate item's pending amount.
16. `expense-budget-planner`: drafts the budget per CC × account × month (open months only); builds the projection; explains variances.
17. `expense-reporting-analyst`: produces the §9 reports and KPIs; schedules snapshots.

### 10.2 Deterministic calculations worth a tool
- `allocate(amount, cc_code, job_code | lines)` → lines with rounding remainder put on the last line; validates 100% totals.
- `contract_to_requests(schedule)` → list of (month, amount, invoice#).
- `deferral_schedule(net, months_N, start, distribution)` → N+1 entries.
- `multi_invoice_split(request, invoice_amount)` → child request plus updated parent.
- `fx_convert(amount, rate, to_reporting, to_local)`.
- `vat_from_gross(gross, net)` and `vat_code_default(account)`.
- `sheet_balance(total, advance, refund)` → owed-to-agency / owed-to-employee / zero.
- `petty_cash_available(gl_balance, unposted_sheets)`.
- `budget_projection(budget, actuals, closed_months)` and `variance()`.
- `approval_route(user, amount, concept)` → ordered approver list respecting limits, self-approval and second approval.
- `estimate_tax_adjustment(item_pending, tax_split)`.
- Validators: OT open status; currency eligibility; closed period; PO-mandatory gate; fiscal-year existence.

### 10.3 Controls to encode
- Segregation of duties: creator ≠ approver unless self-approval is configured; payment and collection permissions separate from settlement posting.
- Amount limits per approver; second approval per concept.
- Three-way-style gate: request approved → PO (approved) → invoice.
- Sheet lock after Send; edits only through a bounce; no de-authorization after posting.
- Closed-period guard on settlements and budget.
- Cost sheets capped by the approved estimate item; currency match.
- Required receipt data for taxed receipts (tax ID, document number, CAI/CAE).
- Hard deletes in the source system: an agentic re-implementation should **replace them with soft-delete and an audit log**.

### 10.4 Exceptions / edge cases
- Foreign currency missing from the list: ask administration to create it, for sheet use only.
- Receipts that mix services: split them pro rata.
- Petty cash nearly empty: submit early.
- Wrong account found during settlement: change it via F2 (gastos/FF), or fix the estimate (costos).
- Contract months in an unopened fiscal year: defer approval.
- Request with a PO that needs changes: remove it from the PO first.
- Settlement with tax split out: adjust the estimate or the item will stay pending.
- Report "missing data" caused by an inclusive date range (end of month): validate date ranges.
- Expensive online report: route it to the offline snapshot.

---

## 11. Gaps / ambiguities

1. **Academia videos.** All eight Academia pages (concepts 14:02, masters 10:52, approval circuit 06:44, request 14:11, petty cash 13:39, expense settlement 09:50, cost settlement 11:09, budget 12:12) contain only titles and durations, no content.
2. **Menu items with no page:** `Contratos de Fee Fijo` (handled in Cuentas), `Cuadro de Gastos`, `Plazas de Medición de Audiencia` (listed under Expense masters; probably misfiled from Media).
3. **Unavailable or dropped options:** `Tipo de Gastos`, `Planilla de Gastos y Costos` (unified), and `Rendición de Gastos y Costos` (a stub only).
4. **Rebilling to clients** of overhead or staff expenses (for example travel billed back to a client) is not described. It is unclear whether expenses on client OTs can flow to CxC invoicing or only reduce margin. Only production costs, through estimates, are clearly client-facing.
5. **Approval amount limits.** The manual says limits exist per approver, but not how they cascade (escalation when over the limit, sequential vs any-of) or whether they apply to requests as well as sheets.
6. **Approval levels.** The meanings of "level 1", "level < 3" and "Supervisor" are not defined in this file; they come from Users & Security.
7. **Contract-to-request amounts.** How the monthly amount is split when several invoices are expected is not stated (equal split assumed).
8. **Deferral amounts.** Equal monthly installments are assumed. The relationship to the contract's `Devengamiento` row is unclear.
9. **Inconsistent wording on the special supplier.** The FF and Costos settlement pages say "Rendición de Costo" must exist as a special FF supplier, while the sheet pages say "Rendición de gastos", "Rendición de costos" and "Fondo Fijo". This is probably copy-paste. Assume one special supplier per flow.
10. **Expense settlement action buttons.** `Reponer` on Gastos and Costos settlements is described with petty-cash wording, so it is unclear whether it is the same as `Pagar`.
11. **Budget presentation.** One page says the summarized presentation does not accept data entry; the guides say it lets you budget by account grouping. Contradictory.
12. **PO states.** Approval and void states for POs are implied but not listed. It is not clear whether an approved PO can be edited.
13. **Internal supplier.** The exact debit/credit sides and the role of obs codes 21 vs 22 are not explained.
14. **Advance issuance.** How advances to employees are created (in Treasury) and linked to a specific sheet under `Asocia Anticipos` is not described here.
15. **Request state naming.** `Normal` vs `Pendiente de Aprobar` overlap. `Rechazada` appears in list filters but not in the state definitions.
16. **Settlement `Eliminar`.** It is said to leave no record of the earlier posting. Whether GL entries are reversed or physically deleted is unclear.
17. **Approval circuit for POs.** Who counts as a "PO approver" profile is not specified.
18. **Fee contract guides** (seven pages) are misfiled under Planilla de Gastos. They are to be covered by the Cuentas spec.
19. **Cost-sheet line concept.** Cost lines have no concept column. Whether several estimate items can be reported on one sheet is unclear (the header takes a single item).
20. **Multi-currency settlement payment.** `Pagar` allows a different payment currency. FX difference handling is not described.
