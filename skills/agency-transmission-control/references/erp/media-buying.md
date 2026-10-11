# Media Buying: Insertion Orders, Media Contracts, Rate Cards, Spot Verification, Overcommissions

> **Provenance.** Functional reverse engineering of a reference agency ERP, derived from its publicly accessible help documentation (reviewed 2026-10-11). Content is paraphrased and restructured; it is not vendor documentation, source code or an endorsement. Bracketed ids such as `[mp301010]` identify the source page used as evidence. Items marked *inferred*, *assumed* or listed under gaps must be validated with your own controller, tax adviser and system owner before they drive postings or payments.

Source: the reference ERP's help documentation (Spanish). Everything below is a paraphrased functional reconstruction meant to drive an open-source agentic skills repo. Spanish field and menu names show up in backticks only so they can be traced back to the source. Source refs use the original help file names, e.g. `[mp301010]`.

---

## 1. Purpose and position in the end-to-end circuit

This module is the **buy side** of the agency media circuit. It sits between **media planning** (the plan, `Plan de Medios`, and its schedules, `Pautas`) and the **financial back office** (supplier invoice reception / AP, client billing / AR, general ledger).

Its responsibilities:

1. **Reference pricing.** It maintains rate cards (`Tarifarios`). Media-published "printed" rates apply to every client, and client-negotiated rates apply to one client. Each rate card holds two price sets: the **buy price** (order, `Orden`) and the **sell price** (schedule/plan, `Pauta`).
2. **Commercial framework with media.** It records buy contracts (`Contratos de Compra de Medios`). A contract can cap consumption, pre-bill a client in installments, pin rate cards, set default discounts and surcharges, define share-of-spend restrictions and confidential discounts, and support adjustments and balance transfers.
3. **Issuing purchase documents.** It turns approved schedule lines into **insertion orders** (`Órdenes de Publicidad`, "OP"), sends them to the media outlet or vendor, and versions them on every change ("cancels and replaces").
4. **Proof of performance.** It verifies that spots actually aired (`Control de Avisos`), either manually or by automatic matching against imported monitoring files (Ibope, Monitor, etc.), using audit codes.
5. **Closing.** It closes orders (`Cierre`). A closed order is frozen and becomes eligible for supplier invoice registration and accounting.
6. **Back-end income.** It manages volume-rebate and overcommission agreements with media vendors (`Contratos de Overcomisión`), the Colombian incentive scales (`Escala de Incentivos`), finder-fee contracts, provisioning, and pass-through of rebates to clients.
7. **Interfaces.** It exports orders and cancellation requests to vendor systems (Caracol and RCN in Colombia) and to advertisers, and imports monitoring data and rate cards.

Circuit position (simplified):

```
Masters (media, pub types, programs, audit codes, providers)
   → Rate cards → Contracts
   → Media plan / schedule (planning module) → client approval (+credit-limit approval)
   → Insertion orders (manual / automatic) → send to media (print/PDF/email/interface)
   → Modifications (versioning) / cancellations
   → Spot verification (manual / automatic monitoring import)
   → Order close → Supplier invoice registration (AP) requires closed orders
   → Client billing of schedule (AR) [gates: approved-to-bill, manual state]
   → Overcommission pending generation → provision / invoice vendor / credit note → client rebates
   → Accounting entries (observation-coded accounts)
```

The Academia pages for offline media buying (general concepts, buying, press and out-of-home, radio/TV/cable, spot control, pre/post evaluation, modifications and rescheduling, reports) contain **only video titles and durations, no text** `[conceptos-generales-de-compra-, compra-de-medios, compra-de-prensa-y-via-publica, compra-de-radio_-tv-y-cable, control-de-avisos---1906, pre-y-post-evaluacion, modificaciones-y-reprogramacio, reportes-y-listados3]`. They only confirm the topic taxonomy.

---

## 2. Process catalogue

Notation: **T** = trigger, **A** = actor, **S** = steps, **I** = inputs, **O** = outputs, **ST** = state transitions, **AP** = approvals/controls.

### 2.1 Rate cards (Tarifarios)

#### P-RC-01 Create rate card header `[mp301168, mp301368]`
- **T:** A new media outlet is onboarded, a new period starts, or a client negotiates its own rates. The manual recommends rate cards especially for TV and radio. They are optional but strongly recommended.
- **A:** Media buyer / media admin.
- **Prerequisites:** The media outlet exists with a media type, publication types exist for that media type (e.g. regular break `Tanda`, product placement `PNT`, out-of-home space rental, taxes, lighting), and programs/locations (`Programas / Ubicaciones`) exist, entered manually or imported from the ratings provider.
- **S:**
  1. Choose the criterion: *by media type*. This creates an empty card for all outlets of that type and is noted as practically unused. The alternative is *by medium*, which is either for all clients or for one client.
  2. Pick the medium and optionally the client. If no client is chosen, the card is the generic printed card.
  3. Enter the description, validity start, and optional validity end. With no end date the card never expires. The manual recommends always setting an end date as a control, because planning outside the validity range then finds no rates.
  4. Enter the currency.
  5. Select the calculation type (`Tipo Cálculo`), see BR-T-01..05.
  6. Choose whether rates are entered per program or per time band (`franja`). If per band, select the time-band configuration.
  7. Enter the reference CPP (`C.P.P. de Referencia`). This field appears in the guides.
  8. `Usa Tarifario Base` = Yes: pick a base card and a coefficient (default 1). The client card is derived from the base. The base rate cannot be edited in the child, and changes to the base propagate to the child. `Usa Tarifario Base` = No: an empty card is created.
  9. Optional copy (`Copiar Tarifario`): pick a source card, a coefficient (default 1, used when price is not proportional to duration, or to apply an increase), and a "filter validity" flag.
  10. Save the header.
- **O:** A rate card header with a version and validity.
- **AP:** A card can be deleted only if it has never been used.

#### P-RC-02 Enter or update rates for one program `[-ingresar-actualizar-tarifas-de-un-programa-...]`
- **Prerequisite:** The header exists.
- **S:** Open `Actualización Tarifarios de Programas` and press Query. Select the medium, holder client, validity, card, and publication type. Optionally filter by time-band config, broadcast days, start/end hour, genre, program validity, program type (program or block), and "only with rate / all". Press Start. In the detail grid, for each program enter the **order gross rate + discounts 1–4** and the **schedule gross rate + discounts 1–4**. The net columns are computed. Moving between cells auto-saves.
- **O:** Per-program buy and sell rate lines.

#### P-RC-03 Mass update a program group `[-ingresar-actualizar-tarifas-de-un-grupo-...]`
- Same query as P-RC-02, then the `Tarifas` button opens three criteria:
  - **Apply amounts:** a fixed amount for order and schedule, flagged as gross or net.
  - **Apply discounts:** discounts 1–4 as a % for order and for schedule.
  - **Copy rate card:** a destination or source card plus a coefficient.
- Press `Calcular` to apply the change to every row visible after filtering.

#### P-RC-04 Partial copy of a rate card `[-copiar-tarifarios-parcialmente-]`
- Filter to a subset of programs. In `Tarifas`, choose Copy Rate Card, pick the source card and a coefficient, then press Calculate. **Each target rate = source rate × coefficient.**

#### P-RC-05 Copy a client rate card from an existing card (header level) `[-copiar-tarifario-de-medio-para-un-cliente-...]`
- New header with `Usa Tarifario Base` = Yes, a source card, and a coefficient. Then refine via P-RC-02.
- Recommendation: keep the same calculation type and publication type in the source and target cards to avoid inconsistencies.

#### P-RC-06 Flat-rate header `[-generar-encabezado-tarifario-de-medio-de-tarifa-plana-]` and CPP header `[-generar-encabezado-tarifario-de-medio-cpp-]`
- **Flat:** the rate entered is the value of **one second**. Plan cost = duration × number of spots × per-second value.
- **CPP:** the rate entered is the value of **one rating point**. Plan cost = duration × spots × point value × program rating. The duration factor is stated in the source. See Gaps.

#### P-RC-07 Out-of-home rate update `[mp301167_viapublica]`
- Same mechanics as programs, with filters limited to program/location validity and rate amount (zero / non-zero). The Tarifas button offers the same three criteria. Internal and external observations are available.

#### P-RC-08 Digital rate update `[mp302836]`
- Cards are usually imported periodically by routine. Query by internet media type, medium, holder client, validity (all or by date), and card. The card shows version, validity, last modification, currency, and calculation type.
- Filters: location validity, rate amount, platform, publication type, format, calculation. If the special config `Tarifas de Internet por Formato y Medida` is on, a **Medida** (size) selector that depends on Format appears.
- Buttons: Round, Tarifas (apply amounts / discounts / copy), Delete selected rows, and an `Aprobar` (approve) button that has no description.
- Digital cards require a **default rate per medium + location + publication type**. Supported calculation types: gross rate with discounts, CPC, CPV (cost per thousand visits), CPA, plus agency-defined types in the master `Tipos de cálculo Internet`. The editing screen captures the "sale price / schedule value" and the "% client discount".

#### P-RC-09 Rounding
- The `Redondear` button rounds every gross rate that has decimals. The rounding rule (precision, half-up or not) is not specified.

