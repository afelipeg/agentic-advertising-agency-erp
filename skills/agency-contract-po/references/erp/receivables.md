# Accounts Receivable (Cuentas por Cobrar)

> **Provenance.** Functional reverse engineering of a reference agency ERP, derived from its publicly accessible help documentation (reviewed 2026-10-11). Content is paraphrased and restructured; it is not vendor documentation, source code or an endorsement. Bracketed ids such as `[mp301010]` identify the source page used as evidence. Items marked *inferred*, *assumed* or listed under gaps must be validated with your own controller, tax adviser and system owner before they drive postings or payments.

Source: the reference ERP's help documentation (AR branch plus training-video stubs). Everything below is paraphrased for an MIT-licensed open-source skills repo. Spanish UI or field names appear in backticks only where they help trace back to the source. Source references use the help file name, e.g. `[mp302009]`.

> Note on the Academia pages: the eight Academia entries (`conceptos-generales-de-cuenta2`, `controles-a-realizar`, `tipos-de-facturacion---0749`, `facturacion-de-planes-de-medio`, `facturacion-de-produccion---13`, `facturacion-manual---bienes-de`, `facturacion-electronica`, `reportes-y-listados2`) only hold video titles and running times: general AR concepts, a 30-minute "controls to perform" session, billing types, billing indirect media plans, production billing, manual/fixed-asset/advance-sale billing, e-invoicing, and reports. They contain no text. Their topics line up with the process catalogue below.

---

## 1. Purpose and position in the end-to-end circuit

The AR module is where the agency turns the work it has committed to and executed into legal sales documents, and then into cash. In an agency ERP, the circuit runs like this:

1. **Upstream (commercial / operations).** Media plans (`Pauta` / `Plan de Medios`) contain advertising orders (`Orden de Publicidad`). Production budgets (`Presupuesto de Producción`, also called `Estimado`) contain line items. Fee contracts (`Contratos de Fee`) contain instalments (`cuotas`). All three hang off a campaign (`JobNumber`) and a work order (`OT`, `Orden de Trabajo`). Once one of them is client-approved and approved for billing, it creates a **pending-to-bill** record (`pendiente de facturar`).
2. **AR billing (this module).** It consumes pending-to-bill records, or builds manual documents, and produces invoices (`Factura`), debit notes (`Nota de Débito`, ND), credit notes (`Nota de Crédito`, NC), Mexican annexes (`Anexo`) and Colombian expense-reimbursement documents (`R/Gastos`). It also bills the agency's *own* revenue from suppliers: supplier commissions, volume incentives and overcommissions.
3. **Fiscal authorization.** E-invoices are validated with the tax authority: CAE from AFIP in Argentina, XML stamping by a PAC in Mexico, DGI TXT files, and so on. The validated document is then printed or exported to PDF and emailed.
4. **AR collection.** Receipts (`Recibo`) apply cash, cheques, transfers, documents and withholding certificates against open items. Customer advances are recorded and later re-applied. Supplier refunds and returned cost advances are also collected here.
5. **Downstream.** The general ledger receives automatic entries from every document. Treasury receives the funds and the third-party cheque portfolio. Accounts payable is reconciled through client-invoice-to-supplier-invoice relationship reports, "collected but not paid" analysis, and finder-fee expense requests. Group reporting covers intercompany flows and Hyperion codes.

AR is the bridge between operations, where profit is planned as sale minus cost, and finance, where revenue and receivables are recognized. It also enforces credit risk (credit limits) and fiscal compliance (VAT books and withholding certificates).

---

## 2. Process catalogue

Conventions: **T** = trigger, **A** = actor, **S** = steps, **I** = inputs, **O** = outputs, **ST** = state transitions, **AP** = approvals or controls.

### 2.1 Billing sources (where billable amounts come from)

| Source | Origin record | Billing type (`Tipo de Facturación`) | Screen |
|---|---|---|---|
| Media investment plus indirect commission | Media plan orders / items | `Inversión/Comisión Indirecta`, subtype Medios | `[mp302009]` |
| Media agency service billed separately | Plans flagged commission = `General` | `Comisión General`, subtype Medios | `[mp302009]` |
| Media order differences | Supplier-invoice reconciliation differences | `Inversión/Comisión Indirecta`, subtype Medios, items marked as differences | `[facturar-diferencias-en-las-ordenes]` |
| Production investment plus indirect commission | Production budget items | `Inversión/Comisión Indirecta`, subtype Producción | `[mp302009]` |
| Production agency service billed separately | Budgets flagged `General` | `Comisión General`, subtype Producción | `[mp302009]` |
| Fee instalments | Fee contracts (media or production) | `Cuotas de Fee` | `[facturar-cuotas-de-fee-*]` |
| Hourly fee (base plus excess) | Fee contracts by hours | Instalments (hours feed them) | `[mp302793]` |
| Advance sale (pre-billing) | None (no plan or budget yet) | Manual, account flagged VA/VC | `[mp301177_soloventaanticipada]` |
| Manual documents | None (free entry), origin General/Medios/Producción | Manual | `[factura-manual]` |
| Fixed-asset sale | Fixed-asset register | Manual (asset) | `[mp301177_solobienesdeuso]` |
| Supplier commissions ("confidential") | Plan/budget items flagged `Com. Proveedor` | Supplier commission billing | `[mp301190]` |
| Supplier volume incentives | Supplier invoices plus incentive scale | Incentive billing | `[mp301191]` |
| Overcommissions | Overcommission contract plus generated pending | Overcommission billing / refund NC | `[mp302739]`, `[mp302736]`, `[mp302780]` |
| Finder fee | Finder-fee contract plus orders | Produces expense requests (payable side) | `[mp302912]` |
| Expense re-billing (direct billing) | Supplier invoices addressed to the client (Mexico `Anexo`, Colombia `R/Gastos`) | Annex / reimbursement documents | `[mp301008]` (transferred invoices tab) |

**Hard partitioning rule:** one document may contain only one source family. Plans, budgets and fees are never mixed, and media and production are billed apart. The manual states this for the main biller and for supplier commissions. One currency per document.

### 2.2 P-01 Automatic billing of media plans (`Facturación de Medios, Producción y Fees`, subtype Medios)
- **T:** A media plan has been approved for billing and has pending lines. This may happen before ad-verification ("open" plan) or after it ("closed" plan).
- **A:** Billing clerk.
- **I:** Point of sale (`Sucursal Actual`); billing client; debt currency; billing type; payment terms (defaulted from the client or product master, editable to avoid weekends and holidays); salesperson; contact; document currency and exchange rate; document kind (Factura or ND); version (Inicial or Final).
- **S:**
  1. Choose a selection mode: `Por Cliente` (lists everything pending for the client; recommended) or `Por Documento` (plan number plus month/year).
  2. Pick currency, billing type and subtype.
  3. In `Documentos a Facturar`, select a whole plan, specific orders, items (with `Selección por ítem`), or group by any column such as media, zone or product.
  4. Run the controls (§5).
  5. Confirm the selection. This opens the invoice preview (`Visualización de Factura`).
  6. Choose a print format and detail level (`Detalle por día`, `Resumido por ítem`, `Resumido por O.T.`, `Resumido a un texto`, or media summary).
  7. Optionally insert notes, apply a rounding adjustment, or (Colombia/Guatemala) review the withholding window.
  8. Confirm. This creates the document.
  9. Send it to fiscal validation (P-14).
- **O:** An invoice linked to plan, orders, OT and JobNumber, with an automatic journal entry.
- **ST:** Pending lines become billed. With version `Final`, the plan is locked against edits. With version `Inicial`, the plan stays editable, and later deltas surface as new pending differences (positive or negative) once ad-verification and supplier-invoice confirmation are done.
- **AP:** Colour cue: closed (verified) plans are shown differently from unverified ones (red), so the clerk knows an estimate is being billed. This is not a block.
- **Options:** VAT perception pass-through (`traslado percepción IVA`) is ticked by default and has no effect unless the agency is configured for it. You can also force the invoice at gross plan value and issue the plan's NC-type discounts as a separate credit note.
- **Additional costs** (`Costos Adicionales`) appear as one aggregated item. They can be billed with the investment or separately, but never partially or item by item. Config `Muestra importe en selección` helps identify that line.

### 2.3 P-02 Automatic billing of production budgets (subtype Producción)
Same skeleton as P-01, with these differences:
- Budgets can be selected whole or item by item, and you can group the list by any column.
- **Partial billing (advances):** (a) `% de anticipo` applied to the whole selection; or (b) `Seleccionar Importes por ítem`, where after confirmation a grid asks for the `A Facturar` amount per item. Either way, a partly billed item **can no longer be edited**. Best practice is to split the work into two items, one for the advance and one for the remainder.
- Detail formats: `Resumido por ítem` (each item's full text and amount), `Resumido por O.T.` (first item's text with the budget total), `Resumido a un texto` (a default text such as "grouped billing of several budgets", which the user overwrites).
- Restriction (repeated across user guides): the budget must be approved for billing; one currency per document.
- Variants documented as user guides: several budgets in one invoice; several items of several budgets; partial amounts per item; a budget picked directly by estimate number and month/year; agency service only for indirect items (requires budget `Facturación = General` and investment already billed); agency service for direct items; applying budgets to an advance sale (P-06).

