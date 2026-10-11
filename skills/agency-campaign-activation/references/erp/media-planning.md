# Media Planning (Planificación de Medios), Plan Import/Export, Planning Academy

> **Provenance.** Functional reverse engineering of a reference agency ERP, derived from its publicly accessible help documentation (reviewed 2026-10-11). Content is paraphrased and restructured; it is not vendor documentation, source code or an endorsement. Bracketed ids such as `[mp301010]` identify the source page used as evidence. Items marked *inferred*, *assumed* or listed under gaps must be validated with your own controller, tax adviser and system owner before they drive postings or payments.

Source: the reference ERP's help documentation (Spanish). All content below is paraphrased and restructured for an open-source agentic re-implementation. File references in `[brackets]` point to the original help page identifiers so reviewers can trace each claim. Spanish field names appear in backticks.

Note on the Academia pages (`conceptos-generales-de-planifi.html`, `planificacion-en-el-sistema.html`, `planificacion-de-tv.html`, `planificacion-de-radio-y-cable.html`, `planificacion-de-prensa_-via-p.html`, `reprogramaciones.html`, `reportes-e-informes.html`, `conceptos-generales.html`, `pasos-a-seguir.html`, `maestros2.html`, `proceso-de-planificacion.html`, `compra.html`, `taxonomia.html`): in the source these are video titles with durations only; no textual content was captured. Their topics (offline concepts, TV, radio/cable, press/OOH/other, rescheduling, reports; digital concepts, steps, masters, planning, buying, taxonomy) are covered by the functional pages described below.

---

## 1. Purpose and position in the end-to-end circuit

Media Planning is the stage where a client campaign (a `JobNumber` opened in the Accounts module) is turned into a priced, scheduled, approvable media budget, and where that budget becomes purchase orders to media vendors.

Upstream inputs:
- An open `JobNumber` (campaign/project) carrying billing client, product, work typology, division and billing code.
- Media master data (media types, media outlets, vendors, programs/placements, publication types, dayparts, zones).
- Negotiation data: rate cards (`Tarifarios`) and media purchase contracts (`Contratos de Compra de Medios`), including confidential vendor commissions.
- Audience data: rating books imported from external measurement providers, refined into rankings (`Rankeos`).

Core outputs:
- A media plan (`Plan de Medios`) split into monthly schedules (`Pautas`), each made of items (`Ítems`, one per program/placement + duration + publication type + rate) and spots per day (`Avisos`).
- Client approval record (by plan or by monthly schedule), optionally a credit-limit override approval.
- Insertion/purchase orders (`Órdenes de Publicidad`) to vendors, versioned.
- Material (creative) assignment per spot and traffic instructions to vendors.
- Post-airing control (spot verification against monitoring data), pre/post evaluation of ratings, and "approved for billing" status that releases spots for client invoicing.

Downstream consumers: Media Buying/Orders, Spot Control (`Control de Avisos`), Client Billing (Accounts Receivable), Vendor invoice registration (Accounts Payable), provider commission invoicing, contract consumption, Production (delivery notes), and analytics/reporting.

Position in the circuit: `JobNumber opened` -> **Book -> Ranking -> Plan -> Client approval -> (credit approval) -> Orders -> Materials/Traffic -> Spot control -> Post-evaluation -> Approve for billing** -> Client invoice / Vendor invoice / Order close with differences.

---

## 2. Process catalogue

Each process lists trigger, actor, ordered steps, inputs, outputs, state transitions, approvals, and source refs.

### P01 Create Rating Book (`Books de Rating`) [mp305040.html]
- Trigger: planner needs audience data for TV/Radio planning; typically refreshed periodically.
- Actor: media planner / research analyst.
- Preconditions: media outlet master linked to a media type and to an external provider media type; programs/placements (manual or imported from provider); external provider (`Proveedor Externo`) per media type; holder client (optional); external measurement markets (`Plazas Externas`).
- Steps:
  1. New book: description, media type, rating provider (must have an interface configured), measurement market(s), period (commonly the 4 weeks prior to today), optional client.
  2. Import tab: rating type (by program or by commercial break `Tanda`; program recommended for TV); select at least one target.
  3. Population tab (supplied by provider): target, total population (universe), minimum % of cases, total cases, sample.
  4. Start: system lists every program with rating per target, and averages per program, per weekday, and overall.
  5. Save. Optional actions: weight each media outlet to a defined factor (`Ponderar`), add more targets, export to spreadsheet, delete obsolete books (recommended periodically).
- Outputs: Book (programs x targets x ratings).
- Refs: [mp305040.html].

### P02 Import Rating Book from provider files [-importar-book-de-rating-.html]
- Preconditions: in the media master, the rating provider, market and provider media code are set.
- Steps: New -> description, media type, rating provider, measurement market, optional client -> choose origin (folder or files) -> define target handling: either update the target values from the file (`Actualizar Valores de Target`) or create a new target from the file data (universe, affinity, etc. editable) -> optional duration-weighted average (`Promedio ponderado por duración`, only when origin is a folder) -> optional bulk insert from a server folder for speed -> Start -> review/edit target in "New Target" window -> Save -> Start (import runs).
- Restrictions: only one market per import. Recommended data age: up to 4 weeks.
- Argentina note: ratings are supplied per break with a fixed duration; if break duration varies by program, weight by duration.

### P03 Rating Book for Discontinuous Market (Argentina only) [mp302747.html]
- Purpose: build a book for a market without periodic measurement by borrowing from measured markets that share programming (network repeaters).
- Steps: New -> media type (only those with rating), rating provider, measurement market, source book (via planning-files selector), source target auto-filled, description -> Base Markets tab: add rows (market, book, target) -> Programs tab: Start loads associated programs; remove unwanted -> Save.
- Rule: shared programs get the average rating across base markets (or the average for the time slot); programs local to the discontinuous market keep their last known rating.

### P04 Create Ranking (`Captura de Rankings` / `Rankings de Medios`) [mp301040.html, mp301051.html]
- Definition: a subset of a book filtered by up to two targets (planning target and negotiation target), media outlets, time window and programs. Mandatory for TV and Radio; Internet may be created without a book.
- With book:
  1. New -> With Book -> planning-files selector: media type; book filtered by client, rating provider, measurement market, rating type.
  2. Select media outlets from the book.
  3. Selection tab: planning target and negotiation target (same if book has one target); start/end hour; airing weekdays; include programs without rating (off by default); optional holder client; optional recompute affinity between the two targets (`Recalcular Afinidad`).
  4. Start -> program detail grid (audience, CPR, cost per thousand, affinity columns per target, toggled by clicking target name). Sort by any column, multi-sort, delete programs, recover last deleted or recover from original book.
  5. Associate a client `JobNumber` (must be open). System auto-loads negotiations and rate cards valid at that date.
  6. Rate-card tab: validity month/year, seconds to apply, net vs gross rate, publication type, currency, exchange rate if foreign.
  7. Optional "Select negotiations": per outlet, default vendor and default contract/rate card.
  8. Save. Consistency check available. Export/print.
- Without book (typical for digital/OOH): select media type and client -> search outlets by site or zone (no limit on count; similar names highlighted) -> Start -> placements grid by location and vendor -> associate JobNumber -> Save.
- Query-only ranking ("Rankeo de consulta"): same steps but without client; it is temporary and is deleted when the query window closes.
- Restrictions: cannot add programs not present in the book; cannot edit ratings inside a ranking.
- Refs: [-generar-rankeo-de-consulta-de-tv-.html], [-generar-rankeo-de-tv-.html].