#### P-RC-10 Import rate cards
- The `Importar` button is enabled only for agencies that update rate cards via an interface.
- **Chile:** download an Excel of active programs loaded from the ServiBanca program grid, fill in the rates, and re-import. Rates are differentiated by publication type (break vs PNT).

#### P-RC-11 Provider tariff keys (Mexico only) `[mp305168]`
- A master of vendor tariff keys for Televisa: provider, auto code, description. Selected when creating a new rate card. CRUD with standard buttons.

#### P-RC-12 Special rate cards `[mp302822]`
- Marked "under construction". No content.

#### P-RC-13 CPR rate card
- When a card is specific to a cost-per-rating purchase type, a **target** and a **book** (ratings source) are attached to it `[mp301167]`.

### 2.2 Buy contracts (Contratos de Compra de Medios) `[mp301004 + 6 guides]`

#### P-CT-01 Create a contract (generic)
- **T:** A client or the agency negotiates terms with a media outlet or vendor for a period.
- **Purposes:** (a) cap consumption of a contract current account, (b) bill the client in advance in installments when the detailed spend is not yet known, (c) attach rate cards and define confidential discounts.
- **Prerequisite masters:** media with media type, publication types, programs/locations, external providers (ratings, monitoring, evaluation), and a rate card per medium.
- **S (main data tab):**
  1. **Client:** an active billing client. The special **Agency** client makes the contract agency↔medium, possibly with *advance payment*. Orders against a prepaid agency contract then carry **no cost** at ordering time.
  2. **Medium or Provider:** depends on the country. If it is a provider, choose the media type; if it is a medium, the media type is auto-filled.
  3. Contract number (auto), description, active flag, validity start/end.
  4. **Type:** Normal or Barter (`Canje`).
  5. **Consumption type:** by Amount or by Seconds/centimetres (the unit depends on the media type).
  6. **Control type:** Cap (`Valor Tope`) or Free consumption (`Consumo Libre`).
  7. **Measure:** a cap in seconds when consumption is by seconds.
  8. **Net balance:** auto-filled from the gross amount entered in Negotiation. Read-only.
  9. Observations.
- **Negotiation tab:**
  - Contract with or without VAT. For amount-based consumption, this decides whether item amounts count with or without VAT.
  - Payment condition. With free consumption it is forced to *cash* (`Contado`). With a cap, a list is offered that includes **Installments** (`Cuotas`).
  - Term (days). It is linked to the payment condition and both update each other.
  - Currency, plus fixed exchange rate (Yes/No) and the rate value.
  - **Gross amount** (the cap).
  - Client discounts 1st–4th.
  - **% agency commission.**
  - **Discount application criterion** (`Criterio Aplicación`). Its values are not listed.
- **Installment specifics:** a generic JobNumber is assigned automatically unless the special config `Elige Job en Contrato de Cuotas` is enabled, in which case a Job selector appears on save.
- **Colombia:** a flag `Pasa por agencia` ("goes through agency") that associated plans inherit automatically.
- **Config `Permite modificar descuentos en ítems con contrato`:** allows editing or adding discounts on plan items that carry a contract.
- **Discounts/Surcharges tab:** default discounts (description + %) and default surcharges (code, description, %, accumulation, value). Surcharges must already exist in the master. Plans that use the contract pick these up.
- **Share tab** (validated over the set of orders consuming the contract):
  - Restriction 1: global share %.
  - Restriction 2: share by location. Type is by time band or none.
  - Restriction 3: share by day. Type is Mon–Fri / Sat / Sun, Mon–Fri/Sat/Sun, or none, with a grid of days and %.
- **Confidential tab:** confidential discount Yes/No. If Yes, choose the compensation mechanism (**agency invoices the vendor** or **vendor issues a credit note**) and the %. An optional % per publication type (rate) can be set, with observations.
- **Assignment tab:** which billing clients of the holder client and which products (macro group / product group) the contract applies to. Default is all.
- **Rates tab:** rate type (printed or negotiated, optional), client (read-only), calculation type (rate-based or CPR), and a grid selecting rate cards by date range (F2 on the code column), with an "only active" toggle.
- **Installments tab** (only when the payment condition is Installments):
  - Administrative data: billing client, provider, unit of measure.
  - Distribution: advance % → advance = gross × %. The remainder is split into **one installment per month of contract validity**. Installment amounts and dates are editable and new installments can be added, but **Σ installments + advance must equal the gross amount**.
  - On save, the system **auto-generates a plan with one schedule (pauta) per installment**, each in status **Pending** and immediately billable.
- **Subcontracts tab:** contract kind Normal, **Parent**, or **Child (subcontract)**. A child selects its medium and parent contract. **Children have no cap; the current account lives in the parent.** There can be one parent with several children, one per media type.
- **Save:** if no rate card was set, the system asks whether to add one now.
- **Other buttons:** Copy (clone into a new contract), Delete (only if never billed), Modify (used for adjustments), Print, External systems (interface codes for programming, ratings, spot control interfaces, or client reports).
- **Rule:** each contract relates to exactly one medium and one client.

Guided variants (each is a specific parameter combination):

| Variant | Consumption | Control | Payment | Subcontract |
|---|---|---|---|---|
| Amount + cap, parent `[...valor-tope-tipo-padre]` | Amount | Cap | any | Parent |
| Amount, no cap, child `[...sin-valor-tope-tipo-hijo]` | Amount | Free | cash | Child (needs parent first) |
| TV/Radio by seconds with cap `[...por-segundos-con-valor-tope]` | Seconds (enter seconds) | Cap | any | Normal |
| Amount + cap in installments `[...valor-tope-en-cuotas]` | Amount | Cap | Installments | Normal |
| Amount + free consumption `[...consumo-libre]` | Amount | Free | cash | Normal |
| Amount + cap `[...por-monto-y-valor-tope]` | Amount | Cap | any | Normal |

#### P-CT-02 Contract adjustment `[mp309255, -ingresar-un-ajuste-de-contratos-de-medios-]`
- **T:** The contract amount must change (positive or negative), e.g. after an installment contract has been invoiced to the client.
- **Prerequisite (guide):** an installment contract exists and has been billed to the client.
- **S:** New → month to adjust (defaults to the current month) → adjustment number (sequential, auto) → in favour of (**Agency** or **Medium**) → holder client → media provider → medium → contract → subcontract (if any) → schedule (auto-fills order) → current balance (auto) → amount to adjust → optional description → Save.
- **O:** An adjustment movement in the contract current account. It affects the consumed balance.
- **Rules:** an adjustment in favour of the agency creates **no pending item in favour of the client**. An adjustment can be deleted only if it has not been invoiced.

#### P-CT-03 Transfer between contracts `[mp309256, -transferencia-de-contratos-]`
- **T:** Move unconsumed balance (all or part) from one contract to another.
- **Prerequisite (guide):** two installment contracts, both billed to the client.
- **S:** New → month → auto adjustment number → origin (holder client, medium, contract, optional subcontract; balance shown) → destination (holder client, contract, optional subcontract; balance shown) → amount → description → Save.
- **Rule:** destination client + contract must differ from the origin.
- **Effect:** the origin balance decreases and the destination balance increases immediately.
- A related guide creates **balance-sheet (patrimonial) GL accounts** `[-ingresar-cuentas-contables-patrimoniales-]`: number (auto), name, default VAT account, category = Patrimonial, subcategory, observation code (special behaviour), currency (only for observation-coded accounts), active, "restrict manual journal entries", modules where postable, main and secondary chart rubric, balance-sensitive flag. This implies that transfers or installment billing post to specific balance-sheet accounts. The accounts are not named.

#### P-CT-04 Contract current account (report) `[mp301006]`
- Filters: billing client (with contracts), product macro group, contract, consumption date range (schedule and order dates), currency.
- Shows the contract number and payment condition, and a grid of movements: consumption, adjustments, transfers, billing.

#### P-CT-05 Contract list `[mp301099]`
- Filters: client, media type, provider, date range, currency, consumption type (all / amount / measure), payment condition, status (all / active), summarized, "only advance payments".
- Display options: show observations, show provider commission.
- Columns include **initial balance, consumed, current balance**. Exports to a dynamic report.

### 2.3 Insertion orders (Órdenes de Publicidad) `[mp301010, mp401010 + guides]`

#### P-OP-01 Generate orders from a schedule (manual)
- **T:** The plan is approved by the client. Some agencies skip approval, in which case "Order" is available as soon as the plan is saved.
- **Prerequisites (guides):** (1) plan approved by the client; (2) if the agency uses credit limits and the plan exceeds the client's limit, the excess must be approved.
- **A:** Media buyer.
- **S:** Query the plan → select the schedule (pauta) → `Ordenar / Orden Manual`.
  - **Header:** schedule number. Although a schedule may span several media, ordering is done **one medium at a time**.
  - **Main filters:** default to the first medium still pending. Orders can be segmented by **material, contract, publication type** (e.g. PNT vs break). The **payment condition to the vendor** can be changed; it defaults from the provider master.
  - **Other data:** two purchase-order numbers, one for the **media investment** and one for the **agency commission**, each with dates.
  - **Footer notes:** working conditions and agreed deliveries.
  - **Body:** shows each spot with its rate. The **buy cost may be overridden** and up to **4 order-only discounts** may be entered.
  - **Grouping mode buttons:**
    - Per item: one order per program/line.
    - Per spot: typical for press, e.g. weekly insertions ordered week by week.
    - Per date: order a date range, e.g. the first fortnight, and leave the rest pending. A "maximum date to order" prompt sets the cut-off.
    - All in one order: every line in the period goes into one order, with a "measure/duration to order = All" option.
    - Day-picking: double-click individual days on the spot distribution grid.
  - Spots included in the draft order turn **black**. Review the visual tab, then Save. Repeat for the next period or medium.
  - When nothing is left pending, the plan shows ordered spots in **blue** with a **lock** column.
