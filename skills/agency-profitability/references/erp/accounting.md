# Accounting (Contabilidad) — functional spec

> **Provenance.** Functional reverse engineering of a reference agency ERP, derived from its publicly accessible help documentation (reviewed 2026-10-11). Content is paraphrased and restructured; it is not vendor documentation, source code or an endorsement. Bracketed ids such as `[mp301010]` identify the source page used as evidence. Items marked *inferred*, *assumed* or listed under gaps must be validated with your own controller, tax adviser and system owner before they drive postings or payments.

> Source: the reference ERP's help documentation (Academia > Contabilidad pages plus every page under the Contabilidad menu: chart of accounts and journal entries, general ledger reports, analytic accounting, legal and tax operations, fixed assets, monthly and year-end closing, opening balances, accounting masters).
> This is an independent paraphrase written for an MIT-licensed agentic-skills repo. No manual text is reproduced. Spanish UI and field names appear in backticks only as identifiers. "Ref" tags point to the source page file names so the mapping can be traced.
> The Academia pages in the source are video-title stubs only (Fundamentos contables: general concepts, chart of accounts, journal entries; Proceso de cierre: monthly close steps, depreciation, bridge account vs. provisions, exchange differences, reports). They add no rules of their own, but they confirm that the vendor thinks of the module as two blocks: the accounting foundations and the monthly close.

---

## 1. Purpose and position in the end-to-end circuit

Accounting is where the agency circuit ends up. All the operational modules post journal entries into it automatically:

- **Media planning and buying** (media plans / `pautas`, orders, contracts)
- **Production estimates** (`presupuestos`)
- **Client billing** (`facturación`)
- **Supplier invoice registration** (`proveedores`)
- **Treasury** (collections, payment orders, deposits, checks)
- **Expenses** (expense requests, cost renditions, petty cash)
- **Timesheets / cost-plus**

Each of those transactions carries a voucher type (`tipo de comprobante`), and every result-account line carries analytic dimensions: JobNumber (campaign/project), OT (`orden de trabajo`, work order), cost center, division, and the billing or owner client. Users seldom post entries by hand in Accounting. The module's own work is to:

1. **Hold the structural masters.** These are the chart of accounts (`plan de cuentas`), the balance-sheet hierarchy (`rubros`), observation codes, voucher types, currencies and rates, tax and jurisdiction tables, and staff (`colaboradores`).
2. **Let users post manual entries.** That covers adjustments, payroll, taxes, opening balances, reporting-only IFRS/USGAAP entries and templates, with an optional two-step approval workflow for provisional entries.
3. **Run the period-end batch jobs that only Accounting can run.** These are:
   - exchange-difference revaluation
   - unbilled-revenue and uninvoiced-cost provisions (Gross Income provision)
   - WIP reclassification
   - expense provision
   - overcommission provision
   - regional service-fee provision
   - closing of work orders (bridge-account result recognition)
   - VAT and gross-receipts-tax (IIBB) positions
   - depreciation
   - inflation adjustment
   - intercompany reclassification
   - the closing of months and the fiscal year
4. **Produce the statutory and management outputs.** These are the trial balance, balance sheet, P&L, general journal and sub-journals, general ledger, P&L by client/job/division/cost center, work-order profitability, statutory tax files (AFIP SICORE, IIBB, DIAN, SENIAT, SUNAT books), and the controls that check each subledger against its GL control account.

Position: Accounting sits **downstream of every module** and **upstream of reporting, consolidation (Hyperion/Magnitude/Cartesis) and tax filing**. The monthly close is what makes it the single source of truth. When a period is pre-closed, the operational modules stop posting into it, and the close jobs then derive the accrual-basis view of revenue, cost and taxes.

---

## 2. Process catalogue

Each process lists: Trigger · Actor · Pre-conditions · Steps · Inputs · Outputs · State transitions · Approvals · Ref.

### P01 — Maintain the balance-sheet hierarchy (rubros)
- **Trigger:** implementation, or a new reporting line is needed.
- **Actor:** chief accountant or implementer.
- **Steps:**
  1. Create the rubro code: up to 6 alphanumeric characters, zero-padded, one hierarchy level per digit.
  2. Give it a description.
  3. Set its type: Assets & Liabilities, Equity, Results, or Memorandum (`Orden`).
- **Output:** a rubro tree.
- **Secondary tree:** an identical secondary tree (`Rubros de Balance Secundario`) gives a second classification, typically a head-office layout.
- **Gap detection:** the chart-of-accounts report highlights missing parent rubros. Clicking the highlighted cell opens creation with the code pre-filled.
- **Ref:** `mp301184`, `mp305184`, `ingresar-rubros-de-balance`, `mp301182`.

### P02 — Create or maintain GL accounts (cuentas contables)
- **Trigger:** implementation; a new bank, tax, or expense line.
- **Actor:** accountant (the observation-code catalogue itself is vendor-maintained).
- **Pre-conditions:** primary, secondary and Hyperion rubros exist.
- **Steps:**
  1. **New:** the system auto-assigns the account number.
  2. **Main data:**
     - name, and secondary name if dual rubro is on
     - default VAT account
     - category, Patrimonial or Resultados (immutable)
     - subcategory
     - observation code (immutable)
     - currency
     - active flag (`Vigente`)
     - inflation-adjust flag
     - NIT breakdown (Colombia only)
     - manual-movement restriction
     - accrual (prepaid) account link, for expense accounts
  3. **Administrative data:**
     - module flags: Clients, Suppliers, Treasury, Expenses, Petty cash
     - primary rubro plus 2-digit order within it
     - Hyperion reporting code
     - secondary rubro
     - balance-sensitive flag plus the alternate rubro used when the balance is a credit (`Principal Sdo Acr.`)
     - responsible user
  4. **Other data** (read-only): a movement summary, plus the linked expense concepts or subaccounts.
- **Rules:**
  - An account with movements cannot be deleted, only deactivated.
  - The 8-character integration code is the 6-character rubro plus the 2-digit position. To re-sequence, free a slot and edit the position.
- **Variant — payment means:** to create a means of payment (cash, bank, FX cash, checks), first enable the matching special settings (`Usa Efectivo`, `Usa Moneda Extranjera`, `Usa Cheques Diferidos`). Then create the account as Patrimonial, Asset/Liability, with no VAT account, the treasury module flag, and the right observation code (see §3.3).
- **Ref:** `mp301183`, `ad_cap_gus_tes_10…`, `ingresarcuentascontablesderesultados`.

### P03 — Maintain subaccounts
- **Trigger:** a new employee or third party needs its own balance (advances, loans, amounts to account for).
- **Rules:**
  - Subaccounts can be created manually only under accounts with observation code **82**.
  - Code-82 subaccounts are numbered under the parent and are optionally linked to a collaborator; the name is taken from the collaborator, or is mandatory when there is none.
  - Accounts **83, 84, 85** (expenses to account for, cost renditions, per-employee subaccounts) are populated from collaborators and can only be queried on this screen.
  - The subaccount opening balance can be edited only during the first fiscal year.
- **Ref:** `mp301151`, `ingresar-sub-cuentas-contables`.

### P04 — Post a manual journal entry
- **Trigger:** an adjustment, payroll, taxes, reclassification, or a reporting entry.
- **Actor:** accountant. Access levels: level 1 can edit automatic lines; levels 2–4 can only add lines.
- **Pre-conditions:**
  - The voucher type exists.
  - The user has create permission.
  - The period and subledger are open, or the voucher type is flagged to allow posting into pre-closed months.
- **Steps:**
  1. Choose the fiscal year and entry type (`Tipo de Asiento`).
  2. Choose the voucher type. The system auto-numbers sequentially per voucher type per year.
  3. Enter the date and comment.
  4. Enter the currency, and the rate if the currency is foreign.
  5. Optionally set an extended comment (visible from the ledger).
  6. Optionally flag *reverse on the first day of next month* and/or *recurrence months*.
  7. Enter the lines (detailed below).
  8. Save. The creator user is stamped automatically.
- **Line fields:**
  - account
  - subaccount or expense concept
  - line comment
  - JobNumber, OT and cost center: mandatory for result accounts and for code **B1** accounts
  - division: when divisions are enabled
  - debit or credit
- **Entry types:**
  - `Otros asientos` — free-form entry.
  - `Asiento Sub-Cuenta o Mov. de fondos` — mandatory whenever an account with subaccounts, or an expense account with several concepts, is used. Also used for treasury accounts (obs. 40, 41, 42, 43, 51, 52).
  - `Ajuste clientes` / `Ajuste proveedores` — see P05.
  - `Asiento de apertura` — see P20.
  - `Cierre de cuentas` — see P19.
  - `Actualización contable` — see P17.
  - `Inverso del REI` — see P18.
- **Outputs:** a posted entry. If the reversal flag is set, the system also posts the reversal entry dated the 1st of the next month. With recurrence set, the entry is replicated into later months.
- **Immutability:**
  - Once saved, only the comments can be edited.
  - Deleting an entry removes it without trace, so the recommended path is **Contra-asiento**: a reversal of the queried entry, dated in an open period.
- **Templates:** a saved entry can be stored as a reusable template file (`.amp`) and recalled with *Ver Asiento Tipo*. The vendor suggests this for monthly payroll and tax entries. The recommended entry types for templates are Otros, Sub-cuenta/Mov. fondos and Actualización contable.
- **Excel import:** available only when the provisional-entry circuit is off.
- **Attachments:**
  - Stored in the database by default.
  - Optionally stored on disk (special setting); historic attachments are moved with a utility.
- **Reporting entries:** an `IFRS (8A)` entry is posted on the last day of the month and auto-reversed by `8B`. It has no statutory effect. Reports can include or exclude 8A/8B. This needs a specific permission.
- **Ref:** `mp301289` and its user guides.

### P05 — Customer and supplier adjustment entries
- **Trigger:** compensating documents without any cash movement.
- **Customer uses:**
  - Apply a received advance to a later invoice.
  - Write off an uncollectible or litigated balance to a doubtful-debtors or legal-collection account.
  - Settle a customer balance against the withholding account when the client later delivers its withholding certificates.
- **Supplier uses:**
  - Apply a supplier advance to the supplier's invoice.
  - Cancel a payable that will not be paid against a P&L account.
