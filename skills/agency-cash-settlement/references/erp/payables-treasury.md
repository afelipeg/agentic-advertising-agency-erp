# Accounts Payable (reception, payments, supplier masters) and Treasury

> **Provenance.** Functional reverse engineering of a reference agency ERP, derived from its publicly accessible help documentation (reviewed 2026-10-11). Content is paraphrased and restructured; it is not vendor documentation, source code or an endorsement. Bracketed ids such as `[mp301010]` identify the source page used as evidence. Items marked *inferred*, *assumed* or listed under gaps must be validated with your own controller, tax adviser and system owner before they drive postings or payments.

> Reverse-engineering spec derived from the reference ERP's help documentation. All content is paraphrased; Spanish identifiers in backticks are field/screen names only. This spec describes the business circuit, not the UI. Source references use the original help file names in brackets, e.g. `[mp301270]`.

---

## 1. Purpose and position in the end-to-end circuit

The agency ERP circuit runs: client brief → estimate/plan (media plan, production budget, expense request) → purchase/insertion orders to suppliers → supplier invoices received and matched to orders → supplier invoices posted to the ledger → client invoiced and collected → suppliers paid → cash/bank reconciled → period closed.

This module group covers the **back half of the cash-out side** and the **whole cash ledger**:

1. **Invoice intake ("traffic")** – logging physical/electronic supplier documents the moment they arrive, routing them to a responsible person for checking, returning defective ones, and handing clean ones to the posting step (`Control y Registración de Facturas Recibidas`, documented in the supplier-invoicing group, out of scope here). Includes the Liveranto supplier portal validation queue and line-level matching of platform invoices (Meta, Google) against digital plan orders via taxonomy codes.
2. **Payables management** – supplier current accounts, open-item and aging reports, payment-delay estimates, balances by client (to support "pay when paid"), supplier claims, salesperson commission settlement.
3. **Payment execution** – payment proposals (payment lists) with two-person approval, payment orders (`Órdenes de Pago`, OP) of several types, withholding-tax computation, and the separate "release" step (`Libranza`) that assigns the funding instruments (cash, checks, transfers, third-party checks, notes, employee expense balances) and creates the accounting entry. Bank-file export/import for bank-executed payments.
4. **Treasury** – bank deposits, inter-bank transfers, bank charges/credits, manual bank reconciliation, own-check books and printing, third-party check portfolio, check rejection, corporate credit cards, liquidity views (availability, average balances, funds movement), withholdings-suffered reconciliation, and Argentina's withholding pass-through report.

Upstream dependencies: supplier master, chart of accounts with observation codes, client receipts (`Cobranzas`, source of third-party checks and of "client has paid" evidence), media/production/expense orders, posted supplier invoices. Downstream: general ledger, tax books (VAT purchase sub-ledger, IIBB position), month-end close.

---

## 2. Process catalogue

Each process lists Trigger · Actor · Steps · Inputs · Outputs · State transitions · Approvals · Source.

### P1. Invoice reception log (supplier invoice traffic)
- **Trigger:** a supplier document (invoice, credit note, debit note) physically or electronically arrives at the agency.
- **Actor:** reception/AP clerk; then the assigned "responsible" checker.
- **Steps:**
  1. Create a reception record; system assigns a sequential traffic number (`Nº Tráfico`) and stamps today as entry date.
  2. Capture document date, document type (invoice / credit note / debit note; in Argentina also the fiscal document category), supplier (may be left blank if the supplier is not yet in the master), document number (point of sale + letter + number), currency, gross total including taxes.
  3. Assign the responsible collaborator who will hold and check the document; optionally link the related billing client; optional notes; optional image attachment.
  4. Save → status Pending (received).
  5. Responsible may be reassigned later (modify → save); the system logs status changes, user and date in the observations trail.
  6. If defective: Return, choosing a predefined return reason and priority plus free text. System assigns a return number and logs reason/user/date.
  7. When the supplier sends a correction: Re-enter the same record.
  8. When the document is posted in the invoice-registration step, the reception record becomes Posted (final).
- **Alternative intake:** Excel import with fixed layouts (one for expense invoices, one for media/production invoices). Imported rows are treated as already reviewed and approved for posting.
- **Inputs:** document data; return-reason master `[mp305267]`.
- **Outputs:** traffic log; per-responsible "received invoices" listing printed to accompany the paper for validation.
- **States:** New → Received/Pending → Returned → (Re-entered → Pending) → Posted. Listing filter adds Pre-registered and Paid.
- **Approvals:** none formal; the responsible's check is the control.
- **Source:** `[mp301267]`, `[ingresar-comprobantes-de-proveedores]`, `[devolver-…]`, `[reingresar-…]`, `[mp301266]`.

### P2. Received-invoices listing and bulk return
- **Trigger:** periodic follow-up or hand-off to responsibles.
- **Steps:** filter by entry date or document date; state (pending, returned, posted, pre-registered, paid); entity (all, supplier, responsible, client, no supplier assigned); supplier type (production, media, expenses, traffic); electronic-credit-invoice only; optional signatures column and traffic-number range. When listing Pending, multiple rows can be selected and returned in one action (return type, auto-number, free-text reason) and the return slip printed.
- **Source:** `[mp301266]`.

### P3. Counter-receipt (`Contrarecibo`) — mainly Mexico
- **Trigger:** after supplier documents are posted, the agency acknowledges receipt to the supplier with a document listing pending items before payment.
- **Modes (configuration):** (a) button on the reception/registration screen after saving an invoice; (b) standalone menu option operating on posted documents.
- **Steps:** pick supplier → system loads its posted documents in a date window; filter by client and by loading user; tick documents; save → independent sequential counter-receipt number; print (copies and number series come from configuration).
- **States:** Pending print → Sent; Annulled (shown in red in listings). Deleting removes as if never created.
- **Source:** `[mp301517]`, `[mp301518]`.

### P4. Invoice batch numbering
- **Trigger:** periodic (e.g., daily) archive control.
- **Steps:** choose date range → generate: every supplier invoice in the range without a batch number receives the next batch number. Listing by billing client with batch number and totals.
- **Source:** `[mp301364]`.

### P5. Temporary staff invoices (Colombia, closed loop)
- **Trigger:** promoters/temporary staff worked on an event budgeted in production.
- **Steps:** (1) temp-staff master holds each person and their applicable withholdings; (2) production budget gets an item of production type "Human Resource"; event organizer requests staff, HR assigns actual people; (3) delivery & evaluation screen confirms attendance or replacement → creates a "pending supplier invoice" for that person; (4) invoice entry selects generic supplier "temporary staff", then the specific promoter with pending billing, then the production estimate item; (5) if the person is in the simplified tax regime, the agency issues an "equivalent document" on the person's behalf and computes withholdings from the temp-staff master. If the person invoices in their own name, the supplier master flag "special supplier" makes the real name appear in the VAT purchase book.
- **Source:** `[mp302773]`.

### P6. Purchase request to client (`Solicitud de Compra`)
- **Trigger:** client requires a document per supplier before issuing its own purchase orders (configuration "purchase request" and client flag).
- **Steps:** date, internal number (auto), manual request number, type = supplier, plan number (only plans whose billing client uses requests), supplier, item type direct/indirect, currency, VAT from plan; secondary data from plan (payment terms editable, job number, client, product); description; footer notes; tick plan lines (year-month, insertion, item, order, description, amount). Allows one client PO number per request instead of one per month in the plan.
- **Source:** `[mp302721]`.