- **O:** One or more insertion orders, each with a number, version, vendor, items, and spot-level calendar.
- **ST:** schedule day status *scheduled* (`pautado`) → *ordered* (`ordenado`).

#### P-OP-02 Generate orders (automatic)
- **S:** Choose the split criterion: per medium, per provider, per publication type + medium, per publication type + provider, per item, or per day. Medium = "All" orders every medium in the schedule for the chosen period. Separate orders can be forced **by material** and **by VAT rate**. Footer notes use a period/medium/model selector with notes 1–3 and a preview per order. Confirm → orders are created → return to the plan.
- **Pricing rule:** the automatic process takes the buy price from the rate card. **If no rate card exists, the buy price is set equal to the client sell price.** Manual mode is meant for when there is no rate card and a buy price different from the sell price must be set.

#### P-OP-03 Reuse an order number
- **T:** A change in duration or billing condition requires keeping the same order number.
- **S:** Manually enter the order number and the schedule number. The system warns that a **version change** occurred, and the user decides whether the vendor must be notified. Then add the spots and costs. The version history is visible from the plan.

#### P-OP-04 Send orders to the vendor
- **From the plan:** "print all orders of the medium" → filter medium → choose paper or **PDF export** → number of copies. A single changed order can be printed via right-click on the spot → Orders.
- **From the order list:** select orders with the check column and print.
- **From the order:** an email button builds a message in the local mail client, using the user's mailbox and the vendor email from the medium master.
- **Special conditions text:** an administrator can place a file `NotaEspecial.txt` in the server's files folder. Its text is printed in a predefined area of the order layout.
- **Print variants** (from the complete list): with values; with commission breakdown (shows the agency service value); by conduit (relation to the requester); as direct (as if the client bought directly).

#### P-OP-05 Modify an issued order
- **Division of change authority:**
  - **On the order:** buy cost/rate, discounts, tax attributes, footer notes, item description, **vendor**.
  - **On the plan only** (replicated to the order): program name, duration, number of spots, publication type, billing condition. These affect both the client-side and buy-side documents.
- **Guide: change vendor** `[-modificar-el-proveedor-...]`.
  - Prerequisite: the new vendor must be associated with the medium in the media master.
  - Plan → Query → open the Visual bar → check `Agrega Avisos a Orden` → Modify → select program + day → double-click the lock flag → Orders/Edit → `Modificar / Modifica Nro. Pro.` → choose the provider → Save.
  - This opens the **Revision-by-modification** window:
    - `Mod. Rev.`: create a new version.
    - `Imp. P. Anu.`: print a "cancels and replaces previous version" legend.
    - Copies, PDF flag, reason description.
  - Accept → close → Save the plan.
- **Guide: change rate and discounts** `[-modificar-tarifa-y-descuentos-...]`: same entry path, then Item data → Modify → new description (optional), new buy rate, new discounts → Save → revision window.
  - **Restriction:** order rates and discounts can be changed only on **indirect items** and only for **clients that do not run audits in the system**.
- **Guide: change header data and notes** `[-modificar-datos-de-la-orden-...]`: Modify → footer-notes tab: model + notes 1–3 → Detail tab text → Save → revision window.
- **No-version option:** if the order **has not been sent** to the vendor, uncheck `Agrega Avisos a Orden`. The order is then re-issued with the **same number and version**.
- **Modification reasons:** the masters include `Motivos de Modificación de Ordenes` and `Categoría de Motivos de Modificación de Ordenes`, which feed the modification-efficiency report.

#### P-OP-06 Delete an order
- Used only to **release spots** so their attributes can be changed in the plan. For other changes, modification is preferred.
- Publisher variant: an order cannot be deleted once approved by the client or approved for billing.

#### P-OP-07 Close an order `[mp301025 guide, mp301010]`
- **T:** Spot verification is done and airing is confirmed.
- **S (from the plan):** Query the plan → `Ordenar / Cerrar Órdenes` → tick orders → Accept. Other paths: from the order (`Control` button → close), or mass close from the complete order list (Control column → Close).
- **Effects:**
  - The order can no longer be modified.
  - The accounting department can register it.
  - **Any spots still unverified are automatically set to verified-and-aired** using the default audit code.
- **Rules:**
  - Supplier invoices can be registered only against closed orders.
  - The manual recommends making closure **mandatory before accounting**. Otherwise accounting closes orders at invoice registration time, without proof of airing.