- **Steps:**
  1. Choose the entry type and the voucher type (`Ordenes de Pago` or receipts).
  2. Set the date, comment, document currency and rate (defaulting to the day's rate).
  3. Pick the client or supplier.
  4. Tick the documents and enter the amount applied to each.
  5. The entry must net to zero.
  6. A counter-account line may be added manually. It must be a treasury-enabled account, plus Job/OT/CC if it is a result account.
- **VAT withholding transfer** (`Traslado de IVA`, special setting): when a customer adjustment touches the **customer VAT withholding account (obs. 18)**:
  - The user may *open* the transfer, which moves the withholding to the related supplier, or *close* it, so no transfer happens.
  - The button locks once the transferred withholding is used in a payment order as a supplier VAT withholding.
- **Approvals:** adjustments are **never provisional**. They hit the subledger immediately, so the user needs definitive-entry rights plus supervisor rights on payment orders or collections.
- **Ref:** `mp301289`, `asociar-un-anticipo-a-la-deuda-pendiente`, `asientos-provisorios`.

### P06 — Provisional entry approval workflow (optional)
- **Trigger:** the special settings for provisional entries are enabled (`Usa Asientos Contables Provisorios`, provisional masters, provisional generation). The second approval level is a further setting.
- **Actors:** preparer → intermediate approver (can approve or reject, cannot post) → final approver (posts, or rejects).
- **Scope:** only `Otros asientos` and `Sub-cuenta/Mov. fondos`. Never adjustments, year close, inflation or REI entries.
- **Steps:**
  1. The preparer saves the entry. It is stored as provisional and has no ledger effect.
  2. A supporting attachment is mandatory before sending; who uploaded it and when is logged.
  3. The preparer sends it for approval, optionally by e-mail.
  4. The approver gets an alert in the home dashboard.
  5. The approver approves (intermediate approval) or rejects with a reason code from `Motivos de Rechazos` plus free text. A rejection notifies the preparer.
  6. The preparer corrects the entry from the journal-entry screen (not from the alert) and resubmits.
  7. The final approver posts entries that are in intermediate-approved status, or rejects them back.
  8. An authorization sheet can be printed.
- **States:** see §4.1.
- **Monitoring:** the `Listado de Asientos Provisorios` report shows timestamps and users for each step, the rejection count, the modification count and the reasons.
- **Deletion:** the creator is responsible for deleting an entry. The movement audit trail identifies the creator.
- **Ref:** `asientos-provisorios`, `mp302775`, `mp302770`.

### P07 — Exchange-difference revaluation (monthly, mandatory)
- **Trigger:** month-end.
- **Pre-conditions:**
  - The month is pre-closed.
  - Buy and sell rates for the last day of the month are loaded.
- **Steps:** there are three independent runs, all mandatory, in any order.
  1. **Receivables:** unpaid customer documents in foreign currency (voucher type 95).
  2. **Payables:** unpaid supplier documents in foreign currency (voucher type 96).
  3. **Foreign-currency GL accounts:** voucher type 8. Accounts with subaccounts are revalued subaccount by subaccount.
- **Each run:**
  1. Run the calculation (Iniciar).
  2. Review the proposed entry and the per-document detail.
  3. Post it (Contabilizar), dated the last day of the month.
- **Reversal:**
  - The system auto-reverses on the 1st of the next month.
  - Exception: the last month of the fiscal year is not reversed. The next year starts from the first-day rate, not the document's booking rate.
- **Undo:** Anula Asiento deletes the entry so it can be recalculated.
- **Manual FX:** the system does not recognise manual FX entries. If a user has posted one, they must also run the automatic entry and then post a manual reversal of their own.
- **Ref:** `mp301290` and its user guides.

### P08 — Gross Income provision (unbilled revenue and uninvoiced cost)
- **Trigger:** month-end. The vendor recommends this approach over the bridge-account approach.
- **Pre-conditions:**
  - Provision accounts exist: PI, PE, PH, PC, optional PP, PA; WP if WIP is used.
  - The Clients, Suppliers and Accounting subledgers are pre-closed for the month.
  - A start date is configured: plans and estimates before it are ignored.
- **Steps:**
  1. Choose the year and the "up-to" month. The "from" date is fixed at system inception.
  2. Optionally choose clients, origin (media / production / both) and production type.
  3. Set the option flags (see BR-30).
  4. Run (Iniciar). The system lists every plan or estimate with pending billing and/or pending supplier invoices.
  5. Select OTs; selecting all after review is advised. If "fees and commission always" is off, tick the agency-service column per line.
  6. Optionally simulate.
  7. Post (Contabilizar): one entry per month, per OT, on the last day, auto-reversed on day 1 of the next month.
  8. View the detail posted, or annul and redo.
- **Approvals:** none in-system. The vendor advises that media and production teams validate their pending items first, and that never-progressed estimates be unapproved.
- **Ref:** `mp301408` and its user guides.

### P09 — WIP reclassification (Trabajos en Proceso)
- **Trigger:** month-end, when `Usa trabajos en proceso (WIP)` is on.
- **Pre-conditions:**
  - A WP account exists.
  - The month is pre-closed.
  - The user has access level 2 and visualization level A.
- **Steps:**
  1. Run the process. It lists plans and estimates where the supplier invoice has been recorded but the client has not been invoiced.
  2. Select by OT or by item.
  3. Post. Media and production are processed together, once per month.
- **Effect:** the supplier cost is reversed out of P&L into the WP balance-sheet account on the last day of the month, and auto-reversed on day 1.
- **Other functions:** simulation; detail by OT; aging breakdown by due date, booking date or real date, with user-defined day buckets in descending order.
- **Pairing:** works together with the Gross Income provision, which handles the revenue side.
- **Ref:** `mp302705`.

### P10 — Expense provision
- **Trigger:** month-end.
- **Pre-conditions:**
  - A PG account exists: a single liability account for all currencies.
  - The month is pre-closed.
- **Scope:** expense requests in status *approved without deferral* whose supplier invoice has not arrived and which have not been accrued.
- **Steps:**
  1. Filter by supplier range.
  2. Optionally highlight items that were in previous provisions.
  3. Optionally revalue foreign-currency requests at the current rate.
  4. Select the requests.
  5. Post: last day of the month, with reversal on day 1.
  6. Simulation is allowed before the pre-close.
- **Constraint:** a single run per month. It cannot be split by expense type.
- **Ref:** `mp302696` and its user guides.

### P11 — Overcommission provision
- **Trigger:** month-end.
- **Pre-conditions:**
  - PO (overcommission) and PD (overcommission refund) accounts exist.
  - Pending items have been generated in "Generación Pendientes de Overcomisiones" (Media module).
- **Steps:**
  1. Choose the month and origin (media / production); for media, optionally a media type or medium.
  2. Run. All pending items are included, with no per-line selection.
  3. Post. The entry auto-reverses on day 1.
- **Output columns:** OT, order, supplier, medium, contract code and type, owner client, product, overcommission amount, refund amount, division, previous-provision flag.
- **Ref:** `mp302737`.

### P12 — Regional service-fee provision (agency-group charge)
- **Trigger:** month-end, for agencies that belong to a holding group.
- **Fee types:** Advisory, Management and Coordination fees. The manual names the Publicis group configuration explicitly.
- **Pre-conditions:**
  - Group membership is configured.
  - WIP is on.
  - Default Advisory and Management percentages are set.
  - Owner clients with regional management are flagged, with their percentage.
  - The fee accounts master is filled in.
  - The month is pre-closed.
  - FX is posted.
  - The GI provision is posted.
  - The IIBB position is posted.
  - OT/WIP closing is done.
- **Steps:**
  1. Choose the month and fee type.
  2. Run. Per client the screen shows: Revenue, NCR allocation, total revenue, gross-receipts tax, net total, fee %, and the service fee.
  3. Optionally override the % per client.
  4. Post. If any prerequisite is missing, the system lists the missing items and lets the user proceed anyway.
- **Undo:** annul is possible.
- **Ref:** `mp302692` and its user guides, `mp302691`.

### P13 — Work-order (OT) closing (bridge-account scheme)
- **Trigger:** month-end. Mandatory when bridge accounts (`cuenta puente`) are used; management-only otherwise.
- **Pre-conditions:**
  - The Clients and Suppliers subledgers are pre-closed.
  - The bridge account groups 01–05 exist in equal counts and are linked to media types and production types.
- **Recommended pre-checks:**
  - Have each department confirm that the job results are correct.
  - For supplier remainders caused by VAT recovered on cost renditions, edit the estimate cost down to the invoiced net. This is the only case in which an already-invoiced item can be edited.
  - For long-stale pending supplier items, use "mark estimates as invoiced". It cancels the pending item with no GL entry and logs the user.
- **Steps:**
  1. Choose the year and range; `Completo` means since inception.
  2. Choose the client type (billing / owner) and the grouping (by OT or by client).
  3. Choose the closing type:
     - **Provisional:** pending items remain.
     - **Definitive:** nothing is pending.
     - **Refundición:** nets the balance-sheet bridge balances of very old, definitively closed OTs.
  4. Optional flags:
     - *no entry*
     - *only OTs with differences*
     - OT status filter: Pending / Provisional / Definitive
     - billing type (media / production / both)
     - *OTs invoiced up to the accounting month*
     - the **accounting month** in which to recognise the result
  5. Select the OTs and Close.
- **Outputs:**
  - One entry per OT (Otros asientos, voucher type **6**) moving the estimation difference (obs 03) to positive (05) or negative (04) result.
  - The OT status changes.
- **Reopening options:**
  - Reopen without annulling the earlier closing entries; a later re-close then recognises only the delta.
  - Annul that period's closing entries.
  - Annul only the refundición entries.
- **Rules:**
  - Do not mix close and open operations in one run.
  - After a provisional close, no further movements may be dated in that period.
  - A definitive close blocks all postings until the OT is reopened.
- **Ref:** `mp301431` and its user guides, `cuenta-puente`, `mp301406`.

### P14 — VAT position (Posición de IVA)
- **Trigger:** month-end.
- **Pre-conditions:**
  - The month is pre-closed.
  - VAT accounts exist: debit fiscal 09, 10, 0A; credit fiscal 11, 12, 13; payable 17; credit balance 08.
- **Steps:**
  1. Choose the year and month.
  2. Set the entry date. It defaults to the last day of the month and also acts as the cut-off for withholdings suffered.
  3. Run. The screen shows two sections:
     - **Section 1:** VAT debit minus VAT credit.
     - **Section 2:** perceptions suffered, withholdings, transfers, and the final balance.
  4. Post (voucher type "Posición de IVA del Mes"). The system nets all VAT accounts:
     - a balance owed goes to VAT payable (17)
     - a credit goes to VAT credit balance (08), which carries forward
  5. If there is a credit and *Incluir Ajuste Manual* is ticked, a dialog lets the user apply part or all of the credit to other tax accounts with amounts.
- **Undo:** annul deletes the entry and re-allows new documents.
- **Reconciliation:** the screen reconciles to the ledger, the VAT purchases sub-journal and the VAT sales sub-journal.
- **Ref:** `mp301216` and its user guides.

### P15 — Non-computable VAT
- **Trigger:** an invoice whose VAT is partly non-creditable.
- **Steps:**
  1. At invoice entry, mark the non-computable portion. It is still posted to normal VAT credit.
  2. In this screen, choose the year and month, select the invoices, and post.
- **Effect:** the entry moves the amount from VAT credit to the **I7** account.
- **Undo:** annul or view the detail.
- **Ref:** `mp302756`.

### P16 — Gross-receipts tax position (IIBB, Argentina)
- **Trigger:** month-end.
- **Pre-conditions:**
  - Taxpayer registers are updated in the client and supplier masters.
  - The home jurisdiction is set.
  - Accounts A0, A1, A2 (per jurisdiction), 60 (per jurisdiction) and AI exist and are linked per jurisdiction per year, with rates and multilateral percentages.
  - Client and supplier subledgers are closed.
  - OTs are closed (if bridge accounts are used).
  - The GI provision is posted (if done monthly).
- **Steps:**
  1. Choose the month.
  2. Choose the criterion:
     - **Multilateral agreement** (`Convenio multilateral`): percentages per jurisdiction must total 100%.
     - **Real income by jurisdiction:** derived from client and supplier addresses, optionally the medium's jurisdiction.
     - **All in home jurisdiction:** optionally separating foreign billing.
  3. Optionally include manual adjustments.
  4. Run. The screen shows:
     - **Movements:** income by cost difference and the applicable rate, totalled per jurisdiction.
     - **Proposed entry.**
     - **Distribution per client:** cost-difference income, agency service, fees, bonuses, total, tax, net.
  5. Post (voucher type "Posición de IIBB del Mes", dated the last day of the month).
- **Undo:** annul or view the detail.
- **Ref:** `mp301426` and its user guides, `mp301427`.

### P17 — Inflation adjustment (Actualización contable / REI)
- **Trigger:** year-end in hyper-inflationary jurisdictions (Argentina, Colombia).
- **Pre-conditions:**
  - The special setting `Corrección Monetaria` is on.
  - The accounts to adjust are flagged.
  - A single REI account with observation code **AC** exists.
  - A revaluation coefficient table is loaded (the FACPCE index for Argentina). A single table should be reused across years by changing the year.
  - The last month of the year is in pre-close.
- **Steps:**
  1. Choose the year, entry type and voucher type *Actualización contable*, the month/year, and the coefficient table.
  2. The detail lists the flagged accounts.
  3. Save. The entry is balanced automatically against AC.
- **Contradiction in the manual:** the user guide says the detail does **not** bring the computed amounts, so the user enters them. See §11.
- **Restrictions:** debits must equal credits, overall and per division.
- **Who can post it:**
  - Under the provisional circuit, only users with definitive-entry rights.
  - Level 1 can edit the automatic lines; levels 2–4 can only add lines.
- **Ref:** `mp301289`, `generar-la-actualizacion-contable`, `mp301231`, `mp302916`, `mp302915`.

### P18 — Reverse REI (Inverso del REI)
- **Trigger:** first day of the following year.
- **Steps:** choose the year and entry type *Inverso del REI*, then confirm.
- **Effect:** the system reclassifies the whole AC balance to the accumulated-results account (**RA**) on the first day of the year.
- **Constraint:** only one per year.
- **Ref:** `reversar-el-rei-del-ejercicio`.

### P19 — Fiscal-year close (Cierre de cuentas)
- **Pre-conditions:**
  - All months of the year are closed.
  - The new year has been generated (P21).
  - The first month of the new year is open.
- **Steps:**
  1. Choose the year, entry type *Cierre de cuentas*, and either voucher type (result close or patrimonial close).
  2. Confirm.
- **Effect:** the system generates three entries: a result-accounts close into account obs **90**, a patrimonial close, and the opening entry of the next year.
- **Iterative re-close:** auditors often need late adjustments. The sequence is:
  1. Delete the closing entry; the opening entry is kept.
  2. Reopen the needed months.
  3. Post the adjustments.
  4. Re-close the months.
  5. Re-run the year close, which updates the opening entry.
  There is no limit on how often this can be done.
- **Ref:** `mp301289`, `generar-un-asiento-de-cierre…`.

### P20 — First opening entry and opening balances (go-live)
- **Trigger:** first use of the system.
- **Steps:**
  1. Post `Asiento de apertura`, dated the first day of the first enabled year. It contains **balance-sheet accounts only**, with the balancing line on obs 90. A results breakdown, if wanted, goes in a separate manual entry with the same date against obs 90.
  2. Load the subledger detail (P22).
- **Later years:** the opening entry is generated by P19 and is query-only.
- **Ref:** `mp301289`, `generar-el-primer-asiento-de-apertura`.

### P21 — Generate a new fiscal year
- **Trigger:** before the last month of the current year ends. The vendor advises the last working day, after hours, with a backup.
- **Pre-conditions:** a rate exists for the last day of the current year; it seeds the new year.
- **Steps:** confirm the closing month and year. The default is the last closing month plus 12.
- **Side effects:**
  - Holidays are generated for the new year.
  - For tables keyed by "Mes Desde" (salary categories, internal staff costs), 12 new monthly rows are created by copying the last month.
  - Deferred-check movements that fall due in the new year are relocated into it.
  - New transactions default to the new year.
- **Undo:** `Reversar Apertura` deletes the year if it has no movements.
- **Ref:** `mp301325`, `generar-un-nuevo-ejercicio-economico`.

### P22 — Load opening subledger balances
- **Trigger:** go-live (or a company absorption).
- **Detail loaders:**
  - **Clients:** document type FC/ND/NC/REC/ANT, branch and number, date, due date, currency and rate (equal to the opening rate), total, optional VAT. Unapplied advances are loaded as ANT. A mass Excel layout is available from the vendor. Documents of an absorbed company use a special origin flag.
  - **Suppliers:** as for clients, plus the invoice letter (Argentina, Guatemala). VAT is needed so that withholdings can be computed at payment time. A non-computable amount is entered for monotributista suppliers.
  - **Notes receivable:** client, receipt number, currency, date, due date, amount.
  - **Third-party checks in portfolio:** client, receipt number and date, bank, check number, due date, currency and rate, amount, issuer tax ID and bank tax ID.
  - **Deferred checks issued:** bank (obs 43 account), check number, payment-order number and date, clearing days, due date, amount. At the due date the system debits deferred checks and credits the bank.
  - **Subaccounts:** per subaccount of 82–85 accounts.
- **Validation:**
  - Document dates must be before the first year.
  - The system **does not** check that the detail totals equal the opening entry. That control is the user's responsibility; the subaccount screen states the equality rule.
- **Correction:** loaded client and supplier documents are queried or deleted from the normal invoice, collection and payment queries, flagged as opening balance.
- **Ref:** `mp301135`, `mp301349`, `mp301295`, `mp301294`, `mp301284`, `mp305151` and their user guides.

### P23 — Pre-close and close of a month (period control)
- **Actor:** a user with the special pre-close permission.
- **Pre-condition:** the last-day rate is loaded.
- **Steps:**
  1. Choose the year and the action (Cerrar or Abrir).
  2. Double-click a month to act on all subledgers, or a cell to act on one subledger.
  - Subledgers: Clients, Suppliers, Treasury, Accounting.
- **Rules:** see §4.2.
- **Ref:** `mp301166` and its user guides.

### P24 — Monthly closing checklist
The sequence the vendor prescribes is in §5, BR-50. **Ref:** `proceso-de-cierre-mensual`.

### P25 — Month-end control routines
- **What it does:** a batch integrity check over the month. It flags customer or supplier documents deleted after being collected or paid (using admin rights), documents with no GL posting, AP/AR control mismatches, credit notes linked to invoices, and unpaid-invoice verification.
- **Output:** a single observations column.
- **Ref:** `mp302677`.

### P26 — Intercompany reclassification
- **Trigger:** month-end, for reporting.
- **Pre-conditions:**
  - Clients and suppliers are flagged as intercompany.
  - The accounts are flagged as intercompany.
  - An IC reclassification account exists (one, or one per movement type).
  - The month is pre-closed and not yet closed.
- **Scope:**
  - Balances with intercompany parties in values to deposit (42/52), deferred checks (93), supplier advances (32), client advances (50), and provisions PG/PC/PH/PI/WP.
  - These are reclassified to IC.
- **Undo:** annul or view the detail.
- **Ref:** `mp302702`.

### P27 — Fixed asset lifecycle
- **Creation (preferred route):**
  - An expense request using a fixed-asset concept whose account is obs **B1** creates the asset automatically when the supplier invoice is entered.
  - Manual creation is possible but discouraged: the GL value must then be posted separately and is not controlled.
  - A bulk import layout is available from the vendor.
- **Asset record:**
  - auto code
  - unique description
  - purchase date
  - purchase value
  - supplier and invoice (auto-filled)
  - cost center
  - division, or a percentage split across divisions
  - active flag
  - inventory code
  - asset concept, which determines the accounts and default useful life
  - useful life in months (editable)
  - depreciation start date (may differ from the purchase date)
  - first-period depreciation amount
  - opening accumulated depreciation (editable for pre-system history)
  - computer specs and assigned user/department
  - read-only adjustment and accumulated balances
- **Rule:** the asset is editable only while it has not been depreciated and the month is open.
- **Disposal by disuse or full depreciation:**
  - The month must not be closed or pre-closed.
  - If that month's depreciation has already been posted, annul it first.
  - Then set the disposal year, month and reason, and confirm. The system posts an entry.
- **Disposal by sale:** "fixed-asset billing" issues a sales invoice, removes the net book value, and books the gain or loss to an obs **BR** account.
- **Deletion:** only by a supervisor, and only when the asset has no invoice and no movements.
- **Ref:** `mp301244`, `ingresar-manualmente…`.

### P28 — Depreciation run
- **Pre-conditions:**
  - The method is configured: monthly or annual; "complete year of acquisition" true or false.
  - Concepts and criteria exist.
  - The month (or, for the annual method, the last month of the year) is pre-closed.
- **Cost-center options:**
  - (a) use each asset's own cost center: tick *Apertura CC por cuenta* and leave *Desestimar defaults* unticked.
  - (b) force a single cost center: select it, tick *Apertura por cuenta* and *Desestimar defaults por bien*.
  - (c) a general cost-center/division allocation key: tick *Apertura CC General* and select the key.
- **Further filters:** exclude inactive, disposed or fully depreciated assets; presentation local or NIIF (show grouped capitalisable items, non-revalued assets); division.
- **Steps:**
  1. Run.
  2. Review, grouped by B1 concept and division.
  3. Post: voucher type **94 — Asiento de Amortizaciones**, entry type Otros, debit depreciation expense and credit accumulated depreciation, by division and cost center.
- **Summary mode:** cannot be posted. It is used to tie the totals to the balance-sheet B1/B2 accounts.
- **Undo:** annul allows assets to be added or disposed of, followed by a re-post.
- **Control:** the total of "period depreciation" must equal the entry total.
- **Ref:** `mp301259` and its user guides.

### P29 — Statutory tax file generation
- **Withholdings and perceptions export (Argentina, Dominican Republic):**
  - Choose type (made to suppliers / suffered from clients), tax, version, year/month (or a free range) and party range.
  - Taxes: income tax (Ganancias), VAT, IIBB, employer contributions (SUSS), cleaning services, digital-service perception.
  - Options: summary; exclude foreign; monotributistas only; SIRFT BAIRES (Buenos Aires province) vs. ARCIBA (city); breakdown by payment order; jurisdiction.
  - Output: fixed-name text files. Examples: income tax made → `SIRETGAN.TXT` + `SUJETOS.TXT`; VAT made → `SIRETIVA.TXT` + `SUJETOSI.TXT`; joint VAT plus income tax → `SIRETIVAGAN.TXT` (requires joint numbering); IIBB made → `ARCIBAFC/ARCIBAFCPER/ARCIBANC.TXT`; employer contributions → `APATRETP.TXT` / `APATRETC.TXT`; suffered → `IVRETGAN`, `AURETGAN`, `IVRETIVA`, `IVPERIVA`, `IIBBRET<jurisdiction>`, `IIBBPER<jurisdiction>`.
- **Withholding certificate numbering:** view and edit the last number per withholding type and year. The next certificate is last + 1.
- **ISLR report (Venezuela, Ecuador):** income-tax and VAT withholding report and export, including the annual SENIAT file and send status.
- **Colombia exogenous information (Res. 3847):** report type national, Bogotá district or Envigado district; form number; by period or cumulative; draft for control or extended. Account-to-concept mapping is kept per form.
- **Colombia DIAN magnetic media (quarterly):** client costs and deductions, accumulated receivables, accumulated payables, agency costs and deductions, with an amount threshold. The output is a draft, not a final file.
- **Peru:** Libro Banco (debits and credits in local and foreign currency per account) and Libro de Inventarios (SUNAT quarterly sections 3.2 cash, 3.3 trade receivables, 3.12 payables 42/43, 3.13 other payables).
- **Expenses by jurisdiction:** costs, bonuses, bank charges, FX differences and expenses per jurisdiction, for IIBB analysis.
- **AFIP taxpayer status refresh:** from the supplier master, look up the CUIT on the AFIP site (captcha), store the status and its expiry, and print the proof.
- **Ref:** `mp301314` and its user guides, `mp302698`, `mp301310`, `mp302699`, `mp302706`, `mp301336`, `mp302717`, `mp302883`, `mp302662`, `mp301584`, `mp301298`.

---

## 3. Entities

### 3.1 Core ledger entities

| Entity | Spanish | Key fields | Identifier | Relationships |
|---|---|---|---|---|
| Fiscal year | `Ejercicio` | closing month, closing year, 12 monthly periods, status, start/end rates | year id | 1..n periods; opening/closing entries; holidays; monthly staff-cost rows |
| Period × subledger | `Mes` × `Subdiario` (Clientes, Proveedores, Tesorería/Caja-Banco, Contabilidad) | state: open (`Con Registraciones`) / `Pre Cierre` / `Cerrado` | (year, month, subledger) | gates posting by all modules |
| Balance-sheet heading | `Rubro de Balance` (primary), `Rubro Secundario`, Hyperion/Magnitude/Cartesis code | 6-char code (one level per digit, up to 6 levels; level 7 is the account), description, type (Activo y Pasivo / Patrimonio Neto / Resultados / Orden) | code | parent derived from the code prefix; accounts attach with a 2-digit position |
| GL account | `Cuenta Contable` | number (auto), name, secondary name, category, subcategory, observation code, currency, VAT account, active, inflation flag, NIT breakdown, manual restriction, accrual account, module flags (CLI/PRO/CB/GTO/F.Fijo), primary rubro + order → integration code (8), secondary rubro, Hyperion code, balance-sensitive + alternate rubro, responsible user, intercompany flag, tax/SAT rubro, required dimensions (Sub, Job, OT, CC, Div) | account number; integration code | rubro; subaccounts; expense concepts; tax account mapping |
| Subcategory | `Subcategoría Contable` | code, description, type (Volumen / No Operativos) | code | standard: Activo/Pasivo, PN, Orden; Gross Income, Compensation, Otros Gastos, Otros Ingresos |
| Subaccount | `Sub-Cuenta` | parent account (obs 82–85), number (scoped to parent), collaborator, name, active, opening balance, year debits/credits, closing balance | (parent, number) | collaborator |
| Expense concept | `Concepto` | links an expense account to finer-grained concepts | — | account; expense requests |
| Journal entry | `Asiento Contable` | year, entry type, voucher type, number (sequential per voucher type and year; shown with `#` prefix for adjustment types), date, comment, extended comment, currency, rate, creator user, status (provisional/posted), reverse-next-month flag, recurrence months, "no-control observation code" flag, attachments, origin module, manual/automatic | (year, voucher type, number) | lines; source document (invoice, receipt, payment order); reversal pair |
| Entry line | `Imputación` | account, subaccount/concept, comment, JobNumber, OT, cost center, division, debit, credit, original foreign-currency amount, client (derived) | — | account; analytic dimensions |
| Voucher type | `Tipo de Comprobante` | entry kind (Otros / Sub-cuenta-Mov. fondos), code (user range 11–89, or 10–90 in one guide), description, allow-in-pre-closed-month flag, list of allowed accounts | code | entries |
| Entry template | `Asiento tipo` | `.amp` file in a shared server folder | file name | entry type, voucher type |
| Rejection reason | `Motivo de Rechazo` | code, description, applicable document types (tasks, supplier vouchers, withholdings, entries), fiscal code | code | provisional entries |
| Currency | `Moneda` | code (01 = local), description, symbol, controlled flag, AFIP code, ISO code, decimals (2–8) | code | rates; per-currency bank, values-to-deposit and to-account-for accounts |
| Exchange rate | `Cotización` | currency, date, buy, sell, year start/end values, reporting rate (optional) | (currency, date) | FX revaluation; documents |

### 3.2 Analytic dimensions
- **JobNumber** (campaign/project): looked up by code or topic, by owner client then product, or by division then client. A special JobNumber "Tiempo y Costos No Cargables a Clientes" collects non-chargeable time and overhead.
- **OT / work order** (`Orden de Trabajo`):
  - Code format `MMNNNNYYYY`. MM 01–12 means a media plan (month of the plan); 13–24 means a production estimate (13 = January). NNNN is the plan or estimate number; YYYY is the year.
  - An OT is created when the client approves a plan or estimate. It holds actual results, including unplanned costs.
  - A generic OT exists for manual postings, but bridge-account postings must go to a specific OT.
- **Cost center** (`Centro de Costos`). There are cost-center groups, and an allocation key (`Apertura CC`) used in depreciation.
- **Division / sub-company** (`División`, `Subempresa`), with division groups. Entries must balance per division.
- **Client:** billing client vs. owner client (`Cliente de Facturación` / `Cliente Titular`), product, client group.
- **Department / production department.**
- **JobNumber distribution code** (`Códigos de Apertura por JobNumber`): a percentage split of an expense across several JobNumbers. The percentages must total 100%.

### 3.3 Observation-code catalogue (behavioural tags on accounts)

| Code | Meaning | Notes |
|---|---|---|
| 00 | no automatic behaviour | default |
| 01 / 02 / 03 | Bridge: client imputation / supplier imputation / estimation difference (liability side) | groups are matched by ordinal position in the integration-code order |
| 04 / 05 | Bridge: negative / positive estimation result (P&L) | |
| 08 | VAT credit balance | |
| 09 / 10 / 0A | VAT debit fiscal: 50% / normal / differential rate | |
| 11 / 12 / 13 | VAT credit fiscal: 50% / normal / differential rate | |
| 17 | VAT monthly payable | |
| 18 | Customer VAT withholding | the transfer-to-supplier feature uses it |
| 20 | Agency service (commission) income | assigned per media/production, taxed/exempt |
| 22 | Fees (`honorarios`) income | |
| 23 | Bonuses (`bonificaciones`) | |
| 30 | Suppliers control (AP) | integrator |
| 32 | Supplier advances | |
| 40 | Cash, local currency | |
| 41 | Foreign-currency cash | one per currency |
| 42 | Values to deposit, local | only one allowed |
| 43 | Bank | one per bank account; single currency |
| 46 | Notes receivable | one local + one per foreign currency |
| 47 | Notes payable (documents issued) | one local + one per foreign currency |
| 48 | Clients control (AR) | integrator |
| 50 | Client advances | |
| 51 | Petty cash | one per fund |
| 52 | Values to deposit, foreign currency | one per currency |
| 53 | Deferred checks issued, foreign currency | one per currency |
| 60 | IIBB perception from suppliers | one per jurisdiction |
| 82 | Account with subaccounts (non-employee) | |
| 83 | Expenses to account for (`gastos a rendir`) | per employee |
| 84 | Cost renditions (`rendición de costos`) | per employee; FX revalued per subaccount |
| 85 | Subaccounts per employee | |
| 86 | Work-in-process account analysed by the WIP analysis report | see §11 vs. WP |
| 90 | Result of the year | the closing and opening entries balance here |
| 93 | Deferred checks issued, local | |
| A0 / A1 / A2 / AI | IIBB payable / IIBB expense / IIBB withheld by clients (per jurisdiction) / IIBB credit balance | |
| IP | IIBB perception on digital services | per jurisdiction |
| AC | Inflation-exposure result (REI) | |
| RA | Accumulated results | |
| B1 … B8 | Fixed assets: original value, accumulated depreciation, revaluation, depreciation expense, revaluation of accumulated depreciation, monetary correction of original value, monetary correction of accumulated depreciation, depreciation of revaluation | |
| BR | Gain or loss on asset disposal by sale | |
| I7 | Non-computable VAT | |
| PG | Expense provision | |
| PI / PE / PH / PC / PP / PA | Provisions: income / costs (egresos) / fees / agency commission / supplier commission / sales for additional costs | as labelled in the GI pages; see §11 |
| WP | Work in process | |
| PO / PD | Overcommission provision / overcommission refund provision | |
| IC | Intercompany reclassification | |

Integrator accounts (48, 30, 82, 83, 84, 85) carry a subledger breakdown. The trial balance's "integration differences" check compares that breakdown with the GL balance.

### 3.4 Tax and other masters
- **VAT rate categories:** code, description, GL account, current rate. Linked to production types and to media through suppliers.
- **IIBB accounts per jurisdiction × year:**
  - the A0, A1, A2, 60 and AI accounts
  - rates for agency service, fees, bonuses and cost difference
  - multilateral-agreement participation % for expenses, sales and general
  - digital-service perception rates
- **Jurisdictions:** Argentine provinces are pre-loaded.
- **Withholdings master** (non-Argentina; Colombia by default, Chile optional):
  - description, person type (legal / natural / foreign)
  - GL account (filtered by the matching observation code)
  - minimum taxable amount, %, progressive-scale flag and scale table
  - deduction amount, fiscal code
  - assigned to suppliers
- **Withholding formulas** (Colombia): a matrix of client condition × supplier condition → applicable withholdings.
- **Person types:** natural or legal person.
- **Tax rubros:** an authority-requested classification assigned to accounts (Datos SAT tab).
- **Tax account mapping:** reporting rubro/account → permanent or temporary type, tax code, reconcile flag. The `Reconciliación de Impuestos` screen is marked as under construction.
- **VTR (Colombia):** a regional tax with an amount per zone. It is assigned to media materials and calculated in plans.
- **Fixed-asset concept:** description, cost center, B1/B2/B4 accounts (plus B3/B5/B6/B7 under inflation adjustment), default useful life in months or years.
- **Depreciation criterion:** code, description, first-period rule S/N/P/M.
- **Revaluation coefficients:** a code plus a 12-month coefficient grid per year.
- **Service-fee accounts:** fee type (Advisory / Management / Coordination) → liability account, P&L account, active flag.
- **Agency-service account assignment:** obs-20 accounts for media taxed, production taxed, media non-taxed and production non-taxed.
- **Staff entities:**
  - **Collaborator:**
    - identity: contact, user link (must exist first to be linked), name, tax ID, file number
    - unique e-mail
    - organisation: category, subcategory, department, cost center, division, start and end dates, severance month and amount
    - timesheet: flags, daily hours, mandatory flag, tolerance days, % client dedication, % tolerance, delegate, extra description, approval flag, approver
    - cost-plus: category, annual cost, annual hours, vacation days, freelance flag
    - monthly variable data keyed by application month
  - **Collaborator categories and subcategories** (a subcategory may link to a staff-cost formula).
  - **Cost-plus salary categories:** sell rate, global or per client, variable by month.
  - **Staff cost formulas:** elements add or subtract; percentage / fixed amount / capped percentage / scale table.
  - **Collaborator-to-client allocation:** percentage per client per period, totalling 100%. Used to re-assign agency hours in client profitability.
- **Departments:** predefined types Normal, Coordinación, Creativos, Cuentas, Producción, Finanzas, Medios y Planificación. They drive Job closing rights: Cuentas closes provisionally, Finanzas closes definitively.
- **Production departments:** a link to production-type groups.
- **Calendar:** holidays (fixed or movable types) and holidays per year (generated with each new year). Due dates that fall on a holiday roll forward to the next business day, with an alert.
- **Branches (`Filiales`):** media agencies only.
- **Service-center sectors and activities:** perfil permissions can view or execute, with a responsible e-mail.
- **Tracking rejection reasons:** origin / impact / category / reason.

---

## 4. Lifecycles

### 4.1 Journal entry
- **Direct posting** (no provisional circuit): Draft (in the UI) → **Posted**. Deletion is possible but discouraged; correction is by a **reversal entry** (contra-asiento) in an open period.
- **Provisional circuit:**
  - `En proceso de armado` (being built) → `Ingresado` (submitted, attachment present) → `Aprobado internamente` (intermediate approval) → `Contabilizado` (posted by the final approver).
  - `Ingresado` → `Rechazado` (by the intermediate approver, with a reason) → back to edit → `Ingresado`.
  - `Aprobado internamente` → `Rechazado final` (by the final approver) → back to edit.
  - The rejection and modification counters accumulate.
- **Auto-generated batch entries** (FX, provisions, WIP, positions, depreciation, IC reclass, service fee, OT closing):
  - **Not posted** → **Posted** (Contabilizar) → **Annulled** (Anula Asiento, which physically deletes the entry and its automatic reversal) → can be posted again.
  - Many of these also generate a mirror **reversal entry on day 1 of the next month**. The reversal is deleted together with the original.
- **Reporting entries:** 8A on the last day of the month, with an automatic 8B reversal.
- **Reverse-next-month entries:** the original plus an automatic reversal dated the 1st of the next month. This is not allowed for opening, close or REI-reverse entry types.

### 4.2 Period (month × subledger)
States: **Open** (`Con Registraciones`) → **Pre-closed** → **Closed**.

- Pre-close blocks new documents in that subledger, but allows the close jobs and voucher types flagged "allowed in pre-closed month".
- Every automatic close job requires pre-close.
- Close requires pre-close plus the mandatory jobs; the system enforces only some of them (see BR-51).
- **Closed → Pre-closed** (Abrir on a closed month) is allowed, though discouraged because it can change reported income and settled taxes.
- **Pre-closed → Open** is strongly discouraged: it **deletes the automatic FX, provision and tax-position entries**.
- Opening an earlier month **cascades open to all later months**.
- A subledger with no registrations cannot be closed.
- Exchange rates can be edited only in open months.

### 4.3 Fiscal year
1. **Generated:** new year = last closing month + 12; holidays and monthly cost rows seeded. Can be reversed while it has no movements.
2. **Operating.**
3. **All months closed.**
4. **Year closed:** result close → patrimonial close → next-year opening entry.
5. Optionally, **closing entry deleted → months reopened → adjusted → re-closed → year re-closed**, which updates the opening entry. This can repeat without limit.

Inflation adjustment runs in the last month while it is pre-closed. The REI reversal runs on day 1 of the next year.

### 4.4 Work order (bridge scheme)
1. **Pendiente:** no result recognised.
2. **Cierre Provisorio:** the result to date is recognised in the accounting month. Pending billing or supplier items remain. Only one provisional close per OT per month. No postings are allowed in that month afterwards.
3. **Cierre Definitivo:** nothing is pending; no further postings. Requesting a definitive close on an OT with pending items silently downgrades it to provisional.
4. **Reopen:** keep or annul the earlier close entries.
5. **Refundición:** nets the bridge balances of legacy definitively-closed OTs; no P&L impact unless never-closed OTs are included.

### 4.5 Exchange revaluation cycle
1. Month M last day: revalue open FX items (AR, AP, FX accounts) at the closing rate.
2. Month M+1 day 1: automatic reversal.
3. M+1 last day: recompute from the original rates.

At fiscal year-end there is no reversal; the new year's base rate is the rate on its first day.

### 4.6 Provisions (GI, WIP, expense, overcommission, service fee, IC)
Each one is a snapshot taken on the last day of month M and reversed on day 1 of M+1. Corrections are normally made in the following month rather than by re-running.

### 4.7 Fixed asset
**Created** (via an expense request with a B1 account, manually, or by import) → **Depreciating** (monthly or annual runs) → **Fully depreciated** or **Disposed** (disuse / full depreciation / sale) → optionally **Inactive**. The asset is editable only before its first depreciation.

---

## 5. Business rules and calculations

**Entry integrity**
- BR-01: An entry must balance (Σ debits = Σ credits) **in total and per division**.
- BR-02: Result accounts, and obs B1 accounts, require JobNumber, OT and cost center. Division is also required if divisions are enabled. Balance-sheet accounts do not carry Job/OT/client.
- BR-03: An account with subaccounts requires the subaccount on every line. An expense account with more than one linked concept requires the concept. Entries with such accounts must use the Sub-cuenta/Mov. fondos entry type.
- BR-04: Accounts with an observation code that are flagged *Restricción Mov. Manual* cannot be used in manual entries, collections or payments. Only level-1 users can override, via *No Controla Código de Observación*. The vendor strongly discourages manual entries to integrator, bridge or subaccount-controlled accounts, because they break the subledger reconciliation and FX revaluation.
- BR-05: A voucher type can restrict which accounts are allowed in its entries.
- BR-06: When an entry touches foreign-currency accounts, the whole entry should be in that currency, to avoid conversion at an unintended rate.
- BR-07: Posted entries are immutable except for the comments. Corrections are by reversal; templates (`.amp`) speed up repeats.
- BR-08: Numbering is sequential per voucher type and fiscal year. User voucher codes come from a limited range; the system reserves 1–9 and 89/90–99.
- BR-09: Deactivate rather than delete. Accounts, assets, voucher types and masters with movements cannot be deleted.
- BR-10: Customer and supplier adjustment entries must net to zero on the subledger side. The counter-account must be treasury-enabled.

**Opening and closing**
- BR-11: The opening entry contains balance-sheet accounts only, balanced against obs 90. The subledger detail must equal the GL balances; the system does not enforce this.
- BR-12: Subaccount opening balances must sum to the parent's opening balance, and are editable only in the first year.
- BR-13: The year close needs all months closed, the next year generated and its first month open. It produces three entries. Re-closing updates the opening entry.
- BR-14: The REI reversal moves the AC balance to RA on day 1 of the next year, once per year.

**Exchange differences**
- BR-15: Customers are converted at the **buy** rate and suppliers at the **sell** rate.
- BR-16: FX difference per open document = amount in foreign currency × (closing rate at month end − booking rate, or the prior base rate). Gains and losses go to the FX result account, an "Otros Ingresos" subcategory. The run is split into AR (voucher type 95), AP (96) and FX GL accounts (8).
- BR-17: Accounts with subaccounts are revalued from the sum of their subaccount balances, not from the parent balance.
- BR-18: Automatic reversal on day 1, except across a fiscal year boundary. The base rate in a new year is the first-day rate.
- BR-19: All three FX runs are mandatory every month. Without them the AR/AP subledgers do not match the GL.

**Depreciation**
- BR-20: The method is configured as monthly vs. annual, and as "complete year of acquisition" (true means a proportional coefficient in the first month makes the first year's charge equivalent to a full year; false means the normal value ÷ life).
- BR-21: First-period criteria:
  - **S:** full first period, as if bought on day 1 of the year.
  - **N:** none in the first period.
  - **P:** proportional by months and days since purchase.
  - **M:** 50% in the first year, with the remaining 50% in the last year of life.
- BR-22: Base charge = current value ÷ useful life (months). Elapsed life (VT) runs from the depreciation start date.
- BR-23: Inflation-adjusted depreciation, per asset, per month:
  - `k = (coef_month / coef_prev_month) − 1`, carried to 10 decimals.
  - `ValorActualizado = original value + original-value adjustment`.
  - `AjustePeriodo = ValorActualizado × k`.
  - `ValorActual = ValorActualizado + AjustePeriodo`.
  - `TotalAAIni = accumulated depreciation + accumulated-depreciation adjustment`.
  - `AmortPeriodo = ValorActual / VidaUtil`.
  - `AjusteAA = TotalAAIni × k`.
  - `TotalAA = TotalAAIni + AmortPeriodo + AjusteAA`.
  - Worked migration example: value 658,232, life 36 months, 10 months already elapsed externally → opening accumulated depreciation = 658,232 / 36 × 10, entered on the asset before the first run.
- BR-24: Depreciation posts debit B4 (and B8 for revaluation depreciation) and credit B2 (and B5), with the asset's or the forced cost center and division.
- BR-25: Disposal by sale books the gain or loss as sale price minus net book value, to BR.

**Inflation adjustment**
- BR-26: Only accounts flagged `Ajusta por Inflación` participate; the manual says result accounts. The coefficient is the month-on-month index ratio from the coefficient table. Use a single table across years, changing only the year.
- BR-27: The entry is balanced against AC. It is posted in the last month of the year, while that month is pre-closed. Reports can exclude the REI entry.

**Provisions and accruals**
- BR-28: Every provision is a last-day posting with an automatic day-1 reversal. Annulling one removes both entries.
- BR-29: Only one Gross Income provision entry per month. It covers all clients and both media and production; partial runs are for simulation only.
- BR-30: GI provision options:
  - `Honorarios y Comisión siempre`: provisions all fee and commission lines even on unselected OTs. The vendor suggests unticking it.
  - `Honorarios`, `Servicio de Agencia`, `Inversión` (billable media/production value).
  - `Incluir No Facturables`: costs of non-billable jobs.
  - `Incluir Pend. de Aprobar para Facturar`.
  - `Sin ingreso pendiente`: provisions pending supplier invoices only where the client was already billed. Always on, and mandatory with WIP.
  - `Ingreso por Dif. de Costos`.
  - `Ajustar al tipo de cambio actual`.
  - Additional costs from media plans are provisioned (PA). They are merged when they share accounts and are not available under WIP.
- BR-31: With WIP on, supplier invoices for jobs not yet billed are moved from cost to WP. The GI provision then handles revenue for billed-but-uncosted items.
- BR-32: The expense provision takes approved, non-deferred, non-accrued expense requests without an invoice. It is a single run per month.
- BR-33: The overcommission provision includes all pending items with no selection; PO for overcommissions, PD for refunds.
- BR-34: Service fee per client = (Revenue + NCR allocation − IIBB tax) × fee %. The default % comes from settings and can be overridden per client. The prerequisite order is pre-close → FX → GI provision → IIBB → OT/WIP close.

**Bridge accounts**
- BR-35: Group *n* of each of codes 01, 02, 03, 04 and 05 is matched by ordinal position in integration-code order. The counts must be equal; the system checks this on entering the report. Naming the related accounts with the same suffix is advised.
- BR-36: Only client and supplier documents (invoices, debit notes, credit notes) post to 01 and 02, via media type / production type assignment. Production types can carry separate client and supplier accounts per JobNumber typology (Advertising, Non-billable, New Business, Own Advertising). Own Advertising media invoices can go to a dedicated supplier account. Bridge difference accounts (03/04/05) move only through OT closing (voucher type 6). No manual entries are allowed on them.
- BR-37: At OT close, difference = client side (01) − supplier side (02) for the OT, and that amount is moved from 03 to P&L: 05 if positive, 04 if negative.
- BR-38: The Control Saldo Cuenta Puente total must equal the bridge rubro in the balance sheet.

**Taxes**
- BR-39: VAT position = Σ VAT debit (09/10/0A) − Σ VAT credit (11/12/13) − perceptions suffered − withholdings suffered (up to the entry date) ± transfers. A positive result goes to 17; a negative one goes to 08 and carries forward. A credit can be applied to other tax accounts.
- BR-40: The non-computable VAT portion is moved from VAT credit to I7. If the VAT position is posted before that reclassification, the full VAT is counted.
- BR-41: The IIBB taxable base for agencies is **own income** = cost difference (sales − cost) + agency service (obs 20) + fees (22) + bonuses (23). Each has its own rate per jurisdiction.
  - Multilateral agreement: allocated by expense, sales and general participation percentages, which must total 100% per year.
  - Real income: allocated by client and supplier address, optionally the medium's jurisdiction.
  - Home: everything in the home jurisdiction, with foreign billing optionally separated.
- BR-42: The IIBB entry: debit A1 expense; credit the A2 withholdings suffered and 60 perceptions suffered (per jurisdiction), the AI prior credit, and A0 payable for the net. A net credit goes to AI.
- BR-43: Withholding certificate number = last stored number + 1, per withholding type. Joint numbering for VAT and income tax is optional.

**Monthly close**
- BR-50: The vendor's closing checklist, in order (O = optional, M = mandatory):
  1. (O) Review finished tasks; attach costs to estimates; identify uncosted tasks.
  2. (O) Reject client-unapproved estimate and plan items (do not delete them).
  3. (O) Close finished JobNumbers. Cuentas closes provisionally, Finanzas definitively; no pending tasks may remain.
  4. (O) Customer, supplier and GL adjustment entries.
  5. (O) USGAAP/IFRS entries (8A, auto-reversed).
  6. **(M) Pre-close the month.**
  7. (O) VAT position.
  8. (O, if assets) Depreciation.
  9. (O) Expense provision.
  10. (O) Income provision (Gross Income), where the client is billed and the supplier invoice is pending. The reverse case, supplier invoiced but client not billed, is treated as WIP or also provisioned.
  11. (O) Overcommission provision.
  12. (O; mandatory if bridge accounts are not used) WIP.
  13. **(M) FX differences:** payables, receivables, foreign-currency accounts.
  14. **(M if bridge accounts are used)** OT closing, only for OTs billed in the month that have a cost difference.
  15. (O) IIBB position.
  16. (O) Regional service-fee provision.
  17. (O) Post-pre-close adjustments, using voucher types allowed in pre-closed months.
  18. **(M) Definitive close.**
- BR-51: The "close a month" user guide lists these prerequisites:
  - all subledgers pre-closed
  - FX posted when foreign-currency balances exist
  - OT results posted (mandatory with bridge accounts)
  - income provision (recommended)
  - IIBB provision (recommended)
  The manual does not say whether the system blocks the close when items are missing. The service-fee screen does warn about missing steps, and lets the user override.
- BR-52: Post-close controls:
  1. The trial balance with integrator breakdown shows no integration differences (AR 48, AP 30, 82–85).
  2. The unpaid-invoices listings for clients and suppliers at the cut-off equal the GL control accounts and the subledger trial balances.
  3. Total Gross Income in the "Inversión y Gross Income por Cliente" report (posted only) equals the P&L Gross Income rubro.
  4. If bridge accounts are used, Control Saldo Cuenta Puente equals the bridge rubro.
  5. Third-party checks in portfolio equal Values to Deposit.
  6. Post-dated deferred checks at the cut-off equal Deferred Checks.
- BR-53: Reopening a month from pre-close to open deletes the automatic income-provision and FX entries; the manual also mentions tax positions.

**Staff cost (feeds P&L by client)**
- BR-54: Internal hourly rate = annual cost (excluding taxes, including vacation and bonuses) ÷ annual working hours, adjusted for vacation days. The client rate comes from the cost-plus salary category, globally or per client, and may vary monthly.
- BR-55: Client profitability = direct billing − related costs = gross margin; + agency services; − non-invoice costs (staff hours, rent, utilities). Overhead in the "non-chargeable" JobNumber is distributed to clients in proportion to hours. Collaborator-to-client percentage tables redirect agency hours to specific clients.

---

## 6. Accounting events and inferred debit/credit patterns

The manual states the patterns marked **(S)**. The patterns marked **(I)** are inferred from the account roles. "AR" is obs 48 and "AP" is obs 30.

| # | Event (origin) | Debit | Credit | Voucher/entry type |
|---|---|---|---|---|
| E01 | Client invoice, result-account scheme (Billing) | AR | Media/production sales income; agency service income (20); fees (22); VAT debit (10/09/0A) | client invoice (auto) (I) |
| E02 | Client invoice, bridge scheme (Billing) | AR | Bridge client account (01); VAT debit | auto (S: posts to 01) |
| E03 | Client credit note | reverse of E01/E02 | | auto (I) |
| E04 | Supplier invoice, result scheme (Suppliers) | Media/production cost; VAT credit (12/11/13); IIBB perception (60) | AP | supplier invoice (I) |
| E05 | Supplier invoice, bridge scheme | Bridge supplier account (02); VAT credit | AP | auto (S: posts to 02) |
| E06 | Supplier invoice for an Own Advertising media job | the Own Advertising supplier account (if configured) | AP | (S account choice) |
| E07 | Expense invoice via expense request | Expense account (+ concept, CC, Job); VAT credit | AP | (I) |
| E08 | Fixed-asset purchase via expense request | B1 original value; VAT credit | AP | (S: creates the asset) |
| E09 | Collection (Treasury) | Cash 40 / values to deposit 42 or 52 / bank 43 / notes receivable 46; withholdings suffered (18 VAT, A2 IIBB, income tax) | AR | receipt (I) |
| E10 | Client advance received | Cash/bank | Client advances (50) or AR advance document | (I) |
| E11 | Payment order | AP | Bank 43 / cash 40 / deferred checks 93 or 53 / notes payable 47; withholdings made (liability) | payment order (S for deferred checks) |
| E12 | Deferred check clears | Deferred checks 93 | Bank 43 | auto at the due date (S) |
| E13 | Customer adjustment: advance applied to invoice | Client advance / AR advance document | AR invoice | Ajuste clientes (S) |
| E14 | Customer adjustment: write-off | Doubtful / legal debtors account | AR | Ajuste clientes (S) |
| E15 | Customer adjustment: withholding certificate received | Withholding accounts (18/A2/…) | AR | Ajuste clientes (S) |
| E16 | Supplier adjustment: advance applied | AP invoice | Supplier advance (32) | Ajuste proveedores (S) |
| E17 | Supplier adjustment: debt forgiven / not payable | AP | P&L account (Job/OT/CC) | Ajuste proveedores (S) |
| E18 | VAT withholding transfer to a related supplier | AP (related supplier) | Customer VAT withholding (18) | via payment order after open-transfer (I) |
| E19 | FX revaluation of receivables, gain | AR | FX gain (Otros Ingresos) | 95 (S type) |
| E20 | FX revaluation of receivables, loss | FX loss | AR | 95 |
| E21 | FX revaluation of payables, loss / gain | FX loss / AP | AP / FX gain | 96 |
| E22 | FX revaluation of FX GL accounts (banks, FX cash, 52/53, 84 subaccounts) | Account (if the rate rose, for assets) or FX loss | FX gain or account | 8 |
| E23 | Day-1 reversal of E19–E22 | mirror | mirror | auto (S) |
| E24 | GI provision: unbilled income | Income provision (PI), a receivable-type balance | Sales income accounts (per OT) | GI provision (S: income/cost accounts vs. provision accounts) |
| E25 | GI provision: uninvoiced cost | Cost accounts (per OT) | Cost provision (PE), a payable-type balance | GI provision |
| E26 | GI provision: fees / agency commission / supplier commission / additional-cost sales | PH / PC / PP / PA | Fee income (22) / agency service (20) / commission income / sales | GI provision (I direction) |
| E27 | WIP reclassification | WP (work in process, asset) | Cost accounts (per OT) | WIP (S) |
| E28 | Expense provision | Expense account (concept, CC) | PG provision | provision (S) |
| E29 | Overcommission provision | PO (receivable) | Overcommission income | (I) |
| E30 | Overcommission refund provision | Refund cost/expense | PD (liability) | (I) |
| E31 | Regional service-fee provision | Service-fee P&L account (per fee type) | Service-fee liability account | (S accounts) |
| E32 | Day-1 reversal of E24–E31 | mirror | mirror | auto (S) |
| E33 | OT close, positive difference | Bridge estimation difference (03) | Positive result (05) | 6 (S) |
| E34 | OT close, negative difference | Negative result (04) | Bridge estimation difference (03) | 6 (S) |
| E35 | OT refundición (legacy netting) | Bridge client 01 | Bridge supplier 02 / 03 | 6 (I) |
| E36 | VAT position, payable | VAT debit 09/10/0A (net to zero) | VAT credit 11/12/13; withholdings and perceptions suffered; VAT credit balance 08 (prior); VAT payable 17 | Posición de IVA (S) |
| E37 | VAT position, credit balance | VAT debit; VAT credit balance 08 | VAT credit; withholdings and perceptions | Posición de IVA (S) |
| E38 | Apply VAT credit to other taxes | Other tax accounts | VAT credit balance 08 | inside E36/E37 (S) |
| E39 | Non-computable VAT | I7 non-computable VAT (expense) | VAT credit | IVA no computable (S) |
| E40 | IIBB position | A1 IIBB expense | A2 withholdings; 60 perceptions; AI prior credit; A0 payable | Posición de IIBB (I) |
| E41 | Depreciation | B4 depreciation (+ B8 on revaluation) | B2 accumulated (+ B5) | 94 (S) |
| E42 | Asset revaluation (inflation) | B3 / B6 | B5 / B7 / AC | (I) |
| E43 | Asset disposal by disuse / full depreciation | B2 accumulated (+ B4 for the residual if disuse) | B1 original value | baja (I) |
| E44 | Asset sale | AR (sale invoice); B2 | B1; BR gain (or BR loss as a debit); VAT debit | fixed-asset billing (S: BR) |
| E45 | Inflation adjustment | Flagged accounts (or AC) | AC (or the accounts) | Actualización contable (S balancing to AC) |
| E46 | REI reversal (day 1 of the new year) | AC | RA | Inverso del REI (S) |
| E47 | Year close: results | Each income account | Each expense account; obs 90 for the net | Cierre resultados (S) |
| E48 | Year close: balance sheet | All credit-balance BS accounts | All debit-balance BS accounts | Cierre patrimonial (S) |
| E49 | Opening entry | Debit-balance BS accounts | Credit-balance BS accounts; obs 90 | Apertura (S) |
| E50 | Intercompany reclassification | IC account / source account | source account / IC | IC (S scope, I direction) |
| E51 | IFRS/USGAAP reporting adjustment | any | any | 8A, auto-reversed by 8B (S) |
| E52 | Payroll (manual, template) | Compensation expenses (Job/CC) | Salaries payable; social security payable; employee subaccounts 85 for advances or loans | user voucher type with subaccounts (S suggestion) |
| E53 | Cost rendition / expenses to account for | Expense / cost (Job/OT) | 83/84 employee subaccount | from the Expenses module (I) |
| E54 | Petty cash rendition | Expense accounts flagged petty cash | Petty cash 51 | (I) |

---

## 7. Cross-module handoffs

| From → To | Handoff | Contract |
|---|---|---|
| Billing → Accounting | posted client documents with account mapping (media type / production type / obs 20/22/23 / VAT category) and dimensions (OT, Job, client, division) | the Clients subledger must be open; this feeds AR, bridge 01 and income |
| Supplier invoices → Accounting | posted supplier documents with OT and estimate links; VAT; perceptions; fixed-asset creation for B1 | Suppliers subledger open; bridge 02 / cost |
| Treasury → Accounting | receipts, payment orders, deposits, checks, withholdings made and suffered, certificate numbering | Treasury subledger open; uses obs 40–53, 93 accounts |
| Expenses → Accounting | expense requests (approved, deferred or not), cost renditions, petty cash; expense concepts; accrual account | the expense provision reads non-invoiced approved requests |
| Media → Accounting | plans and orders pending billing or invoice (GI provision); overcommission pending items; additional costs; media jurisdiction for IIBB; Own Advertising typology | the GI, WIP and overcommission provisions read them |
| Production → Accounting | estimates and items, approval status (pending client approval / pending approval to bill / pending billing), production type, "mark as invoiced" | GI/WIP provisions and OT close read them |
| Accounts / JobNumber → Accounting | JobNumber close (Cuentas provisional, Finanzas definitive); a closed Job blocks new hours, tasks and estimates | dimension validity |
| Timesheet / Collaborators → Accounting | hours × internal rate and client rate; collaborator-to-client allocation; overhead distribution | client profitability and P&L by client |
| Accounting → all modules | period state (open / pre-closed / closed) gates posting; exchange rates; holidays (due dates); fiscal years | the gating rule must be enforced centrally |
| Accounting → Reporting / Consolidation | Hyperion codes, secondary rubros, consolidated balance sheet, reporting rate, 8A/8B, IC reclassification, tax account mapping | external |
| Accounting → Tax authorities | SICORE/ARCIBA/SIRFT files, IIBB position, VAT position, DIAN, Res. 3847, SENIAT, SUNAT books | country plug-ins |
| Masters → Accounting | client and supplier masters (intercompany flag, taxpayer registers, regional-fee flag and %, withholdings assigned, person type) | |

---

## 8. Configuration and country-specific behaviour

**Global special settings (`Configuraciones Especiales`) referenced:**
- provisional entries (generate / masters / intermediate approval / e-mail notices)
- disk storage for attachments
- dual rubro (secondary)
- bridge account (`Cta. Puente`)
- WIP (`Usa trabajos en proceso`)
- monetary correction (inflation)
- monthly depreciation; complete year of acquisition
- cash, foreign currency and deferred checks usage
- reporting rate (`Usa Cotización Reporting`)
- joint VAT plus income-tax withholding numbering
- `Usa Tabla de Ret. Rentas`
- group membership (e.g. Publicis) and default % Advisory / Management fee
- home IIBB jurisdiction
- GI provision start date
- `Tienen Filiales`
- divisions / sub-companies
- timesheet approval
- VAT withholding transfer

**Permissions:**
- Access levels 1–4 on Asientos Contables. Level 1 can edit automatic lines and override observation-code control.
- A special pre-close permission.
- Separate activities for provisional vs. definitive entries.
- Permission for the 8A reporting entry.
- Supervisor rights for asset deletion and for adjustments.
- Access level 2 and visualization A for WIP.

**Argentina:**
- AFIP: currency codes for e-invoicing; CUIT on checks; supplier taxpayer-status lookup with expiry.
- SICORE exports for income tax and VAT (made and suffered, versioned).
- IIBB: Buenos Aires City (ARCIBA) and Buenos Aires Province (SIRFT BAIRES) files; multilateral agreement; digital-service perception (IP).
- SUSS employer contributions; cleaning-service and temporary-service withholdings; advertising contribution suffered.
- Monotributista handling.
- Invoice letter (A/B/C).
- FACPCE resolution 539/18 inflation indices; revaluation coefficients (the manual mentions Buenos Aires tax-office valuations).
- Bridge-account rationale: IIBB on agency own income per the agreement with the advertising agencies' association.

**Dominican Republic:** withholding and perception exports.

**Colombia:**
- NIT breakdown on accounts.
- VTR zone tax.
- Exogenous information under Res. 3847 (national, Bogotá, Envigado), with an account-to-concept mapping.
- DIAN quarterly magnetic media (drafts).
- Withholding formulas matrix; withholdings table by default.
- Inflation / monetary correction.

**Venezuela / Ecuador:** ISLR and VAT withholding report; SENIAT annual export.

**Peru:** Libro Banco; Libro de Inventarios y Balances (SUNAT sections 3.2, 3.3, 3.12, 3.13, quarterly).

**Chile:** withholding table by configuration.

**Puerto Rico:** income-tax (`Rentas`) withholding types in the withholdings report.

**Mexico:** "Datos SAT" tab on accounts holding the tax rubro. Beyond that, no specific SAT e-accounting (XML trial balance, chart grouping code) features are described.

**Guatemala:** supplier invoice letter.

**Group reporting:**
- Hyperion / Magnitude / Cartesis codes.
- Secondary rubros.
- Consolidated balance sheet (paid service; bimonetary split).
- Reporting rate; IFRS/USGAAP 8A/8B.
- Intercompany reclassification.
- Tax accounts (permanent / temporary) for tax reconciliation (under construction).

---

## 9. Reports and KPIs

| Report | Purpose and key options |
|---|---|
| Plan de Cuentas | Chart listing by primary rubro, secondary rubro, Hyperion (with or without accounts), bridge accounts, or account number. Scope: current chart, accounts used in a year, or accounts created in a year. Filters: category, active, movements. Shows required dimensions (Sub/Job/OT/CC/Div). Drag-and-drop re-rubro; missing-rubro highlighting |
| Balance de Saldos (sumas y saldos / trial balance) | Opening, debits, credits, closing per account. Year or free range. Primary/secondary/Hyperion. Filter by observation code; exclude cost center or CC rubro. Totals at levels 1–7. Optionally after-close. Integrator breakdown with an **integration differences** tab. Zero balances; Hyperion column; summary by A/L/P&L; USGAAP; order by integration code; drill to ledger |
| Balance Patrimonial | Balance-sheet accounts at a date. Detailed or summary. Month-by-month columns. Bimonetary breakdown of FX accounts. Prepaid (accrued, not invoiced) expenses. Division. Two-column layout. After-close (obs 90). Include/exclude 8A/8B. Exclude post-pre-close invoices. Exclude REI. **Display in any controlled currency at the as-of rate.** Its total must tie to the P&L |
| Balance Patrimonial Consolidado | Multi-company selection; bimonetary split |
| Estados Contables | Balance sheet plus P&L combined |
| Estado de Resultados (P&L) | Period and cumulative-to-date columns. Breakdown by **owner client or client group**. Detail by division, division group, cost center or CC group. Exclude a cost center or group. Currency filter. Exclude REI. USGAAP. Month-by-month |
| Diario General y Sub Diarios | Chronological journal. All, automatic, manual, or post-pre-close invoices. Sub-journal by module (Clients with branch, Suppliers with VAT condition, Treasury and Accounting with voucher type). Per-entry totals. Dimensions. Original FX amount. Movement type and creator user. Next-year movements |
| Mayor General de Cuentas (general ledger) | By account number, integration code, Hyperion, subaccount, cost center, owner or billing client, division, **client-supplier comparison** (income vs. related supplier cost and status), or balance rubro. Breakdowns: CC, client, product, division, concept. Include closing entry. Normal or monthly summary by origin module. Module, manual/auto and media/production filters. Original-currency view. Extended comments. Drill to the document |
| Movimientos Contables por OT | Every posting by client → OT → document → line (product, estimate or plan, topic, PO, account) |
| Movimientos de Ordenes de Trabajo | **Job profitability:** posted results plus pending-to-bill and pending-to-receive lines and the projected final result. By OT, JobNumber, client and product, all, or plan. Date concept options: OT date, sent-to-results date, client invoice date, supplier invoice date, provision date. P&L tab: posted vs. fully-posted. Charts |
| Análisis de Trabajos en Proceso | Movements of the obs-86 account by client, with client and supplier documents, **aging**, and balance per OT. Cut-off date for GL comparison. Can post (after pre-close) |
| Control Saldo Cuenta Puente a Fecha | Four variants: balance control (pending supplier / pending client / pending to post, per OT); OT movements at a date; OT movements between dates; bridge balance report. Must tie to the BS bridge rubro. Can post pending OT closes |
| Reporte Dinámico de Contabilidad | User pivot/grid over GL movements with templates, filters (dates, manual/auto, accounts, currency, modules, origin, closing entry), and **weekly scheduled offline generation** |
| Reporte de Ingresos y Egresos | Income by product, concept, media type, income type (media / production / fees / commission / other), income account, account × division, or account × media type. Expenses: compensation, other, all. Monthly |
| Reporte de Workflow (dynamic) | Estimate items with status (pending client approval / pending approval to bill / pending billing), supplier, amount |
| Libro Banco / Libro de Inventarios | Peru statutory |
| Listado de Asientos Provisorios | Workflow audit and cycle time |
| Anexo Bienes de Uso | Fixed-asset roll-forward: opening value, revaluation, additions, disposals, closing; accumulated depreciation opening, revaluation, disposals, charge, closing; net book value. Detailed or summary by concept |
| Reporte de Retenciones | Withholdings made and suffered, by party, with receipt or payment order and certificate numbers, by division |
| Listado de Egresos por Jurisdicción | Expenses per jurisdiction |
| Inversión y Gross Income por Cliente (referenced, in Billing/Media) | Revenue by client; must tie to the P&L Gross Income rubro |
| Rentabilidad de Cliente (referenced) | Client P&L after overhead distribution by hours |

**KPIs:**
- Gross Income (revenue) by client, job, division and month
- job margin (posted vs. projected)
- WIP balance and aging
- unbilled revenue and uninvoiced cost provisions
- bridge balance per OT
- FX result
- VAT payable or credit
- IIBB per jurisdiction
- depreciation charge vs. NBV
- overhead absorption
- client profitability %
- provisional-entry cycle time and rejection rate
- integration differences (target zero)
- days to close

---

## 10. Implications for agentic skills

### 10.1 Suggested atomic skills (jobs)
1. `coa.manage_rubro`, `coa.manage_account`, `coa.manage_subaccount`, `coa.validate_structure` (missing parents, bridge group parity, mandatory obs-code accounts per enabled feature).
2. `je.post_manual` (validate BR-01 to BR-06, dimensions, voucher restrictions, period gating), `je.reverse`, `je.post_with_auto_reversal`, `je.recurring`, `je.template_save/apply`, `je.import_excel`.
3. `je.provisional.submit / approve_intermediate / approve_final / reject` (with reason codes and required attachment).
4. `adj.customer_apply_advance`, `adj.customer_writeoff`, `adj.customer_withholding_settle`, `adj.supplier_apply_advance`, `adj.supplier_forgive`, `adj.vat_withholding_transfer`.
5. `period.pre_close(subledger|all)`, `period.close`, `period.reopen` (with cascade warning and auto-entry deletion warning).
6. `close.fx_revalue(ar|ap|fx_accounts)`.
7. `close.gi_provision(simulate|post|annul)`, `close.wip(simulate|post|annul)`, `close.expense_provision`, `close.overcommission_provision`, `close.service_fee_provision`, `close.ic_reclass`.
8. `close.ot_close(provisional|definitive|refundicion)`, `close.ot_reopen`.
9. `tax.vat_position`, `tax.vat_noncomputable`, `tax.iibb_position(criterion)`, `tax.export_withholdings(country,tax,type)`, `tax.certificate_numbering`, `tax.country_reports(...)`.
10. `fa.register_asset`, `fa.depreciate(period, cc_mode)`, `fa.dispose(disuse|sale)`, `fa.revalue`.
11. `year.generate`, `year.close`, `year.reopen_for_adjustments`, `year.inflation_adjust`, `year.reverse_rei`.
12. `opening.load_entry`, `opening.load_subledger(clients|suppliers|notes|third_party_checks|deferred_checks|subaccounts)`, `opening.reconcile_to_gl`.
13. `report.trial_balance`, `report.balance_sheet`, `report.pnl(breakdowns)`, `report.journal`, `report.ledger`, `report.job_profitability`, `report.wip_aging`, `report.bridge_control`, `report.fa_annex`.
14. `control.month_end_checks` (BR-52 plus the P25 routines), `control.integration_differences`.
15. Orchestrator: `close.run_monthly_checklist` sequences BR-50, stops at mandatory gates, and produces a close pack.

### 10.2 Deterministic calculations worth a tool (not an LLM)
- Entry balancing per currency and per division; dimension requirement resolution from account flags.
- Integration code derivation and rubro tree build; level totals.
- FX revaluation per open document and per subaccount (buy vs. sell rate), with year-boundary base rate logic.
- GI provision engine: per OT, pending billing × components (investment, fee, commission, supplier commission, additional cost, cost difference); pending supplier invoice; option flags; WIP interplay.
- WIP selector: supplier-invoiced and client-unbilled items.
- Bridge OT close difference and account pairing by ordinal position.
- VAT position netting with carry-forward and credit application.
- IIBB base per jurisdiction under the three criteria; rate per component; multilateral percentage validation.
- Service-fee calculation.
- Depreciation with the S/N/P/M criteria, complete-year option, monthly/annual, and the inflation formula (10-decimal coefficient).
- Inflation adjustment coefficient ratio; REI reversal.
- Year-close entries (results to 90, BS close, opening).
- Staff hourly cost and client profitability with overhead allocation.
- Statutory file writers (fixed-width / CSV layouts per authority and version).
- Due-date holiday roll-forward.

### 10.3 Controls to encode
- Hard gates:
  - pre-close required for every close job
  - only one GI provision per month
  - no definitive OT close with pending items
  - no posting into closed or pre-closed periods unless the voucher type allows it
  - immutable posted entries
  - no deletion of used master data
  - no provisional route for adjustments, close entries or REI
  - a mandatory attachment for provisional entries
- Soft warnings:
  - manual lines on obs-coded or integrator accounts
  - reopening that deletes auto entries
  - cascade reopen
  - missing prerequisites for the service fee
  - missing last-day rate
  - opening subledger detail ≠ GL
  - bridge group count mismatch
- Segregation of duties: preparer ≠ intermediate approver ≠ final approver; pre-close permission; level-1 override logging.
- Reconciliations after close: BR-52 items 1–6 plus the P25 routines; depreciation entry total = calculated total; VAT position = ledger = sub-journals.

### 10.4 Exceptions and edge cases for agents to handle
- Late supplier invoices after a provisional OT close: the posting must be dated after the close month.
- A manual FX entry already posted: run the auto FX entry, then a manual reversal.
- Audit adjustments after the year close: delete the closing entry, reopen, adjust, re-close.
- VAT recovered on cost renditions causing a phantom pending item: edit the estimate cost.
- A stale pending supplier invoice: "mark as invoiced" (no GL entry).
- A non-computable VAT reclassification posted after the VAT position.
- A disposal in a month whose depreciation is already posted: annul the depreciation first.
- Fixed assets migrated with prior accumulated depreciation.
- Company absorption opening balances.
- Unknown creator of a provisional entry: use the movement audit trail.
- New controlled currency: historic rates are back-filled; real rates must be fixed manually if transactions exist.
- A fiscal year generated too early: transactions default to the new year (reverse if empty).

---

## 11. Gaps and ambiguities

1. **Inflation adjustment amounts.** The overview says the system computes the adjustment on flagged result accounts with coefficients and balances it against AC. The user guide says the detail does not bring the computed values and the lines are entered per account. A separate screen, "Generación de Ajuste por Inflación", and "Rubros de Ajuste por Inflación" have one-line descriptions only. The calculation basis (monthly movements × coefficient to year end?) is not specified.
2. **Nature of the AC account.** One page calls it an equity account; the user guide calls it a results account ("Resultado por Exposición a la Inflación"). The REI reversal moves it to RA.
3. **Provision code semantics.** The GI pages map PI = income, PE = costs, PH = fees, PC = agency commission. The intercompany page labels PC as "cost provision", PH as "agency service (commissions)" and PI as "fees". The intercompany list is likely mislabelled, but this should be confirmed.
4. **WIP account code.** The WIP analysis report reads an **obs 86** account, while WIP closing uses a **WP** account. They may be the same concept under the bridge scheme vs. the provision scheme, or two different accounts.
5. **Exact GL debit/credit for automatic entries** (billing, supplier invoices, payments, FX, provisions, IIBB) is not given. §6 marks the inferred patterns.
6. **Whether month close is blocked** when mandatory jobs (FX, OT close) are missing, or is only advisory.
7. **Reopen side effects.** Pre-close → open deletes the provision and FX entries; the main page also says positions. It is unclear whether depreciation, WIP, the expense provision, overcommissions and OT closings are deleted.
8. **The FX account** (gain/loss) observation code is not named. The "Otros Ingresos" subcategory is the only hint.
9. **Voucher type code range:** 11–89 in the overview and 10–90 in the user guide. Reserved ranges are 1–9 and 89–99. Fixed system numbers seen: 6, 8, 8A/8B, 94, 95, 96.
10. **Depreciation criteria vs. the "complete year" setting:** how the per-concept criterion (S/N/P/M) interacts with the global flag; whether the criterion links to a concept or to the run (the run filter is called "Criterio").
11. **Overcommission flows** (generation of pending items, invoicing of overcommissions to media) live in another module; only the provision is described.
12. **Service fee "NCR Allocation"** is not defined.
13. **Doubtful-debt provisioning** (as opposed to write-off) is not described.
14. **Mexico SAT e-accounting** (catalog XML, trial balance XML, journal policies) is not covered beyond a tax-rubro tab. The "Certificación Mensual" and "Traslado de Retenciones" menu items under Operativa Legal y Fiscal have no page content.
15. **Tax reconciliation screen** is "under construction". Tax-account (permanent/temporary) usage is unclear.
16. **Consolidation mechanics** (eliminations, FX translation) are not described; only multi-company selection is.
17. **Recurrence months:** whether recurring entries are generated at save time or at each period open.
18. **The Asiento de Refundición** entry pattern and voucher type are not specified.
19. **Treatment of IIBB perception on digital services** at billing time is mentioned but not detailed.
20. **Rounding and decimal rules** (beyond the 10-decimal coefficient and currency decimals of 2–8) are not specified.
21. **Academia pages** contain titles and durations only; there is no content to extract.