### P05 Create Media Plan — generic header (`Planes de Medios`) [mp301002.html]
- Trigger: campaign approved internally; planner builds a budget proposal.
- Actor: planner (requires planning permission).
- Mandatory preconditions: open JobNumber; media type exists; outlets linked to media type with at least one vendor; publication types defined (e.g., break spot vs. product placement `PNT`).
- Optional preconditions: daypart (`Franjas`) configuration adjusted; rate cards; contracts (including confidential terms); targets; additional charges enabled.
- Header steps:
  1. New -> Plan. Main data: select JobNumber via client -> product -> campaign lookup. Billing client, product, work typology fill automatically (read-only). With permission, the plan number may be chosen (to reuse a number deleted by mistake).
  2. Media data: validity from/to (min 1 day per overview, 2 days per guides; max 12 calendar months), media type, topic (`Tema`, defaulted from JobNumber, should be made descriptive), optional client contact.
  3. Other data: client purchase-order number for the whole plan (`Nº Pedido cliente`) and per-month budget/PO number (`Nº presupuesto`) — referenced on invoices.
  4. Billing: division (defaults from JobNumber, applies to the whole plan); billing split code (`Código de Apertura`) when JobNumber billing code allows it; payment term in days (single value; editable only by access levels 1A/1B, and only if config allows); "order only" flag (`Solo Para Ordenar`: no client billing and no vendor invoice expected); allow mixing direct and indirect items; agency-fee calculation type; agency-fee %, or fixed amount; agency-fee discount % (`% Bonificación`); agency-fee billing mode `Junto` (same invoice as media) or `General` (separate later invoice; media must be invoiced first).
  5. Currency: default is the outlet's currency; another currency can be chosen; foreign currency requires a reference exchange rate per month (indicative only; actual rate applied at invoice time).
  6. Rating (TV, Cable, Radio): criterion Book, Ranking, or Manual; choose source via planning-files selector; Target 1 (planning, shown to client) and Target 2 (negotiation, used by vendor). Manual mode adds two free-entry rating columns per item without validation.
  7. Default negotiations: shows contracts and rate cards per outlet for this client.
  8. Budget/Objective: overall budget, TRP objective, optional detail grid by criterion (vendor or zone) x month amounts. Produces an achieved-vs-objective and surplus summary.
  9. Additional costs tab (only when special config enabled and publication types flagged): pick defined extra charges; at the end compute them over selected items with a percentage and choose to which vendors the order is sent.
  10. Confirm -> Visual tab opens.