#### P-OP-08 Reopen an order
- **Conditions:** no supplier invoice is attached (check the order's billing tab; any supplier invoice must be cancelled first), **and** the month's schedules must not be closed.
- **Path:** the `Control` button → open. Mass open is available from the order lists.
- Open/close can be repeated freely until a supplier invoice locks the order.

#### P-OP-09 Deliver order / record PO number (complete list) `[mp301117_ejecutar_completo]`
- **Deliver:** for closed orders, records a delivery date (`Fecha de entrega`).
- **Save PO number:** an editable "Purchase order no." column, saved with `Grabar N° OC`.

#### P-OP-10 Publisher ("Editora") order entry `[mp301445]`
This variant is for agencies or publishers selling print space; the order acts as both sale and placement.
- **Header:** Job (campaign/project) of client + product; advertiser, magazine, product; billing parameters, currency and FX, selected media and negotiations.
- **Other data:** barter % or amount (inherited from the master, editable); internal request no.; `Modifica Revisión` (checked by default, so every save creates a new revision); client PO number (editable after save, or per month if config `Numero de Pedido de Cliente Mensual`); rate card; opening code (multiple-billing split across billing clients by % when the Job billing code is "assign in schedule/estimate"); payment condition (from the billing client, or client/product if the client says payment term is defined per product, for the media area); currency (local, foreign, or the medium's); approved by client; order without VAT; approved to bill.
- **Totals:** Gross, Discounts, Subtotal, Credit-note discounts (`Descuentos N/C`), Net, Total spots, Billable, Total barter.
- **Items:** item number (never reused, gaps allowed), ad type, description (25 chars max; a Text tab is available for longer text), discounts and credit-note discounts %, rate (auto from publication type), total spots → computed gross, discounts, subtotal, credit-note discounts, net. Item actions: new, save, delete, recover (before the order is saved), modify.
- **Admin control tab:** per item and date: order no., status, client, client invoice no., credit note.
- **Audit tab:** per spot: aired or not, air time, controller, rating info.
- **Buttons:**
  - New: blank order, or **Copy order**, with an option to change JobNumber, include or exclude spots, keep or reset rates.
  - Header edit.
  - Delete: blocked if approved by client or approved to bill.
  - Approvals:
    - **Approve credit limit:** allowed only if order amount + client AR balance ≤ client credit limit.
    - **Approve by client:** required before ordering when the config is on.
    - **Approve to bill:** required before client billing when the config is on.
    - **Disapprove to bill.**
  - Reject: reject the whole order or one order, if not billed.
  - Recover a rejected order: if not billed.
  - Work order (`Orden de Trabajo`): view the derived work order.
  - Printer setup.

#### P-OP-11 Publisher: orders pending approval `[mp301446]`
- Filter by month range and report type (billing client, holder, product, advertiser, magazine, seller).
- Grid: select, month, no., JobNumber, client, product, theme, amount, net, barter total, billable, payment condition.
- The **Approve** button approves the selected orders by client in bulk.

#### P-OP-12 Publisher: activity by advertiser / last action `[mp301612, mp301599]`
- Activity by advertiser: drill-down by client, advertiser, seller, or magazine.
  - Orders tab: month, order no., magazine, advertiser, product, seller, detail, status, amount, currency, FX amount, payment condition, voucher no., budget no., billing client, JobNumber, campaign.
  - Quotes and contact reports: date, no., magazine, edition no., advertiser, user, mail text.
  - Tasks: JobNumber, task no., request/read/agreement/completion dates, delay, subject.
- Last action: lists clients, advertisers, or sellers with their last activity date and opens the activity screen.

### 2.4 Spot verification (Control de Avisos) `[mp301102 + guides, mp301441]`

#### P-SV-01 Configure prerequisites
- Audit codes master (`Códigos de Auditoría`).
- Special config `Código Auditoría por defecto en Cierre de Orden` (Billing branch). It must hold a universal "aired OK" code valid for all media types.
- For automatic control:
  - External provider configured to accept monitoring.
  - Medium flagged as spot-controlled and linked to the external provider.
  - For radio, system zones mapped to the monitoring provider's markets (IBOPE "plazas").
  - Medium linked to the external interface in the Media master's Interface tab.

#### P-SV-02 Import monitoring file `[mp301449 + guides]`
- **T:** Daily. The monitoring vendor delivers airing logs for the agency's advertisers.
- **S:**
  1. Select the monitoring provider.
  2. Set options: "exclude clients" and "do not associate materials".
  3. Import and pick the file.
  4. If exclude-clients is on, review the list of clients found in the file and mark non-agency clients for exclusion from future imports (`Grabar Clientes Excluidos`). This is useful when the file is unfiltered.
  5. If channel codes are unmapped, the system lists "chains not associated". Fix this in External Providers → Media tab: enter the provider's medium code in `Cód. Int. 04`. Then in Media → Interface tab, select the provider line and the medium; the code is propagated.
  6. Map unknown **clients** (F2 lookup of holder clients) → `Grabar Clientes`.
  7. Map **products** (the client comes from step 6) → `Grabar Productos`.
  8. Map **materials** (filtered by matching duration) → `Grabar Materiales`. Skipped when "do not associate materials" is set.
  9. The system reports "import finished successfully".
- **Maintenance:**
  - **Links:** review or remove code associations per entity.
  - **Spots:** a calendar of dates with imported spots, with previous/next month navigation. **Delete** all imported spots for a given date.
- **File format:** the monitoring file must contain certain mandatory columns, which the manual does not list. The agency name must be set in the external provider, and medium names must match the vendor's naming. Example vendors: Monitor (Argentina), Ibope.

#### P-SV-03 Automatic control
- **S:**
  1. Filters:
     - Date from/to.
     - Spot status: verified / unverified / all.
     - Criterion: one order (month/year + order no.), all clients, one plan, one medium, client + medium, a duration, or a version (then media type).
     - Provider.
     - Client division (when criterion = client).
  2. Automatic block: source directory, tolerance minutes, and options **match material** (otherwise match by duration/measure only), **match program** (otherwise by time only), **match publication type**.
  3. Press **Automatic control** and choose **Normal** or **With tolerance**.
- **Matching results:**
  - **Exact single match:** row turns green; the default audit code is assigned; actual air time, break number, and position in break are stored.
  - **Multiple candidates:** fields underlined; the user clicks the row and picks the right imported record from an "air time" combo.
  - **Ordered but not in the file.**
  - **In the file but not ordered.**
- Results feed the plan's Audit tab.

#### P-SV-04 Manual control, spot by spot
- **S:** Filters → Start → click each spot → Detail tab: audit code (the controller's user is recorded), optional air time, break no., position in break, observations → Save.

#### P-SV-05 Bulk/summary control (e.g. radio paper certificates)
- **T:** The vendor certifies a count, e.g. 98 of 100 planned spots aired, without per-spot detail.
- **S:** Start → `Resumen` → choose the summary criterion: by medium, client, program, measure, or material → enter the quantity in the "uncontrolled" column → press **Control OK** or **Control deficient** → Save.
- **Recommended practice:** mark only the **failed** spots as deficient, which lets the planner reschedule them. Leave the rest unverified; at order close they become "aired OK" automatically. Which specific spots are marked failed is arbitrary in bulk mode.

#### P-SV-06 Remove a control
- Select the controlled spots → `Eliminar Control` → confirm.
- **Not allowed on a closed order.**

#### P-SV-07 Publisher spot control `[mp301441]`
- Manual only.
- Filters: month range, criterion (advertiser, billing client, holder client, product, magazine, seller, all), publication type, status (only client-approved, or all).
- Grid: date, order no., item, internal request no., advertiser, product, seller, magazine, location, observations, publish-from, material.
- Selecting rows and saving stamps the **"OK Arte"** column with the controlling user.

#### P-SV-08 Manual order-state workflow `[mp302788]`
- Enabled by config `Usa Gestión Manual de Estados`.
- Master of control states, defined per agency department. Each state has an auto sequence code, a description, and a responsible user.
- Orders move between users as each department assigns its state.
- At client billing, the system checks that orders are in the state set by config `Facturar si estado manual es igual a`.
- In order lists, orders under manual management show in **blue**.

### 2.5 Digital ad-server costs `[mp302857]`
- **Prerequisites:** AdServers and tracking types exist in the masters.
- **S:** New → ad server → client (one or all) → start date (defaults to the current month) → for each tracking type, a **cost** (shown on the vendor order) and a **sell price** (shown on the client schedule) → Save. CRUD.

### 2.6 Overcommissions / rebates `[mp302730, mp302734, contrato-de-overcomisiones-cen, mp301192, mp302911]`

#### P-OC-01 Define overcommission contract types `[mp302734]`
- **Fields:** auto code; origin (**Media** or **Production**); description; **income GL account** (only observation codes 23 Bonuses, U4 Vendor commissions, 20 Agency service fees are selectable); **client-rebate GL account** (codes 23, 20, U7).
- Can be deleted only if never invoiced.

#### P-OC-02 Create an overcommission contract `[mp302730]`
- **Prerequisite accounts:**
  - U4: vendor commission income. Mandatory, kept separate from ordinary agency income.
  - 23: media bonuses. Used when the vendor issues a credit note.
  - U7: rebate to clients of vendor commission.
  - **PO:** overcommission billing provision.
  - **PD:** client-rebate provision.
- **Main data:**
  - **Provider** = contract holder, one per contract. The legal entity affected by the result.
  - Auto code, description.
  - Status: active or annulled.
  - **Start and end dates** (mandatory).
  - **Calculation base:** gross or net order spot value. The definition varies by country.
  - **Currency.** Orders in other currencies are converted for scale and cap evaluation. If the currency is foreign, a **fixed rate** option (single rate for local purchases) is offered; otherwise the rate at pending-generation time is used.
  - **% reduction:** deducted from the purchased amount before calculation, e.g. to mirror withholding taxes the vendor suffers.
  - **Contract type.**
  - **Calculation type** (5 preloaded; see BR-OC).
  - **Scales:** from, to, % or amount. An empty "to" means unbounded.
  - **Limit amount:** cap on total commission.
  - **Deduct vendor commission:** whether plan-level vendor commission % is subtracted from the base.
- **Clients tab:** include or exclude mode; holder clients, then optionally specific products per client.
- **Publication types tab:** include or exclude mode plus a list.
- **Billing tab:**
  - **Billing type:** *agency issues invoice* to the vendor, or *vendor issues credit note* (netted against payments or paid).
  - **Generation order:** when several contracts exist with the same vendor, the sequence in which they apply. Later contracts subtract commissions already computed by earlier ones from their base.
  - **Cut-off period:** for every month of the contract, mark **Bill** or **Provision**. Bill months allow invoicing (or leaving pending and provisioning). Provision months are provision-only. This supports billing cycles from monthly to annual while recognising income monthly. **The last contract month must be Bill.**
  - **Opening criterion:** a grid of medium and billing client of the contract.
- **Client rebates tab:** per client, the rebate type is **Total**, **Partial %** (a % of the computed commission, "on billing"), or **Partial fixed amount**. The default is stored on the holder client. The **document type** to issue to each client is chosen per client. The options mirror the vendor side, with the agency acting as the supplier.
- **Divisions tab:** the agency division that receives the income, or default from the campaign.
- **Media tab:** media of the vendor covered. Default is all.
- **Buttons:** New, Query (by provider), Copy, Save, Modify, Delete (only if not invoiced), **Annul** (only if not invoiced), Cancel.
- **Downstream (other modules):** "Generate overcommission pendings" → "Overcommission billing" (invoice to vendor) or provision → "Mark overcommission rebates as invoiced" to cancel a pending.

#### P-OC-03 Centralized (consolidated group) contracts
- **Prerequisites:** centralized master administration and centralized overcommission contract types enabled. Contract types are created in the consolidated database and propagate to all subsidiaries. The holder clients and vendors must not be restricted in any subsidiary. The contract type must be associated in the consolidated database.
- An extra tab selects the subsidiaries the contract applies to.
- **Rules:**
  - Create, modify, and delete only in the consolidated database; subsidiaries are view-only.
  - A provision month blocks billing in every subsidiary; a bill month leaves a pending in every subsidiary.
  - Exclusions of clients or products that don't exist in a subsidiary are silently ignored there.
  - Each subsidiary bills or provisions only its own pending; the consolidated entity cannot bill or provision.
  - A consolidated overcommission order list across subsidiaries is available.

#### P-OC-04 Incentive scale (Colombia) `[mp301192]`
- Colombian name for a volume-discount scale billed to media vendors, **computed on registered supplier invoices**.
- **Fields:**
  - Provider (the party invoiced).
  - Client: a specific client or **AGC – Agency** for total agency spend. The manual says the scale works only on total agency investment, not differently per client, which partly contradicts the client field; see Gaps.
  - Description.
  - Excluded client (separately negotiated).
  - Validity: none, or start/end.
  - Scope: media type, medium, publication type of that vendor.
  - **Scale size:** number of brackets.
  - Grid: % and "from". "To" is auto-set from the next row's "from"; the last bracket is unbounded.
  - "Not included": exclusions of billing clients, media, publication types, with type-ahead and a select-all header click.
- **Use:** after supplier invoices are registered, run "Incentive billing to providers" (another module).

#### P-OC-05 Finder-fee contracts `[mp302911]`
- A commission **payable** to an intermediary or facilitator for bringing business.
- **Fields:** client, media type, contract no., description, active flag + period, **calculation type: on net investment or on client profitability**, negotiated %, observation, **expense concept / expense GL account**, currency.
- **Downstream:** generate finder-fee pending → issue invoice. The direction of that invoice is unclear; see Gaps.

### 2.7 Import/export `[mp309243, mp301246, importacion-y-exportacion-de-p]`

#### P-IE-01 Export orders
- Document: **orders** or **cancellation requests** (`Pedidos de anulación`).
- Filters: billing or holder client; date type (order month or spot airing day) + range; currency format/currency; **status: Issued or Sent**.
- Grid: month, order, schedule, plan, JobNumber, medium, provider, holder client, product, amount, FX amount, client number, **electronic order ID**.
- Select rows → `Interfaz` sends them to the configured target.
- Purpose-built interfaces exist for **Caracol and RCN (Colombia)** and for specific advertisers or agencies.

#### P-IE-02 Import/export with advertisers
- The help page is missing ("AYUDA INEXISTENTE").

#### P-IE-03 Plan import/export (menu only, owned by planning)
- Schedule export, master import, and schedule import for contracts, clients, products, providers, media, schedules, and zones, plus external interfaces. Contract import implies contracts can be loaded from external files.

---

## 3. Entities

| Entity (ES / EN) | Key fields | Identifier | Relationships |
|---|---|---|---|
| `Tarifario` / Rate card | criterion (media type / medium), medium, holder client (null = printed/general), description, version, valid from/to (to optional), currency, calc type, per-program vs per-band, time-band config, reference CPP, base card + coefficient, publication type, target + book (CPR), internal/external observations, last modified | card code + version | 1 medium; 0..1 client; 0..1 base card; N rate lines; referenced by contracts (by date range) and plan items |
| Rate line | program/location (or band), broadcast days, start/end time, genre, program type, publication type; **order**: gross, d1–d4, net; **schedule**: gross, d1–d4, net; digital: platform, format, size, calc type, default flag | card + program + pub type | belongs to rate card |
| `Clave de Tarifa de Proveedor` / Vendor tariff key (MX) | provider, code, description | code | selected on rate card |
| `Contrato de Compra` / Buy contract | client (billing or Agency), medium or provider, media type, number, description, active, from/to, type (Normal/Barter), consumption (Amount/Seconds-cm), control (Cap/Free), measure cap, net balance, with/without VAT, payment condition, term, currency, fixed FX + rate, gross amount, client d1–d4, % agency commission, discount application criterion, `Pasa por agencia` (CO), default discounts, surcharges (code, %, accumulation, value), share restrictions, confidential (flag, mechanism, %, % per pub type), assigned billing clients/products, rate type, calc type (Rate/CPR), rate cards by date range, installment data (billing client, provider, unit, advance %, schedule of installments), kind (Normal/Parent/Child) + parent, external codes | contract no. (+ subcontract no.) | 1 client, 1 medium; N children; N installments → generated plan + schedules; N adjustments/transfers; consumed by order items |
| Installment (`Cuota`) | number, date, gross amount | contract + no. | generates a schedule (pauta) in Pending status |
| `Ajuste de Contrato` / Contract adjustment | month, adjustment no., in favour of (Agency/Medium), client, provider, medium, contract, subcontract, schedule, order, balance, amount, description | month + no. | contract current account |
| `Transferencia entre Contratos` | month, no., origin (client, medium, contract, sub), destination (client, contract, sub), amount, description | month + no. | two contracts |
| `Orden de Publicidad` / Insertion order | month/year, order no., version/revision, schedule (pauta), plan, JobNumber, medium, provider (vendor), holder and billing client, product, material, contract, publication type, payment condition to vendor, currency/FX, VAT flag, PO no. (investment) + date, PO no. (agency commission) + date, footer notes 1–3 + model, status (open/closed; issued/sent; deleted; cancellation request), delivery date, electronic order ID, manual-management state, conciliation status (MX), approval flags (credit limit, client, to bill) | month + order no. + version | N items; N spots; linked to supplier invoice(s), client invoice(s) |
| Order item | item no. (never reused), ad/publication type, description (25 chars), program/location, days, number of spots, rate, measure/duration, discounts (and credit-note discounts), surcharges, gross, discounts, subtotal, net, barter spaces, tax attributes, direct/indirect flag | order + item no. | N spots |
| Spot (`Aviso`) | date, scheduled start/end, duration, material/version, status (scheduled/ordered/billed/rejected), control status (aired/failed/uncontrolled + custom), audit code, actual air time, break no., position in break, controller user, observations, rating | plan item + date + seq | 0..1 imported monitoring record |
| `Código de Auditoría` / Audit code | code, description, OK/deficient semantics, media types | code | spot control |
| Monitoring import record | provider, date, channel code, client code, product code, material code, duration, air time, break, position | provider + date + row | mapped via code links to medium, client, product, material |
| Code link (`Links`) | entity type, external code, internal ID | — | external provider ↔ masters |
| Manual control state | sequence code, description, department, responsible user | code | orders |
| AdServer cost | ad server, client (or all), start date, per tracking type: cost, sell price | ad server + client + date | digital plan/order items |
| Overcommission contract type | code, origin (Media/Production), description, income account, rebate account | code | contracts |
| `Contrato de Overcomisión` | provider (holder), code, description, status, from/to, base (gross/net), currency, fixed FX + rate, % reduction, type, calc type, scales [from, to, %/amount], limit amount, deduct vendor commission, client incl/excl + products, pub type incl/excl, billing type (invoice / credit note), generation order, monthly cut-off flags (Bill/Provision), opening grid (medium × billing client), client rebate per client (type, %, amount, doc type), division, media, subsidiaries (centralized) | code | N order calculations (contract × month × generation order) |
| Overcommission order record | order, contract, calc month, generation order, base, commission, rebate, state (pending, invoiced, annulled, provisioned, inactive) | order + contract + month | invoice/credit note; provision entries |
| Incentive scale (CO) | provider, client or AGC, description, excluded client, validity, media type/medium/pub type, size, [%, from, to], exclusions | provider + id | supplier invoices |
| Finder-fee contract | client, media type, no., description, validity, calc type (net investment / profitability), %, observation, expense concept, currency | no. | pending → invoice |
| Masters referenced | media, media types, publication types, programs/locations, time bands, targets, genres, external providers, interface types, zones, external markets, materials, duration coefficients, surcharges, default surcharges, media discounts, agency service, additional costs, order-modification reasons + categories, internet platforms/formats/placements/calc types/tracking types/buy types, AdServer, units of measure | — | `[maestros-de-medios]` |

---

## 4. Document lifecycles

### 4.1 Rate card
Draft header → lines entered → **active** within validity → (optional) superseded by a new version or copy → may be deleted **only if unused**. Base-card edits cascade to derived client cards.

### 4.2 Buy contract
Created (active flag Yes) → [installments: plan and schedules auto-generated in Pending, billable] → consumption by order items (amount or seconds, with or without VAT) → adjustments (± in favour of agency or medium) and transfers (out/in) → expiry by date or active = No.
Delete is allowed only if never billed. A child contract consumes from the parent's current account.

### 4.3 Schedule spot (from the order's perspective)
`pautado` (scheduled) → `ordenado` (ordered: black in the draft order, blue in the plan, locked) → verification: aired / failed / uncontrolled → order closed (uncontrolled spots become aired with the default code) → client billed (`facturado`). A spot can also be `rechazado` (rejected).
Failed spots are candidates for **rescheduling** (makegood) in the plan. The makegood itself is done in planning.

### 4.4 Insertion order
```
Draft (spots selected) → Saved/Issued (number assigned, version 1)
   → Sent (printed / PDF / email / interface)  [export filter: Issued vs Sent]
   → Modified → new version (Mod.Rev.) with optional "cancels & replaces" legend
        (no new version if not yet sent)
   → [Deleted: releases spots; shown red in lists]
   → [Cancellation request (Pedido de anulación) exported to vendor systems]
   → Closed (after verification) ⇄ Reopened (only if no supplier invoice and month schedules not closed)
   → Supplier invoice registered (requires Closed) → locked
   → Delivered (delivery date recorded, closed orders)
```
Publisher variant: Saved → Approved credit limit → Approved by client → Approved to bill → Billed. Rejected and recovered while not billed. Delete is blocked once client-approved or bill-approved. Every save creates a revision when `Modifica Revisión` is checked.

### 4.5 Certification and matching to the supplier invoice
- Certification = spot verification (manual, automatic, or bulk), recorded per spot with an audit code, plus close.
- The payments report shows per order: **whether it is certified and the date**, the **certification code**, the **supplier invoice number**, and the **payment date**. It can show the real vendor or an intermediary vendor `[mp302858]`.
- Matching rule: a supplier invoice can only be registered against **closed** orders. Registering it blocks reopen. Removing it (cancelling the invoice) is needed to reopen.
- The Mexican complete order list adds a **conciliation status** filter, and the planning menu has "TV Azteca automatic reconciliation". This implies an order↔vendor-statement reconciliation process; its detail is out of this file.

### 4.6 Overcommission
Contract active → orders within validity and scope → **Generate pendings** (per contract × month × generation order) → each month either **Provision** (income accrued, PO account; client rebate accrued, PD) or **Bill** (agency invoice to vendor → U4/23/20 income; or vendor credit note → 23) → client rebates issued per client document type (U7/23/20) → "mark rebates as invoiced" to cancel a pending.
Contract-level: Annulled or Deleted only if nothing has been invoiced. Report states: pending, invoiced, annulled, provisioned, inactive.

---

## 5. Business rules and calculations

**Rate cards and pricing**
- **BR-T-01 Flat rate:** item cost = rate × measure × spots, or rate × standard measure × spots. For TV/radio flat cards the rate is per second: cost = duration_sec × spots × rate_per_sec.
- **BR-T-02 CPP:** cost = duration × spots × CPP × program_rating (as stated by the guide). The concept text instead says cost = rate × rating points of the item. Requires a book/ranking on the plan and ratings loaded on the programs.
- **BR-T-03 CPM** (TV/radio, and digital as "CPM/CPV visits"): cost = (impressions / 1000) × rate. Implied; no formula given.
- **BR-T-04 Guaranteed CPP:** listed with no formula.
- **BR-T-05 Digital:** gross rate with discounts; CPC = clicks × rate; CPV = (visits/1000) × rate; CPA = actions × rate; custom types from the master. The calculation type is stored per item.
- **BR-T-06 Dual price sets:** every rate line has an *order* (buy) gross + 4 discounts and a *schedule* (sell) gross + 4 discounts, each yielding a net.
- **BR-T-07 Coefficient copy:** target_rate = source_rate × coefficient (default 1). Used for duration non-proportionality or uplift.
- **BR-T-08 Base-card inheritance:** a client card with `Usa Tarifario Base` keeps the base gross rate read-only and adds its own discounts. Base changes propagate.
- **BR-T-09 Rate precedence:** a client-specific card overrides the printed card for that client and medium/provider. A contract can pin which card applies per date range.
- **BR-T-10 Validity:** a plan date outside a card's validity yields no rate.
- **BR-T-11 Mass "apply amount"** may be entered as gross or net. If net, the gross must be back-solved; the method is not stated.
- **BR-T-12 Automatic ordering without a card:** buy price = sell price.

**Discounts and surcharges**
- **BR-D-01** Up to **4 sequential discounts** per price set (client on contract or schedule; vendor on order).
- **BR-D-02 Cascade:** the manual doesn't state the formula. The conventional and recommended default is multiplicative: net = gross × Π(1 − dᵢ). The contract's `Criterio Aplicación` suggests an alternative mode exists (e.g. additive: net = gross × (1 − Σdᵢ)), or a mode that sets whether contract discounts replace or add to card discounts. Make this configurable.
- **BR-D-03** Surcharges carry a %, an **accumulation** flag, and a value. A reasonable reading: accumulative surcharges compound on the running subtotal, non-accumulative ones apply on gross.
- **BR-D-04 Credit-note discounts** (`Descuentos N/C`) are tracked separately from invoice discounts: Subtotal = Gross − Discounts; Net = Subtotal − Credit-note discounts. Billable and barter totals are reported separately.
- **BR-D-05** Discounts on items with a contract are editable only if config `Permite modificar descuentos en ítems con contrato` is on.

**Contracts**
- **BR-C-01** Balance = gross amount − Σ consumption ± Σ adjustments − transfers out + transfers in. Consumption counts item amounts **with or without VAT** per the contract flag, or seconds when consumption is by seconds.
- **BR-C-02 Cap control:** consumption must not exceed the cap. Free consumption has no cap.
- **BR-C-03** Free-consumption contracts force the cash payment condition. Installments are only possible with a cap.
- **BR-C-04 Installments:** advance = gross × advance%. Default n = months in validity, each installment = (gross − advance)/n. User edits allowed subject to **advance + Σ installments = gross**. One schedule per installment, status Pending, billable immediately. The rounding remainder is not specified; put it in the last installment.
- **BR-C-05** Children have no cap; they consume the parent balance.
- **BR-C-06** Adjustments in favour of the agency create no client pending. By implication, adjustments in favour of the medium may create one; not stated.
- **BR-C-07** A transfer requires a different destination client + contract than the origin.
- **BR-C-08** An agency-client prepaid contract means ordering against it books **zero cost**.
- **BR-C-09 Share validation:** Σ(order spend at medium within scope) / Σ(total relevant spend) ≥ the global share %, and per band or per day % when configured. The denominator is not defined; see Gaps. The planning menu has `Control de Share por Contrato`.
- **BR-C-10 Confidential discount:** % (optionally per publication type) of qualifying spend, settled by agency invoice to the vendor or by vendor credit note.
- **BR-C-11 Currency:** a foreign-currency contract can fix an FX rate for converting local-currency consumption; otherwise the transaction-date rate applies.
- **BR-C-12** Delete a contract, adjustment, transfer, or contract type only if not billed or invoiced.

**Orders**
- **BR-O-01** An order belongs to exactly one medium and one vendor. A schedule with several media yields several orders.
- **BR-O-02 Mandatory gates (configurable):** client approval of the plan/order; credit limit, where ordering is allowed only if order amount + client AR balance ≤ credit limit, or the excess is approved.
- **BR-O-03 Split keys:** medium, provider, publication type, material, contract, VAT rate, item, day/date range, spot.
- **BR-O-04 Edit authority:** cost, discounts, taxes, notes, and vendor on the order; structural attributes on the plan only.
- **BR-O-05** Order rate and discount edits are allowed only on **indirect** items and for clients **without in-system audits**.
- **BR-O-06 Versioning:** a modification of a sent order creates version n+1 with an optional "cancels and replaces" print. An unsent order can be re-issued without a version bump.
- **BR-O-07** Item numbers are never reused.
- **BR-O-08 Close:** required before supplier invoice registration. It auto-certifies uncontrolled spots with the default audit code. Close is irreversible once a supplier invoice exists.
- **BR-O-09 Reopen** requires no supplier invoice and month schedules not closed.
- **BR-O-10** A vendor change requires the new vendor to be linked to the medium.
- **BR-O-11** The vendor payment condition defaults from the provider master and can be overridden per order. In the publisher variant, the client payment condition comes from the billing client or the client/product.
- **BR-O-12 Multi-billing:** an opening code splits billing among billing clients by participation %.
- **BR-O-13** Client billing gates: `Aprobada para Facturar` when configured; manual state = the configured state when `Usa Gestión Manual de Estados` is on.

**Spot verification**
- **BR-V-01 Normal match:** actual air time ∈ [item start, item end].
- **BR-V-02 Tolerance match:** actual air time ∈ [item start, item end + tolerance_min].
- **BR-V-03 Match keys:** medium (via code link), client, product, date, time window, plus material (if "match material", otherwise duration/measure), program (if "match program", otherwise time only), and publication type (optional).
- **BR-V-04 Classification:** unique match → auto-certify with the default code and copy air time, break, and position; multiple → user disambiguation; ordered-not-aired; aired-not-ordered.
- **BR-V-05** A control cannot be removed on a closed order.
- **BR-V-06 Bulk control** marks N spots OK or deficient in a summary group without identifying them.

**Overcommissions** (all amounts converted to the contract currency)
- **BR-OC-00 Base:** B = Σ qualifying order item amounts (gross or net per contract) within validity and scope (vendor; media; clients and products incl/excl; publication types incl/excl) × (1 − %reduction) − [vendor commission if "deduct vendor commission"] − [overcommissions already computed by contracts with an earlier generation order].
- **BR-OC-01 Fixed % without scales:** C = B × p. Example: 1,500 × 5% = 75.
- **BR-OC-02 Value scale (fixed amount per bracket):** C = amount of the bracket containing B. Example brackets 1,000–1,999 → 100; 2,000–4,999 → 250; 5,000–6,999 → 350; ≥7,000 → 500. B = 5,500 → 350.
- **BR-OC-03 % scale, absolute (slab):** C = B × p(bracket containing B). With 2/3/5/7%: 1,500→30; 3,000→90; 5,500→275; 8,000→560.
- **BR-OC-04 % scale, marginal:** C = Σ over brackets of (portion of B within bracket) × bracket p. The first bracket is taken from 0, not from its lower bound. With 5/3/2/1% at thresholds 2,000/5,000/7,000: 3,000 → 2,000×5% + 1,000×3% = 130; 5,500 → 100 + 90 + 10 = 200; 8,000 → 100 + 90 + 40 + 10 = 240.
- **BR-OC-05 % scale, stepped increments:** C = B × p₁ + Σ_{k≥2, B>from_k} (B − from_k) × (p_k − p_{k−1}). With 2/3/5/7%: 3,000 → 60 + 10 = 70; 5,500 → 110 + 35 + 10 = 155; 8,000 → 160 + 60 + 60 + 20 = 300. This is algebraically the same as a marginal bracket computation using each bracket's own rate. See Gaps.
- **BR-OC-06 Limit:** C = min(C, limit amount) when a limit is set. Whether the limit is per contract period or per month is not stated.
- **BR-OC-07 Monthly recognition:** commission is computed each month. Months flagged Provision accrue only; Bill months allow invoicing. The last month must be Bill. Implied: cumulative scales should be evaluated on cumulative-to-date base, with each month's commission = C(cum_to_month) − C(cum_to_prev_month). The manual doesn't state this explicitly; see Gaps.
- **BR-OC-08 Retroactivity:** a contract signed mid-period can cover past orders. Pendings are generated retroactively.
- **BR-OC-09 Client rebate:** Total → R = C; Partial % → R = C × r (the source also mentions "on billing"); Partial fixed → R = fixed amount. Issued per client with the selected document type.
- **BR-OC-10 Incentive scale (CO):** a % by bracket of investment on **registered supplier invoices**, per vendor, optionally scoped. "To" is auto-derived and the last bracket is unbounded. Whether it is slab or marginal is not stated; slab is the likely reading.
- **BR-OC-11 Finder fee:** F = % × (client net investment) or % × (client profitability).

**Currency and FX**
- **BR-FX-01** Lists offer **Multicurrency** (original currency + an FX-amount column, totals per currency) or **Consolidated** (original amounts + a column converted at the applicable rate).
- **BR-FX-02** The dynamic report consolidates at a rate "at date" or "fixed rate", with a manual or automatic quotes grid. The commission summary uses either the month-end rate or a single rate.

**Rounding**
- **BR-R-01** The rate card "Round" button removes decimals from gross rates. Precision and mode are unspecified.

**Taxes**
- **BR-TX-01** Order items carry tax attributes. Orders can be split by VAT rate. Orders and contracts can be flagged without VAT. Lists can show amounts with VAT. Withholding taxes are reflected indirectly via the overcommission % reduction.

---

## 6. Accounting impacts

- **Overcommission income:** posted at billing or provision to the contract type's income account. Allowed observation codes: **U4** (vendor commissions; mandatory dedicated account), **23** (media bonuses, used when receiving vendor credit notes), **20** (agency service fees).
- **Client rebates:** posted to the contract type's rebate account (**U7** rebate of vendor commission to clients, or 23/20).
- **Provisions:**
  - **PO** (overcommission billing provision): monthly accrual of rebate income not yet invoiced, because vendors often settle semiannually or annually while the income belongs to each month.
  - **PD** (client-rebate provision): accrual of the amount owed back to clients.
  - Implied pattern: Dr receivable/provision asset (PO) / Cr income (U4); on invoicing, reverse the provision and post the real receivable.
- **Contract installments and transfers:** require **balance-sheet (patrimonial) accounts with observation codes**, with restricted manual posting, currency, and balance sensitivity. Installment billing to the client before media consumption implies a client advance or deferred liability. The specific codes are not given in this file.
- **Finder fee:** posted to a selected **expense concept / expense account**.
- **Order close** is the control point that lets accounting register the supplier invoice. Media cost recognition happens at supplier invoice registration, in AP, outside this file.
- **Confidential discounts:** settled by agency invoice to the vendor or vendor credit note. The accounting codes are not given; likely the same 23 / U4 family.

---

## 7. Cross-module handoffs

| From → To | Object handed off | Trigger / gate |
|---|---|---|
| Masters → Buying | media, pub types, programs, time bands, audit codes, external providers, surcharges, discounts, modification reasons, digital taxonomies | setup |
| Buying (rate cards, contracts) → Planning | buy and sell rates, default discounts and surcharges, contract assignment, share rules, `Pasa por agencia` (CO), installment plan auto-creation | plan item pricing |
| Planning → Buying | approved schedule (pauta) spots | client approval + credit-limit approval |
| Buying → Vendor | insertion order (print/PDF/email/interface Caracol/RCN), cancellation requests, versions | issue/modify |
| Monitoring vendor → Buying | daily airing files (Monitor, Ibope) | import + code mapping |
| Buying → Planning | audit tab results; failed spots → rescheduling/makegood | verification |
| Buying → AP (supplier invoice reception) | closed orders, certification status | close (mandatory before invoice) |
| AP → Buying | supplier invoice no. and payment date (payments report); invoice locks reopen | invoice registration |
| Buying/Planning → AR (client billing) | schedules (incl. installment schedules), billable flags, approved-to-bill, manual state check, multi-billing opening codes, client PO numbers | billing run |
| Buying → Overcommission billing | qualifying orders → pendings → vendor invoice / credit note; client rebates | pending generation |
| AP (registered supplier invoices) → Incentive billing (CO) | invoice base | after registration |
| All → GL | income U4/23/20, rebates U7, provisions PO/PD, balance-sheet accounts for contracts, expense for finder fee | posting |
| Consolidated DB → Subsidiaries | centralized contract types and contracts | centralized config |

---

## 8. Configuration and country-specific behaviour

**Special configurations named in the source:**
- `Código Auditoría por defecto en Cierre de Orden` (Billing branch): the default "aired OK" code for auto-match and close.
- `Usa Gestión Manual de Estados` + `Facturar si estado manual es igual a`.
- `Elige Job en Contrato de Cuotas`.
- `Permite modificar descuentos en ítems con contrato`.
- `Numero de Pedido de Cliente Mensual`.
- `Tarifas de Internet por Formato y Medida`.
- `Comisión Proveedores` (must not be "Not used" for the vendor commission list).
- Client approval required before ordering; approval required before billing; credit-limit control.
- Centralized master administration + centralized overcommission contract types (consolidation).
- Rate card import via interface (per agency).

**Country behaviour:**
- **Mexico:** Televisa vendor tariff keys; order conciliation status filter; TV Azteca automatic reconciliation and Azteca Online user assignment (planning menu).
- **Colombia:** `Pasa por agencia` on contracts; incentive scales; order interfaces with Caracol and RCN.
- **Chile:** ServiBanca program-grid Excel download/upload for rate updates.
- **Argentina:** Monitor as a monitoring source. Ibope is mentioned generically for radio markets.
- **Country-dependent:** contracts are signed with a medium or with a provider; the definition of gross vs net for overcommission bases varies.

**File and interface formats:**
- Monitoring file with mandatory columns (unspecified), mapped by external codes (`Cód. Int. 04`).
- Rate card import (agency-specific); Chile Excel round-trip.
- Order export via programmed interfaces; electronic order ID field.
- Reports export to Excel, HTML, PDF, and text.
- `NotaEspecial.txt` server file for printed conditions.
- Email via the local mail client.

---

## 9. Reports and KPIs

| Report | Purpose / key fields | KPI derivable |
|---|---|---|
| Basic order list `[mp301117_ejecutar]` | fast list; filters by date criterion (spot date vs creation), client/product/plan/Job, media type, zone, medium, provider, currency format, cancellation requests (exclude / last only / deleted only), contracts, direct/indirect, barter/installments/bonus/prepaid (exclude/include/only), without PO, only issued, exclude "only to order", exclude additional costs; optional columns: client invoice, supplier invoice, extra details, subtotals by medium, amounts with VAT, client product code; red = deleted, blue = manual state | orders issued, open vs closed, uninvoiced closed orders |
| Complete order list `[mp301117_ejecutar_completo]` | multi-select media types/providers, open/closed status, MX conciliation status; mass close/open, deliver, PO number, print variants, dynamic report | close cycle time, delivery compliance |
| Schedules and orders list `[mp301162]` | schedules with their orders; filters: exclude installment schedules, only closed, schedule status (ordered/issued), non-billable, fees, control status (OK / deficient / uncontrolled); save default filters | % spots certified, failure rate |
| Rate list `[mp305167]` | rates by medium/type/general, client vs printed, validity month, pub type, genre, program type, non-zero, order vs schedule view, time bands; shows contract discount for client × medium | rate inflation, negotiated discount depth |
| Contract list / Contract current account | initial / consumed / current balance; movements | contract burn rate, % consumed vs time elapsed |
| Efficiency list `[mp303014]` | audit of orders by date, holder/billing client, providers; customizable view | airing efficiency by vendor |
| Order modification efficiency `[mp302020_motivos_modif_orden]` | modifications by campaign with reason fields; pivot-like field selection | modification rate, reasons Pareto |
| Order payments report `[mp302858]` | certified flag and date, certification code, supplier invoice, payment date, real vs intermediary vendor | certify-to-invoice and invoice-to-pay lead times |
| Dynamic order report `[mp402832_4]` | ad-hoc pivot/grid; filters: spot date, plans (comma list), clients, provider, media type, currency, day state (billed/rejected/ordered/scheduled), spot control state, Job billing code; FX consolidation; templates; weekly scheduled offline run at 00:00; online queries blocked when costly | any |
| Overcommission order list `[mp302755]` | per order: overcommission, rebate, state, with sub-rows per contract × month × generation order; origin media/production; criterion client/provider; currency; state pending/invoiced | rebate yield % of spend |
| Overcommission contract list `[mp302867]` | contracts by activity date and provider, with their scales | — |
| Vendor commission list `[mp301120]` | commission % assigned in plans; by date or invoice; vendor or client; orders all/closed/open; pending to invoice, invoiced, pending assignment; division | uninvoiced commissions |
| Commission summary `[mp301652]` | summary by billing client; net or gross base; cut-off date; FX month-end or single rate | — |
| Dynamic overcommission report `[mp402832_10]` | states pending/invoiced/annulled/provisioned/inactive; division; origin | provision vs invoiced |
| Publisher reports | investment summary by ad type `[mp301447]` (direct, indirect, agency service, bonuses, other, VAT, total; grouped by account observation codes; charts), summary by client `[mp301448]` (ordered and share %), pending approval, activity | share of ad type, advertiser share |

---

## 10. Agentic-skill implications

### 10.1 Atomic jobs (candidate skills / tools)
1. `ratecard.create_header`: inputs are medium, client?, validity, currency, calc type, program vs band, base card + coefficient, or copy source + coefficient. Validates that masters exist.
2. `ratecard.upsert_lines`: per program or band; buy and sell gross + d1..d4. Returns nets.
3. `ratecard.bulk_apply`: modes `amount{gross|net}`, `discounts`, `copy{source, coef}` over a filter set (days, hours, genre, program type, validity, non-zero, digital platform/format/size).
4. `ratecard.resolve_rate(client, medium, program, pubtype, date, side)`: precedence is contract-pinned card → client card → printed card. Errors if out of validity.
5. `ratecard.import`: CSV or Excel adapters (Chile-style round-trip, vendor feeds, MX tariff keys).
6. `contract.create`: validates combinations (free → cash; installments → cap; child → parent exists; seconds → measure).
7. `contract.generate_installments`: deterministic split plus plan and schedule creation in Pending.
8. `contract.balance(contract_id, as_of)`: aggregates consumption (VAT flag, amount vs seconds), adjustments, transfers, children.
9. `contract.adjust` / `contract.transfer`: with guards (not billed; origin ≠ destination).
10. `contract.check_share(contract_id, period)`: global, by band, by day.
11. `order.generate(schedule_id, mode=manual|auto, split_keys, date_cutoff, overrides)`: gates are client approval and credit limit. Pricing comes from the rate card, falling back to the sell price.
12. `order.modify(order_id, changes, notify_vendor)`: enforces edit authority, the indirect/no-audit rule, and versioning ("cancels and replaces").
13. `order.send(order_ids, channel=pdf|email|interface)`: renders layouts (with values / commission breakdown / conduit / direct) and appends the special-conditions text.
14. `order.close` / `order.reopen`: auto-certify on close; reopen guards.
15. `monitoring.import(file, provider)`: parse, apply code links, queue unmapped entities for human mapping, apply client exclusion list, delete by date.
16. `verification.auto_match(filters, mode=normal|tolerance, keys)`: returns matched / ambiguous / ordered-not-aired / aired-not-ordered.
17. `verification.manual_mark` / `verification.bulk_mark(group, qty, ok|deficient)` / `verification.unmark` (not on closed orders).
18. `overcommission.compute(contract_id, month)`: base build + calc-type engine + limit + generation order + client rebates. Output is pendings flagged Provision or Bill.
19. `overcommission.post(pending_ids, action=provision|invoice|credit_note)`: builds journal lines with the PO/PD/U4/23/U7 mapping.
20. `incentive.compute(provider, period)`: on registered supplier invoices.
21. `finderfee.compute(contract, period)`.
22. `orders.export(filters, interface)`: Caracol and RCN adapters as plugins; cancellation requests.
23. `reports.*`: order list, contract current account, payments lead-time, overcommission ledger, modification Pareto, verification efficiency.

### 10.2 Deterministic calculations worth dedicated tools
- `net = gross × Π(1−dᵢ)`, with a configurable additive mode; surcharges with accumulation.
- Item cost per calc type: flat (rate × measure × spots; per-second × duration × spots), CPP (as configured: rate × rating [× duration × spots]), CPM/CPV ((qty/1000) × rate), CPC, CPA.
- Coefficient copy: `rate × coef`.
- Installment schedule: advance and equal monthly split with the remainder on the last installment; the invariant sum must equal gross.
- Contract balance aggregation.
- Credit check: `order_amount + ar_balance ≤ credit_limit`.
- Air-time window match with tolerance.
- Overcommission engines: fixed %, value scale, slab %, marginal %, stepped-increment %; limit; % reduction; vendor-commission deduction; sequential contract base reduction; monthly incremental on cumulative base; FX conversion with a fixed or transaction rate.
- Client rebate: total, %, fixed.
- FX consolidation views (multicurrency vs consolidated; month-end vs fixed).

### 10.3 Controls to encode
- Orders cannot be generated without plan client approval (configurable) and within the credit limit or with excess approved.
- Supplier invoice registration is impossible unless the order is closed.
- Closing uncontrolled spots auto-certifies them. The agent should **warn** and suggest verification first.
- No reopen after a supplier invoice exists; no control removal on a closed order.
- Delete rate cards, contracts, adjustments, contract types, and overcommission contracts only if unused or uninvoiced.
- Versioning is mandatory for sent orders. The vendor is notified on version change.
- Vendor change requires a medium↔vendor association.
- The last overcommission month must be Bill. Centralized contracts are editable only in the consolidated entity.
- Transfers require origin ≠ destination. Installment sums must reconcile.
- Manual state gate before client billing.

### 10.4 Exceptions and human-in-the-loop points
- Unmapped monitoring codes (channels, clients, products, materials) need a human mapping decision. The agent proposes fuzzy matches.
- Ambiguous auto-match (multiple candidates) needs a human pick.
- Aired-not-ordered spots: a possible vendor error or an unordered bonus spot. Flag for the buyer.
- Ordered-not-aired spots: propose a makegood or rescheduling, or a credit claim.
- Rate missing (out of card validity) needs a manual price.
- Contract cap exceeded or share restriction breached: escalate.
- Credit-limit breach: requires approval.
- Order modification after sending: decide whether to version and notify.
- Overcommission retroactive contract: regenerate pendings for past months; check already-invoiced months.

---

## 11. Gaps and ambiguities

1. **Discount cascade formula** is not stated (multiplicative vs additive), and the values of the contract's `Criterio Aplicación` are not listed. Surcharge "accumulation" semantics are undefined.
2. **CPP formula inconsistency:** the concept text says rate × rating points; the guide says duration × spots × point value × rating. A duration factor in CPP is unusual and may be an error in the guide. Guaranteed CPP and CPM have no formulas.
3. **Marginal vs stepped-increment overcommission types** give identical results to a progressive bracket computation with each bracket's own rate. The examples use different rate sets but the algorithm looks the same. It is unclear how either treats amounts **below the first bracket's lower bound** (the examples start the first bracket from 0 although it reads "1,000–1,999"). The value scale and slab types also don't define the result below the first bracket (assume 0).
4. **Monthly vs cumulative evaluation** of scales and **limit scope** (period vs month) for overcommissions are not specified. Neither are the "generate pending" algorithm and the provision reversal mechanics, which live in other modules.
5. **Client rebate "partial %"** says both "% of computed commission" and "calculated on billing". The base is ambiguous.
6. **Incentive scale**: the manual says it applies only to total agency investment, yet it has a client field and per-client exclusions. Slab vs marginal is not stated.
7. **Finder fee** direction: it is described as payable to an intermediary, yet the flow ends in "issue invoice". It is unclear whether the agency invoices or self-bills. The "client profitability" base is not defined.
8. **Share restriction denominator** (share of what total: the client's spend in the media type, the market, the period?) is not defined.
9. **Order list date criterion labels look swapped**: "Creation" is described as spot publication date and "Issue" as order creation date.
10. **Contract adjustment** consequences when in favour of the medium (client pending? AP impact?) are not stated. The balance-sheet accounts used by transfers and installments are not named.
11. **Monitoring file layout** (mandatory columns) and the **order export interface formats** (Caracol, RCN, advertiser interfaces) are not documented. The Import/Export to Advertisers page is missing.
12. **Special rate cards** (`Tarifarios Especiales`) is under construction. The digital rate card `Aprobar` button is undocumented, so a rate card approval workflow is implied but unspecified.
13. **Makegoods/rescheduling** are referenced (failed spots → reschedule; Academia video on modifications and rescheduling), but the mechanics are in planning, not here.
14. **Supplier invoice matching** (amount tolerance, partial invoicing, price variance handling between order net and invoice) is not described. Only the "closed order required" rule and the payments report are documented.
15. **Rounding** precision and mode for the Round button and for installments are unspecified.
16. **Mexican conciliation status** values and the TV Azteca reconciliation process are referenced but not described.
17. **Confidential discount** accounting and settlement timing (per order, per period?) are not described.
18. **Title mismatch:** the page `Reporte dinámico de Órdenes` is titled "dynamic report of overcommission orders" but its filters are plan/order-centric. Treat it as a generic order dynamic report.
19. **Publisher (Editora) variant** mixes sale and purchase concepts (advertiser, magazine, seller, quotes). Its relation to the agency buy-side order is unclear. It looks like a separate operating mode for publisher tenants.