### 2.4 P-03 Agency-service-only billing (`Comisión General`)
- **T:** The plan header or budget header has `Facturación = General`, meaning commission is billed separately from investment, and the investment has already been billed.
- **S:** Choose billing type `Comisión General` and the subtype, select documents, confirm.
- **Direct items** (supplier bills the client directly): the agency bills only its service fee, using billing type `Inversión/Comisión Indirecta` filtered to direct items.
- **Peru:** general commission and advance commission can be combined in a single media invoice when the plan qualifies.

### 2.5 P-04 Fee instalment billing (`Cuotas de Fee`)
- **T:** A client fee contract is approved for billing. Its instalments are due.
- **S:** Billing type `Cuotas de Fee`, subtype Medios or Producción, select instalments, choose a format, confirm.
- **Hourly fees:** contracts that work as a base fee plus billable excess hours feed instalments. The report "Billable hours pending to bill" `[mp302793]` shows hours inside instalments not yet billed and hours not yet included in any instalment, filtered by JobNumber or owner client.

### 2.6 P-05 Billing order differences
- **T:** After a supplier's invoice is registered against a plan order, differences arise in spots, rate or discounts. They come from three places:
  - (a) differences accepted in AP's "differences pending billing" report;
  - (b) a supplier invoice that will never arrive, where the credit is transferred to the client (AP "mark budgets as not billed by supplier");
  - (c) volume credit notes received from suppliers and passed on to the client.
- **S:** Same as P-01, selecting the difference lines. The result is an invoice (positive delta) or a credit (negative delta).

### 2.7 P-06 Advance sale (`Venta Anticipada`): pre-billing and consumption
- **Purpose:** Bill the client before any plan or budget exists. The billed amount sits in a balance-sheet liability account and is drawn down as real work gets billed.
- **Prerequisites:** special config `Usa Facturación Venta Anticipada = True`; a balance-sheet account with observation code `VA`, which **must** have an associated VAT account; optionally an account with code `VC` for advance-sale commission.
- **P-06a Issue the advance-sale invoice.** Screen `Facturación Venta Anticipada`; operation `Factura de Venta Anticipada` (or `...de Com.` when a VC account exists); origin General/Medios/Producción; detail lines use JobNumber/OT, the VA account only, text, VAT account (auto), net, VAT (auto, editable) and supplier (optional). Output: an invoice posted against the VA liability, which opens a consumable balance.
- **P-06b Consume.** When billing a plan or budget through P-01/P-02, the `Venta Anticipada` tab appears, but only if the client already has an advance-sale invoice. Set `Aplicar a Fact de Vta Ant. = Sí`, then pick one or more advance invoices and edit `Imp. a Descontar` on each. Then decide `Incluye S. Ag.`:
  - **Yes:** investment and agency commission are both drawn from the advance. The consumption invoice is issued at **zero** value; it is informational for the client, but it still posts an entry that moves VA to revenue.
  - **No:** only the investment is drawn down. An invoice with taxes is issued for the commission.
- **P-06c Credit note for advance-sale application** (`N/C de Aplicación Venta Anticipada`): reduces an advance invoice when the client was over-billed. It must reference the advance invoice (type, letter, number; fiscal year if the number repeats across years).
- **P-06d Credit note cancelling the advance-sale remainder** `[mp301617]`: refunds the unconsumed balance. One NC per advance invoice. The default is the whole remainder; `Modificar saldo a anular` lets you cancel only part of it. **Cannot be deleted or voided once issued.**
- **Zero-value invoices are forbidden** in some countries (Chile, Colombia are named). Workaround: create an internal point of sale, suggested code 99, whose numbering starts at 1, and issue consumption documents there.
- Overcommission and supplier billing can also draw down an advance invoice issued to the *supplier* (P-11).
- Recommended governance: a double approval on plans and budgets that will draw down an advance (client approval, then approval for billing).

### 2.8 P-07 Manual documents (`Facturación Manual`)
- **Operation types:**
  - `Comprobante Manual`: Factura, N/Crédito or N/Débito with no association.
  - `N/C Asociada a Comprobante`: references an invoice or ND by type, letter and number.
  - `N/C Administrativa`: typically a financial discount. The guide says it is always issued at value 0; see Gaps.
  - **NC/ND without reference** (since release 4.6): tied to a period instead of a document, for volume or financial discounts. It can later be applied to any invoices during collection. Not allowed on electronic credit-invoice points of sale.