- Body steps (Visual tab): add item (double-click empty cell or Item -> Add from programs help / Add from program list): outlet, vendor (defaults to the outlet's default vendor), program (manual or from imported list), publication type, unit of measure. Then per item: start/end hour, item purchase start/end dates, measure (seconds for TV/Radio/Cable; cm x columns for press; circuits/boards for OOH), spots per date in the day grid, rate type (Normal/Package), rate/amount, discounts/surcharges. If programs were imported, only their airing days are selectable.
- Detail tab per item: vendor (changeable only while not ordered), currency, publication type (one per item), billing type (Billable/Bonus/Barter), direct vs indirect, agency fee applies (checkbox), VAT applies (checkbox, default on), vendor commission, contract and rate card.
- Administrative control tab (read-only): per spot date: order number, status, vendor (short name) from whom invoice is expected; client invoice and vendor invoice numbers appear when registered automatically.
- Audit tab: control status per spot (aired, dropped, intermediates such as "aired but cut"); pre and post-evaluation ratings per target.
- Totals panel: whole plan or selected period; group 1: investment, bonus, gross, discounts; group 2: totals with agency fee and taxes. Footer notes (3 free notes or client/document-specific predefined models). Media data (types, book, targets). Objective summary.
- Save -> confirmation.
- Outputs: Plan with N monthly Pautas (one per calendar month touched).

### P06 Media-type specific plan variants
- TV with program list [-generar-un-plan-de-medios-de-tv-y-utilizar-el-listado-de-programas-.html]: Item -> Add from Program List; sort; enter spot count per program; system proposes a distribution across days in a "Spot Distribution" window; clicking weekdays or dates excludes them and the system redistributes among the remaining; confirm per program or confirm all.
- TV without rating with rate card and contract [-generar-plan-de-medios-sin-datos-de-rating-para-tv-con-tarifario-y-contrato-.html]: Rating criterion Manual; on the Detail tab pick contract and rate card per item.
- TV from ranking [-generar-plan-de-medios-asociado-a-un-rankeo-para-tv-.html]: Rating criterion Ranking.
- Press [-generar-plan-de-medios-para-prensa-.html]: columns `Cmts.` and `Cols.`; surcharges tab with code, value, accumulated flag, percent flag.
- Radio [ad_cap_gus_med_19-...]: Rating Manual; hours optional; max 99 spots/day.
- Internet (classic plan) [-generar-plan-de-medios-para-internet-.html]: placement (`Ubicación`), height (`Alto`) and width (`Ancho`), rate type `C.P.M./Tipo`; max 99 spots/day.
- Out-of-home [-generar-plan-de-medios-para-via-publica-.html]: `Días` (≤ plan days), boards `Ctls.`, circuits `Ctos.`; day grid entry shows an X regardless of the number typed.
- Group-billed plan [-generar-un-nuevo-plan-de-medios-facturable-a-un-grupo-de-clientes-.html]: JobNumber with billing code "assign in schedule or estimate"; billing clients linked to the holder; split percentages defined in `Códigos de Apertura de Facturación`; choose split code in the header.

### P07 Copy plan / generate plan from an existing plan [mp301002.html, ad_cap_gus_med_23-...]
- From a queried plan press New -> Copy Plan: options "copy without spots" (Y/N) and "copy plan rates" (Y/N) -> header (can change JobNumber/client and validity) -> on confirm choose spot relocation: `No Mover Avisos` (keep positions), `Trasladar` (shift all spots starting from the first available week day with spots, keeping order), `Rotar` (keep each spot's weekday; spots falling outside go to the end respecting weekdays) -> save.
- Validation: system checks that vendors, outlets, placements, etc. are still active and warns on any non-current master.
- Recommendation: keep the same number of days; if shortened, excess days are dropped.

### P08 Import TV plan from PlanView optimizer [-importar-un-plan-de-medios-de-tv-generado-en-planview-.html]
- Precondition: feature enabled by vendor.
- Steps: New -> Import Plan -> select JobNumber and file -> fill header (TV) -> Confirm -> "durations per material-item" window (enter duration per material) -> "contract selection" (assign a contract per outlet) -> import -> Save.
- Restrictions: one schedule and one media type per import.

### P09 Revision scheme (plan versioning) [-habilitar-el-esquema-de-revisiones-en-los-planes-de-medios-.html, mp301002.html]
- Enable `Modifica Revisión Plan` in Visual sidebar -> Revisions. Every save prompts a reason and creates a new revision, browseable later.
- On client approval, revision counter resets to 0 for ordering; the approved revision is the one to execute; after that revisions can again be stored.

### P10 Client approval — whole plan [-aprobar-por-cliente-un-plan-de-medios-.html]
- Preconditions: config `Circuito Aprobación Medios` ≠ None (restricted or strict); `Período de Aprobación por Cliente` = whole plan.
- Steps: query plan -> Approvals -> Approve by Client -> confirm -> observations (system proposes the revision name to identify the approved version) -> accept.
- Rules: only users with client-approval permission; unapproved spots should be rejected (or deleted) beforehand; orders cannot be issued on unapproved plans; if credit limits are used and exceeded, credit override approval must come first.

### P11 Client approval — per monthly schedule [-aprobar-por-cliente-una-pauta-...]
- Same as P10 but config = per schedule; choose the `Pauta` to approve via "Monthly approvals".

### P12 Credit-limit override approval [ad_cap_gus_med_25-...]
- Preconditions: special config `Límite de Crédito en Medios/Producción` = true; credit limit set on billing client; plan exceeds the limit.
- Steps: query plan -> Approvals -> Approval by client -> confirm the override -> choose schedule if multiple -> confirm. Result: schedule approved by client and credit excess approved.
- Restriction: user must hold credit-limit approval authority.

### P13 Reject spots (proposal not accepted) [mp301002.html, -rechazar-avisos-de-una-pauta-pendiente-de-ordenar-.html]
- Steps: query plan -> Approvals -> Reject -> pick schedule if several -> select spots (single, block by right-drag, or all) -> confirm.
- Effect: rejected spots shown in red; excluded from spot count, totals and printed schedule; history retained. Preferred over deletion.

### P14 Recover rejected spots [mp301002.html]
- Approvals -> Recover -> select spots (they turn purple during selection) -> confirm. Spots return to their pre-rejection state, including the possibility to re-link associated orders.

### P15 Cancel ordered spots [mp301002.html]
- Ordered spots cannot be rejected directly: delete/annul the order first; the process asks whether to reject its spots, whether to issue a cancellation request to the vendor and bump the plan revision, and whether to delete spots (recommended: no; reject instead to keep history).

### P16 Generate orders (automatic) [-generar-una-orden-de-publicidad-para-todos-los-items-de-un-medio-de-un-plan-.html, ...-proveedor-...]
- Preconditions: client approval; credit override if needed.
- Steps: query plan -> choose schedule -> Order -> Automatic Order -> criterion (by outlet `Medio` or by vendor `Proveedor`) -> order period from/to -> filter by material (Y/N) -> footer notes per outlet (from model and/or manual Note 1-3) -> confirm. Ordered spots turn blue.
- Radio/TV planner variant [mp402803.html]: Order button groups by outlet/contract/material/publication type per preset criteria; user confirms each order or selects a subset (rest stay pending); if pauta vs order rate differences exist, user must validate the order to accept them (per-program breakdown shown); footer notes generic or per outlet, plus an observation per outlet.

### P17 Modify order with new version [-modificar-una-orden-de-publicidad-generando-una-nueva-version-.html]
- Steps: query plan -> enable `Agrega Avisos a Orden` -> Modify -> unlock item (double-click lock flag in `Lockeo` column; red = locked, green = unlocked) -> change spot counts -> Save -> "Revision by order modification": check `Mod. Rev.` to create a new order version, optional description -> plan revision reason -> system annuls the replaced version and issues the new one.
- If the order was not yet sent, versioning may be skipped (uncheck): order re-issued with same number and version.
- Planner variant: right-click spot -> edit order -> adjust rate/discounts/notes/observations -> save with category and reason -> new version to send.

### P18 Annul an order [ad_cap_gus_med_64-anular-una-orden-de-publicidad-mp301002.html]
- Steps: query -> Modify -> select program -> unlock -> Orders/Annul/Orders -> confirm -> answer whether to reject spots -> "Order revision modification" grid: `Mod. Rev.` (new version), `Imp. P. Anu.` (print "annuls and replaces" legend), copies, PDF, reason -> accept -> save plan with revision reason.

### P19 Add spots to an un-ordered schedule [-agregar-avisos-a-un-programa-de-una-pauta-sin-ordenar-al-medio-.html]
- Modify spot counts per day directly; cannot leave a program with zero spots.

### P20 Add spots and push into existing order [-agregar-avisos-en-una-pauta-e-incorporarlos-a-la-orden-relacionada-.html, mp301002.html]
- Enable `Agrega Avisos a Orden`; unlock; change counts (changes shown light-blue); on save the related order is updated automatically with an "annuls and replaces previous version" note (or modified in place if `Mod. Rev.` unchecked). Changes that can flow this way: program, duration, spot count, publication type, billing type, direct/indirect, contract.

### P21 Bulk negotiation change (release 4.6+) [mp301002.html]
- Toolbar action to change negotiations en masse on plans with open, unbilled orders.

### P22 Material distribution (automatic) [mp301002.html, -asignar-material-a-todos-...-.html (5 variants), mp402803.html]
- Precondition: materials created in master (`Materiales`).
- Steps: query -> Modify -> Materials/Distribute -> Main data: domain (spots without material vs all spots — replaces), ordered vs un-ordered spots, date range, application criterion (none/item/zone/outlet/daypart; daypart requires selecting a daypart configuration file then dayparts), application form (in period, day by day, item by item), durations to cover, weekdays, distribution basis (Spots / TRPs [average or pre-evaluation] / Investment amount), filter material by measure, update item measure, filter material by product -> Distribution tab: materials (F2 = same duration only, F4 = any duration) with spot count or %; computed "quantity to distribute" must match total -> Apply (repeatable) -> view with colors (Materials/View) -> manual tweaks via right-click assign/unassign -> Save.
- If "update item measure" is on, assigning a material of different duration changes the spot duration in schedule and order (allows planning with an average duration and splitting later).
- Changing any main-data filter clears the distribution grid.

### P23 Manual material assignment to specific spots [-asignar-material-a-un-determinado-aviso-de-un-plan-de-medios-.html]
- Materials/View -> unlock if ordered -> select program/day -> right-click Materials/Assign -> distribution mode (by measure or by spot), filter by product, filter by measure -> pick material -> confirm -> save with revision reason. Manual mode allows leaving spots without material; control is manual.
- Planner variant: material assigned at item level applies to all periods of the item.

### P24 Royalty-contract material assignment [-asignar-material-con-contrato-de-regalias-a-un-plan-de-medios-.html]
- Material linked to a royalty contract (talent/music rights). On save, system validates that each spot date falls within the royalty contract validity; violations listed in "validity error reasons"; plan cannot be saved until fixed (shorten assignment, extend contract, or use another material).

### P25 Spot rescheduling after control [-reprogramar-un-aviso-de-una-pauta-.html]
- Precondition: spot control done.
- Steps: enable add-to-order; Modify; unlock; remove the dropped spot and enter a replacement count on the new day; save with revision reason.
- Restrictions: programs cannot be left empty; spots already billed to client cannot be rescheduled or modified.

### P26 Delete program from un-ordered plan [-eliminar-un-programa-con-avisos-del-plan-pendiente-de-ordenar-.html]
- Item/Delete then save with revision reason. Deleted spots are unrecoverable (use revisions/rejection instead).

### P27 Pre-evaluation of TV plan (via TVData / IBOPE) [-generar-pre-evaluacion-...-.html, -recuperar-pre-evaluacion-.html, -visualizar-...-pre-evaluacion-.html]
- Preconditions: target assigned; each program has start/end hour; external monitoring provider configured.
- Export: A&F -> Pre-evaluate -> Evaluate: projected date, end of period, material, outlet, evaluation = Pre, real hours = Yes, real-hours criterion -> system checks weekday alignment -> writes a TXT named with plan number to a chosen path for TVData.
- Import: A&F -> Pre-evaluate -> Retrieve result -> pick file -> if target names differ, map primary and secondary targets -> save. Results in Audit tab.
- Method (planner variant): Complete (frequency not split by outlet) or Disaggregated (per outlet). Week selectable; frequencies retrieved.
- Exception: spots IBOPE omits (no break detected, effectively rating 0) are flagged; planner shifts hour later (morning programs) or earlier (late-night programs) and re-evaluates.
- Restriction: projected date must be the same weekday as the plan's first spot.

### P28 Post-evaluation [-generar-post-evaluacion-...-.html, -recuperar-post-evaluacion-.html, -visualizar-...-post-evaluacion-.html]
- Precondition: spot control executed.
- Same export/import pattern with evaluation = Post; results in Audit tab; bands include post-evaluation and "post-evaluation projected".

### P29 Re-rate plan from post-evaluation [-actualizar-tarifas-de-un-plan-de-medios-segun-resultados-de-post-evaluacion-.html]
- Optional add-to-order flag so the rate update flows to the order; Modify; unlock; Tools -> Actions -> Recalculate rates per post-evaluation (updates spot ratings, and therefore CPP-based rates); save.

### P30 Spot control (verification) [mp402803.html, -visualizar-avisos-con-control-deficiente-...-.html]
- Precondition: monitoring data imported (`Importación de Archivos de Monitoreo`).
- Steps: query plan -> Control Spots -> system pulls all aired spots for the advertiser, plan period and plan channels -> map planned materials to monitored materials (mapping remembered) -> run auto-match -> statuses EXACT / APPROXIMATE / NO MATCH -> for NO MATCH: manual association (pick unassigned monitored spot same day/channel), manual control (enter airing time), or leave as no-match (= dropped) -> dropped-spots tab actions: None (keep dropped), Remove from plan, Recovered (back to pending control).
- Visuals: pink vertical line marks the date up to which all spots are controlled; filter "deficient control" shows non-aired spots underlined/pink.
- Rules: billed spots can still be controlled; controlled spots cannot be modified; dropped spots generate vendor and client differences at order close; "temporary control" config allows no-match without marking dropped.

### P31 Approve for billing [ad_cap_gus_med_27-aprobar-para-facturar-un-pauta-de-medios-mp301002.html]
- Preconditions: config approval circuit restricted/strict or `Aprobación para Facturar` = true; spots ordered; if circuit strict/restricted, client approval first.
- Steps: query -> Approvals -> Approve for Billing -> pick schedule -> select spots (single/block/all) -> confirm. Spot numbers display in red.
- Restriction: user permission required.

### P32 Query / view / print [-consultar-...-.html, -visualizar-...-semanalmente-.html, -visualizar-...-por-medio-y-zona-.html, -imprimir-una-pauta-de-medios-.html]
- Query by plan number or by month/year/schedule number. Format weekly or monthly (preference persisted per user). Grouping: Zone/Outlet, Zone/Outlet group, Zone/Daypart, Outlet group/Zone, Outlet/Zone, Daypart/Zone, Station/Outlet, By item, Custom (persisted). Print schedule; export to Excel/HTML/PDF (prompt to include/exclude rejected spots; export does not keep print layout).

### P33 Distribution analysis [-visualizar-el-reporte-de-analisis-de-distribucion-...-.html (2)]
- Distribution panel: criterion, target, rating origin (average / pre / post / post-projected) -> simple view; add more criteria for a joint comparative view. Any plan change refreshes the analysis. One criterion at a time in simple view.

### P34 Radio & TV Planner (`Planificación de Radio y TV`) [mp402803.html]
- Newer grid-based planner for TV and Radio only, always from a Ranking.
- Two approaches: (A) refine book into a ranking with only desired outlets/programs/hours; (B) take the full ranking, assign spots, then delete programs without spots from the plan.
- Steps: open ranking -> Generate Plan -> "destination plan" dialog: send ranking to new plan or append to existing plan; validity (1 day to 12 calendar months); topic; billing client; agency-fee calc type (net, gross, after first discount, fixed per month); fee %; fee billing (Junto/General); payment term (from billing client; editable by 1A/1B if allowed); division; client PO -> Visual: enter spots per day; right side shows rate, sale price and discounts; average rating shown for the day where a spot is entered.
- Grid: group by dragging columns (subtotals), filter, "show only items with spots", Excel-like copy/paste/move of spot cells (asks add vs replace), F11 full screen, column drag-and-drop (not inside day grid), multi-select.
- Columns: item number (+ expand material breakdown), program, duration (one per item), start/end hour (used for control and pre/post-buy), rating block (average rating, weighted rating, cost per point, TRPs), daily spots, total spots, rate type (Normal = rate x duration x spots; Package = total), rate (from rate card/contract or manual), gross, discount %, discount amounts, net (gross - discounts), net cost per spot (net / spots), bonus amount, billable amount.
- Save warns if no materials assigned. Save Draft writes an XML file (only before first definitive save); Get Draft reloads it — used to present alternatives, then commit the chosen one.
- Modify: query by plan number, by schedule+month+year, F5 (user's last plan), F6 (company's last plan). Editable: start date (not after first spot), move publication period by whole weeks keeping weekday (warns about items left without contract/rate card), end date (not before last spot), topic, planning target (only targets in the book), footer notes. Billing client only via moving the JobNumber or changing its client in "JobNumber status and content".
- Objective widget: Investment, TRP, Reach objectives (optional); Frequency = TRP / Reach (not editable); deviation = objective vs plan computed automatically; based on planning target.
- Item actions (right-click): delete item (blocked if billed to client or vendor invoice registered), new manual item (copies item except program/spots; rating editable), duplicate item, unlock weekday (beyond program airing days, for the whole period), add program from book (already-used programs greyed; cannot add twice — duplicate instead), insert comment, reject/unreject.
- Item limits: one duration per item; a rate/negotiation change mid-flight requires a new item from that date; a different material requires a different item.
- Detail tab: vendor, publication type, billing type (Bonus/Barter/Billable), direct, contract (lists valid contracts for client+vendor+outlet; locked once ordered), rate card (selecting it replaces the rate or CPP and recomputes; switching to manual rate resets rate to 0), currency (locked if contract/rate card fixes one), payment (`Por Pauta` normal billing; `Por Adelantado` when the contract is installment-paid: consumes contract balance and is shown on invoice as "paid in advance").
- Approval: Status -> Approve by Client, or from client schedules listing; approved plans can be disapproved.
- Analysis: after save, charts for investment by outlet, TRP by outlet, coverage distribution (after pre-evaluation); "Analysis and distribution" grid with bands Target / Pre-evaluation / Post-evaluation / Post-evaluation projected per target (planning and buying).

### P35 Digital Planner (`Planificación Digital`) [mp402831.html]
- Prereq configuration: generic media type mapping (`Tipos de Medio Genéricos`), rate cards per media type, dynamic categories (`Categorías Dinámicas`).
- Mandatory masters: external providers for the media type, coverage zones, outlets assigned to zones, programs/placements, publication types, digital calculation types, digital platforms, digital formats (display, rich media, search, video ads, etc.), digital buy types, tracking types, placement types, AdServers.
- Steps:
  1. Media & measurement selection: create a ranking (mandatory) with or without book; pick sites (select all by clicking column header; similar names shown red); choose client JobNumber (open) and outlets; after saving the ranking, negotiation conditions (contracts, rate cards) can be adjusted.
  2. Generate Plan (enabled once ranking linked to JobNumber): destination data (validity, topic, calc form, agency-fee %, defaults from masters; payment term editable by 1A/1B).
  3. Digital planning screen: Save Draft available anytime.
     - Main data: topic, agency-fee mode and %, footer notes, client PO (optional).
     - Visual (mandatory per item): platform, publication type, format (implies measure), buy type, clicks, impressions, CTR, gross rate, AdServer; expandable row shows status, clicks, impressions, CTR, planned net; some fields editable by buy type.
     - Detail: vendor, billable, direct/indirect, contract, rate card, currency.
     - Additional costs: AdServer cost per contracted site as % of investment or fixed value (`Costo Pauta`); requires placement type and tracking type per item; totals for schedule and order, direct or indirect, include agency fee or not.
     - Freeze column / freeze band for wide grids.
     - Mass changes: platform, publication type, buy type, format, measures, materials, AdServer, dynamic categories (assign on first item, system offers to propagate).
  4. Approval (permissioned).
  5. Generate order (plan must be approved): "Order" window, assign cost per item manually (defaults to planned value), optional vendor discounts shown on internal order, validate rates adjusted, confirm; optional export/print; item shows Ordered.
  6. Modify digital order: right-click order status -> edit -> change gross rate, discounts, client PO, notes -> save; versions tracked; plan shows latest version.
  7. Planned vs actual: plan must be ordered; e.g., CPC buy: updating negotiated clicks with actual clicks recomputes final rate for both sale and purchase.
  8. AdServer sync: plan ordered and AdServer set per item; press AdServer to upload; Sizmek interface retrieves actual served clicks (may differ from vendor-reported negotiated clicks).
  9. Order adjustment from Google/Meta invoices: requires client taxonomies applied to orders, vendor invoice registered automatically via e-invoicing (Liveranto) with complement identifying billed orders, and prior reconciliation. Menu "Adjust Orders by Vouchers" appears when modifying a plan with Meta/Google items and at least one ordered month. Auto-match items to invoice lines by taxonomy order; manual linking for leftovers. On accept: open order if closed (blocked if e.g. billed), switch items to fixed-cost calc, apply invoice line amount as billable amount for schedule and order, close order. Grid shows only lines matching this plan's taxonomy or lines with no taxonomy; only items pending adjustment with same currency as the line.

### P36 Magazine issue layout (`Análisis por Nº de Revista`) [mp302673.html]
- For publisher-side use (magazine): date range, issue number (after choosing magazine), pages, show ads as thumbnails; report type "Magazine", criterion all vs approved orders, publication type (ad size: 1/3, 1/2, full).
- Movements tab: ads scheduled for the issue with advertiser, product, salesperson, order number, internal number, position, notes, size, material, first-publication date, last page; Art OK flag (editable), repeats (previous order), rate, barter total, billable (= rate - barter), payment terms; colors: red = art not confirmed, white = unplaced, blue = placed. Actions: view order, give Art OK, assign material (then save).
- Notes tab: editorial articles (fixed/not, position, pages, page, responsible, deadline); edit title; pages editable if unassigned.
- Grid tab (visible only with issue set, report = Magazine, criterion = all, publication type = all): printable spread; Modify Grid enables right-click actions: add ads, add notes, insert/delete double page, shift block, unassign, reserve ad page/half page. Insert/delete double page and shift are saved immediately; add/unassign pending until Save (shown lighter). Red name = first page of an article; red dot shows order number.

### P37 Media tracking management (`Gestión de Seguimiento de Medios`) [mp309263.html]
- Precondition: management types and actions defined.
- Filter by management type, media type, criterion (one order / without management / with next action / next action overdue), dates, outlet, client, vendor, order month and number -> select orders -> Comments: contact (outlet contacts), phones, email, comment, next action with date/time -> alerts track progress. Used for vendor discrepancy claims, certification requests, proof-of-publication follow-up.

### P38 Material delivery and tracking [mp309251.html, mp309253.html]
- Requires special config "Control of delivery and receipt of materials". Tracks when each material was delivered to an outlet and its validity to avoid re-delivery. Material statuses: Sent to outlet, Returned by outlet, Requested, Received, Pending request, Received by outlet. Listing shows outlet, delivery lead time, client, product, material, measures, status, days overdue, first spot date.

### P39 Delivery notes (`Remitos`) [mp301275.html, -ingresar-remitos-de-produccion-.html]
- Auto-numbered sequential document accompanying materials delivered to clients; client signs as proof of receipt. Types: Estimate (month + estimate number -> select production items), Free (JobNumber, for not-yet-quoted deliveries), Plan (select schedules of a plan), Materials (media type, outlet, client, contact -> select materials with send status), Budget (billing client, dates, status, estimate number). Save requires selected documents. Delete only if not marked received. Mark as received action. Print with optional logo and 2 footer notes; copy count from production config.

### P40 TV Azteca online (Mexico only) [mp308236.html, mp301206.html]
- User mapping: link system user to TV Azteca online-ordering user code and password; deletable only if never used for imports.
- Automatic reconciliation: report of orders sent via TV Azteca's online system vs actual airing; accept airing or send response messages to the outlet; filters client, product, date range.

### P41 Inter-agency schedule exchange [mp309237.html, mp306062.html, mp301247.html, mp301397.html, mp301393-mp301390.html]
- Export schedules to an associated agency running the same ERP (both enabled): filter by holder client or product, date range, status (pending export / exported / all); grid of month, schedule no., plan no., JobNumber, billing client, holder, product, campaign; mark pending.
- Media hub interface (`Usa Central de Medios`): web-service sync of masters, plans and orders between a central media buying hub and agencies; shows last task export date and last sync; status tab requires hub server path in special config; buttons Sync Agency-Hub, Import.
- TXT-based import of schedules from another installation: import file, then map received clients (code, legal name, generic client, billing client), contracts (client, product, vendor, agreement number), outlets (code, name, zone), products, vendors (code, legal name, tax ID, address), zones (code, name) to local masters; save.

### P42 External and generic plan import [mp300506.html, mp302876.html]
- External interfaces: import schedules/orders from third-party systems (IMGlobal, Media Planning; also import clients MP Online and TV Azteca clients, campaign report, generate code, disuse write-off).
- Generic import: TXT in predefined layout; choose file; assign to a campaign (JobNumber).

### P43 Planning files maintenance [mp301069.html, mp301068.html]
- Selection of Planning Files: list programs with planner, filter by target/zone, columns affinity, reach, rating; sort; delete programs; recover; add targets. Deletion of planning files: page exists without content.

### P44 Contract copy (referenced from plans) [-copiar-contrato-de-medios-.html]
- In Media Purchase Contracts: query (holder client, outlet, contract no.) -> Copy -> new client, outlet, description, valid = yes, start/end, purchase condition type, consumption type, control type, notes -> Negotiation: contract without VAT, payment term days, currency, fix exchange rate + rate, gross amount (when consumption type = amount), client discounts 1st-4th, agency commission %, discount application criterion -> Assignment: billing clients and products allowed -> Rates: negotiation type, calc type, valid rate cards -> Sub-contract: type Normal -> Save (prompt to add rate card if none). Each contract ties one outlet and one client.

---

## 3. Entities and master data

| Entity (ES / EN) | Key fields | Identifier | Relationships |
|---|---|---|---|
| `JobNumber` / Campaign-project | holder client, product, billing client, work typology, topic, division, billing code (`no facturable`, `asignar posteriormente`, `asignar en pauta o estimado`, `asignado en JobNumber`, `cliente por defecto`), open/closed | JobNumber code | 1..N plans, rankings; from Accounts module |
| `Plan de Medios` / Media plan | number, JobNumber, media type, validity from/to, topic, contact, client PO, division, split code, payment term, order-only, mix direct/indirect, agency-fee type/%/amount/discount/billing mode, currency + monthly reference FX, rating criterion, target 1/2, book/ranking, budget, TRP objective, objective detail, additional costs, footer notes, revision no., attachments | plan number (choosable with permission) | has 1..12 `Pautas`; belongs to JobNumber |
| `Pauta` / Monthly schedule | month/year, schedule number, per-month client budget/PO number, approval status | month + year + number | belongs to plan; has items; exported between agencies |
| `Ítem` / Line item | item no. (≤999 per schedule), outlet, vendor, zone, program/placement, publication type, unit of measure, start/end hour, purchase start/end, measure (sec / cm x cols / circuits & boards / height x width / format), rate type, rate, discounts, surcharges, billing type, direct flag, agency-fee flag, VAT flag, vendor commission, contract, rate card, currency, payment mode, comment, rating values, materials, lock flag | plan + schedule + item no. | many spots |
| `Aviso` / Spot (day cell) | date, count (≤99/day), material, state (planned, client-approved, ordered, approved-for-billing, billed, rejected), control status, pre/post rating, order number/version | item + date (+ seq) | linked to order, client invoice, vendor invoice |
| `Orden de Publicidad` / Insertion order | number, version, vendor/outlet, period, footer notes, observations, cost, vendor discounts, client PO, state (open, closed, partially closed), internal status (unsent, in control, claimed, to send to unit, returned by marketing, with WE issued), linked delivery note | order no. + version | generated from schedule items |
| `Revisión` / Plan revision | number, reason, timestamp, approved flag | plan + revision no. | |
| `Book de Rating` | description, media type, rating provider, market, period, client, rating type (program/break), targets, population data, weights | book code | source for rankings, plans |
| `Rankeo` / Ranking | book, planning target, negotiation target, outlets, hours, weekdays, client, JobNumber, rate-card settings (validity, seconds, net/gross, publication type, currency, FX), default negotiations per outlet | ranking code | source for Radio/TV and Digital planners |
| `Target` | name, universe, affinity, cases %, total cases, sample | code | per book |
| `Plaza Externa` / Measurement market | provider market code | | books |
| `Proveedor Externo` / External provider | per media type; types: rating, airing monitoring, evaluation | | books, monitoring, pre/post |
| `Medio` / Media outlet | media type, default vendor, zone, provider code, rating provider, market, opening (`apertura`) | code | vendors (N), programs |
| `Tipo de Medio` / `Tipo de Medio Genérico` | TV, Cable, Radio, Press, Magazine, OOH, Internet...; generic mapping for digital | | |
| `Programa / Ubicación` | name, outlet, airing days, start/end hour | | items |
| `Tipo de Publicación` | buy type (break spot, PNT, sizes), additional-cost enablement, dynamic categories | | items |
| `Franjas` / Daypart configuration | named config file with time blocks | | analysis, material distribution |
| `Tarifario` / Rate card | outlet, program rates, CPP rates, validity, currency | code | contracts, items |
| `Contrato de Compra de Medios` | client, outlet, description, valid, start/end, purchase condition type, consumption type (e.g., amount), control type, VAT inclusion, payment term, currency, fixed FX, gross amount, client discounts 1-4, agency commission %, discount application criterion, allowed billing clients and products, rate type/calc, rate cards, sub-contract type, negotiated share, advance-payment installments | contract no. | items; share control |
| `Material` | name, duration/measure, product(s), royalty contract | code | spots |
| `Contrato de Regalías` / Royalty contract | validity | | materials |
| `Cargo Adicional` / Additional charge | definition, % | | plans (header tab) |
| `Recargo` / Surcharge | code (e.g., position, color) | | items (press, internet, OOH) |
| `Modelo de Notas al Pie` | per client and document type (schedule, order) | | |
| `Cliente Titular` / `Cliente de Facturación` | credit limit, payment term, agency-fee type/%, fee billing mode, accepts vendor commission, contracting mode direct/indirect | | |
| `Código de Apertura de Facturación` | split % per billing client | | group-billed plans |
| `Proveedor` / Vendor | legal name (for vouchers), short/trade name (searches, admin tab), check payee name, tax ID, commercial activity | | items, orders |
| Digital masters | platforms, formats (-> measure), buy types (CPC, CPM...), tracking types, placement types, AdServers, digital calc types, taxonomies | | digital items |
| `Usuario Azteca` (MX) | system user, Azteca code, password | | |
| `Tipo de Gestión` / Action | management type, actions, next action | | tracking |
| `Remito` / Delivery note | number, type, JobNumber, billing client, product, items, received flag | sequential | |
| `Reserva Presupuestal` / Budget reserve | reserve, fund areas (`Área de bolsa`), consumed, balance | | budgets, schedules |
| Magazine objects | magazine, issue, pages, editorial notes, reservations | | magazine layout |

---

## 4. Document lifecycles

### 4.1 Plan
Draft (optional XML draft outside DB) -> Saved (revision n) -> [revisions on each save if enabled] -> Client-approved (approved revision recorded; revision counter reset to 0) -> Ordered (partially or fully, by schedule) -> In execution (materials, traffic, control) -> Approved for billing (spot-level) -> Billed (spot-level). Optional: disapproval of an approved plan (Radio/TV planner). Deletion discouraged; rejection preferred.

### 4.2 Schedule (`Pauta`)
One per calendar month in the plan validity. States driven by its spots: pending approval -> client-approved (if per-schedule approval) -> credit-approved (if needed) -> ordered -> approved for billing -> billed. Exportable to partner agency (pending export / exported).

### 4.3 Spot state machine
```
PLANNED --approve_client--> CLIENT_APPROVED --order--> ORDERED (blue)
PLANNED|CLIENT_APPROVED --reject--> REJECTED (red; excluded from totals/print)
REJECTED --recover--> previous state (purple while selecting)
ORDERED --control--> {AIRED | APPROXIMATE->resolved | DROPPED | intermediate e.g. AIRED_CUT | UNCONTROLLED}
DROPPED --action--> {kept DROPPED | REMOVED | RECOVERED->UNCONTROLLED}
ORDERED --approve_for_billing--> BILLING_APPROVED (red number)
BILLING_APPROVED --client invoice--> BILLED (locked)
ORDERED --annul order (+reject)--> REJECTED
```
Locks: once a spot has associated vouchers it is blocked (e.g., cannot modify after client billing; cannot delete item with client invoice or registered vendor invoice; controlled spots immutable; vendor/contract cannot change once ordered). Ordered items show a lock flag that must be toggled (red->green) to edit.

### 4.4 Insertion order
Generated (version 1) -> sent -> modified (new version that "annuls and replaces" prior, or in-place if unsent) -> annulled (optional cancellation request) -> spot control -> closed (differences generated for dropped spots) / partially closed. Digital orders: reopened and re-closed during invoice-based adjustment; edit history of versions retained.

### 4.5 Approval configuration
- `Circuito Aprobación Medios`: None / Restricted / Strict.
- `Período de Aprobación por Cliente`: per schedule / whole plan.
- `Aprobación para Facturar`: true/false.
- `Límite de Crédito en Medios/Producción`: true/false.
- Order issuance blocked until client approval (when circuit ≠ None) and until credit override if over limit.

### 4.6 Ranking / book
Book: created/imported -> optionally weighted -> modified (add targets) -> deleted. Ranking: created (with/without book) -> linked to JobNumber -> negotiations set -> saved -> used to generate plan(s) or append to existing plan. Query ranking: transient.

---

## 5. Business rules and calculations

R1. Plan validity: minimum 1 day (overview, Radio/TV planner) or 2 days (step-by-step guides) — see gaps; maximum 12 calendar months (360 days). One schedule per calendar month touched, so at most 12 schedules; a plan from 15-Jan to 15-Jan next year is invalid (13 months).
R2. Reducing plan dates can drop spots outside the new range. Start date cannot move after the first spot; end date cannot move before the last spot (Radio/TV planner).
R3. Max 999 items per schedule; max 99 spots per item per day.
R4. Gross amount, Normal rate type:
- TV/Radio/Cable: `gross = duration_sec x spots x rate_per_second`.
- Press: `gross = cm x columns x spots x rate_per_cm_column` (guide phrasing also multiplies by airing days; spots per day summed across days is equivalent).
- OOH: `gross = circuits x rate_per_board_unit`; boards count and exposure days do not affect price.
- Internet (classic plan): `gross = height x width x airing_days x spots x CPM_amount` (as documented).
- Digital planner: gross rate per item with buy type; CPC-type final rate recomputed from actual clicks (`final = actual_clicks x unit_rate`, inferred).
R5. Package rate type: entered amount is the item total. For multi-month items: default split into equal parts per month regardless of spots; optional special config splits proportionally to purchased days (`month_amount = total x days_in_month_with_purchase / total_purchased_days`).
R6. Discounts cascade in entry order. Shorthand `10+5+3` means three successive discounts. Recommended formula: `net = gross x Π(1 - d_i/100)`; discount amount = gross - net. (Sequential application is implied by "applied in order"; confirm.)
R7. Surcharges must be predefined (e.g., press position or color); each has value, accumulated flag (`Acum`) and percent flag (`%`). Surcharge amount totals in the Discounts/Surcharges amount column.
R8. `net_investment = gross - discounts (+ surcharges)`; `net_cost_per_spot = net_investment / total_spots`.
R9. Billing type per item: Billable (default; billable amount = net), Bonus (`Bonificable`: priced but fully waived; billable 0; carried to the order; per Radio/TV planner, not billed to client and not paid to vendor, only agency fee charged), Barter (`Canje`: has value; not billed by default unless config enables; client pays vendor in goods/services).
R10. Direct vs indirect: indirect = vendor invoices agency, agency invoices client, buy/sell may differ. Direct = vendor bills client (or, in countries with a direct-billing scheme, bills in agency's name and agency passes the cost via a special voucher); agency earns only the fee; plan investment must equal order cost (no buy/sell spread). Mixing requires header flag.
R11. Agency fee (`Servicio de Agencia`) calc types: on net, on gross, on amount after first discount, fixed amount (per month in Radio/TV planner). `fee = base x fee_pct` (or fixed). Agency-fee discount: `fee_net = fee x (1 - bonif_pct)`, shown in plan totals and invoice. Item-level opt-out checkbox excludes item from base. Billing mode `Junto` (with media) or `General` (separate invoice after media is invoiced).
R12. VAT applies per item by default (checkbox). Reports may include/exclude VAT. Flowchart subtotals can add ITBIS tax per special config.
R13. Vendor commission (confidential): received as %, credit note, or agency-issued invoice (recommended). No commission generated in a month without spots. Requires agency usage and client configured to accept it; billing form may be per item.
R14. Payment term: single integer days (no 30/60/90 schedules; descriptive text allowed but due date uses the single value). Editable only by access levels 1A and 1B and only if config "allow editing payment term in plans" is on.
R15. Currency: per plan and per item; foreign currency requires reference FX per month; actual FX set at invoicing/vendor invoice. Contract or rate card with fixed currency locks item currency. Reports offer multicurrency, consolidated at day, consolidated at schedule rate, or fixed FX.
R16. Rate card selection replaces item rate (or CPP value for CPP rate cards) and recomputes cost; switching to manual sets rate to 0.
R17. Rate or negotiation change mid-period requires a new item from the change date; different duration or material requires separate items; one publication type per item.
R18. Ratings: average rating per program/weekday/overall from book; weighted rating by duration where breaks vary (Argentina). Discontinuous market: shared programs = mean of base-market ratings (or slot mean); local programs = last known rating.
R19. Audience metrics (standard definitions, to confirm against implementation): `TRP = Σ(spots x rating_target)`; `GRP` same on base/household; `CPR (cost per rating point) = net_cost / TRP`; `CPM (cost per thousand) = net_cost / (audience / 1000)` with `audience = rating% x universe`; `affinity = rating_target / rating_reference x 100`; `Frequency = TRP / Reach` (explicitly documented); objective deviation = objective - plan.
R20. Material distribution must allocate exactly 100% / total spots / total TRPs / total amount ("quantity to distribute" check).
R21. Material assignment with "update item measure" changes the duration of the spot in schedule and order (and hence price by R4).
R22. Royalty validity: every spot date must be within its material's royalty contract validity, else save blocked.
R23. Spot matching: EXACT = day, channel, material, program name, time all match; APPROXIMATE = day, channel, material match but program name dissimilar or time outside program by more than tolerance (default 20 minutes, configurable); NO MATCH -> dropped unless manually associated/controlled or temporary-control config.
R24. Dropped spots generate vendor and client differences at order close.
R25. Pre/post evaluation projected date must share weekday with first plan spot; spots with no detected break should be shifted (later for morning, earlier for late night) and re-evaluated.
R26. Copy relocation modes: No move, Translate (shift to first available week with spots keeping order), Rotate (keep weekday). Move-period in Radio/TV planner shifts by whole weeks preserving weekdays.
R27. Order generation: pauta-vs-order rate differences require explicit user validation. Digital order cost defaults to planned value; may be edited.
R28. Google/Meta adjustment: items set to fixed cost; billable amount for schedule and order = matched invoice line amount; same currency only; order reopen blocked if billed.
R29. Rejected spots excluded from totals and printouts; deletion loses history.
R30. Client approval requires plan within credit limit or prior override.
R31. Magazine: billable = rate - barter total.
R32. Advance-payment contracts: items with payment `Por Adelantado` consume the contract balance and are not invoiced again (shown as paid in advance). Report filters handle installments (`Cuotas`) and advance payments separately.
R33. Attachments: levels 1-2 delete, 1-4 attach, 1-6 open.
R34. Book import: one market per import; recommended data no older than 4 weeks.
R35. Ranking: cannot add programs absent in book; cannot edit ratings.
R36. Contract share control: compares planned/bought/actual investment %, rating % and duration % against negotiated share percentages per contract.

---

## 6. Financial impacts

- Plan totals produce: gross, discounts, net investment, bonus amount, billable amount, agency fee (after fee discount), taxes; these drive client invoicing once spots are approved for billing.
- Agency revenue: spread between sale and cost on indirect items, agency fee, and confidential vendor commissions (invoiced or credited). Direct items yield only fee.
- Credit exposure: plans checked against billing client credit limit; override requires approval.
- Order close: dropped spots produce vendor and client differences (credits/debits) — a downstream financial adjustment.
- Advance-payment contracts and fees: spots consume prepaid balances instead of generating new invoices.
- Additional costs (e.g., AdServer fees) can be direct or indirect and may or may not carry agency fee.
- Digital Google/Meta: billable amounts realigned to actual vendor invoice lines (cost = sale on adjusted items).
- Group billing: invoicing split across billing clients by split-code percentages.
- Division assignment allocates plan revenue to a business unit.

---

## 7. Cross-module handoffs

| Direction | Counterpart | Data |
|---|---|---|
| In | Accounts (`Cuentas - Seguimiento de los Trabajos - JobNumber`) | open JobNumber, client, product, division, billing code; JobNumber status screen to change client |
| In | AR masters | billing clients, holder relation, split codes, payment terms, credit limits, fee settings |
| In | Media masters | outlets, vendors, programs, publication types, dayparts, materials, royalty contracts, surcharges, additional charges, digital masters |
| In | Buying contracts & rate cards (`Compra de Medios, Contratos y Tarifarios`) | contracts, rate cards, default negotiations; share control is invoked from contracts screen |
| Out | Media Buying / Orders | insertion orders and versions, annulments, footer notes |
| In/Out | Spot Control & monitoring import | aired spots; control statuses; dropped spots |
| Out | Client Billing (AR) | spots approved for billing; billable amounts; agency fee mode; client PO/budget numbers; payment term; division; split |
| Out | Payables (AP) | expected vendor per spot; vendor invoices auto-registered (incl. Liveranto e-invoices for Google/Meta) matched to orders |
| Out | Vendor commission billing | commissions per month with spots |
| Out | Contracts/fees | consumption of contract amounts and installments |
| Out | Production | delivery notes (estimate, plan, materials, budget types) |
| Out | Budget reserves | schedules consume reserve balances |
| Out | Analytics | dynamic reports, investment statistics |
| Ext | Partner agencies / media hub | schedules, masters, orders via TXT or web services |

---

## 8. Configuration, country behaviour, external systems

Special configurations referenced: approval circuit (None/Restricted/Strict); client approval period (schedule/plan); approve-for-billing; credit limit in media/production; allow editing payment term in plans; package proportional split; additional costs enabled (+ per publication type); barter billable; temporary spot control; delivery/receipt control of materials; media hub usage (`Usa Central de Medios`) and hub server path; production delivery-note copies; ITBIS subtotal; vendor-commission billing per item; release 4.6 bulk negotiation change.

Country-specific:
- Argentina: discontinuous-market books; rating per break with fixed duration and duration-weighted averages; vendor tax ID shown as CUIT in vendor import.
- Mexico: TV Azteca online ordering user mapping, automatic reconciliation, TV Azteca and MP Online client imports.
- Venezuela: investment listing by client-product/outlet (max one-month range), with a client-specific export format (Procter).
- Dominican Republic (inferred from ITBIS): flowchart subtotals with ITBIS.
- Chile (inferred): expense table sorted by RUT.
- Client-specific reports: Telecom investment report, Vivaki BSC report.

External systems and formats:
- Rating providers via configured interfaces; IBOPE named for pre/post evaluation; TVData application receives TXT export (named by plan number) and returns result files with targets to map. Kantar is not mentioned explicitly.
- Monitoring providers: monitoring files imported; external ads listing compares monitoring data to orders.
- PlanView optimizer (TV plan import file).
- IMGlobal, Media Planning (external plan interfaces).
- Sizmek AdServer (upload plan; retrieve served clicks).
- Google and Meta invoices via Liveranto e-invoicing with taxonomy-based line matching.
- Inter-agency TXT files (zones, clients, outlets, products, vendors, contracts, schedules) and web services for media hub.
- Generic TXT plan import (predefined layout).
- Draft plans as XML files.
- Exports: Excel, PDF, HTML, text; print layouts customizable by vendor.

---

## 9. Reports and KPIs

| Report | Purpose / KPIs | Ref |
|---|---|---|
| Campaign Control (`Control de Campaña`) | spots planned/ordered per month; filters by schedule, client, product, JobNumber, budget, product groups, publication type; vendor/outlet/zone; division; installments; advance payments; only ordered; include rejections; include differences (rate, duration, count); multicurrency/consolidated; charts; dynamic report | mp301089 |
| Share Control by Contract | budgeted/bought/actual investment %, rating %, duration % vs contract share; bonus filter | mp302085 |
| Investment Statistics | investment by client and media type; order vs schedule rate; consolidation | mp302031 |
| Media Statistics | billable, bonus, barter, total investment, profitability %, cm, spots, seconds, result, agency fee, vendor commission; planned vs ordered; summarised by media type/vendor/outlet/version/product/client/category/zone/agency/campaign; audit filter; VAT; timeout | mp301111 |
| Spots Listing | day-by-day spots with schedule, order, version, size, product, client, plan, topic, audit | mp301575 |
| External Spots Listing | monitoring vs order data | mp302715 |
| Investment by Client-Product/Outlet (VE) | net investment, spot count, period, order, version, buy type | mp301172 |
| Master Plan Listing | total and per-order investment with client and vendor invoice numbers | mp302877 |
| Client Calendar Schedule | calendar of outlet, program, spots, duration, material; totals by material | mp301088 |
| Traffic Schedule (`Pauta Tráfico`) | day, hour, spots, program, duration, material, order — tells vendors how to rotate creatives in reserved slots | mp301101 |
| Media Flowchart | unified multi-plan view; agency fee (fixed and general), total units (seconds or impressions), monthly subtotals | mp300504 |
| Post-Buy | plan evolution: budgeted vs bought vs actual by plan/schedule/JobNumber, criterion, duration, bonus, target | mp301085 |
| Expense Table (`Cuadro de Gastos`) | consumption by vendor, contract type and consumption method; online/offline; editable columns | mp302733 |
| Dynamic Media Report | user-built pivot/grid; templates; filters (dates by spot date, plan numbers, clients, vendor, media type, currency, day status, control status, JobNumber billing code); consolidated fields; weekly scheduled generation at 00:00; online vs offline database | mp402832_1 |
| Media Investment Summary by Client | 34 report types: CPR analysis, consumption by contract, by vendor/outlet/material/time/publication type, month-by-month variants, real fulfilled, real fulfilled and billed, investment vs billed, advance vs normal sale, daypart summary, etc. | mp301138 |
| Telecom Investment Report | per-order status, delivery note, claims | mp302907 |
| BSC Vivaki | pending to bill, contract consumption, spot detail with status, without delivery note, vendor voucher aging | mp302781 |
| Budget Reserve Listing | reserve consumption and balance by fund area; detailed vs summarized | mp302769 |
| In-plan analysis | totals, objective vs actual, distribution analysis by criterion and rating band; investment and TRP by outlet; coverage distribution | mp301002, mp402803 |

---

## 10. Agentic-skill implications

### 10.1 Atomic agent jobs (skills)
1. `rating-book-ingest`: parse provider files into a Book (one market per run); validate freshness (≤4 weeks); handle target creation/update; optional duration weighting.
2. `discontinuous-market-book` (AR): derive ratings from base markets.
3. `ranking-builder`: filter book by targets/outlets/hours/days; compute affinity; attach JobNumber; resolve valid contracts and rate cards at date.
4. `plan-header-composer`: derive defaults from JobNumber and billing client; validate validity window, currency/FX, fee settings, permissions on payment term.
5. `plan-item-builder`: add items from ranking/program list; distribute N spots over allowed days; enforce item limits.
6. `pricing-engine` (deterministic tool): gross/net/fee/tax per item and totals.
7. `objective-tracker`: compare plan vs budget/TRP/reach objectives.
8. `approval-gatekeeper`: enforce approval circuit, credit limit, permissions; record approved revision.
9. `order-generator`: group approved spots into orders by criterion; detect rate differences; version/annul.
10. `material-distributor`: allocate materials by spots/TRPs/amount with constraints (duration, product, royalty validity).
11. `traffic-instructions`: produce traffic schedule per vendor.
12. `spot-matcher`: reconcile monitoring data to ordered spots with tolerance; propose actions on dropped spots.
13. `pre-post-evaluator`: export evaluation file, import results, map targets, re-rate.
14. `billing-release`: approve spots for billing; hand off to AR.
15. `digital-planner` + `digital-actuals-sync` + `invoice-order-adjuster` (Google/Meta by taxonomy).
16. `plan-copy`: copy with relocation modes and master-validity checks.
17. `interagency-exchange`: export/import schedules and map masters.
18. `report-builder`: dynamic pivot over spot-level facts.

### 10.2 Deterministic tools with formulas
```
gross_item(type, rate_type, ...):
  if rate_type == PACKAGE: return amount
  TV/RADIO/CABLE: duration_s * spots * rate_per_s
  PRESS:          cm * cols * spots * rate_per_cm_col
  OOH:            circuits * rate
  INTERNET:       height * width * days * spots * cpm_amount   # as documented
package_month_split(total, months, mode, purchased_days_by_month):
  EQUAL: total / months
  PROPORTIONAL: total * purchased_days[m] / sum(purchased_days)
apply_discounts(gross, [d1..dn]): net = gross * Π(1 - di/100)   # cascade
apply_surcharges(base, [(v, is_pct, is_acc)]): add v or base*v/100; accumulated -> compounding
net_cost_per_spot = net / spots
billable = net if BILLABLE else 0
agency_fee(base_type, pct|fixed, bonif_pct):
  base ∈ {net, gross, gross*(1-d1/100)}; fee = base*pct or fixed_per_month; fee*(1-bonif_pct)
TRP = Σ spots_d * rating_d ;  CPR = net / TRP ;  CPM = net / (rating% * universe / 1000)
frequency = TRP / reach ;  deviation = objective - actual
affinity = rating_target / rating_reference * 100
material_alloc check: Σ alloc == total (spots | TRP | amount)
spot_match(planned, aired, tol=20min) -> EXACT | APPROX | NONE
validity_check(start, end): 1..360 days, ≤12 calendar months -> schedules = months touched
royalty_check(spot_date, contract.start, contract.end)
weekday_check(projected_date, first_spot_date)
```

### 10.3 Controls
- JobNumber must be open; user permissions per action (plan, approve client, approve billing, credit override, payment term edit levels 1A/1B, attachment levels).
- Orders only after client approval (if circuit) and credit override (if exceeded).
- Locked items cannot change vendor/contract once ordered; billed spots immutable; controlled spots immutable.
- Direct items: cost must equal sale.
- Rejection over deletion for audit trail; every save with revision reason when revisions are on.
- Rate differences pauta vs order require explicit validation.
- Royalty validity, material allocation totals, max spots/day, max items/schedule.
- Masters must be active on copy/move; warn on items left without contract or rate card.

### 10.4 Exceptions
- Plan over credit limit; JobNumber closed; inactive masters on copy; items without contract/rate card after date move.
- Rating import with multiple markets; target name mismatch at evaluation import.
- No-break spots in pre/post evaluation.
- Dropped spots; approximate matches; missing monitoring data (manual control).
- Order reopen blocked (billed) during Google/Meta adjustment; unmatched invoice lines; currency mismatch.
- Rescheduling billed spots (forbidden); leaving a program with zero spots (forbidden).

---

## 11. Gaps and ambiguities

1. Minimum plan validity: overview and Radio/TV planner say 1 day; every step-by-step guide says "not less than two days". Needs resolution.
2. Discount cascade semantics (sequential vs additive) is implied ("applied in order") but not formalized; surcharge "accumulated" meaning unclear.
3. Internet classic-plan formula multiplies height x width x days x spots x CPM — dimensionally odd; likely legacy; digital planner uses impressions/clicks/CTR instead. Confirm.
4. Press formula wording multiplies by "days of airing" in one guide and by spot count in the overview.
5. Exact formulas for CPR, cost per thousand, affinity, weighted rating, reach are not given (only Frequency = TRP/Reach). Standard industry definitions assumed.
6. Agency fee "fixed amount" is per month in the Radio/TV planner; generic plan does not specify periodicity.
7. Additional costs calculation and vendor routing are described only qualitatively.
8. Order grouping criteria in the Radio/TV planner (outlet/contract/material/publication type) — precedence not specified.
9. Spot state color legend is referenced but the full list of states/colors is not enumerated in text.
10. Several screens have no content in source: Eliminación de Archivos de Planificación, Exportación de Pautas Central de Medios (description only), Entrega de Materiales (usage missing), Importación de Planes Interfaces Externas (buttons unnamed), Importación Genérica (TXT layout not documented); "Cambiar Estado" in Seguimiento de Materiales could not be enabled per the source author's own note.
11. Academia video pages contain titles only; taxonomy rules (used for Google/Meta matching) are not documented here.
12. "Importación de Pautas - Productos" page shows zone fields (likely copy error in source).
13. Kantar, Nielsen or other rating providers are not named; only IBOPE/TVData. Provider file formats unspecified.
14. How dropped-spot differences are valued (rate per spot, proportional net) is not stated.
15. Monthly reference FX vs actual invoice FX differences: accounting treatment not stated here.
16. Budget reserve linkage (how schedules consume reserves) is only listed in reports.
17. Magazine layout belongs to a publisher scenario; relevance to agency circuit is marginal.