### P7. Portal invoice validation (Liveranto)
- **Trigger:** supplier uploads invoice (+XML, attachments) to the supplier portal, or invoice arrives via mail import.
- **Actor:** formal/tax validator, then requester of the good/service (two different people recommended), then poster.
- **Steps:** filter by queue (Pending, Rejected-pending-export, Approved, Posted), origin (media order / production order / expense order / manual), document date or upload date, supplier, currency; optional columns client, job topic, origin. Each row shows how it entered (portal, mail import, manual), the order(s) the supplier linked, attachments and XML, and an amount-match indicator (match vs discrepancy between invoice and order). Actions: Approve → later Post (only rows in Approved queue); Reject with a classified reason → later Recover when the supplier corrects it.
- **Posting rule:** posting consumes the linked order: production PO (bound to production item/task), media insertion order (bound to media type in plan), expense PO (bound to expense concept).
- **States:** Pending → Approved → Posted; Pending → Rejected (pending export to portal) → exported → Recovered → Pending.
- **Source:** `[mp302844]`.

### P8. Line-level reconciliation of platform invoices (taxonomy)
- **Trigger:** automatically imported invoices from digital platforms whose lines carry a taxonomy order code.
- **Preconditions:** taxonomy in use; taxonomy assigned to the supplier; automatic import.
- **Steps:** list invoices filtered by associated yes/no/all, date (document or load), supplier, currency. Per line: description, taxonomy order number, derived year/month/order/item and plan number (hyperlinked to the digital plan), billing type direct/indirect, billed amount, ordered amount (0 if unmatched), difference = billed − ordered, association state. Unmatched lines are associated manually in the digital plan's "adjust orders by invoice" function (permission-gated).
- **States:** invoice Associated when every line is linked; otherwise Not associated.
- **Source:** `[mp302942]`.

### P9. Payment proposal (payment list) — create, review, approve
- **Trigger:** recurring payment run (e.g., weekly on Fridays; list prepared a day earlier).
- **Actors:** analyst (prepares) and approver (user with level 1 / "save list as final" permission).
- **Steps (prepare):**
  1. Choose list = New; set the intended payment date.
  2. Filter: due-date range of open invoices; criterion (supplier, supplier type, media type, or supplier control account) with ordering; supplier range; client filters (characteristics of related client invoices); currency; payment method (check or transfer — segments suppliers); early-payment options; optional saved filter template (shareable, editable, deletable).
  3. Optional controls: "with client control" shows the status of the related client invoice; "show fully collected" shows the receipt that collected it, its date and, if paid by check, the check due date. This is the pay-when-paid evidence.
  4. Run → open items listed; tick items to pay.
  5. Calculate → payable summary per supplier; withholdings computed here if configured to do so; optionally mark "check issued by bank".
  6. Save → list in status Provisional. **All listed items are locked** (even unticked ones) until the list is approved; they disappear from manual OP selection but still appear as unpaid in reports.
- **Steps (approve):** approver opens Existing list by payment date/description → run → sees ticked items plus other eligible items → may untick/tick → save and calculate (withholdings) → Approve → status Definitive (pending release). Unticked items are released for future runs.
- **Extras:** export candidate list to spreadsheet for offline validation and re-import with "Yes" in the selection column (import only on an existing list); "Audit" view shows each item with the supplier-invoice note and, for expense requests, the request detail; Colombia "include incentives" filters deduct billed incentives from invoice balances.
- **Restrictions:** only Definitive lists can be paid; lists are paid from the OP screen.
- **Source:** `[mp301160]`, `[mp501160]`, `[generar-lista-…-provisoria]`, `[consultar-lista-…]`, `[aprobar-lista-…]`.

### P10. Payment orders from an approved list (automatic by list)
- **Trigger:** approved list exists for the payment date.
- **Steps:** new OP, type "automatic by list", fiscal year, optional manual number, date; choose list, description, payment currency, rate if foreign; confirm → if withholdings are computed at release, a window shows suppliers with their withholdings to tick; then generation window: generation type (pay with normal checks, deferred checks, transfer, or generate without instrument), order (supplier code or alphabetical), email notification, bank account, first check number (suggested; overridable), clearing hours for normal checks → save → list of generated OP numbers and amounts → confirm. One OP (and its release) per supplier. No release is generated for items flagged "check issued by bank".
- **Restrictions:** one payment method per list; one bank account per list; no partial payment of a list; foreign-currency debt cannot be paid with a different foreign currency.
- **Source:** `[generar-ordenes-de-pago-en-base-a-una-lista-de-pagos]`, `[mp301160]`.

### P11. Manual payment order — supplier invoices
- **Trigger:** ad-hoc payment outside a list.
- **Steps:** new OP, type "supplier payment", fiscal year, date (editable), optional manual number (supervisor/level 1 only: `Recuperar Nº`), beneficiary supplier (search by name or tax ID), description, debt currency (+rate). Taxes tab: income-tax withholding category, VAT withholding %, IIBB withholding % — editable for this payment only, never written back to the master. Confirm → open items for that supplier in that currency; tick, optionally reduce "to pay" for partial payment; optional manual lines (rounding, unexpected cost; expense accounts require job number, work order, cost center and debit/credit direction). Save → OP status Pending payment. Then Pay (release) — see P16.
- **Restrictions:** one debt currency per OP; multiple invoices per OP; multiple instruments per release; invoice cannot be netted against a credit note inside an OP (use an adjusting entry instead).
- **Source:** `[mp301270]`, `[generar-una-orden-de-pago-a-proveedores]`.

### P12. Supplier advance
- Same header as P11; after confirming, use action "add advance" → an advance line appears → enter amount → save (Pending payment) → release. Advances' later consumption is visible in the supplier payment inquiry (OP number, date, amount applied).
- **Source:** `[generar-una-orden-de-pago-de-anticipo-de-proveedores]`, `[mp301369]`.

### P13. Payment of pending notes (documents)
- Same header; after confirming, a Documents tab lists the agency's pending payable notes for the supplier; tick and set partial amounts; save; release.
- **Source:** `[generar-una-orden-de-pago-a-proveedores-de-documentos-pendientes]`.

### P14. Refund to client
- **Precondition:** client has an unapplied advance or credit note.
- Type "client refund"; beneficiary = billing client; debt currency must equal the advance's currency; tab lists advances paid and credit notes issued; tick and set amounts; save; release. Not covered by payment lists (use manual OP).
- **Source:** `[generar-una-orden-de-pago-de-devolucion-a-clientes]`, `[mp301270]`.

### P15. Miscellaneous payment (concept without document) and cost advance
- **Miscellaneous (`Pagos Varios`):** free-text beneficiary; description; debt currency; Manual entries grid: account, subaccount or expense concept, comment, and — for P&L accounts only — job number (agency generic job allowed), work order, cost center; debit amount. Balance-sheet accounts do not require job/OT/CC. Unlimited lines. Used for tax payments, fund replenishment, transfers between own banks, occasional suppliers with bank data (Argentina HSBC "various suppliers").
- **Cost advance (`Anticipo de Costos`):** preconditions — account with observation code 84 ("cost rendition"), collaborator exists as subaccount, production estimate with an item for supplier "Cost rendition" approved by client. Choose estimate month and number (only client-approved shown), rendition account and collaborator subaccount, beneficiary, currency = item currency; in manual entries pick the estimate item and amount; amount may be ≤ budgeted item, never above (blocked). Save → Pending payment → release.
- **Source:** `[generar-una-orden-de-pago-de-un-concepto-sin-comprobante]`, `[generar-nueva-orden-de-pago-de-anticipo-de-costos]`, `[mp301270]`, `[mp302905]`.