- **Origin** `General` / `Medios` / `Producción` adds a `Medio` or `T. Prod.` column, which feeds the analytics reports.
- **Detail grid:** JobNumber (F2 = owner client's jobs, F3 = generic agency jobs; must be in Open state), OT (auto from the job or chosen), task/media, revenue account (only AR-applicable accounts; the VA account is blocked), text, VAT account (auto from the revenue account), net, VAT (auto, editable), supplier (from the job or "no supplier").
- **Taxes tab (Argentina):** manual perception percentage when the agency is a perception agent.
- **Manual production documents** require an open production OT.
- **Formats:** `Detallado` or `Resumido a un texto`. Production uses the three production formats.
- **AP: NC/ND approval circuit.** When config `Usa Circuito de Aprobación Notas de Crédito = TRUE`, unassociated NC/ND are saved as **provisional**: not applied and not posted. Users holding the specific approval activity then approve or reject them from the document query. Supported by the alert "NC cancelling customer invoice pending approval" and the list `[mp302918]`, which has states Ingresada / Aprobada / Rechazada.

### 2.9 P-08 Fixed-asset sale (`Bien de Uso`)
- **T:** The agency sells one of its own fixed assets, registered manually or through an expense request.
- **S:** Billing client (owner client optional), operation fixed to Factura, origin General. Detail: JobNumber (agency or client), OT, asset (F2 list), text, VAT account, net, VAT. Confirm.
- **O:** An invoice; the asset is shown on the invoice's "fixed assets sold" tab. It implies the asset is written off (the derecognition entry is handled by fixed assets; not detailed here).

### 2.10 P-09 Supplier commission billing (`Facturación de Comisión a los Proveedores`)
- **Concept:** A "confidential" commission negotiated with a media or production supplier. It can be collected in two ways: (a) the supplier issues a credit note, which is registered in AP and is visible to auditing clients; or (b), the recommended way, the agency invoices the supplier, which turns the supplier into a billing client.
- **Prerequisites:**
  - Special config `Comisión Proveedores = Factura`. A noted quirk: toggle `Forma de cobro por ítem` to NO, save, then back to YES, save.
  - The supplier is linked to a billing client (supplier master, `Cliente Asociado`) and has type Media and/or Production.
  - An account with observation code `U4` (book as other income), or code `22` (book as gross income, linked in config as `Cuenta Contable de Imputación`).
  - Volume scales exist when volume commissions are used.
  - The real client has commissions enabled.
- **Assignment upstream:** in the plan (`Detalle`, column `Com. Proveedor`) or the budget (`Datos del ítem`, column `Com`), the user sets:
  - `Registro Comisión Proveedor`: `Emite factura al proveedor` or `Recibe N.C. del proveedor`.
  - `Tipo de Comisión`: `Sin comisión` (default), `Con comisión` or `Comisión a asignar`.
  - With `Con comisión`: `Tipo de cálculo` and `Porcentaje`.
- **Billing steps:**
  1. Validate first with the pending-commissions lists.
  2. Point of sale; document kind (Factura or ND; selectable in Argentina).
  3. Filters: `Sólo órdenes cerradas` (media; only verified orders), `Sólo facturado x proveedor`, `Sólo facturado al cliente`, `Incluye Bonif./Canje`.
  4. Calculation base: `Sobre Bruto` (gross rate, ignoring the plan discount), `Sobre Neto` (includes surcharges) or `Solo sobre 1° Descuento`.
  5. Country options: Facturar con IVA (Exterior); Colombia `Incluye Pronto Pago`; Guatemala `Factura de Exportación`.
  6. Date range of commission generation.
  7. `Conceptos` filter: Solo Comisión / Solo Volumen / Comisión y Volumen. Volume requires supplier invoices already registered.
  8. Supplier (only those with pending items appear); billing type Medios or Producción.
  9. Additional data, then confirm, select documents, confirm the selection, preview, rounding, confirm.
- **Restrictions:** media and production are billed separately; no mixing of currencies; commission on foreign-currency plans or budgets is not allowed (local currency only).

### 2.11 P-10 Supplier incentive billing (`Facturación de Incentivos a Proveedores`)
- **Prerequisites:** a discount or incentive scale per supplier; the supplier registered and associated as a billing client; a bonus account set on each production type and media type.
- **T:** Period close, after supplier invoices are registered.
- **S:**
  1. Supplier.
  2. `Tipo Facturación`: `Sin Retroactivos` (tier rate applied only to invoices not covered by earlier incentive invoices), `Solo Retroactivos` (only invoices already covered once, i.e. the top-up), or `Incluye Retroactivos` (tier reached by cumulative investment, applied to all selected invoices).
  3. `Estado de Facturación`: Todas / Pagadas / No Pagadas.
  4. Order date range and supplier-invoice registration date range.
  5. Optionally issue without withholdings.
  6. Confirm. The system shows `Inversión Proveedor` and `% Incentivo a Aplicar`.
  7. Select invoices in the `Selección Facturas de Proveedor` window, which is colour-coded by payment status and shows early-payment % and amount where present.
  8. Save, preview (`Detallado` per supplier invoice or `Resumido a texto` with a default label), confirm.
- **Alternative:** "Mark incentive pendings as billed" `[mp301191_true]` cancels the pending with a reference number (for incentives billed manually).

### 2.12 P-11 Overcommissions (contract-driven supplier rebates)
- **P-11a Generate pending** `[mp302736]`:
  1. Choose the month. It is also the cut-off date for orders.
  2. Choose the supplier (only those with an overcommission contract and activity) and the contract.
  3. Informational fields: process (`Facturación` or `Provisión` for that month, from the contract); version (increments on each recalculation); state (`Inactivo`, `Pendiente`, `Provisionado`, `Facturado Parcial`, `Facturado`).
  4. Contract parameters: validity; calculation type (fixed % without scales; value scale; % scale with absolute increment; % scale with marginal increments; % scale with stepped increments); contract type; `Orden Generación Pendiente` (sequencing across several contracts with the same supplier, where earlier contracts' overcommissions are subtracted from the base); `Monto Límite` (cap); `% Reducción` (pre-calculation deduction from the purchase amount, e.g. to offset withholdings the supplier suffers); `Tipo Facturación` (`Genera Factura` or `Recibe Nota de Crédito`); contract currency (orders converted into it); exchange rate.
  5. Optional supplier's own settlement amounts per client (`Importe Liquidación del Proveedor`). When present, the system does not calculate; it spreads the entered amount across that client's orders.
  6. Grid: orders, pre-selected. Orders already overcommission-billed are locked as selected. Orders belonging to an earlier-sequenced contract with no pending this month are locked as unselected and shown in red. Columns: order, supplier invoice, media, owner client, product, order amount (gross or net per contract base), base to bill, base to provision, billed, provisioned, pending to bill, pending to provision.
  7. `Netea`, on by default: negative amounts are netted against positive ones. When off, a credit note is produced for the negatives.
  8. Generate. `Recalcular` re-runs the calculation on later investment changes, even after partial billing. `Eliminar` is only allowed if nothing has been billed or provisioned.
- **P-11b Bill overcommission** `[mp302739]`: supplier, load type (media or production), currency, then per-client pending lines with contract % and amount. Select all or per client. Optional config splits the billing per billing client and shows plan and order numbers. Can draw down an advance invoice issued to the supplier. Confirm (irreversible).
- **P-11c Mark overcommission pending as billed** `[marcar-pendientes-de-overcomis]`: cancels the pending with a manual-invoice reference number, with no entry. A supervisor can unmark it by clicking the `FACTURADO (M)` cell, which returns it to `PENDIENTE`.
- **P-11d Refund to the original client** `[mp302780]`: when the contract says part of the overcommission goes back to the client, an NC is issued to the owner client from pending refunds. Options: `Solo cobradas` (only overcommissions already collected) and `Calcular Devolución Sobre Monto Over Cobrado`.
- **P-11e Mark refund as billed** `[mp302771]`: cancels the refund pending, searched by supplier or owner client, with a reference number.
- **Report** `[mp302870]`: overcommissions and incentives marked as billed, with an unmark action.

### 2.13 P-12 Finder fee `[mp302912]`
- **T:** A finder-fee contract exists for a client.
- **S:** New. Choose the client whose investment is the base; the contract number is assigned consecutively. The system shows the commission defined in the contract. Choose the beneficiary supplier, then Generate: orders in the period matching the contract (e.g. radio orders) are listed. Select and save.
- **O:** One **expense request** (`solicitud de gasto`) per order, waiting for the supplier's invoice. This hands off to AP (control and registration of received invoices, then payment order).

### 2.14 P-13 Cancel a pending-to-bill (`Marcar Presupuestos como Facturados al Cliente`)
- **T:** Approved work will not be billed (costs were incurred but the client will not be charged), or it was already billed manually before the plan or budget existed.
- **S:** Select by client or by document; currency; billing type; subtype; enter a reference number (e.g. the manual invoice number); select items; confirm.
- **O:** The pending is cancelled. **No journal entry**, but the result is reduced in effect, because cost now has no matching sale. The plan or budget keeps its planned values; the linked document number shows in red, together with the user who marked it.
- **AP:** A supervisor can right-click the red number to remove the mark and make the item pending again.

### 2.15 P-14 Fiscal validation, printing and delivery (`Impresión de Facturas`)
- **T:** Documents have been confirmed. Billing can run in parallel; validation is a separate, later step.
- **S:**
  1. Filter: CAE status `Pendiente Solicitar`, the electronic point of sale, and request type (`Normal` for domestic, `Exportación` for foreign clients). Do not narrow by client, because the authority validates consecutively and an earlier pending document for another client blocks the rest.
  2. Start. Select all, then `Solicitar C.A.E.`. Granted: the CAE number and its expiry show. Rejected: the reason shows in `Motivo del Rechazo`; fix it and retry. `Solicitar últ. comp. aprobado` returns the last authorized number.
  3. Set the PDF directory (`Asignar Directorio PDF`), one shared location.
  4. Tick `Imprime a PDF`, select, then `Imprimir Comprobantes`.
  5. Email: the PDF print enables email to the billing client's address plus the collection contact; a CC mailbox is configurable.
  6. Other tools: draft print (no record); copy count; TXT export (DGI layout); `Adjuntar XML Timbrados` (Mexico; attaches the PAC-stamped XML from a configured path); `Actualizar Estado Comprobantes` (pulls e-invoice status and stores responses in the configured EFact directory); final purchase-order number assignment per document; `Administrar Comp. Relacionados` (exports a folder per client invoice holding a per-supplier sub-folder of supporting documents, the invoice XML, purchase orders and plans/budgets).
- **ST:** CAE pending, then authorized or rejected. Not printed, then printed. Printing counts as sent to the client.
- **Contingency (Argentina):** when the e-invoice service is down, pre-printed CAI forms may be used. CAI code and expiry are maintained per letter in `[mp301169]` and must later be reported in the VAT position.

### 2.16 P-15 Credit note that cancels an invoice (`Nota de Crédito Anula Factura de Cliente`) `[mp301187]`
- **T:** An invoice was wrong, and the plan or budget must be freed for re-billing.
- **S:** Point of sale; document to cancel (Factura, ND, or Anexo for Mexico) by letter and number (F2 search). Data is auto-loaded: dates, editable due date, currency, rate, state, client, product, loader. Payment terms; contact; salesperson. `Asignar Sucursal NC` checks that the NC's point of sale matches the one assigned to the original invoice's point of sale. `Confirmar N/C` opens a preview: format, language (the format, and the plan or budget texts, must exist in that language), observations, notes, rounding. Confirm.
- **O:** An NC mirroring the invoice. The plan or budget is released (back to pending). Partial cancellation is allowed **except in Colombia**.
- **AP:** If the invoice is already collected, config `Restringe NC cliente con comprobante asociado` must be off. **The NC cannot be deleted or voided once issued.**
- **Edge case:** deleting or voiding an NC that cancelled an invoice (supervisor-only) leaves the invoice "without support". The receivable reappears as open while the plan or budget stays re-billable, so there is a risk of duplicate billing. Remedy: mark the plan or budget as billed with the original invoice number.
- **De-association:** from the document query, `Desaplicar Compensación de saldos` (also `Asociar Nota de Crédito/Factura`) detaches the NC from the invoice. Both return to unpaid, and the NC then behaves like a manual NC.

### 2.17 P-16 Delete versus void an invoice (`Consulta de Facturas de Clientes`) `[mp301008]`
- **Delete (`Eliminar`):** removes the document and its entries entirely and frees the plan or budget for re-billing. It leaves a numbering gap, which is fixed by manually resetting the next number in point-of-sale numbering, issuing again, and restoring the counter.
- **Void (`Anular`):** keeps the document with state `Anulada` and reverses its entries. The same number cannot be reissued.
- **Bulk void of unissued numbers** `[mp301169]`: date, type, letter, point of sale, and a from/to range (inclusive).
- **Other query tools:** audit history; `Corregir saldo impago` (recomputes the open balance from the applied receipts); editable due date (for collection forecasting); prints (Mexico annex Excel; Venezuela fiscal credit certificate).

### 2.18 P-17 Collections: receipts (`Cobranzas`, `Mantenimiento de Recibos`) `[mp301265]`
- **Receipt types (`Tipo de Recibo`):**
  1. `Cobros a Clientes`: against invoices, NDs, NCs and advances.
  2. `Devolución de Proveedores`: a supplier returns money for an advance or a credit note; only advances or NCs can be collected.
  3. `Cobros Varios`: income with no prior document (partner contributions, guarantee cheques), posted to chosen accounts. Balance-sheet accounts need no job dimension; P&L accounts require JobNumber, OT and cost center (agency generic job via F3, or a client job).
  4. `Devolución de Costos`: a collaborator returns the unused part of a production cost advance (P-19).
- **Common header:** fiscal year; posting date (editable; it drives the entry date); receipt number (auto; manual `Seleccionar Nº` for supervisors only, e.g. when receipt books are handed to several collectors); issuer (search by name or alias); description; **debt currency** (one per receipt); **collection currency** (may differ; it restricts the cash and bank accounts offered); exchange rate; observations; three footer notes.
- **Customer receipt steps:**
  1. Confirm the data. This shows open documents (advances pending application, invoices, NDs, NCs) and portfolio documents.
  2. Tick documents; edit `A Cobrar` for partial collection.
  3. Under `Registros Manuales`, enter each withholding suffered (observation-coded withholding account, comment, debit amount) or a cents adjustment.
  4. Save. This opens `Cobrar Con…`: collection date and instruments.
  5. Confirm. When withholdings exist, the `Retenciones de Clientes` window asks per withholding for the invoice number, withholding date, certificate number and amount.
  6. Save.
- **Instruments:**
  - Cash in local currency, to the cash box or petty cash.
  - Foreign-currency cash.
  - Third-party cheques: bank (create inline if missing; tax ID optional), cheque number, endorsable (default yes), special, issue date, due date, amount, issuer tax ID, bank tax ID.
  - Bank transfer: bank, reference (may be 0), amount.
  - Documents (promissory notes): issue date, term in days (gives the due date), amount, issuer tax ID.
  - Several instruments can be combined until the total is covered.
- **Customer advance:** after confirming the data, the toolbar action `Agregar Anticipo` adds an advance line with an `A Cobrar` amount.
- **Advance requests:** pending requests from P-20 appear in an extra section for cancellation.
- **Peru:** bulk import of `detracciones` (withholding-like deposits) receipts from an Excel file. Requires config `Control de detracción del cliente` and a detraction account.
- **ST:** Receipt is `Cobrado` on save. The documents it covers are locked from other receipts. Invoice open balances fall; fully paid documents leave the open-items list.
- **Restrictions:**
  - No collecting foreign-currency documents with instruments in a different foreign currency.
  - No mixing debt currencies in one receipt.
  - One integrator (control) account per receipt (e.g. local and intercompany kept apart).
  - Withholdings only through observation-coded accounts.
  - Non-endorsable third-party cheques cannot be passed on in payments.
- **Accounting:** an automatic entry, including an extra **FX difference** line when foreign-currency debt is cancelled. The entry is read-only (viewable from the receipt). To change it, void and recreate the receipt. Manual entries against integrator accounts are discouraged.
- **Attachments:** supporting files are exported together with the receipt PDF.

### 2.19 P-18 Void, delete, re-apply a receipt
- **Void (`Anular`):** needs permission level `1A`. If the receipt's month is pre-closed or closed, the user picks a void date; otherwise the receipt is voided at its own date. Taxes are reversed, and recreating the receipt may change the amount. Not allowed if third-party cheques from the receipt have already been handed to suppliers.
- **Delete (`Eliminar`):** leaves no trace; the receipt can be recreated, and `Recuperar` reuses the number to avoid gaps (a config limits how many numbers may be skipped). Not allowed in pre-closed months, or when cheques were passed to suppliers.
- **Re-apply (`Reapropiar`):** for an advance receipt whose work has since been invoiced. Query the receipt, press `Reapropiar`, tick the invoices (partial amounts allowed), save. When advances and receivables use different accounts, a reclassification entry is posted.
- **Opening-balance receipts and advances** `[mp301208]`: viewable under the pseudo-year `Saldo inicial`, where they can be deleted and re-entered. Normal-year receipts are read-only there.

### 2.20 P-19 Return of cost advances (`Devolución de Costos`)
- **Prerequisites:** a production budget, client-approved, with an item whose supplier is `Rendición de Costos` (cost settlement) for the advanced amount; a cost advance paid to the collaborator through a payment order; collection instruments set up.
- **S:** Receipt type `Devolución de Costos` adds the `Datos Rend. Costo` tab: budget month, estimate number, settlement account, collaborator sub-account. Confirm. Under manual records, choose the budget item and enter the returned amount (credit). Save. Pick the open cost advances of that collaborator and the amount to apply. Then `Cobrar Con…`, then confirm.

### 2.21 P-20 Customer advance requests (`Pedidos de Anticipos a Clientes`) `[mp302652]`
- **Purpose:** a formal, non-accounting request for funds before production starts.
- **Prerequisites:** a client-approved budget with at least one `Rendición de Costos` item.
- **S:** New. Month/year (auto-numbered; optional manual request number), client, estimate. Select items, then `Aplicar`: total or percentage. Amounts may be partial but not above the item total. Save; print or PDF to the client.
- **ST:** pending collection, then collected (cancelled inside a receipt).

### 2.22 P-21 Collection management (`Gestión de Cobranzas`) `[mp301522]`
- **Prerequisite:** config `Usa seguimiento de Facturas`; client contacts in the agency contact book, linked to the client entity.
- **Views:**
  - `Facturas sin reclamo` (open items never chased, grouped by client and age).
  - `Por fecha de próxima acción`.
  - `Por fecha de próxima acción vencida` (planned but not done).
  - `Facturas con fecha de cobro` (route sheet for field collectors).
  - `Facturas completo` or a single client.
  - Escalations (service-center tasks route the issue to a responsible sector or person, e.g. the account executive).
- **S:** Tick invoices, then `Comentarios`: contact, comment, next action date and time, `Pasar a Cobrar` (the next step is collection), next-action description. Save. Optional email reminder (`Enviar mail de reclamo`, with a configurable generic CC mailbox). Alerts fire on next-action dates and on collection-day items.
- **ST:** A tracked item leaves the list once a receipt is posted. If collection fails, a new comment puts it back into the chase cycle.

### 2.23 P-22 Delivery notes and labels
- **Customer invoice delivery notes** (`Remitos`) `[mp305205]`: New, client, client receipt date, invoice date range and product, then select invoices, save, print (copies, signer, optional cost relation, footer notes). States: pending to send / sent. Listed in `[mp306205]`.
- **Mailing labels** `[mp301205]`: lists clients with sales in a date range (optionally by issuing user or by product contact) and prints labels.

### 2.24 P-23 Client-specific distribution (Colombia)
`[mp302798]`, `[mp302799]`: one Colombian agency, one client. Plans and budgets are attached to the owner client and funded through client advances (the mandate screen and advance requests). At year end, supplier invoices are distributed to many billing clients (stations) using a client-provided key, such as fuel volume per station. The general pattern this generalizes is `Códigos de Apertura de Facturación` (§3).

---

## 3. Entities

| Entity (ES / EN) | Key fields | Identifier | Relationships |
|---|---|---|---|
| `Cliente de Facturación` / Billing client (legal entity) | Legal name (`Razón Social`), alias, fiscal address, postal address (mandatory in Colombia for XML), tax ID (CUIT AR, RUT CL; check-digit validated), contacts for invoice follow-up, validity, `En Conflicto` flag, AR control account (obs. code 48; locked once documents exist), extra integrator accounts (with validity; a separate one for commissions/overcommissions), associated supplier, `Excluir Facturas` (ignore direct investment), salesperson, `Práctica Auditoría` (forbids cost≠sale), Intercompany flag plus code, credit-limit level, payment-term mode (per client or per product), production term, media due-date type, media term, default billing type (Direct, with pass-through or not; Indirect), production approval type (`A Presupuestar` / `Pre-Aprobado`), agency-service calc base, commission billing timing (`Junto` / `General`), supplier commission flag, adserving cost, VAT condition (Exterior adds document type and number), VAT withholding coefficient, VAT reduction %, perception exemption %, IIBB perception agent plus number, high-risk register flag plus expiry, IIBB jurisdiction, simplified regime, export flag, IIBB perception type (mandatory), reduction period, cheque-tax category, Hyperion code, reporting term, provider-client code, external interface, per-media direct/indirect exceptions, contract flag plus expiry, logo, attachments | Auto code (immutable) | 1..n with owner clients; optional 1:1 supplier; n invoices |
| `Cliente Titular` / Owner client (brand / trade name) | Name; JobNumbers | Code | n:n with billing clients (one default) |
| `Anunciante` / Advertiser | Used when the agency is a media owner or publisher selling to intermediary agencies (config `Tiene Anunciantes`) | Code | Advertiser to owner client (intermediary agency); advertiser to billing client; validity instead of deletion |
| `Código de Apertura de Facturación` / Billing split code | Description, owner client, lines {billing client, %} with at least 2 lines summing to 100 | Auto code | Used in plan or budget headers when the job's billing type is "with split" |
| `Límite de Crédito` / Credit-limit level | Description, responsible approver (user), amount (local currency) | Auto code | Assigned to billing client (default "no limit"); cannot be deleted once used |
| `Vencimiento por Producto` / Due date by product | Owner client, billing client, product, production term, media term | — | Applies when the client's term mode is "by product" |
| `Pronto Pago` / Early-payment table | Description, entity (clients), type (relative to supplier invoice, capped or uncapped), {media type, %} | Auto code | Needs configs `Usa Pronto Pago Proveedores` and `Usa Tabla Pronto Pago Proveedores` |
| `Vendedor` / Salesperson | Linked user or contact, name, address, phones, validity, commission % for media and for production | — | Assigned to clients and invoices |
| `Nota al Pie` / Invoice footer note | Client (all or one), document type (all, Factura, NC, ND), note type (normal, export, foreign currency), currency, Notes 1–6 with keyword placeholders | — | Printed on documents |
| `Sucursal` / Point of sale | Auto code (4 digits in AR), description, `Sucursal Actual` (default), supplier-commission flag (R4.8i), type Normal/Electronic, validity, last-used number per {document type × letter A/B/C/E} | Code | At least one active; deletable only if unused |
| `Comprobante de Venta` / Sales document | Type (Factura, NC, ND, R/Gastos, Anexo, Factura de Crédito, Boleta de Venta PE), letter, point of sale, number, date, due date (editable), currency, rate, state (Activa/Anulada), billing client, owner client, product, loader user, contact, salesperson, delivery note, print format, version (Inicial/Final), origin (Medios/Producción/General), billing type, amounts (taxable, exempt, VAT, supplier VAT, VAT perception, IIBB perception, income/VAT/profit withholdings, unregistered VAT, total, unpaid balance), integrator account, CAE plus expiry or rejection reason, printed flag, final PO number, advance-sale parent invoice, applied NC (number, amount), NCF (DO), act number (CO) | Type + letter + POS + number (+ fiscal year) | Lines link to OT, JobNumber, media or production type, product, division; links to receipts, purchase orders, supplier invoices (transferred), fixed assets sold |
| Sales document line / OT movement | OT, client, account, amount, direct VAT, text, JobNumber, division, media or production type, product, supplier | — | Off-ledger management detail mirroring the entry |
| `Recibo` / Receipt | Type, fiscal year, number, posting date, collection date, issuer, description, debt currency, collection currency, rate, observations, notes 1–3, state (Cobrado/Anulado) | Year + number | Applies to documents (amount each); instruments; manual records; withholding certificates; attachments |
| Receipt instrument | Cash {account, amount}; FX cash; cheque {bank, number, endorsable, special, issue, due, amount, issuer tax ID, bank tax ID}; transfer {bank, ref, amount}; document {issue, term, due, amount, issuer tax ID} | — | Feeds treasury and the cheque portfolio |
| Customer withholding certificate | Invoice number, withholding date, certificate number (default 0000000), amount, withholding account | — | Per receipt line |
| `Anticipo de Cliente` / Customer advance | Amount, currency, receipt | — | Re-applied to invoices later (`Reapropiar`) |
| `Pedido de Anticipo` / Advance request | Month/year, number, client, estimate, items {%, amount}, state | Month/year + number | Production budget items (cost settlement) |
| Collection follow-up comment | Invoices, contact, comment, next action date and time, `Pasar a Cobrar`, description | — | Alerts, escalations |
| `Remito` / Delivery note | Client, number, client receipt date, invoices, state | Number | Invoices |
| Overcommission contract (master elsewhere) | Validity, calc type, base (gross or net), sequence, cap, reduction %, billing mode, currency, client refund % | Number | Overcommission pending (month, version, state) to invoices or NCs |
| Supplier incentive scale (master elsewhere) | Tiers of investment and % | — | Incentive invoices |
| Finder-fee contract | Number, client base, commission, beneficiary supplier | Consecutive | Expense requests |
| `Motivo de Anulación` / Void reason | Description | Code | Captured when voiding |
| `Municipio` / Municipality or district | Name | — | Geography for tax |
| `Cliente de Punto` / Point (loyalty) client | Names (given name plus two surnames), contact data, document type and number, tax responsibility, person type, CIIU | — | Config for points |
| Collaborator account register (`registro de cuenta`) | Auto document on sub-accounts with obs. codes 82–85 | — | Aging of employee advances |

**Observation codes** (account tags that drive behaviour): `48` customer AR integrator/control accounts; `VA` advance-sale liability; `VC` advance-sale commission; `U4` supplier commissions as other income; `22` gross income (supplier commissions); `23` media bonuses; `82`–`85` collaborator sub-accounts (expenses or costs to settle, employee advances).

---

## 4. Document lifecycles

### 4.1 Plan/budget-sourced invoice
`Approved for billing (pending)` → [optional `Pedido de Anticipo` / advance receipt] → **invoice confirmed** (state `Activa`; version Inicial keeps the source editable, Final locks it) → **fiscal authorization** (`CAE pendiente` → `Autorizado` | `Rechazado` → fix and resubmit) → **printed / PDF / emailed** (printed = delivered) → [`Remito` sent] → **collection follow-up** (comments, next actions, escalation) → **receipt applied** (partial applications lower the open balance; full application leaves the open list) → closed.

Branches:
- **Differences** after verification (when Inicial): new pending lines become a supplementary invoice or a credit.
- **Cancellation:** `NC Anula Factura` (full, or partial where allowed) releases the source back to pending; or **void** (`Anulada`, entries reversed, number burnt); or **delete** (vanishes, source released, numbering repaired manually).
- **NC de-association:** both documents return to unpaid.
- **Write-off of pending** without billing: marked as billed.

### 4.2 Advance sale
`Advance invoice (VA liability)` → collected like any invoice → **consumption** through plan or budget billing (zero-value or commission-only document; VA moves to revenue) → remainder either consumed, reduced by `NC de Aplicación VA`, or refunded by `NC Anula Diferencia VA` (irreversible).

### 4.3 Manual NC/ND under the approval circuit
`Ingresada (provisional, not posted)` → `Aprobada` (posted and applied) | `Rechazada`.

### 4.4 Overcommission pending
`Pendiente` (version n) → [`Recalcular`, version n+1] → `Provisionado` (month process = provision) → `Facturado Parcial` → `Facturado`; or `Marcado (M)` → (supervisor) back to `Pendiente`. The refund side runs in parallel: pending refund, then NC to the client or marked as billed.

### 4.5 Receipt
`Draft` → `Cobrado` (posted, documents locked) → `Anulado` (dated reversal) | deleted (no trace; number recoverable) | `Reapropiado` (advance applied to invoices, optional reclassification).

### 4.6 E-document status
`Pendiente solicitar CAE` → `CAE otorgado` (number plus expiry) / `Rechazado` (reason). Mexico: stamped XML attached; status refreshed from the e-invoice response directory.

---

## 5. Business rules and calculations

1. **One source family per document.** Plans, budgets and fees are never mixed. Supplier commissions: media and production apart.
2. **One currency per document.** The user guides add that plans, budgets, fees and supplier commissions denominated in a foreign currency cannot be billed (local currency only). This conflicts with the foreign-currency fields on every billing screen; see Gaps.
3. **Agency service (commission) base**, per billing client (`Tipo Cálculo Medios`): `Bruto` (gross order amount), `Neto` (after all discounts, including surcharges), `1° Descuento` (after the first discount, the rate card), or `Importe Fijo`. Formula: `commission = base × commission% ` (or the fixed amount).
4. **Commission billing timing:** `Junto` puts investment and commission on one document. `General` puts commission on a separate document, at the same time or grouped by period, and requires the investment to have been billed first.
5. **Direct versus indirect:** `Indirecto` means the supplier bills the agency and the agency bills the client the full investment plus commission. `Directo` means the supplier bills the client and the agency bills only its service. Direct work "passing through the agency" is booked via a bridge account (`Cuenta Puente`); "not passing" keeps only a copy. Exceptions can be set per media in the client master. `Excluir Facturas = SI` drops direct investment from pending-to-bill and pending-to-receive lists so jobs can close; only agency service stays pending.
6. **Supplier commission base** (P-09): `Sobre Bruto` = gross rate, ignoring the plan discount; `Sobre Neto` = net including surcharges; `Solo 1° Descuento` = rate after the first discount, ignoring the rest. `Incluye Bonif./Canje` toggles whether bonus or barter items enter the base. `commission = Σ eligible_order_base × item%`. Volume part = `Σ registered supplier-invoice investment × tier%`.
7. **Incentive tiering:** `tier% = scale(Σ supplier investment in the selected window)`. `Sin Retroactivos` applies `tier%` to invoices not yet covered. `Solo Retroactivos` applies `(tier% − previously applied%)` to already covered invoices (inferred). `Incluye Retroactivos` applies `tier%` to all selected invoices. Early payment shows `pp% × amount` per invoice where configured.
8. **Overcommission:**
   - `base_i = order_amount_i(gross|net) converted to contract currency × (1 − %Reducción)`, minus overcommission from earlier-sequenced contracts.
   - Total: `over = f_calcType(Σ base)`, where f is one of: fixed %; value scale; % scale with absolute, marginal or stepped increments.
   - Cap: `over = min(over, Monto Límite)`.
   - Distribute `over` across orders pro rata to base.
   - `pending_i = over_i − billed_i` (or `− provisioned_i` in provision months).
   - Negatives: when `Netea`, offset against positives; otherwise issue a credit note.
   - When a supplier settlement is supplied, distribute the supplier's figure per client instead of calculating.
   - Client refund `= over_collected × refund%` when `Calcular Devolución Sobre Monto Over Cobrado`.
9. **Advance-sale consumption:** with `Incluye S. Ag. = Sí`, `VA_draw = investment + commission` and the invoice total is 0. Otherwise `VA_draw = investment` and the invoice total is `commission + taxes`. Across several advance invoices, `Σ Imp.a Descontar_k = VA_draw`. Each `Imp.a Descontar_k ≤ remaining_k`.
10. **Partial production billing:** `bill = % anticipo × Σ selected item sale` or `bill_i = user amount ≤ item remaining`. Once billed, the item is locked.
11. **Version semantics:** Inicial means billed while still editable, and differences are billed later. Final locks the source. Recommended: if Inicial turns out to have no difference, mark it billed to lock. In AR, GT, PE and VE the version is shown on the document.
12. **Controls before confirming the selection** (toggleable): *single due date* (all selected media or production types must share a due date, otherwise blocked); *single product* (one product per invoice, otherwise blocked); *item-level selection*.
13. **Rounding:** `Importe Redondeo` (net) and `IVA Redondeo` are added to the calculated totals. The maximum permitted adjustment is set by a supervisor in the special configurations. Not permitted where the authority recalculates VAT. Example from the source: +0.20 on net, −0.01 on VAT, to match a client's round PO.
14. **VAT:** line VAT `= net × rate(VAT account linked to the revenue account)`, editable. `Facturación con IVA (Exterior)` (AR, CR, PA, CL, or a client marked Exterior) forces VAT and switches to letter E. AR unregistered-taxpayer surcharge: rate 10.5% shown separately. Costa Rica: optional stamp tax (`Timbre`).
15. **Perceptions (Argentina):** VAT perception pass-through is default-on in automatic billing. IIBB perception applies by client perception type, jurisdiction, high-risk register membership (with expiry) and reduction % within a validity period. Manual documents accept a manually entered perception %.
16. **VAT withholding by client** (collection side): `effective_withholding% = config 'Porcentaje Retención IVA' × client coefficient`. The source's example: a client withholding 80% is entered as coefficient 1.60, which implies a 50% base config. There are separate client fields for VAT reduction % and perception exemption %.
17. **Income/VAT/ICA withholdings at invoicing (Colombia, Guatemala):** when the client master requires it, a window lists each concept with `min taxable base` (from the withholdings master), `invoice amount`, `%`, `total to withhold = amount × % if amount ≥ min base`, and the account.
18. **Withholdings suffered at collection:** entered as debit lines on observation-coded accounts. The system distributes a withholding *proportionally* across the documents in the receipt. Users should overwrite this with certificate-accurate amounts per invoice. Certificate number defaults to 0000000 and a warning shows if it is left that way.
19. **Exchange differences:** when a receipt cancels foreign-currency debt, `FXdiff = FC_amount × (rate_collection − rate_invoice)` is posted automatically as an extra entry line. Reports in "contable" format revalue open FC items at the cut-off date rate. Prior-year items use the prior year-end closing rate as "original".
20. **Due-date calculation:**
    - Production: client term days, or `contado`, or `days from invoice date`, or instalments.
    - Media types:
      - `before media due − n days`
      - `end of month + 30`
      - `end of month + 15`
      - `end of fortnight + 15`
      - `end of fortnight + 10`
      - `end of fortnight + n`
      - `per spot date` (each spot its own)
      - `end of month + n`
      - `invoice date + n`
      - `media due date + n`
    - Precedence: product-level terms when the client mode is "by product"; otherwise client terms. Editable on the invoice, and in bulk from the unpaid list.
21. **Credit limit exposure:** `exposure = approved-but-unbilled plans/budgets + unpaid invoices ± unapplied NC/advance balances` (sign of the last term not stated; logically it reduces exposure). The check runs at client approval of a plan or budget. If exposure exceeds the limit, the level's responsible user must approve first, and client approval comes after that. The report splits exposure into unpaid balance, media pending without supplier invoice, and media pending with supplier invoice. In consolidated groups, both company-level client configs must allow it.
22. **Interest on overdue balances (report-level):** `interest = open_balance × rate × days_overdue`, where `days_overdue = cut-off or system date − due date`. The rate period and convention are unspecified.
23. **Delay (`Mora`)** in the collections detail: `collection_date − due_date`. Bank deposit date is shown to confirm effective cash.
24. **Aging buckets:** user-defined rows of day offsets. A positive value means overdue between this row's days and the row above. A negative value means due within this row's days and the row below. Basis: due date, accounting date, or real (issue) date. Rows are shown in descending order.
25. **Numbering:** the stored number per POS × type × letter is the *last used*; the next document takes +1. Countries without POS store `00` plus the number. Electronic POS triggers e-invoice controls. Deleting a document requires manual counter repair.
26. **Billing split codes:** `Σ % = 100`, with at least 2 billing clients belonging to the same owner client.
27. **Audit practice:** clients flagged `Práctica Auditoría` cannot have cost ≠ sale in plans and budgets. This is why supplier commissions are collected by invoicing the supplier rather than by marking up.
28. **Zero-value documents** are prohibited in CL and CO. Use an internal POS (suggested 99).
29. **NC partial cancellation** of invoices is not allowed in Colombia.
30. **Collections:** one debt currency; one integrator account; instrument currency must match the debt's foreign currency (or be local); non-endorsable cheques cannot be passed on.
31. **Pending cancellation (mark as billed)** creates no entry and records the user. A supervisor can reverse it.
32. **Commission on supplier billing** is only for suppliers linked to a billing client of type Media or Production.

---

## 6. Accounting impacts (journal entries)

The manual says every document shows a "journal summary" (`Conceptos` tab) and that receipt entries are automatic and read-only. It does not list the accounts. The patterns below are inferred from the account tags and descriptions, so implementers should treat them as configurable templates.

| Document | Debit | Credit | Notes |
|---|---|---|---|
| Indirect media/production invoice | AR integrator (48) total | Media/production sales or cost-recovery accounts (by media or production type); agency commission revenue; VAT output; perceptions payable (AR) | Line-level OT/JobNumber/division dimensions |
| Agency-service-only invoice | AR (48) | Commission revenue; VAT output | |
| Fee instalment invoice | AR (48) | Fee revenue; VAT output | |
| Direct billing passing through agency | Bridge account / AR | Bridge account / supplier | `Cuenta Puente`; detail not given |
| Advance-sale invoice | AR (48) | VA liability (balance sheet); VAT output | VA account must link a VAT account |
| Advance-sale consumption (zero invoice) | VA liability | Revenue (investment ± commission) | Document total 0 but entry posted |
| Advance-sale consumption (commission billed) | VA liability; AR for commission + VAT | Revenue; VAT output | |
| NC application / NC cancels remainder of VA | VA liability; VAT output | AR (48) | |
| NC cancels invoice | Mirror of original | Mirror of original | Releases source |
| Void invoice | Reversal of original entry | | Document kept as `Anulada` |
| Delete invoice | Entry removed | | No trace |
| Manual invoice / ND | AR (48) | Chosen revenue account; VAT account linked to it | |
| Provisional NC/ND (approval circuit) | none until approved | | |
| Fixed-asset sale | AR (48) | Asset-sale account / VAT | Asset derecognition presumably in fixed assets |
| Supplier commission invoice | AR of supplier-as-client (48, or a dedicated commission integrator) | `U4` other income, or `22` gross income; VAT | |
| Supplier incentive invoice | AR (supplier-client) | Bonus account set on the media/production type; VAT | |
| Overcommission invoice / provision | AR (supplier-client) or provision asset | Overcommission income | Provision months use the "to provision" base |
| Overcommission refund NC | Overcommission income / refund expense | AR of client | |
| Mark pending as billed | none | | Economic loss implicit (cost without sale) |
| Customer receipt | Cash / petty cash / bank / third-party cheques in portfolio / notes receivable / withholding-credit accounts (observation-coded) | AR (48) per document | Plus FX difference line (gain or loss) |
| Customer advance receipt | Funds | Customer advances (if separate account) or AR (48) | |
| Re-apply advance | Customer advances | AR (48) | Only when separate accounts are used |
| Supplier refund receipt | Funds | Supplier advance / supplier AP (NC) | |
| Miscellaneous receipt | Funds | Chosen accounts (P&L lines carry Job/OT/cost center) | |
| Return of cost advance | Funds | Cost-settlement account / collaborator sub-account (82–85) | Linked to budget item |
| Receipt void | Reversal at void date | | Taxes reversed |
| Finder fee | (no AR entry) | | Creates expense requests in AP |

Integrator accounts must not receive manual entries; this avoids unsupported differences between the ledger and the subledger.

---

## 7. Cross-module handoffs

| From / To | Handoff |
|---|---|
| Media planning → AR | Approved-for-billing plan orders become pending to bill. Plan status (open or closed after ad verification) shows as colour. Plan header carries billing mode (Junto/General), split code, supplier-commission flags, additional costs, NC discounts. |
| Production → AR | Approved budgets and items; `Facturación` mode; partial-billing locks; `Rendición de Costos` items for advances and cost returns; approval type per client. |
| Fee contracts → AR | Instalments and hours (base plus excess). |
| AP → AR | Supplier invoice registration produces differences (positive or negative) to bill; "mark as not billed by supplier" transfers credit to the client; volume credit notes from suppliers are passed on; registered invoices feed volume commissions and incentives; overcommission base uses supplier invoice numbers. |
| AR → AP | Finder fee produces expense requests. Supplier refunds collected. Client-to-supplier invoice relationship and collected-not-paid reports drive payment timing. Supplier advances/NCs collected back. |
| AR → Treasury | Receipt instruments: cash boxes, bank accounts, third-party cheque portfolio (endorsable flag), notes. Voids are blocked if cheques were endorsed to suppliers. "Values to deposit" option in the unpaid report. |
| AR → GL | Automatic entries for every document. Integrator accounts (48). FX difference. Period pre-close and close restrict delete/void dates. Revaluation at cut-off. |
| AR ↔ Fiscal authority | CAE (AFIP), CAI contingency, PAC XML (MX), DGI TXT, SIRED / CITI / unified purchases-and-sales VAT (AR), SAT TXT (GT), certifications (CO), NCF (DO), SUNAT series (PE). |
| AR → Group reporting | Intercompany flags and codes, Hyperion codes and reporting terms, consolidation base (intercompany debt), local intercompany results. |
| AR ← Users / Approvals | NC/ND approval activity; credit-limit approver per level; supervisor-only actions (manual receipt number, unmarking billed pendings, deleting NCs that cancelled invoices, rounding limits); permission `1A` to void receipts. |
| AR ← Contacts | Contacts for invoice follow-up and collection emails; service-center escalations. |
| AR ← Fixed assets | Assets available for sale. |
| AR → Salesperson commissions | Salesperson on invoices; % for media and production (calculation screen listed in the menu but not documented). |

---

## 8. Configuration and country-specific behaviour

### 8.1 Special configurations named
`Usa Facturación Venta Anticipada`; `Comisión Proveedores = Factura` (plus `Forma de cobro por ítem`) and `Cuenta Contable de Imputación`; `Muestra importe en selección`; editable invoice text at any time; maximum rounding amount; `Usa Circuito de Aprobación Notas de Crédito`; `Restringe NC cliente con comprobante asociado`; `Límite de Crédito Medios / Producción` (mandatory or optional, plus notified responsible); `Usa seguimiento de Facturas`; generic collection email (`Usa correo genérico en cobranza`); outgoing CC address; `Tiene Anunciantes`; `Usa Divisiones de Empresa` (sub-companies); `Usa Intercompany Local`; `Usa Circuito de Contratos Con Cuentas Diferidas` (background biller); overcommission billing by billing client; `Administra Comprobantes Relacionados` + `Permite Adjuntar Múltiples Archivos` + `Ruta Archivos Relacionados`; XML stamped path and EFact response directory; `Porcentaje Retención IVA`; `Impuesto al Cheque`; monthly client tax-status check (blocks invoicing on anomalies, imports registers with validity); `Usa Pronto Pago Proveedores` + `Usa Tabla Pronto Pago Proveedores`; `Control de detracción del cliente` + detraction account (PE); DGI numbering control by document type and by fiscal quality (DO); receipt-number skip limit; points-client config; collaborator aging process; default document type per POS. **Requirement:** every currency (local and controlled) must carry its fiscal or audit identifier, or AR e-invoicing fails.

### 8.2 Country matrix

| Country | Behaviour in AR |
|---|---|
| **Argentina** | AFIP e-invoicing with CAE requested in consecutive batches (normal or export), certificate validity check; CAI contingency forms; letters A/B/C/E; 4-digit POS; VAT perception and IIBB perception (types, jurisdictions, high-risk register, reductions, simplified regime); unregistered 10.5% VAT; Exterior → letter E; Factura or ND choice for supplier commissions; VAT sales subledger with SIRED, CITI, unified purchases/sales, related-parties TXT; billing by client report (net billed per client and period, with tax IDs, accounts obs. 48, direct/indirect, intercompany); income by jurisdiction (multilateral agreement participation); income-tax withholding exclusion / self-withholding report (commission, agency service and fee collections; media bonus account 23); cheque tax; version final visible. |
| **Mexico** | `Anexo` always issued with the invoice (direct-billing annex) with its own query, NC and Excel print; transferred supplier invoices tab; PAC-stamped XML attached (CFDI); unpaid list breakdown of VAT pending transfer per month; background biller with deferred-account contract circuit (one agency). |
| **Colombia** | Income/VAT/ICA withholding window at invoicing; `R/Gastos` expense-reimbursement document with transferred invoices; act number field; monthly certification of transferred withholdings (by certification, client, mandate, shared income); no zero-value invoices; no partial NC cancellation; early-payment option in supplier commission billing; postal data mandatory for XML; client-specific distribution screens; mandates. |
| **Chile** | RUT tax ID; IVA Exterior option; no zero-value invoices. |
| **Guatemala** | Income withholding window; export invoice letter; SAT TXT of issued and received documents (goods/services taxed/exempt, VAT); version final shown. |
| **Peru** | `Boleta de Venta`; combined general plus advance commission; detracciones bulk import in receipts; SUNAT series column in the client current account; version final shown. |
| **Dominican Republic** | NCF prefixes per document type; fiscal-quality selector (fiscal, non-fiscal, government, special regime, free zone); fixed NCF on the client. |
| **Costa Rica / Panama** | IVA Exterior option; Costa Rica stamp tax. |
| **Ecuador** | Expense-reimbursement marker when the invoice is a fee ticket (`boleta de honorarios`). |
| **Venezuela** | Fiscal credit certificate print; version final shown. |
| **Uruguay** | Not mentioned anywhere in this group. |

---

## 9. Reports and KPIs

| Report | Purpose / KPI |
|---|---|
| Unpaid customer invoices `[mp301141]` | Open items by due-date range or **as-of cut-off** (reconstructs balances at a past date for ledger reconciliation); by client or global (days overdue); interest at a given rate; include undeposited cheques as unpaid; multi-currency, contable (revalued at the cut-off rate, editable) or mixed; **aging buckets** (configurable); VAT pending transfer (MX); bulk due-date edit; participation % per client; collection comments; group by integrator account; exclude commission invoices (costs only). Core **aging** and **DSO-input** report. |
| Client current account `[mp301147]` | Chronological ledger per client, opening balance, include NCs, currency or revalued view, drill to document; SUNAT series. |
| Client balance sheet `[mp301148]` | Opening, movements and closing per client for a range; monthly summary of billing, collections, refunds, cash; per-document detail; reconcile to the ledger by account. |
| Invoices with collection detail `[mp301112]` | Receipts per invoice, deposit date, instrument breakdown, **delay days**, totals by currency, filter by invoice, receipt or OT date. |
| Customer invoices with supplier balance `[mp301095]` | Status matrix of client invoice versus supplier invoice (collected-not-paid, paid-not-collected), sale minus cost difference. Cash-cycle control. |
| Client invoices related to supplier invoices `[mp301119]` | Per client invoice, linked supplier invoices, margin difference, missing supplier invoices, tolerance filter, advance-paid contracts, payment columns. |
| Consumption billing with payments and collections `[mp302868]` | Per order: billed, collected, collection dates against supplier payment dates. Flags payments made before collection. |
| Billing board `[mp301090]` | Real billing month by month, previous months, current month, new work ordered, adjustments, carried-over pending, **estimated total for the month**, income pending. |
| Invoice control by plan/estimate item `[mp301087]` | Invoice to plans and items (three media groups plus gross), production items and suppliers, collection status. |
| Billing by media/production type `[mp301086]`; summary by client/department `[mp301419]`; summary by client `[mp301422]` (indirect, direct, agency service, fees, bonuses, other; participation %; agency service as % of billing); summary by product and concept `[mp301421]`; investment by client `[mp301420]` | Revenue mix analytics; intercompany and Hyperion codes; manual versus automatic; collected only. |
| Income by jurisdiction `[mp301425]` | Agency service, fees, bonus, cost difference per jurisdiction, participation % (AR). |
| VAT sales subledger `[mp301104]` | Statutory sales book by rate; totals by type and by taxpayer category; fiscal exports. |
| Intercompany invoices `[mp302695]`; intercompany debt `[mp302785]`; local intercompany results `[mp302786]` | Group reporting. |
| Credit-limit report `[mp301546]` | Limit, usage and gap per client; drill to approvals history and per-plan pending. |
| Advance-sale consumption detail `[mp301091]`; dynamic advance-sale report `[mp402832_9]` | Remaining balance by invoice or client, cut-off composition of the VA account; pivot/grid, templates, scheduled weekly offline runs. |
| Credit/debit notes by client `[mp302703]`; pending NC list `[mp302918]` | Credit control and approval status. |
| Collaborator balance aging `[mp302919]` | Employee advance sub-accounts (82–85) aged at cut-off. |
| Annex collections `[mp301636]` | Annexes collected in receipts against supplier payments (cheque, beneficiary, differences). |
| Invoice list `[mp301618]` | Automatic or general (includes receipts, settlements, advances), net, commission, tax, total by media or production type. |
| Delivery notes `[mp306205]`; overcommissions/incentives marked `[mp302870]`; billable hours `[mp302793]` | Operational. |

**KPIs to derive** (not computed by name in the source, but available from the reports):
- **DSO** = AR balance ÷ billing over the period × days.
- **Aging %** per bucket.
- **Overdue %**.
- **Average delay days** (from `Mora`).
- **Collected-not-paid exposure** and **paid-not-collected exposure**.
- **Credit-limit utilization**.
- **Agency service share of billing**.
- **Advance-sale unconsumed balance**.
- **Pending-to-bill** (approved, not invoiced).
- **CAE rejection rate**.
- **Follow-up SLA** (overdue next actions).

---

## 10. Agentic-skill implications

### 10.1 Atomic jobs (candidate skills or tools)
1. `ar.list_pending_to_bill(client|document, source, subtype, currency)`: returns plan, budget or fee lines with closed/open status, due date, product, amounts.
2. `ar.validate_billing_selection(lines, controls)`: enforces single source, currency, due date and product; checks approved-for-billing; flags unverified (open) plans; additional costs as a single unit.
3. `ar.compute_invoice(lines, client_master, options)`: commission (rule 3), billing mode Junto/General, direct/indirect, VAT and perceptions, withholdings window (CO/GT), rounding within the limit, partial % or amounts, advance-sale draw-down. **Deterministic tool.**
4. `ar.issue_document(draft, pos, version, format)`: numbering (last+1 per POS × type × letter), posts the entry, locks or releases the source per version.
5. `ar.request_fiscal_authorization(pos, request_type)`: consecutive batch, capture CAE or rejection reason, retry loop; MX XML attach; status refresh.
6. `ar.render_and_send(doc_ids)`: PDF to the shared directory; email to the billing client plus collection contact plus CC; footer notes with keyword substitution.
7. `ar.issue_credit_note(kind ∈ {cancel_invoice, associated, administrative, unreferenced_period, va_application, va_remainder, overcommission_refund}, …)`: kind-specific validations (country partial rule, paid-invoice config, POS match, irreversibility warning).
8. `ar.approve_credit_note(id, decision)`: approval circuit.
9. `ar.void_or_delete(doc_id, mode, reason)`: void reasons master; numbering repair advice; "invoice without support" detection.
10. `ar.mark_pending_billed(lines, reference)` and `ar.unmark` (supervisor).
11. `ar.supplier_commission_run(supplier, subtype, concepts, base_mode, filters)`.
12. `ar.incentive_run(supplier, mode, paid_filter, windows)`.
13. `ar.overcommission_generate(month, supplier, contract)` / `recalculate` / `bill` / `refund` / `mark`.
14. `ar.finder_fee_generate(contract, orders)` → AP expense requests.
15. `ar.advance_sale_issue` / `consume` / `balance(client|invoice, as_of)`.
16. `ar.record_receipt(type, header, applications, instruments, withholdings)`: currency and integrator-account guards; FX difference; certificate capture.
17. `ar.reapply_advance(receipt, invoices)`; `ar.void_receipt(date)`; `ar.delete_receipt` (period guard).
18. `ar.advance_request(budget, items, pct|amount)`.
19. `ar.collections_followup(view)`: worklists, comment logging, next action, reminder emails, escalation.
20. `ar.aging(as_of, buckets, basis, currency_mode, accounts)`; `ar.current_account`; `ar.client_balance`.
21. `ar.credit_exposure(client)` and `ar.credit_check_on_approval(plan|budget)`.
22. `ar.fiscal_books(country, period)`: sales VAT subledger and country exports.
23. `ar.client_master_upsert` (tax ID validation, control account lock after first document, terms, tax profile).

### 10.2 Deterministic calculations worth a tool
- Commission base and amount (rule 3), plus supplier commission (rule 6).
- Due date engine (rule 20, including fortnight and month-end logic, weekend/holiday shift).
- VAT, perception and withholding calculators (rules 14–18), with country tables and thresholds.
- Incentive tier lookup and retroactive top-up (rule 7).
- Overcommission engine (rule 8): five calculation types, sequencing, cap, reduction, netting, settlement distribution.
- Advance-sale draw-down allocator (rule 9).
- Partial billing allocator (rule 10).
- FX difference (rule 19) and revaluation at cut-off.
- Aging bucketizer (rule 24); interest (rule 22); delay (rule 23); DSO.
- Credit exposure (rule 21).
- Billing split by % (rule 26), with a remainder-cent policy.
- Withholding proportional distribution across receipt lines, with an override.
- Numbering allocator with gap detection.

### 10.3 Controls and approvals to encode
- Approved-for-billing precondition. Credit-limit approval comes **before** client approval.
- NC/ND approval circuit. Supervisor-only overrides: manual receipt numbers, unmarking billed pendings, deleting cancelling NCs, rounding cap. Permission `1A` for receipt void.
- Period pre-close and close: no deletes; voids need a date.
- Integrator account immutability after the first document; one integrator per receipt; no manual entries on integrators.
- Irreversibility warnings for NC cancel invoice and NC VA remainder.
- Audit-practice clients: forbid cost ≠ sale.
- Client tax-status register check before invoicing (when enabled).
- Fiscal: consecutive authorization; do not filter by client when requesting CAE.

### 10.4 Exceptions the agent must handle
- CAE rejection (reason, fix, resubmit) and an expired AFIP certificate.
- Zero-value document in CL or CO (route to the internal POS).
- Deleted cancelling NC ("invoice without support"; mark the source as billed to avoid duplicates).
- Version Inicial differences (supplementary invoice or credit).
- Partly billed production item that needs changes (split items).
- Multiple currencies or integrator accounts in one receipt (split receipts).
- Withholding certificate number missing (0000000).
- Third-party cheque already endorsed (cannot void or delete the receipt).
- Overcommission recalculation after partial billing (version bump; credit note for negatives if not netting).
- Paid invoice that needs cancellation (config gate).
- Client excluded or non-vigent, or flagged `En Conflicto` (warn).
- Missing currency fiscal identifier (e-invoice failure).

---

## 11. Gaps and ambiguities

1. **Academia pages** contain only video titles, so no content is available for "controls to perform" (30 min), which is likely a month-end AR checklist.
2. **Foreign-currency billing:** the user guides repeatedly say billing in a foreign currency other than local is not allowed, yet every screen offers currency and exchange-rate fields, and reports handle foreign-currency invoices. Probably the rule is "the document currency must equal the source's currency" or a per-agency restriction. Needs confirmation.
3. **Administrative NC "always value 0":** this contradicts its stated use as a financial discount. Perhaps it is a zero-valued administrative document with amounts in specific lines, or a documentation error.
4. **Supplier commission "volume" guide** selects `Producción` while its title says media. The guides contain copy-paste inconsistencies, and prerequisites mention production budgets for media commissions.
5. **Exact journal accounts** are never listed; §6 is inferred. The revenue recognition for indirect investment (gross revenue versus pass-through) is not specified.
6. **Credit exposure sign** for unapplied NCs and advances is not explicit.
7. **Interest formula** (simple or compound, rate period) is unspecified.
8. **Retroactive incentive math** (the delta between tiers) is inferred.
9. **Overcommission calculation types** are named but not defined (absolute vs marginal vs stepped increments).
10. **Mark as billed "produces a result" with no entry:** how the P&L reflects it is not explained (probably via the cost already posted without matching revenue).
11. **"Listado de Comisiones a Clientes", "Listado de Prontos Pagos", "Visualización de Factura", "Cálculo de Porcentaje de Comisión Vendedores", "Facturación Bienes de Uso" (menu)** appear in menus but have no page in this group.
12. **Facturador BackGround, Municipios, Deuda Intercompany, Resultados por Intercompany Local, Motivos de Anulación** pages are stubs.
13. **Uruguay** and other countries in the brief are absent. Mexico's CFDI is referenced only through PAC XML stamping and annexes, with no CFDI versions, cancellation flows or payment complements (`complemento de pago`). Treat these as out of scope for this source.
14. **DSO and collection KPIs** are not computed by name; they must be derived.
15. **Receipt type name mismatch:** the void and delete guides refer to `Cobros Normal` while the main page lists `Cobros a Clientes`.
16. **Withholding distribution:** the manual says it is proportional but also says it cannot be calculated automatically. Treat it as a proportional default plus a manual override.
17. **Pronto Pago master** is under client masters but describes supplier early-payment discounts by media type with "entity = clients only". The intent is unclear (likely early-payment discounts granted to clients mirroring supplier tables).
18. **Background biller (Mexico deferred accounts)** is agency-specific and undocumented.