### P16. Payment release (`Libranza`)
- **Trigger:** OP in Pending payment; treasurer decides funding.
- **Steps:** open OP → Pay → choose payment currency (defaults to OP currency; foreign rate shown and editable) → payment (accounting) date → add one or more instruments:
  - **Cash (local):** cash or petty-cash account + amount.
  - **Foreign cash:** foreign-currency fund account + amount.
  - **Normal check:** bank account → system proposes the first unreleased check number of that checkbook (overridable if still unreleased); issue date = payment date; default clearing 48 h → computed due date (editable); amount; "signed" flag.
  - **Deferred check:** as above but due date entered manually and must be > 48 h.
  - **Transfer:** bank account, reference number (0 allowed), debit term (0), amount.
  - **Third-party checks:** choose endorsable checks in portfolio (from client receipts); may be less than the total, remainder via another instrument.
  - **Own notes:** term in days → due date; amount.
  - **Third-party notes:** pick from portfolio.
  - **Expenses to render:** collaborator subaccount who previously paid on the agency's behalf (or holds an advance) + amount.
  - Optional supplier email notification (address from supplier master; body lists documents paid, instruments and withholdings).
- **Outputs:** OP status Paid; accounting entry dated at payment date; check records moved to issued; email.
- **Rules:** release date drives the accounting period (OP dated 31st, release on the 2nd → books in next month). Each instrument must map to an account with the proper observation code and currency; only instruments defined for the chosen currency are offered.
- **Source:** `[librar-una-orden-de-pago]`, `[mp301270]`.

### P17. Undo flows: delete release, delete OP, annul OP
- **Delete release (`Eliminar Pago`):** removes the instruments; OP returns to Pending payment. Not allowed in a pre-closed month (must annul instead).
- **Delete OP:** only if not paid (delete release first); leaves no trace; number can be reused via manual numbering; a configurable maximum number gap (`Máx. Saltos Orden de Pago`) limits skipping.
- **Annul OP:** only when status Paid; asks for an annulment date in an open period; reverses all computed withholdings (re-issuing may compute a different amount); trace kept.
- **Bulk delete** from the detailed payments listing, optionally restricted (`Restringir anulación`) to require user, task number and reason.
- **Source:** `[eliminar-la-libranza-de-un-pago]`, `[eliminar-una-orden-de-pago]`, `[anular-orden-de-pago]`, `[mp301300]`.

### P18. Payments with availability control
- **Trigger:** treasurer funds a batch of pending OPs and approved lists.
- **Steps:** view balances per funding source as of a date (negative balances visible); pick the bank and instrument (normal/deferred check); select pending OPs (no release yet) and approved lists to fund; see total vs available; save. Recommended over releasing OP by OP.
- **Source:** `[mp301412]`.

### P19. Bank-executed payments (export / import)
- **Preconditions:** configuration "generate payment list by bank"; bank interface configured and tested with the vendor; supplier bank accounts in master (one marked main; bank-account key such as CBU computed from data).
- **Export:** choose bank → OP date range auto-filled with OPs pending release; payment method (common/deferred check, transfer) auto; issue date and export date must be > 1 day and < 15 days from today; status Pending send / Sent; file path and bank-defined format, concept, "not to order" flag, printed signature, supplier email; bank account data (transaction class, branch, account number mandatory). Run → select OPs → "write to disk" → file for the bank portal; selected OPs become Released with payment date/type.
- **Import:** bank returns which check/instrument executed each payment; choose import date, bank and method; upload file; the release and accounting are recorded on that date (OPs had no entry until then).
- **Source:** `[mp301302]`, `[mp301299]`, `[mp302910]`, `[mp302893]`.

### P20. Supplier claims and portal sync
- Supplier raises claims in the web portal; nightly sync (or manual "synchronize") imports claims and publishes received invoices, payment status, downloadable OP and withholding certificates. Agency answers a claim with an estimated payment date or an observation → status Answered. Alert lists unanswered claims.
- The same screen records **check pickup**: mark (with date) which signed checks the supplier collected; can be unmarked. Reconciliation should then consider only delivered checks.
- **Source:** `[mp309264]`, `[mp301309]`, `[mp302792]`.

### P21. Salesperson commission settlement
- Period + basis (invoice detail or work order) + state "not settled" → list client invoices with computed commission from salesperson master percentages, **regardless of collection** → tick and settle → invoices flagged commission-settled. Optional mandatory salesperson invoice number (configuration). Wrong settlement can be annulled. A read-only listing lets salespeople follow their status (gross commissionable base and commission).
- **Source:** `[mp301221]`, `[mp301220]`.

### P22. Bank deposits and inter-bank transfers
- **Trigger:** collected values (cash, third-party checks) to be deposited; funds moved between own banks.
- **Steps:** new deposit: fiscal year, optional manual number (level 1), destination bank account, date, clearing hours, currency auto (rate if foreign), optional deposit slip number; tabs: own normal checks from other accounts, own deferred checks, cash amount, third-party checks in portfolio (tick, with due dates), transfers from another bank (source bank, transfer number, amount). Save → deposit with summary and journal entry (view only).
- **Rules:** only same-currency funds as the destination account; transfers can alternatively be recorded with a miscellaneous OP (recommended for control).
- **Source:** `[mp301261]`, `[registrar-transferencias-bancarias]`, `[generar-depositos-bancarios]`, `[consultar-…]`, `[eliminar-un-deposito-bancario]`.

### P23. Bank charges and credits
- **Trigger:** daily review of bank statement charges (maintenance, overdraft, check tax, perceptions) or credits.
- **Steps:** type Debit or Credit; fiscal year; posting date; bank account; bank tax ID (recommended for the VAT book); bank movement date; lines: job number (agency generic recommended), work order, detail, account (expense accounts code 07 via F2; IIBB perception accounts code 60; VAT perception accounts code 15), expense concept, VAT account, cost center, net amount → VAT auto-computed (overridable). Save → optional print of the entry.
- **Rule:** only charges captured here feed the VAT purchase book and VAT/IIBB position screens.
- **Source:** `[mp301283]`, `[registrar-debitos-bancarios]`, `[registrar-creditos-bancarios]`.

### P24. Manual bank reconciliation
- **Trigger:** daily or periodic, against the bank statement.
- **Steps:** fiscal year; type Manual; bank; "date to" (date from defaults to last reconciliation); check status filter (withdrawn / not withdrawn / all); annul = No → Run. All system movements arrive **pre-ticked** as reconciled; recommended practice: untick all, then tick each movement that appears on the statement; running balance must equal statement balance. Save Provisional (resume later) or Definitive (reconciled set becomes the opening balance of the next reconciliation; report shows remaining unreconciled items and totals of deposits and payments).
- **Annul/modify:** set "date to" to the last reconciliation date with annul = Yes → shows only that reconciliation's items → Delete (releases all) or Modify (untick specific items) → save.
- **Rules:** reconciliation is extra-accounting and only sees treasury-originated movements (OP, receipts, deposit slips, bank debits/credits) or journal entries of type "funds movement". Manual ledger adjustments of other types will not appear.
- **Source:** `[mp301282]`, `[generar-conciliacion-bancaria-provisoria-]`, `[generar-conciliacion-bancaria]`, `[anular-conciliacion-bancaria]`. Automatic reconciliation codes exist but are undocumented `[mp302947]`.

### P25. Own checkbooks, check printing and check lifecycle
- **Checkbook registration:** type normal/deferred (deferred enabled per country), bank (accounts code 43), first number, quantity (default 50).
- **Printing:** requires a bank-specific check layout and OPs paid with checks. Choose fiscal year, check type, bank, issue date (oldest pending suggested) → number range; foreign-currency coupon option; print all; crossed checks (deposit-only, two lines top-left). Emit → beneficiary per check (from supplier master "check payee" field, overridable; "update master" writes it back) → confirm per check or all. Reprinting shows only a warning.
- **Inquiry/maintenance:** per check shows OP date, debit term, status, due date, OP number, amount, signed flag; actions: mark signed, mark printed/not printed (when printed outside the system); annul (only if linked to an OP — first undo the release and repay with another check; afterwards it can only be deleted, except printed checks which can only be annulled); delete unused checks (e.g., wrongly loaded, or bank-issued checks not picked up and not linked to an OP).
- **Source:** `[mp301157]`, `[ingresar-chequera-…]`, `[consultar-cheques-propios]`, `[mp301280]`, `[emitir-e-imprimir-cheques]`, `[mp301278]`.

### P26. Check rejection
- **Own check rejected** (supplier could not cash): new rejection → type own, normal/deferred, fiscal year of issue, bank, check number → shows issue date, currency, amount → rejection date (default today; drives entry date) → confirm → release window to enter replacement instruments in the same operation → original OP shows rejected check (red) and replacement.
- **Third-party check rejected** (client's check endorsed to a supplier or deposited): two effects — (a) supplier debt reopens and must be settled with replacement instruments as above; (b) client owes the agency: amount moves to the "rejected checks" account (observation code 45), not to the client's invoice current account. No debit note or bank-fee calculation is generated. In the next client receipt, a "rejected checks" window lets the user select it and receive a replacement value.
- **Deferred replacement:** two special configurations allow rejecting without immediately entering the replacement (e.g., waiting for client funds); vendor support validation advised.
- **Source:** `[mp301291]`, `[generar-rechazo-de-cheques-propios]`, `[rechazar-cheques-de-terceros]`.

### P27. Corporate credit card
- **Setup:** configuration "uses corporate card"; petty-cash-type account per card and currency; card master (description, accounts for pesos/dollars, bank fee and VAT accounts, statement closing day, payment due day, purchase and financing limits); additional cards per holder (system user) with card number.
- **Charges:** recorded in a petty-cash sheet against the card account (with attachments linked per line; approval circuit; tax breakdown or direct save). Installment purchases: register the full invoice normally, then cancel supplier debt with an adjusting entry of type "credit card supplier adjustment", leaving the balance on the card account (not compatible with early-payment discount configuration).
- **Statement matching:** new statement → system loads rendered sheet items and adjustment-paid installments → all pre-ticked; untick items not on this statement (carry forward) → save, validating total equals the issuer statement; separate lines per currency.
- **Payment:** only on/after the due date, OP type "corporate card payment" selects the statement; one line per currency; cancels card account against bank.
- **Source:** `[mp302900]`, `[mp302901]`, `[mp302899]`.

### P28. Withholdings suffered reconciliation and pass-through
- **Suffered income-tax withholdings:** filter by account, reconciled status, date, client; with "not reconciled", tick withholdings (balance column updates) → save → remaining list. Drill to originating transaction.
- **Argentina VAT withholding pass-through:** report of client VAT withholdings (from receipts) that are transferable to the related suppliers, showing receipt, client documents affected, linked supplier documents, OP and payment, transferred vs pending amounts; filter media/production, by receipt or OP date, clients, suppliers.
- **Source:** `[mp302661]`, `[mp302748]`.

### P29. Electronic collection file and payroll import (legacy)
- Generate a file with client debt for electronic collection (no detail documented) `[mp302774]`.
- Payroll import from a flat file into a journal entry — superseded by provisional journal entries with an approval circuit `[mp301379]`.

---

## 3. Entities

| Entity (ES / EN) | Key fields | Identifier | Relationships |
|---|---|---|---|
| `Recepción de Factura` / InvoiceReceipt | traffic number, entry date, document date, doc type, fiscal doc category (AR), supplier (nullable), doc number, currency, gross total, responsible, related client, status, last modified, observations log, return number/type/priority/reason, attachment | `nro_trafico` (sequential) | → Supplier, User (responsible), BillingClient, ReturnReason; → SupplierInvoice once posted |
| `Razón de Devolución` / ReturnReason | code, description | code | used by InvoiceReceipt, portal rejection |
| `Contrarecibo` / CounterReceipt | number, date, supplier, client filter, loaded-by filter, lines(doc date, type, number, amount, due), status | independent sequence | → Supplier, SupplierInvoice[] |
| `Lote de Facturas` / InvoiceBatch | batch number, date range | sequence | → SupplierInvoice[] |
| `Solicitud de Compra` / PurchaseRequest | date, internal no., request no., type=supplier, plan, topic, supplier, item type direct/indirect, currency, VAT, payment terms, job number, client, product, description, notes, lines | internal no. | → MediaPlan lines, Supplier, client PO number |
| `Comprobante Portal` / PortalInvoice | upload date, doc date, supplier, currency, origin (media/production/expense/manual), entry channel, linked orders, XML, attachments, match flag, status, rejection reason | portal id | → Order(s), SupplierInvoice |
| `Línea Taxonomía` / PlatformInvoiceLine | invoice, line no., description, taxonomy order no., year/month/order/item, plan no., billing type, billed, ordered, difference, associated | invoice+line | → DigitalPlanOrder |
| `Lista de Pagos` / PaymentList | description, payment date, criterion, filters/template, payment method, status (provisional/definitive), selected items, withholdings, check-by-bank flag per supplier | description + date | → SupplierInvoice[] (locks), → PaymentOrder[] |
| `Template de filtros` / ListFilterTemplate | name, saved filters, owner | name | shared among list users |
| `Orden de Pago` / PaymentOrder | fiscal year, number, type, date, beneficiary, description, debt currency, rate, tax overrides (income-tax category, VAT %, IIBB %), observations, footer notes, selected documents with balance and amount to pay, manual entries, status, list ref, attachments | (fiscal year, number) | → Supplier/Client/free beneficiary, SupplierInvoice/Advance/Note/CreditNote, PaymentRelease, Withholding[] |
| `Registro Manual` / ManualEntryLine | account, subaccount/concept, comment, job number, work order, cost center, debit, credit, estimate item (cost advance) | line | → Account, Job, CostCenter |
| `Libranza` / PaymentRelease | payment currency, rate, payment date, instruments[], email notification | 1:1 with OP | → Instrument lines, JournalEntry |
| Instrument line | kind (cash, foreign cash, normal check, deferred check, transfer, third-party check, own note, third-party note, expense-to-render), account/bank, number/reference, issue date, clearing hours/term, due date, amount, signed | per line | → OwnCheck, ThirdPartyCheck, Note, Collaborator subaccount |
| `Retención` / Withholding | tax type (income tax, VAT, IIBB, ICA, IGV, non-domiciled income), base, rate/category, amount, certificate | per OP | → PaymentOrder, Supplier |
| `Chequera` / Checkbook | type normal/deferred, bank account, first number, quantity | bank+type+range | → OwnCheck[] |
| `Cheque Propio` / OwnCheck | bank, number, type, OP, issue date, debit term, due date, amount, status, signed, printed, picked-up date, payee | bank+type+number | → Checkbook, PaymentOrder, Deposit |
| `Cheque de Terceros` / ThirdPartyCheck | internal code (6 chars), issuer bank, number, issue date, due date, currency, rate, amount, client, receipt no./date, status, endorsable flag, delivered to (supplier OP / bank deposit) | internal code | → Receipt, ThirdPartyBank, PaymentOrder or Deposit |
| `Documento` / Note (own / third-party) | internal no., issue/release date, OP, supplier or client, amount, currency, due date | internal no. | → PaymentOrder / Receipt |
| `Depósito Bancario` / Deposit | fiscal year, number, bank, date, clearing hours, currency, rate, slip no., lines by kind | (fiscal year, number) | → Bank account, ThirdPartyCheck[], JournalEntry |
| `Débito/Crédito Bancario` / BankCharge | number, type, fiscal year, date, bank, bank tax ID, bank movement date, lines (job, OT, detail, account, concept, VAT account, CC, net, VAT) | sequence | → JournalEntry, VAT book |
| `Conciliación Bancaria` / BankReconciliation | fiscal year, bank, date from/to, type, status provisional/definitive, reconciled movement ids, opening/closing balance | bank+date-to | → treasury movements |
| `Tarjeta Corporativa` / CorporateCard | code, description, accounts per currency, fee/VAT accounts, closing day, due day, limits | code | → AdditionalCard[], CardStatement[] |
| `Tarjeta Adicional` / AdditionalCard | card, holder user, card number | code | → CorporateCard, User |
| `Resumen de Tarjeta` / CardStatement | card, due date, selected items, total per currency | card+due date | → PettyCashSheet lines, Adjustment entries, PaymentOrder |
| `Banco de Terceros` / ThirdPartyBank | 3-digit code, description, tax ID | code | → ThirdPartyCheck |
| `Proveedor Vario` / OccasionalPayee (AR) | code, name, contact email, tax ID, bank accounts (bank, account code, branch, type, number, currency, default, usable for bank list) | code | → Miscellaneous OP |
| `Entidad de Banco para Interface` / BankInterface | bank, code type, interface code, detail, company | code | → bank export/import |
| `UTE` / JointVenture | supplier, member suppliers with % share (sum 100) | supplier | → tax calc |
| `Categoría de Monotributo` / SimplifiedTaxCategory (AR) | code, description, max annual income, activity (both/goods) | code | → Supplier |
| `Reclamo` / SupplierClaim | number, supplier, invoices, status, estimated payment date, answer | number | → portal |
| `Liquidación de Comisión` / CommissionSettlement | period, basis, invoices, salesperson, %, commission, salesperson invoice no. | per invoice | → ClientInvoice, Salesperson |
| Management types/actions | code, description, origin (supplier/client/job), active | code | collection/supplier follow-up process |
| `Proveedor Online` / OnlineOrderSupplier | code, description, URL, port, agency code, user | code | order interface |

Account observation codes (classification tags on GL accounts used as hard filters): 30 supplier control accounts; 43 bank accounts; 07 expense (and bank income) accounts; 60 IIBB perceptions; 15 VAT perceptions; 45 rejected checks; 84 cost rendition; AM Argentine VAT perception on digital services.

---

## 4. Document lifecycles

**InvoiceReceipt:** New → Received (Pending) ⇄ Returned (re-enter returns to Pending) → Posted (terminal). Listing also exposes Pre-registered and Paid as derived states. Delete only before posting.

**PortalInvoice:** Pending → Approved → Posted; Pending/Approved → Rejected → (pending export) → Exported to portal → Recovered → Pending.

**PlatformInvoice (taxonomy):** Not associated → Associated (all lines linked).

**CounterReceipt:** Created → Pending print → Printed/Sent; → Annulled; delete = never existed.

**PaymentList:** New (unsaved) → Provisional (items locked) → Definitive/Approved (unselected items unlocked) → Paid (OPs generated). Audit is a view, not a state.

**PaymentOrder:**
```
Draft --save--> PendingPayment --release--> Paid --annul(date in open period)--> Annulled
PendingPayment --delete--> (gone; number reusable)
Paid --delete release (not in pre-closed month)--> PendingPayment
PendingPayment --bank export "write to disk"--> Released(by bank) --bank import--> Paid (instrument detail)
```
Accounting entry exists only in Paid/Released states.

**OwnCheck:** Available (in checkbook) → Released in OP (not printed) → Printed → Signed → Delivered/Picked up → Cleared (reconciled). Side paths: Rejected (replacement issued); Annulled (only when linked to an OP; terminal except delete for non-printed); Deleted (unused). Status labels in source: not picked up, not printed, printed, rejected, annulled; listing criteria add post-dated, unreleased, undelivered, delivered, overdue undelivered.

**ThirdPartyCheck:** In portfolio (from receipt) → Delivered to supplier (OP) | Deposited (deposit) → Cleared; any → Rejected (moved to account 45) → Replaced via new receipt. Endorsable flag editable.

**Deposit:** Saved → (deleted without trace). **BankCharge:** Saved → deleted (entry removed with document).

**BankReconciliation:** Provisional ⇄ edited → Definitive → (annul: Delete or Modify) → back to unreconciled/provisional.

**CardStatement:** New → Saved (total matched) → Paid via OP on/after due date; may be deleted and rebuilt before payment.

**CommissionSettlement:** Unsettled → Settled → Annulled → Unsettled.

**SupplierClaim:** Open (unanswered alert) → Answered.

---

## 5. Business rules and calculations

1. **Reception before posting.** A received document may stay without supplier; it must be posted through invoice registration to reach Posted. Returned documents cannot be posted until re-entered. Excel-imported receipts are assumed approved.
2. **Two-person invoice approval (recommended).** Formal/tax validation and receipt confirmation by the requester should be different users before posting a portal invoice.
3. **Order match indicator.** Portal invoice vs order amount: equal → OK; different → discrepancy flagged for analysis. Taxonomy line difference = billed − ordered (ordered = 0 if no order).
4. **Batch numbering.** Next batch number is applied to every supplier invoice in range lacking one; never re-numbers.
5. **Payment candidate selection.** An item is a list candidate if: open balance > 0; due date in the selected range; matches criterion filters (supplier/type/media type/control account), currency, and payment method segment; not already locked by another list or pending OP. Optional evidence: related client invoice status and "fully collected" receipt (date, check due date). Selection is human.
6. **Locking.** Items in a Provisional list, or in an unreleased OP, are excluded from any other list/OP but remain in open-item reports. Unselected items unlock on list approval; deleting an OP unlocks its items.
7. **List payment constraints.** Single payment method, single bank account, whole list (no partial), one OP per supplier, ordering by supplier code or name.
8. **Withholding timing.** Agency-wide configuration `No Calcula Retenciones en Pago por Lista`: false → computed when saving/calculating the list; true → computed at OP release. Not selectable per list.
9. **Withholding inputs.** Per OP the user may override income-tax category, VAT withholding %, IIBB withholding %; overrides apply to that OP only. Supplier master supplies defaults (income tax, VAT, IIBB, advertising contribution; ICA in Colombia). Joint ventures split the computation by member % (must total 100). Simplified-tax (monotributo) suppliers use category-specific treatment and an annual invoicing cap.
10. **Withholding reversal.** Annulling an OP reverses all its withholdings; re-issuing recomputes and may change the net.
11. **Generic withholding formula (design assumption; the manual gives no formula):**
    `base = Σ(amount_to_pay_i × net_ratio_i)` where `net_ratio_i = taxable_net_i / gross_i` of each invoice;
    `wh_t = max(0, base × rate_t − already_withheld_t_in_period)` subject to per-tax minimum thresholds;
    `net_payment = Σ amount_to_pay_i − Σ wh_t − early_payment_discount`.
12. **Argentina digital-service perception.** Recorded via a miscellaneous OP against account code AM; system shows all invoices of configured foreign digital suppliers (paid or not) and the user enters the perception per invoice; no system validation — expected value is 21% of the invoice net (`perception = 0.21 × net`); control is the agency's responsibility.
13. **Costa Rica.** OP to a foreign supplier is blocked unless the income-tax withholding is approved; summary adds a line "income-tax withholding".
14. **Early-payment discount.** With `Usa Pronto Pago Proveedores`, list can apply supplier discount %: `discount_i = balance_i × pct_supplier` when payment date ≤ agreed early date ("next payment date" field); option to list only suppliers with discount. Manual overrides of the computed discount are reported separately. Colombia: internal credit notes for early-payment discounts (over-commission contracts) are identified and applied at payment.
15. **Currency.** One debt currency per OP. Payment currency chosen at release; foreign debt cannot be paid with a different foreign currency; local-currency payment of foreign debt allowed with editable rate. Deposits and transfers only in the destination account's currency.
16. **Exchange difference (inferred).** For foreign-currency items: `fx_diff = amount_FC × (rate_payment − rate_book)`, where `rate_book` is the rate at which the invoice was booked or the prior fiscal-year closing rate if from a previous year. Reports' "accounting" format shows `original_LC` and `updated_LC = amount_FC × rate_at(date_to)` (rate editable; must be entered manually when date_to is not a month end). Funds-movement report shows FX adjustments separately.
17. **Check defaults.** Normal check: issue date = payment date; due = issue + 48 h (editable). Deferred check: due must be > 48 h after issue. Transfer: reference may be 0, term 0. Next check number = lowest unreleased number in the checkbook for that bank/type; manual number must be unreleased. Checkbook default quantity 50.
18. **Check state rules.** Annul only checks linked to an OP (after undoing the release); printed checks can only be annulled, never deleted; unused, unlinked checks can be deleted. Reprint allowed with warning.
19. **Third-party checks** must originate from a receipt; only endorsable ones can pay suppliers; partial use allowed with other instruments covering the remainder.
20. **Rejection.** Own-check rejection requires replacement instruments in the same operation (unless deferred-replacement configuration). Third-party rejection books the amount to account 45; client replacement via next receipt; no fees or debit note computed. Entry date = rejection date.
21. **Release period.** Accounting date = release payment date, not OP date. Deleting a release is forbidden in a pre-closed month; annul instead with an open-period date.
22. **Numbering.** OP numbers auto-sequential per fiscal year; manual numbering only for level-1/supervisor; maximum allowed gap configurable. Deposit manual numbering level-1 only.
23. **Bank export window.** `today + 1 day < export_date < today + 15 days` (same validation for issue date). Exported OPs flip to Released.
24. **Reconciliation matching.** `reconciled_balance = opening_reconciled_balance + Σ(ticked deposits/credits) − Σ(ticked payments/debits)`; must equal statement closing balance before saving Definitive. Only treasury movements are candidates; default pre-ticked; recommended reconciling only picked-up checks. Definitive reconciliation sets next opening balance; annulment restricted to the latest reconciliation.
25. **Bank charges.** Expense lines only to code-07 accounts; IIBB perceptions to code-60; VAT perceptions to code-15; `VAT = net × VAT_rate(VAT account)` overridable; exempt lines have no VAT account. Only charges recorded here feed tax books.
26. **Availability.** `availability = opening_balance + deposited_collections − checks_in_transit − transfers_in_transit`, where checks in transit are own checks delivered to suppliers but not yet cashed and transfers in transit are supplier transfers not yet debited (see gap 16 on whether deposits are already inside the book balance).
27. **Average bank balance.** `avg_month = Σ_d end_of_day_balance_d / days_in_month` for code-43 accounts.
28. **Payment delay estimate.** `est_client_collection = invoice_date + 40 days`; `est_supplier_payment = est_client_collection + 7 days` (fixed parameters in source).
29. **Aging buckets.** User defines descending positive day thresholds (e.g., 90, 60, 30, 0) and labels; base date = due date, accounting date or document date; items allocated to the bucket where `days_overdue ≥ threshold`; ascending order breaks the report. Optional interest on overdue: `interest = balance × rate × days_overdue / 365` (rate user-entered; day-count not specified).
30. **Cut-off reports.** "Cut to date" open items use a month-end date; deferred checks not yet due may be treated as unpaid; post-closing invoices can be excluded; advances may sit in separate accounts.
31. **Cost advance cap.** `advance_amount ≤ budget_item_amount` for a client-approved estimate.
32. **Commissions.** `commission = commissionable_gross × salesperson_pct`, computed on invoices whether collected or not.
33. **Card statement.** `Σ selected items (per currency) = issuer statement total`; payment OP only on/after due date.
34. **Contrarecibo/card/portal** are optional modules gated by configuration.
35. **No netting in OP.** An invoice cannot be cancelled against a credit note within an OP; use an adjusting entry.
36. **Joint venture shares** must sum to exactly 100%.
37. **Simplified-tax cap.** `Σ invoices_year(supplier) + new_invoice ≤ category_max_annual_income` else block/alert.
38. **Payment notifications** read the supplier email from the master; require the email service configured.
39. **Restricted deletion.** With `Restringir anulación`, bulk payment deletions require user, task number and reason.

---

## 6. Accounting impacts

| Event | Debit | Credit | Notes |
|---|---|---|---|
| Invoice reception / portal approval | — | — | No entry; posting happens in invoice registration (other group). |
| Payment list saved/approved | — | — | Only locks items. |
| OP saved (pending) | — | — | No entry until release. |
| Release – supplier invoices | Supplier control account (code 30) for amounts paid | Funds account(s) per instrument (bank 43, cash/petty cash, third-party checks in portfolio "values to deposit", notes payable, collaborator expense-to-render subaccount); withholdings payable per tax | Manual lines add expense/other accounts with job/OT/CC. |
| Release – supplier advance | Supplier advances | Funds | Later applied to invoices. |
| Release – client refund | Client advance / credit note balance | Funds | |
| Release – miscellaneous | Accounts from manual grid | Funds | P&L lines need job/OT/CC. |
| Release – cost advance | Cost rendition account (84) / collaborator subaccount | Funds | Tied to estimate item. |
| Release – AR digital perception | Perception account (AM) | Card/bank | |
| Corporate card payment | Card account (petty-cash type) per currency | Bank | |
| Installment purchase | Supplier control | Card account | Adjusting entry "credit card supplier adjustment". |
| FX at payment | FX loss / Supplier | Supplier / FX gain | Inferred; shown as "various adjustments". |
| Deposit | Bank | Values to deposit (third-party checks), cash, source bank (transfer) | |
| Bank debit | Expense (07) + VAT credit + IIBB perception (60) / VAT perception (15) | Bank | Feeds VAT purchase book and IIBB position. |
| Bank credit | Bank | Income account (07) | |
| Own check rejected | Reverses original instrument; new instrument booked | | Entry at rejection date. |
| Third-party check rejected | Rejected checks (45) | Supplier (reopened) or bank | Replacement instruments settle supplier; client clears 45 via receipt. |
| OP annulment | Reverse of release entry including withholdings | | Dated in open period. |
| Release deleted | Entry removed | | Not allowed in pre-closed month. |
| Reconciliation | none | | Extra-accounting. |
| Commission settlement | not specified | | Gap. |

Every treasury document exposes a read-only "view entry" (account, subaccount, comment, job, cost center, division, debit, credit). Entries cannot be edited; the originating document must be annulled/deleted and recreated.

---

## 7. Cross-module handoffs

| From | To | Payload |
|---|---|---|
| Media planning / digital plan | P7, P8 | Insertion orders, taxonomy order codes; "adjust orders by invoice" back in the plan |
| Production budgets | P5, P15 | HR items, cost-rendition items (client-approved) |
| Expense requests | P7, P9 audit | Expense POs, request detail |
| Supplier invoice registration (out of scope) | P1→Posted, P9, P11 | Posted invoices with due dates, client link, currency, tax breakdown |
| Client billing & receipts (`Cobranzas`) | P9 (collected evidence), P16/P22 (third-party checks), P26 (rejected-check replacement), P28 | Receipt number/date, checks, withholdings suffered |
| P16 / P22 / P23 / P26 | General ledger | Journal entries |
| P23 | VAT purchase book, VAT & IIBB position | Tax lines |
| P16 withholdings | Withholding certificates, tax returns, supplier portal | Certificates (Peru file naming `Ret.Renta_<Supplier>_OP_<number>_<year>.pdf`) |
| P19 | Bank portal | Payment file; return file |
| P20 | Supplier portal (Liveranto / web) | Invoice status, OPs, certificates, claims |
| Petty-cash sheets (expense module) | P27 | Card charges with approval |
| Provisional journal entries | replaces payroll import | |
| Month-end close | P17, P21 | Pre-close blocks release deletion |

---

## 8. Configuration and country-specific behavior

**Special configurations (Cash & Banks and others):**
- Counter-receipt print on registration; counter-receipt post-invoice menu.
- Purchase request; client flag "uses purchase requests".
- Calculate withholdings at list vs at release.
- Uses supplier early-payment discount.
- Split AP functions (create OP vs release as separate permissions).
- Maximum OP number gap.
- Salesperson invoice mandatory for commissions.
- Simplified-tax supplier control (AR).
- Generate payment list by bank; bank interface per entity; HSBC usage (AR); bank accounts for occasional payees.
- Uses corporate card.
- Restrict deletion (audit fields).
- Deferred checks enabled (per country).
- Client-to-supplier withholding pass-through (AR).
- Two settings to reject checks without immediate replacement.
- Email service (agency and terminal) for notifications.
- Signature image for Peru non-domiciled income certificates.
- Permissions: level 1 to approve lists, manual OP/deposit numbers; "save list as final" permission; plan view/modify permissions for taxonomy adjustment.

**Country behavior:**
- **Mexico:** counter-receipts; direct/indirect billing type filter in paid-invoice listing; electronic invoice XML in portal.
- **Colombia:** temporary staff loop with equivalent document for simplified-regime individuals; incentives deducted in payment lists; early-payment discount reports and internal discount credit notes; ICA withholding column.
- **Argentina:** fiscal document categories at reception; simplified-tax categories with annual caps; tax-authority listing with tax IDs of supplier, instrument issuer and intermediary; IIBB withholdings/perceptions; digital-service VAT perception (21%); HSBC occasional payees; bank key (CBU) generation; VAT withholding pass-through; third-party bank tax IDs for regulatory reports.
- **Peru:** supplier current account with IGV withholding variant; non-domiciled income withholding certificate.
- **Costa Rica:** foreign-supplier income-tax withholding approval gate.
- **Dominican Republic:** supplier NCF column in open-items report.

---

## 9. Reports and KPIs

| Report | Purpose | Key options |
|---|---|---|
| Supplier balance summary | Opening, debits, credits, closing per supplier/currency | fiscal year, control accounts (30), currency + rate at date-to, non-zero only, monthly sheet, per-document sheet |
| Supplier payment inquiry | Payments per document; advance consumption | year, supplier, type (OP, advance, adjustment), balance without OP, unpaid balance, division |
| Supplier current account (+ IGV variant) | Chronological movements | between-years dates, accounts, supplier range, together/separate, intercompany only, opening balance, in-transit invoices, real vs accounting date, multicurrency vs accounting format |
| Paid invoices with payment detail | Invoice-to-payment trace | invoice and payment dates, origin media/production/general, direct/indirect (MX), paid only, tax-authority listing (AR), amount breakdown (taxable, exempt, VAT, VAT wh., ICA, income-tax wh.), include unpaid, export format |
| Unpaid supplier invoices | Open items, aging | cut-to-date / unpaid / unpaid without OP; by supplier or general by overdue; interest %; exclude post-closing; include deferred checks; client type/range; PO type; client-invoice relation; doc types; multicurrency/accounting/mixed; aging buckets config; group by control account; intercompany; foreign only; product; initial invoices; NCF (DO) |
| Early-payment discounts | Discounts obtained/granted | normal, monthly, manual, to clients, by client |
| Payment delays | Estimated supplier payment dates | supplier range, due range, currency |
| Supplier balance by client | Unpaid payables per billing client (pay-when-paid view) | date-to, accounts, supplier type, owner clients, accounting/bi-currency, summarized by client |
| Initial invoices marked non-billable | Close orders where no further invoice expected | dates, suppliers, clients, currency; select → orders Closed |
| Counter-receipt listing | | supplier, status, client, user, annulled only, summarized |
| Payment list audit | Composition with notes | export |
| Payments & receipts detailed | Print/notify; find unreleased OPs; bank payment states | payment composition, bulk delete, bulk attachments |
| Own checks listing | 13 criteria (due, issue, OP, number, annulled, unreleased, post-dated, post-dated cut-off, undelivered, delivered, overdue undelivered, rejected, by deposit) | bank, type, beneficiary kind, signed, exclude rejected, occasional supplier |
| Third-party checks listing | Portfolio, delivered, rejected (pending only), by receipt, cut-to-date vs "values to deposit" ledger | apertures by date/client/due/number/supplier/bank/deposit/OP; endorsable/non/special |
| Notes receivable / payable | Portfolio and delivery | |
| Average monthly bank balances | Daily composition per bank | |
| Bank availability summary | Liquidity after in-transit items | |
| Funds movement | Opening, inflows, outflows, deposits, bank debits, rejected checks, adjustments (FX), available | accounting vs financial (value date) criterion; general vs bank-only |
| Withholding pass-through (AR) | Transferred vs pending | |
| Card statement | Charges vs statement | |
| Commission listing | Salesperson self-service | |

**KPIs derivable:** DPO; % overdue payables by bucket; payables covered by collected client invoices (pay-when-paid coverage = payables whose client invoice is fully collected / total payables due); early-payment discount captured vs available; unreconciled items count and age; checks issued not picked up; days from reception to posting (traffic number timestamps); portal rejection rate and reasons; OP number gaps; average bank balance; availability vs approved lists.

---

## 10. Agentic-skill implications

### 10.1 Atomic jobs (candidate skills)
1. `log-invoice-receipt` – create/return/re-enter reception records; parse PDF/XML to fields; propose responsible.
2. `validate-portal-invoice` – formal/tax checks, order match, recommend approve/reject with reason (human decides).
3. `match-platform-invoice-lines` – map taxonomy codes to plan orders; compute differences; propose associations.
4. `issue-counter-receipt` (MX).
5. `assign-invoice-batch`.
6. `propose-payment-list` – build candidate set from due dates, client-collected evidence, cash availability, early-payment opportunities.
7. `compute-withholdings` – deterministic engine per country.
8. `prepare-payment-orders` – per supplier, currency-split, with manual lines.
9. `plan-payment-release` – suggest instrument mix and check numbers given balances (no execution without approval).
10. `export-bank-payment-file` / `import-bank-payment-result`.
11. `record-deposit`, `record-bank-charge`.
12. `reconcile-bank` – statement parsing and matching suggestions.
13. `manage-checks` – checkbook registry, printing queue, pickup marking, rejection workflow.
14. `match-card-statement`.
15. `answer-supplier-claim` – draft estimated payment date from rules.
16. `ap-aging-report`, `supplier-balance-by-client`, `funds-movement`, `availability`.
17. `settle-commissions`.

### 10.2 Deterministic calculations worth a tool
| Tool | Inputs | Formula / logic |
|---|---|---|
| `payment_candidates` | open items, due window, filters, locks, client receipts | Rule 5–6; flag `client_collected = client_invoice.balance == 0` and `collected_date`, `check_due_date` |
| `withholding_calc` | supplier tax profile, overrides, invoices, period accumulations, country rules | Rule 11 (+ UTE split `wh_member = wh × share%`, monotributo category) |
| `early_payment_discount` | balances, supplier pct, payment date, early date | Rule 14 |
| `fx_difference` | FC amount, book rate, payment rate | Rule 16 |
| `aging_buckets` | items, base date, thresholds (validated descending) | Rule 29 |
| `payment_delay_estimate` | invoice date | Rule 28 (parameters configurable: 40, 7) |
| `availability` | book balance, in-transit checks/transfers | Rule 26 |
| `avg_bank_balance` | daily balances | Rule 27 |
| `reconcile_match` | system movements, statement lines | exact match on amount + (check no. / reference) then amount + date tolerance; Rule 24 balance proof |
| `next_check_number` | checkbook, released set | Rule 17 |
| `check_due_date` | issue date, type, clearing hours | Rule 17 (deferred > 48 h validation) |
| `bank_export_date_valid` | today, date | Rule 23 |
| `op_number_gap_check` | used numbers, max gap | Rule 22 |
| `card_statement_match` | items per currency, statement totals | Rule 33 |
| `cost_advance_cap` | estimate item, requested | Rule 31 |
| `monotributo_cap` | YTD invoices, category max | Rule 37 |
| `bank_charge_vat` | net, VAT rate | Rule 25 |
| `ar_digital_perception_check` | invoice net, entered perception | expected 21% of net; flag deviations |

### 10.3 Controls (non-negotiable)
- **Payments stay human-approved.** Agents may draft lists, OPs and release proposals; only an authorized human approves a list (level-1/"final" permission), releases an OP, sends a bank file, or confirms bank-import results.
- Segregation of duties: preparer ≠ approver of lists; OP creator ≠ releaser when "split functions" is on; invoice formal validator ≠ requester confirmation.
- Agents never override supplier tax master data; per-OP overrides require a stated reason and human confirmation.
- Annul/delete of OPs, releases, checks, deposits and reconciliations require human confirmation with audit fields (user, task number, reason).
- Locks: an agent must respect item locks; never create parallel OPs for locked items.
- Period guard: refuse release deletion in pre-closed periods; annul with open-period date only.
- Reconciliation Definitive save only when the balance proof equals the statement.
- Bank file generation is irreversible in effect (OPs flip to Released) → explicit approval.
- Supplier notifications are sent only after release and (practically) after signature.

### 10.4 Exceptions to handle
- Supplier missing in master at reception; duplicate document number for same supplier.
- Portal invoice amount ≠ order; unmatched taxonomy lines; invoice without order (manual origin).
- Client not yet collected but supplier overdue/claiming → escalate.
- Multi-currency debt for one supplier → split OPs.
- Insufficient availability vs approved list → partial list not allowed; re-approve a smaller list.
- Check number already released / checkbook exhausted.
- Bank import with unknown OP or amount mismatch.
- Rejected checks (own and third-party), deferred replacement.
- Foreign supplier withholding not approved (CR).
- Card statement total mismatch.
- Withholding recomputation after annulment changes net.
- Release dated in a different period than OP.

---

## 11. Gaps and ambiguities

1. **Academia pages contain only video titles and durations** (advance purchase, Liveranto, AP concepts, controls, invoices in traffic, media/production/expense invoice registration, volume credit notes, treasury concepts, masters, OP, cash flow, release, collection, reconciliation, reports). No substantive content; cash-flow forecasting in particular is undocumented.
2. **No withholding formulas, thresholds, tables or certificate formats** are given (only fields: income-tax category, VAT %, IIBB %, ICA, IGV, non-domiciled income). Rule 11 is a design assumption.
3. **Pay-when-paid is not enforced automatically**; the system only displays client-invoice status and collection receipts. Whether a hard rule ("pay only if client paid") exists is unknown.
4. **FX difference posting** at payment is not described; only report formats and an "FX adjustments" section in funds movement.
5. **Automatic bank reconciliation** (bank codes master) and bank branch interface codes are stubs.
6. **Purchase order import** is "under construction".
7. **Electronic collection file** and **supplier contacts listing** have no detail.
8. **Advance application** to invoices (how an advance OP is later consumed) is only visible as an inquiry, not as a process.
9. **Commission settlement accounting** and whether settlement creates a payable/OP is not stated.
10. **Two configurations for deferred check replacement** are not named.
11. **The interplay between "Paid" invoice state and partial payments** (partial balance states) is not explicit.
12. **Expense-to-render example** references screenshots not present; exact entries inferred.
13. **"Divide Funciones" permissions** granularity beyond create vs release is unknown.
14. **Liveranto sync semantics** (conflict handling, frequency beyond nightly) unspecified.
15. **Payment list "Cheque en Banco" flag** suppresses release generation; how those OPs are later released (presumably via bank import) is implied, not stated.
16. **Availability formula** wording is loose (whether deposited collections are already in book balance).
17. **Interest on overdue** day-count basis not specified.
18. **Calculo Mensual de Resguardo** appears in the Treasury Payments menu index but has no page.
19. **Supplier Online orders** (URL/port/agency code) integration behavior unspecified.
20. The out-of-scope branch "Facturación Proveedores" is listed here only as a menu index; its processes (invoice registration, volume credit notes, incentives, VAT purchase book) are assumed covered by another spec.
