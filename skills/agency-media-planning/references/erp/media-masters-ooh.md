# Media Master Data & Out-of-Home (OOH / "Vía Pública") Billboards

> **Provenance.** Functional reverse engineering of a reference agency ERP, derived from its publicly accessible help documentation (reviewed 2026-10-11). Content is paraphrased and restructured; it is not vendor documentation, source code or an endorsement. Bracketed ids such as `[mp301010]` identify the source page used as evidence. Items marked *inferred*, *assumed* or listed under gaps must be validated with your own controller, tax adviser and system owner before they drive postings or payments.

> Source: the reference ERP's help documentation (`Medios > Maestros de Medios` and `Carteles Vía Pública`), ~2.9k lines, ~115 help pages.
> This document is a clean-room, paraphrased functional specification for an open-source agentic re-implementation. It describes business behaviour, not UI. Spanish field names appear in backticks only as identifiers.
> Source references use the help page id, e.g. `[mp301056]` = Medios (media outlet master).

---

## 1. Purpose and position in the end-to-end circuit

The media master data layer is the **reference backbone** of the agency's media circuit. Every downstream document — media plan (`pauta`/`plan`), insertion order (`orden de publicidad`), ad-verification/monitoring (`control de avisos`), supplier invoice matching, client billing and accounting postings — resolves its codes, rates, calculation modes, tax treatment and ledger accounts through these masters.

Position in the E2E circuit:

```
Org & party masters (clients, suppliers, products, JobNumbers)
        │
        ▼
MEDIA MASTER DATA  ◄── external providers (ratings, monitoring, programming, ad servers)
  generic media type → media type → publication type
  media outlet (medio) → programmes/placements → dayparts, targets
  materials (creatives), surcharges, discounts, extra costs, agency fee %
  accounting accounts per media type / publication type
        │
        ▼
Rate cards & contracts (other spec) → Media plan → Insertion order → Ad verification
        │                                                     │
        ▼                                                     ▼
Supplier invoice & payment due-date (from medio)        Client billing / accounting
```

Two important framing facts:

1. **Media type is the bridge between planning and accounting.** The help text says explicitly that the `Tipo de Medio` holds the ledger accounts (sales, cost, rebates, differences) that make postings automatic `[mp301045]`. Media is created by the Media department; accounts are filled in later by Administration from the accounting masters menu.
2. **The OOH module ("Carteles Vía Pública") is a media-owner / seller-side module**, not an agency buying tool. It manages a physical inventory of billboard faces (`carteles`), salespeople (`vendedores`), reservations and orders from advertisers, posting (`fijación`) crews, face condition and maintenance, and advertiser agreements with prepaid balances `[mp302805][mp302812][mp302856][mp301549]`. In an open-source rebuild it should be modelled as an optional "inventory seller" vertical that reuses the same party, JobNumber, rate-card and billing infrastructure.

---

## 2. Process catalogue

All master screens share the same CRUD lifecycle (§2.0). Specific processes follow.

### 2.0 Generic master maintenance pattern (applies to ~80 masters)

| Aspect | Behaviour |
|---|---|
| Trigger | Implementation set-up, new commercial relationship, new outlet/programme, external-provider onboarding |
| Actor | Media administrator (most masters); Administration/accounting (ledger tabs); users with specific profile levels for restricted fields |
| Steps | New → system assigns sequential code (some masters allow manual or "generate from description" code) → fill main data → optional tabs (associations, exceptions, external codes) → Save |
| States | `vigente` (active) yes/no; some masters also carry validity dates |
| Delete rule | Physical delete only if the record was never used in any transaction; otherwise set inactive. This is universal across the manual. |
| External systems | Many masters have an "external systems" action that stores an interface code per external provider (ratings, monitoring, programming, ad server, client reporting) |
| Copy | Some masters (media outlets, extra costs, restrictions, content types) support copy-to-new |

### 2.1 Process catalogue table

| # | Process | Trigger | Actor | Key steps | Inputs | Outputs | Controls/approvals | Ref |
|---|---|---|---|---|---|---|---|---|
| P01 | Define generic media types | System implementation | Implementer | Create generic type with calculation basis (cm/column, seconds, elements) and, for seconds, the duration-pricing mode | — | Generic type catalogue | Required parent for every media type | mp302675 |
| P02 | Define agency media types | Implementation; new reporting split (e.g., TV capital vs. TV interior) | Media admin, then Accounting | Media creates main data; Accounting assigns ledger accounts | Generic type, media-type group, cut-off hour, ad-control flag, free-plan flag, unit-of-measure usage, manual-rate lock, base duration and pricing mode | Media type with accounts | Ledger accounts must exist beforehand with the right observation codes | mp301045 |
| P03 | Define publication types | Per media type (auto-created default) | Media admin / Accounting | Rename default "generic rate"; add Spot/Product placement/Separator etc.; set default measure, own-rate flag, digital publication mode, per-outlet measure exceptions, default surcharges, applicable media types, additional-item ledger accounts | Media type | Sub-classification used in rate cards, reports, accounting | At least one per media type | mp301041 |
| P04 | Register a media outlet | New outlet / new zone or media type for existing outlet | Media admin | Enter name, zone, media type, genre, press graphic type, adjustment factor, station code, validity, ad-control flag, global-order flag, currency, agency code at outlet, group, contact; link ≥1 supplier (one default); administrative data (material formats, lead time, due-date rule, VAT, jurisdiction); programming origin (own/network); daypart set; location; interface codes | Zones, media types, suppliers | Media outlet record | One outlet per (zone × media type); copy to enable other zones | mp301056 |
| P05 | Retroactive VAT update | Supplier/outlet changes VAT condition | Media admin | Run retroactive-VAT process from a given date | Outlet, effective date | Re-rated VAT % on existing plans | Ensures supplier invoice matches plan | mp301056 |
| P06 | Maintain programmes / placements | New season grid, new press section, new digital placement | Media admin or import | Manual entry or bulk import from programming/ratings provider; resolve duplicates (merge or create variant) | Outlet, type (programme/time block), days, start/end time, genre, rate type, press page/section, cm, columns | Programme/placement catalogue | Free-plan flag on media type governs whether planners can type ad-hoc programmes | mp301118, import guide |
| P07 | Import programme grid (Chile) | Daily from intermediary provider | Media admin | Choose external provider, measurement market, date range → import active grid | Provider file | Updated programme list | Similar names flagged for user decision | mp301118, mp302665 |
| P08 | Copy programming to repeater stations | Repeater outlet configured as network-dependent | Media admin | Copy grid from network outlet | Source & target outlets | Programmes on repeater | — | mp301118 |
| P09 | Define dayparts | Implementation; outlet with different day boundaries | Media admin | Edit default set (code 1); add named bands with weekday checkboxes and start/end | — | Daypart configuration | Must cover 7 days × 24 h with no overlap; "show incomplete bands" helper | mp301084 |
| P10 | Maintain targets | Ratings import or manual | Media admin | Description, measurement market, generic media type, population/universe/%/sample/min base, audience kind, socio-economic level, sex, ages | Ratings book | Target catalogue | Auto-calc of universe or % | mp301083 |
| P11 | Assign targets to programmes per client/product | Planning prerequisite | Planner | Choose client, product (or all), media type (or all), outlet, default target; override per programme | Targets, programmes | Client-specific programme target map | — | mp309248 |
| P12 | Configure external providers | New ratings/monitoring/e-order/taxonomy provider | Media admin | Create provider, external-system type (media/banks/production), measurement type (by band or by programme), generic media type, band duration, measurement-day grouping; enable interface types with file paths/masks; map markets and outlets to provider codes | Zones, outlets | Interface configuration | Mapping is manual per agency | mp302665 |
| P13 | Map external outlets, markets, channels | Interface onboarding | Media admin | Create external outlets per market & media type; external markets; monitoring channel names; client-specific external outlet codes; bulk external-code assignment per entity and client | Provider files | Code cross-reference tables | — | mp306056, mp305027, mp305056, mp302722, mp302741, mp302902 |
| P14 | Maintain materials (creatives) | New creative/version from client | Media/traffic | Client, description, media type, publication type, measure (press) / duration (TV/radio) / circuit measure (OOH), market category, interface code, material category, products, surcharges, graphic data, royalty contracts | Client, products | Material record | Products empty ⇒ valid for all client products | mp301012 + 5 guides |
| P15 | Link material to royalty contracts | Talent/music royalty contract exists | Traffic | Select available contracts → move to selected; system shows common validity window | Royalty contracts | Material–contract link | Common validity shown | royalty guide |
| P16 | Define surcharges and default values | Commercial policy | Media admin | Create surcharge reason (all or one media type) → per outlet × client set value as fixed add-on or % of gross → tick it on the material → computed at plan time | — | Auto surcharges in plans | — | mp301204, mp306204 |
| P17 | Define additional costs (second commission) | Agency charges extra % or fixed per item | Media admin | Create cost per media type: order-to (outlet/supplier), internal/external, same-outlet flag, publication type, currency, calc type, %/fixed amount, per-client override | Config flags enabled | Child plan items generated from parent items | Requires "generates additional costs" + digital planning flags | mp309267 |
| P18 | Define agency service (fee) percentages | Client onboarding / renegotiation | Account/finance | Per client: media fee %, production fee %, media rebate %, production rebate %; per-product override; apply-to-all | Client, products | Default fee % in plans and production estimates | — | mp306050 |
| P19 | Define agency fee by digital publication type | Digital pricing policy | Finance | Generic type (digital only) → publication type → default % → per-client %; restrict which publication types are usable per buy type | Config flag + user-profile permission | Item-level fee in digital plans | — | mp302927 |
| P20 | Define duration coefficients | Media priced by non-proportional duration | Media admin | Choose criterion (by outlet or by supplier), outlet/supplier, client, optionally publication & media type; fill factor per second 1–200 | Base factor | Coefficient table | Supplier criterion is a Dominican Republic option, off by default | mp301521 |
| P21 | Define audit (ad-verification) codes | Monitoring set-up | Media admin | Code, description, control type OK/Deficiency; media types where valid, external code, allows-reschedule flag; deficiency origin (quantity or %) | Media types | Verification reason codes | An "OK" code must exist and be referenced in config as the closing-adjustment code | mp301082 |
| P22 | Media follow-up management | Need to track actions on orders/plans | Media ops | Define management types (origin order/plan, related contact client/outlet/supplier) and actions per type | — | Follow-up catalogue | — | mp309260, mp309261 |
| P23 | Order modification reasons | Order changes/suspensions | Media ops | Categories (client, outlet, agency) → reasons; prompted when an ordered plan is changed or items appended | — | Reason codes on order changes | Mandatory selection at save time when appending to an order | mp309244, mp309245 |
| P24 | Footnote templates | Document printing | Admin | Per client (holder or billing) and document type (plan, insertion order, production estimate, production PO), up to 6 notes with merge keywords | — | Printed footnotes | Editable per document | mp301585 + guide |
| P25 | Restrictions by entity | Limit which masters a client may use | Admin | Restriction on holder client / outlet / supplier / digital publication type; entity subset; client groups | — | Allow-lists applied at plan creation | Selected = allowed, unselected = blocked | mp302898, mp302929, mp302930 |
| P26 | Taxonomy configuration | Digital plans sent to ad server/sites | Digital ops | Template strings per level (product, plan, item, creative, UTM) using tags; restrict to ad servers or sites | Tag dictionary, external codes | Naming strings / UTM URLs | Active flag | mp302894 |
| P27 | Media-agency hub (Central de Medios) set-up | Company configured as media hub | Admin | Create agencies with billing scheme, divisions, sync interface; associate outlets to agency with agency code; assign holder clients to agencies | Divisions, billing clients | Hub routing & billing scheme | Requires "is media hub" parameter | mp301062, mp309239, mp302688 |
| P28 | Advertiser / holder-client set-up | Agency sells a service via intermediaries | Admin | Create advertiser (code, market category/sub-category, tax id, active, generate holder client); associate holder↔billing, holder↔advertiser, advertiser↔billing | — | Advertiser hierarchy | Mandatory on JobNumbers once enabled | mp301076 |
| P29 | Salesperson assignment | OOH / seller-side commission | Sales admin | Assign salesperson to advertiser × product type × billboard type | — | Commission routing | — | mp301074 |
| P30 | Basic suppliers | Intermediary supplier needs to report the "real" supplier | Admin | Create minimal supplier (name, tax id, address); later convert to full supplier | Config flag | Basic supplier | — | mp309265 |
| P31 | Equivalent-unit weighting | Productivity analytics | Ops manager | Weight per employee category/sub-category × media type × entity type (plan/order/cancellation) | Config flag | Workload KPI | — | mp302683 |
| **OOH** | | | | | | | | |
| P40 | Maintain billboard inventory | New face, new municipal permit | OOH inventory manager | Code, type, zone, format, street, number, between-streets, landmark, municipal permit codes, permit validity, lat/long, notes, rate-card item, image, construction material, initial state | Types, formats, circuits, states, materials | Billboard face | At least an "available" state must exist | mp301561 |
| P41 | Reserve billboards | Salesperson negotiating | Salesperson | New reservation → JobNumber (auto-fills holder, advertiser, product, billing client, campaign) → one billboard type & one zone → salesperson → rate item → assign faces to block them | JobNumber, rate card | Reservation (`reserva`) | Faces must be enabled & free on dates | mp302805 |
| P42 | Create order (direct or from reservation) | Advertiser PO received | Salesperson | New order or "generate order" from reservation → client PO number, opening code (multi-billing split), payment terms, FX rate, supplier commission, agreement, tariff type N/P, rate card, circuits, quantity, start date, outings, rate, discounts | Reservation or JobNumber | Order (`orden`) with per-month sub-orders | Rate card mandatory to order | mp302805 |
| P43 | Assign faces to orders/reservations | After order/reservation | Responsible planner (profile-restricted) | From order or planning screen; filters: block occupied, release reserved, release free-of-charge, release all; filter by street/number; select faces → save | Availability | Face-order link | Turning off "restrict to tariff-item linked faces" requires access level 1 | mp302805, mp302812 |
| P44 | Assign creative (motif) to order | Creative arrives from advertiser's agency | Traffic/ops | Add one or more motifs with % share of faces | Motifs master | Order–motif link | Mandatory before posting order | mp302805, mp301557 |
| P45 | Availability / occupancy planning | Approaching dates with unsold inventory | OOH planner | Occupied report per date, available faces by period/type/format/zone; offer distressed inventory at lower price | Orders, reservations | Availability picture | Sales must key reservations to keep data reliable | mp302812 |
| P46 | Posting order (`orden de fijación`) | Upcoming posting date | Posting coordinator → commercial lead → crew | 3 stages: Build → Control close → Issue posting sheet | Orders with faces & motifs | Posting instructions (remove image X, put image Y) | Only responsible role can reopen; free extra faces can be granted | mp302856 |
| P47 | Face condition audit & maintenance | Field report of damage | Ops | Change face state (OK / needs maintenance / out of circuit / repaired); audit report of state changes and timing | States master | Maintenance history | Out-of-circuit faces cannot be assigned | mp302806, mp302814 |
| P48 | Advertiser agreement (`convenio`) | Volume deal / prepaid deal / barter | Commercial/finance | Party level, number, validity, type M/C, payment N/A/C, currency, FX, discounts, billable & bonus amounts, linked rate card | Client/advertiser/product | Agreement with running account | Inactive or expired agreements cannot be linked | mp301549 |
| P49 | Reject / copy / delete orders | Deal lost / repeat buy / error | Salesperson | Reject frees faces; copy creates new order on new date; delete only if not invoiced and no motifs | Order | — | — | mp302805 |
| P50 | Invoicing control | Month end | Billing | Order list vs. VAT sales sub-ledger; per-month sub-orders; discounts shown net vs. credit-note | Orders, invoices | Reconciliation | — | mp302811 |

---

## 3. Media master-data model

### 3.1 Hierarchies

**Classification hierarchy**

```
GenericMediaType (TV, Radio, Press, OOH, Internet…)        [2-digit code, calc basis]
  └── MediaType (agency-defined, e.g. "TV Capital")       [2-digit code, accounts]
        ├── PublicationType (Spot, PNT, Separator…)        [≥1, default "generic rate"]
        ├── MediaTypeGroup (optional, reporting)
        └── MediaOutlet / Medio (one zone × one media type) [4-digit code]
              ├── Supplier links (≥1, one default)  → Supplier / representative
              ├── Programme | TimeBlock | Press page/section | Digital placement
              │      └── Genre, rate type, days, start/end
              ├── Daypart set (Franja horaria)
              ├── Network parent (programming inheritance)
              └── External codes per provider
```

**Geography hierarchy**: `País` → `Región` → `Zona` (agency-defined reporting location, mapped to provider "plazas") → `Ciudad`. Plus `Regiones por Cliente Titular` (client-specific zone groupings) and `Plazas Externas` / `Plazas de Medición` (provider measurement markets).

**Party hierarchy (media-side)**: `Cliente Titular` (holder client / intermediary) ↔ `Anunciante` (advertiser / end client) ↔ `Cliente de Facturación` (billing client) → `Producto`. In hub mode: `Central de Medios` → `Agencia` → `División`.

**Creative hierarchy**: `Cliente Titular` → `Material` (creative/version/motif) → products, surcharges, royalty contracts, category, content type, material type, language.

### 3.2 Entity catalogue

Below, **R** = required, **O** = optional, **C** = conditional.

#### Classification & calculation

| Entity (ES) | English | Key fields | Notes |
|---|---|---|---|
| `Tipo de Medio Genérico` | Generic media type | code (2-digit auto) R; description R; `tipo_calculo` R ∈ {cm/col, seconds, elements}; `forma_calculo` C (seconds only) ∈ {proportional, respects factors, does not respect factors} | Internet must use "elements" |
| `Tipo de Medio` | Media type | code (2-digit auto) R; description R; generic type R; group O; `hora_corte` C (seconds); `controla_avisos` R (default for outlets); `dias_limite` C (if controls ads); `pauta_libre` (free entry of programmes) R; `usa_unidad_medida` ∈ {no, optional, mandatory}; `impide_tarifas_manuales` flag; `duracion_base` C; `calculo_tarifa` C; ledger accounts (see §6) | One outlet ↔ exactly one media type; a plan has exactly one media type |
| `Grupo de Tipos de Medio` | Media type group | code, description | Reporting only |
| `Tipo de Publicación` | Publication type | media type R; code auto; description R; active; `medida_en_plan` (from type vs. manual); default measure C; `tarifa_propia` flag; digital `modo_publicacion` ∈ {programmatic, auction, none}; per-outlet measure exceptions; default surcharges; applicable media types (subset of same generic); additional-item accounts (sales/cost) | Auto-created default per media type |
| `Tipo de Publicación (Editora)` | Publisher publication type | code, description, ledger account, active | For publisher (editorial) business line |
| `Unidad de Medida` | Unit of measure | media type R; code; description (module, pixel…); active | Selectable per plan item; flows to orders & stats |
| `Coeficiente de Duración` | Duration coefficient table | criterion ∈ {by outlet, by supplier}; outlet or supplier; client O; publication type O; media type O; rows (seconds 1–200 → factor) | Base factor = 1 at base duration |
| `Franja Horaria` | Daypart set | code (1 = default); description; rows {band name, Mon..Sun flags, start, end} | Full week coverage, no overlaps |
| `Formato de Digital` | Digital format | code; description; measure kind ∈ {pixels, seconds/minutes, n/a}; default measures (1..n); per-outlet measure exceptions; outlet aliases; allowed buy types; external codes | Package formats carry multiple measures |
| `Medida de Digital` | Digital measure | code; description; kind ∈ {pixels, seconds/minutes}; numeric or alphanumeric value; active | |
| `Tipo de Cálculo Digital` | Digital calc type | generic calc ∈ {per unit, per click, per impression, fixed}; code; description (e.g. "CPV – cost per view"); active; outlet restriction | Quantity × rate |
| `Tipo de Compra Digital` | Digital buy type | code; description (traditional, auction, performance, display, social…); outlet restriction | |
| `Tipo de Placement Digital` | Placement type | code; description | Tied to ad-serving monitoring |
| `Tipo de Tracking Digital` | Tracking type | generic calc ∈ {cost/unit, cost/click, cost/impression, fixed}; code; description | Ad-serving cost basis |
| `AdServer` | Ad server | code; description; outlet (internet); supplier; publication type; external provider; active; costs per tracking type | Ad-serving cost booked separately from media |
| `Plataforma Digital` | Device platform | code; description (desktop, mobile…); outlet restriction | |
| `Funnel` | Funnel stage | code; description; publication types (none = all) | Assignable in plans |
| `Retargeting` | Retargeting type | code; description; 3-char short code | |
| `Colores` | Colour | media type; code; description; active | Optional plan column |
| `Descuentos de Medios` | Discount label | code; description | Categorises discounts off gross rate |
| `Recargo` | Surcharge | code; description; media type (one or all) | |
| `Recargo por Defecto` | Default surcharge value | outlet; client; surcharge; value; `acumulado` (fixed add-on) vs `porcentaje` (% of gross); active | Applied when ticked on material |
| `Costo Adicional` | Additional cost | media type; code; description; `ordenar_al` ∈ {outlet, supplier}; active; internal/external; same-outlet flag; publication type; currency; calc type; %; fixed amount; per-client overrides | Generates child items |
| `Servicio de Agencia` | Agency service % | holder client; media fee %; production fee %; media rebate %; production rebate %; per-product overrides | |
| `Servicio de Agencia por Tipo de Publicación` | Fee by publication type | generic type (digital); publication type; default %; per-client %; allowed buy types | |
| `Categoría Dinámica` | Dynamic category | code; description; active; mandatory flag; sub-item kind ∈ {list, text, number, date}; special flag; restrictions by holder client, billing client, product, generic type, media type, product group | Locked once linked to closed/billed items |

#### Outlets, programming, audience

| Entity | English | Key fields |
|---|---|---|
| `Medio` | Media outlet / vehicle | code (4-digit auto) R; name R; zone R; media type R; media genre O; press graphic type C; `factor_ajuste_cm` C (modular press); station code O; active + validity from/to O; `controla_avisos` ∈ {yes, no, per media type}; `permite_orden_global` (default yes); currency R; agency code at outlet O; media group O; contact O; email O; hub-associated flag; suppliers ≥1 with default R; material formats (text) O; material lead time O; due-date rule R; VAT condition R ∈ {100% taxed, 50% taxed, untaxed}; tax jurisdiction R; programming origin ∈ {own, network} + network parent C; `es_cadena` flag; daypart set; address/phone/notes O; country/region/city; interface codes; digital order-time alerts per supplier |
| `Programa / Ubicación` | Programme / placement | outlet R (zone derived); type C ∈ {programme, time block} (TV/radio); page/section C (press); weekday flags; description; cm, columns, modules C (press); start/end time; active; genre C; rate type ∈ {own, time block} + block ref; notes; external provider link (digital) |
| `Género de Medios` | Outlet genre | media type; code; description |
| `Género de Programa` | Programme genre | code; description; external codes |
| `Grupo de Medios` | Outlet group | code; description |
| `Productora` | Production company | code; description (linked to programmes from the plan) |
| `Target` | Audience target | code; description; measurement market; generic media type; active; population; universe; %; sample; minimum base; audience kind ∈ {persons, housewives, households}; SES level ∈ {high, mid, low}; sex; age range; external codes |
| `Asignación de Target por Programa` | Client programme-target map | holder client; product (or all); media type (or all); outlet; default target; per-programme override |
| `Revista`, `Número de Revista`, `Nota Periodística` | Magazine, issue, editorial note | magazine; issue number; reserved ad pages; note description, page position, pages, owner, deadline, completion date (publisher line) |
| `Idioma` | Language | code; description (US/Puerto Rico only; on materials) |

#### Geography and external mapping

| Entity | Key fields |
|---|---|
| `País` | code; description |
| `Región` | country R; code; description |
| `Zona` | code; description; country O; region O; per-provider interface codes (one column per interface type) |
| `Ciudad` | code; zone R; description |
| `Región por Cliente Titular` | holder client; 3-char code; description; zones[] |
| `Plaza Externa` / `Plaza de Medición` | code; description |
| `Medio Externo` | market; media type; code; description |
| `Proveedor Externo` | code; description; external system type ∈ {media, banks, production}; measurement by band or programme; generic media type; programming start/end; supplier link; band measurement days ∈ {daily, 2 groups, 3 groups}; band duration ∈ {1, 15, 30 min}; first band minutes; band count; enabled interface types (with path & file mask); market codes; outlet codes; zone (digital) |
| `Interfaz de Canales de Monitoreo` | channel name; media type; outlet; zone |
| `Medio Externo por Cliente` | holder client; external code; description; key; outlets[] (1 code → n outlets) |
| `Asociación de Medios Externos` | outlet × supplier → client's code and name for that outlet |
| `Asociación Códigos Proveedor-Cliente` | supplier; billing client; supplier's code for client; client's code for supplier |
| `Código de Avisador` | outlet; client type (holder/billing); client; advertiser control code printed on orders |
| `Asociación Masiva de Códigos Externos` | external provider; entity; per-client code; default value |

#### Parties (media-side)

| Entity | Key fields |
|---|---|
| `Agencia` (hub mode) | code; description; activity start date; billing client link; VAT responsibility type; web sync flag; RAP number (Argentina); active; billing scheme flags; divisions[]; external provider codes |
| `Asociación Agencia–Medio` | outlet; agency; agency code for outlet |
| `Asignación Cliente Titular–Agencia` | holder client; agency; attachments; provisional status until approval |
| `Anunciante` | code (manual or generated); description; market category/sub-category; tax id; active; generate-holder-client flag |
| `Asignación de Vendedores` | advertiser; product type; billboard type; salesperson |
| `Proveedor Básico` | code; name; tax id (CUIT/NIT); address, city, postcode, phones, email, notes; convertible to full supplier |

#### Materials and document support

| Entity | Key fields |
|---|---|
| `Material` | holder client R; code auto; description R; active R; media type R; publication type R; measure C (press/internet: cm×col; OOH: posters per circuit); duration C (TV/radio seconds); market category O; notes O (recommended: verification provider's creative name); interface code O; material category O; products[] (empty = all); surcharges[]; graphic data (photo, text, optical, disk, colours, extra separation) C; royalty contracts[]; content type O; dynamic categories |
| `Categoría de Materiales` | holder client; manual code; description |
| `Tipo de Material` | code; description; file type |
| `Tipo de Contenido` | media type; code; description; active |
| `Categoría de Archivos a Adjuntar` | origin ∈ {plan, order, estimate}; document type text; may be required by a billing requirement |
| `Modelo de Nota al Pie` | client type; client (none = all); document ∈ {media plan, insertion order, production estimate, production PO}; code; description; notes 1–6; keywords |
| `Categoría/Motivo de Modificación de Órdenes` | category (client/outlet/agency); reason |
| `Código de Auditoría` | code; description; control type ∈ {OK, deficiency}; media types[] with external code and allows-reschedule; origin ∈ {quantity, percentage} |
| `Tipo de Gestión` / `Acción de Gestión` | description; media type or all; origin ∈ {order, plan}; contact ∈ {client, outlet, supplier}; active / actions per type |
| `Taxonomía` | holder client (or all); description; templates for product, plan, item, creative, UTM; active; restrictions (ad servers / sites) |
| `Restricción por Entidad` / `Grupo de Restricciones` | restriction master ∈ {holder client, outlet, supplier, digital publication type}; entity subset; group scope (all or listed clients) |
| `Ponderación de Unidades Equivalentes` | employee category; sub-category; media type; entity type; weight |

#### OOH entities

| Entity | English | Key fields |
|---|---|---|
| `Tipo de Cartel` | Billboard type (CPM municipal face, totem, backlit, gantry, kiosk, column, wall, mega-print…) | code; description; uses circuits flag; allocation mode (bulk-quantity vs. individual face); location filter flag; multi-order flag (split across month end) |
| `Formato de Cartel` | Face format/size | billboard type R; code; description (size text with unit) |
| `Circuito` | Circuit (route/area for posting) | billboard type R; code; description |
| `Estado de Cartel` | Face condition state | code; description; state kind ∈ {OK, needs maintenance, out of circuit, repaired} |
| `Material de Cartel` | Construction material | billboard type R; code; description |
| `Responsable de Cartel` | Responsible sales exec | billboard type R; zone R; system user R |
| `Motivo` (OOH creative) | Poster motif | advertiser R; code auto; media type = OOH; material type (e.g. graphic); description; image file |
| `Cartel` | Billboard face | code auto; internal code; type R; zone R; format R; street R; number; between-streets; landmark; municipal permit ids (Buenos Aires AGIP / SISOP); permit validity; lat/long; notes; rate-card item (active items only); image; construction material; state |
| `Ítem de Ubicación` | Location item | page "under construction" — undefined |
| `Tarifario VP` / `Ítem de Tarifario VP` | OOH rate card & items | Listed in menu only; content not documented (BASE generic rate card vs. advertiser-specific; items reference billboard type + location) |
| `Reserva` | Reservation | own sequence; JobNumber; holder; advertiser; product; billing client; campaign; billboard type (one); zone (one); salesperson; status ∈ {pending face assignment, pending order}; items; faces |
| `Orden VP` | OOH order | own sequence + internal number; JobNumber & derived parties; type; zone; salesperson; client PO number; opening code (split billing); payment terms; currency & FX; supplier commission (billed vs. credit note, condition, %, status); notes; totals; items; faces; motifs (with %); admin control (internal order no., invoice no., credit notes); per-calendar-month sub-orders |
| `Ítem de Orden VP` | Order line | agreement O; currency; tariff type ∈ {N normal, P package}; rate card R; rate item; description; circuits C; number of faces; start date; outings; rate; 4 cascading discounts; 4 credit-note discounts |
| `Fijación` | Posting batch | listing type; billboard type; zone; posting date; per-order lines (product, faces ordered, total to post, changes, carried-over flag); status ∈ {built, closed, reopened}; free extra faces |
| `Convenio VP` | Advertiser agreement | level ∈ {client, client/advertiser, advertiser, advertiser/product}; number (sequential); client reference; description; active; validity from/to; type ∈ {M amount cap, C consumption}; payment ∈ {N normal, A prepaid, C barter}; notes; currency; FX; 4 discounts + 4 credit-note discounts; billable amount; bonus amount; linked rate card |

### 3.3 Proposed canonical schema (JSON-ish)

```jsonc
// --- classification ---
GenericMediaType { id: "02", name, calcBasis: "CM_COL"|"SECONDS"|"ELEMENTS",
                   durationPricing?: "PROPORTIONAL"|"FACTORS"|"MANUAL_PER_DURATION" }
MediaType { id: "07", name, genericTypeId, groupId?, cutoffHour?: "02:00",
            controlsAds: bool, controlWindowDays?: int, freeProgrammeEntry: bool,
            unitOfMeasureUse: "NONE"|"OPTIONAL"|"MANDATORY", lockManualRates: bool,
            baseDurationSec?: int, durationPricing?: enum,
            accounting: { mode: "BRIDGE"|"RESULT", taxedSplit: bool,
                          salesAccount, costAccount, rebateAccount,
                          diffIncomeAccount, diffExpenseAccount, ownAdvertisingCostAccount,
                          untaxed?: {...same} } }
PublicationType { id, mediaTypeId, name, active, isDefault: bool,
                  measureSource: "TYPE"|"PLAN", defaultMeasure?, ownRate: bool,
                  digitalMode?: "PROGRAMMATIC"|"AUCTION"|"NONE",
                  outletMeasureExceptions: [{outletId, measure}],
                  defaultSurchargeIds: [], applicableMediaTypeIds: [],
                  additionalItemAccounts?: {sales, cost} }
// --- geography ---
Country{id,name} Region{id,countryId,name} Zone{id,name,countryId?,regionId?,
  providerCodes:{[providerId]:{[interfaceCode]:string}}} City{id,zoneId,name}
ClientRegion{clientId, code: "ABC", name, zoneIds:[]}
// --- outlets ---
MediaOutlet { id: "0423", name, zoneId, mediaTypeId, genreId?, pressGraphicType?,
  cmAdjustFactor?, stationCode?, active, validFrom?, validTo?,
  controlsAds: "YES"|"NO"|"INHERIT", allowsGlobalOrder: bool, currency,
  agencyCodeAtOutlet?, outletGroupId?, contactId?, email?, hubAssociated?: bool,
  suppliers: [{supplierId, isDefault, active}],          // min 1, exactly 1 default
  admin: { materialFormats?, materialLeadDays?, dueDateRule: DueDateRule,
           vat: "TAXED_100"|"TAXED_50"|"UNTAXED", taxJurisdiction },
  programming: { origin: "OWN"|"NETWORK", networkOutletId?, isNetwork: bool, daypartSetId },
  location: {countryId, regionId, cityId, address?, phone?, postcode?, notes?},
  externalCodes: {[providerId]: string},
  orderAlerts?: [{supplierId, thresholdAmount, message}] }
DueDateRule { kind: "SUPPLIER_TERMS"|"MONTH_PLUS_DAYS"|"FORTNIGHT_PLUS_DAYS"|
                    "PER_SPOT_DAYS"|"INVOICE_DATE_PLUS_DAYS", days?: int }
Programme { id, outletId, kind: "PROGRAMME"|"TIME_BLOCK"|"PRESS_SECTION"|"DIGITAL_PLACEMENT",
  name, weekdays: [bool x7], start?, end?, genreId?, rateBasis: "OWN"|"TIME_BLOCK",
  timeBlockId?, pageSection?, cm?, columns?, modules?, active, notes?, externalProviderId? }
DaypartSet { id, name, bands: [{name, weekdays:[bool x7], start, end}] }
DurationCoefficientTable { id, criterion:"OUTLET"|"SUPPLIER", outletId?, supplierId?,
  clientId?, publicationTypeId?, mediaTypeId?, factors: {[sec 1..200]: number} }
Target { id, name, marketId, genericTypeId, active, population, universe, pct,
  sample?, minBase?, audience:"PERSONS"|"HOUSEWIVES"|"HOUSEHOLDS", ses?, sex?, ageFrom?, ageTo? }
ProgrammeTargetMap { clientId, productId|"ALL", mediaTypeId|"ALL", outletId,
  defaultTargetId, overrides:[{programmeId,targetId}] }
// --- commercial defaults ---
Surcharge { id, name, mediaTypeId|null }
DefaultSurcharge { outletId, clientId, surchargeId, value, mode:"FIXED_ADD"|"PCT_OF_GROSS", active }
AdditionalCost { id, mediaTypeId, name, orderTo:"OUTLET"|"SUPPLIER", active, internal: bool,
  sameOutletAsItem: bool, publicationTypeId, currency, calc:"PCT"|"FIXED", pct?, amount?,
  clientOverrides:[{clientId, calc, pct?, amount?}] }
AgencyServiceRate { clientId, mediaPct, productionPct, mediaRebatePct, productionRebatePct,
  products:[{productId, mediaPct, productionPct, mediaRebatePct, productionRebatePct}] }
AgencyServiceByPubType { genericTypeId:"DIGITAL", publicationTypeId, defaultPct,
  clients:[{clientId,pct}], allowedBuyTypeIds:[] }
// --- creatives ---
Material { id, clientId, name, active, mediaTypeId, publicationTypeId, measure?, durationSec?,
  marketCategoryId?, notes?, interfaceCode?, materialCategoryId?, contentTypeId?, languageId?,
  productIds: [] /* empty = all */, surchargeIds: [], graphic?: {photo,text,optical,disk,colours,extraSeparation},
  royaltyContractIds: [], externalCodes:{} }
// --- OOH ---
BillboardType { id, name, usesCircuits: bool, allocation:"BULK_QUANTITY"|"INDIVIDUAL",
  filterByLocation: bool, allowsMultiOrder: bool }
Billboard { id, internalCode, typeId, zoneId, formatId, circuitId?, street, number?,
  betweenStreets?, landmark?, permit:{municipalCode?, taxCode?, validFrom, validTo},
  geo?:{lat,lng}, notes?, rateItemId?, imageRef?, constructionMaterialId, stateId }
BillboardState { id, name, kind:"OK"|"NEEDS_MAINTENANCE"|"OUT_OF_CIRCUIT"|"REPAIRED" }
Motif { id, advertiserId, mediaType:"OOH", materialType, name, imageRef }
OohReservation { id, jobNumber, parties:{holderId,advertiserId,productId,billingClientId,campaign},
  billboardTypeId, zoneId, salespersonId, status:"PENDING_FACES"|"PENDING_ORDER"|"ORDERED"|"REJECTED",
  items:[OohItem], billboardIds:[] }
OohOrder { id, internalNo, reservationId?, jobNumber, parties, billboardTypeId, zoneId,
  salespersonId, clientPoNumber?, openingCode?, paymentTerms, currency, fxRate?,
  supplierCommission?:{settlement:"INVOICE"|"CREDIT_NOTE", condition, pct, status},
  notes?, items:[OohItem], billboards:[{billboardId, from, to}],
  motifs:[{motifId, sharePct}], monthlySlices:[{month, amount, invoiceNo?, creditNotes:[]}],
  status:"DRAFT"|"ASSIGNED"|"MOTIF_ASSIGNED"|"POSTED"|"INVOICED"|"REJECTED",
  clientApproval:"PENDING"|"APPROVED"|"APPROVED_FOR_BILLING" }
OohItem { agreementId?, currency, tariffType:"N"|"P", rateCardId, rateItemId, description,
  circuitIds?:[], faces:int, startDate, outings:int, rate,
  discounts:[pct x≤4], creditNoteDiscounts:[pct x≤4] }
PostingBatch { id, billboardTypeId, zoneId, postingDate, status:"BUILT"|"CLOSED",
  lines:[{orderId, productId, facesOrdered, facesToPost, adjustment, carriedOver}] }
OohAgreement { id, level:"CLIENT"|"CLIENT_ADVERTISER"|"ADVERTISER"|"ADVERTISER_PRODUCT",
  clientId?, advertiserId?, productId?, clientRef?, name, active, validFrom, validTo?,
  type:"AMOUNT_CAP"|"CONSUMPTION", payment:"NORMAL"|"PREPAID"|"BARTER", currency, fxRate?,
  discounts:[≤4], creditNoteDiscounts:[≤4], billableAmount, bonusAmount, rateCardId }
```

---

## 4. OOH document lifecycles

### 4.1 Billboard face (inventory unit)

```
created (state=available/OK, permit valid)
   ├─► assigned to reservation (blocked)  ─► released (reservation rejected / "release reserved")
   ├─► assigned to order (occupied for dates) ─► posted ─► period ends ─► free
   ├─► NEEDS_MAINTENANCE  (still assignable; e.g. no light, broken glass)
   ├─► OUT_OF_CIRCUIT     (not assignable) ─► REPAIRED (assignable again)
   └─► permit expired / inactive (should not be sold; implied)
```
Every state change is timestamped and appears in the state audit (which faces break most often, how long repairs take, how much construction material is needed; may motivate relocating a face) `[mp302806][mp302814]`.

### 4.2 Reservation → Order

1. **Reservation** created by a salesperson to hold inventory. Status starts *pending face assignment*, then *pending order* once faces are assigned `[mp302805]`.
2. **Confirmation**: when the advertiser's PO arrives, "generate order" converts it; alternatively an order is created directly without reservation.
3. **Rejection** of a reservation or order that will not proceed is the recommended way to free faces for other clients.
4. **Order** carries a client PO number, payment terms (default from billing client, editable), currency/FX, optional supplier commission and agreement.
5. **Face assignment** by a responsible user (profile restricted), with release options (block occupied, release reserved, release free-of-charge, release all) `[mp302812]`.
6. **Motif assignment** (one or more motifs, each with a share %) — prerequisite for posting.
7. **Monthly slicing**: an order spanning calendar months is shown as one order per month so each month can be invoiced separately.
8. **Client approval states** used in investment statistics: not approved by client → approved by client → approved for billing `[mp301443]`.
9. **Invoicing**: invoice number and any credit notes are written back to the order's administrative control section `[mp302805]`.
10. **Copy**: a repeat buy is created by copying an order to new dates.
11. **Delete** only if not invoiced and no motifs assigned.

### 4.3 Posting order (installation / rotation)

Three stages `[mp302856]`:

| Stage | Who | What | Exit |
|---|---|---|---|
| Build (`Armado`) | Posting coordinator | Filter by billboard type (one batch per type), zone, posting date → system lists orders to post, flags faces carried over from the previous posting, shows ordered vs. to-post totals | Save |
| Control close (`Cierre de control`) | Commercial lead with special rights | Adjust faces-to-post up or down (difference shown as "changes"); may grant extra free-of-charge faces | "Close posting" locks it; only the responsible can "reopen" |
| Posting sheet (`Orden de fijación`) | Crew | Printable/exportable list: which image to remove and which motif image to put up, per face/circuit | Physical posting |

Rotation is therefore modelled as a periodic posting batch replacing the previous motif with the new one. Photo evidence of installation (proof-of-posting) is **not** described; the only images are the face reference image and the motif image.

### 4.4 Maintenance

Handled through face states and the audit report (§4.1). There is no work-order entity for repairs; repair need is inferred from state and the audit is used to plan materials.

### 4.5 Removal

Not explicitly modelled. Implicitly, a face becomes free at the end of the ordered period, and the next posting sheet instructs removal of the old image. Permanent removal of a face would be an inactive state or deletion (only if unused).

### 4.6 Agreement (convenio) running account

```
created (active, validity) → orders linked → consumption accumulates
   type M: blocks further linking once billable amount is fully consumed
   type C: no cap, account only
payment A: generates an instalment for advance invoicing, consumption then tracked
payment C: supplier settles through goods/services (barter)
→ expired / inactive (cannot be linked)
```
The agreement tracks only linked **orders**, not invoices; the vendor recommends using advance-sale invoicing for financial control. Differences between the agreement account and the advance-sale balance arise when invoices/credit notes are issued without linking an order `[mp301549]`.

---

## 5. Business rules and calculations

**Classification & integrity**

1. A media outlet belongs to exactly one media type and one zone; to sell the same outlet in another zone or media type, a separate outlet record is required (copy function with zone multi-select) `[mp301056]`.
2. A media plan has exactly one media type; splitting TV into capital/interior media types forces separate plans `[mp301045]`. Vendor advice: avoid zone splits at media-type level; report by zone groups instead `[mp302675]`.
3. Each media type has at least one publication type; the system auto-creates a default "generic rate" publication type per media type `[mp301041]`.
4. Every outlet has ≥1 supplier link and exactly one default supplier; only suppliers enabled for media are eligible `[mp301056]`.
5. Records used in any transaction cannot be deleted, only deactivated (universal).
6. Dynamic categories on an item cannot be changed if the item has a client-invoiced spot/month, a closed order, a rejected order, or is included in a general plan close `[mp309246]`.
7. Material with no products selected is valid for all products of the client `[mp301012]`.
8. If an attachment category is linked to a mandatory billing requirement, the attachment must exist before the plan/estimate can be approved or invoiced `[mp302777]`.
9. When a media type has `pauta_libre = No`, manual plan items may only use registered programmes; with `Yes`, free-text programmes are allowed `[mp301045]`.
10. When `impide_tarifas_manuales` is set, only users at the top access level (1A) may enter/edit rates, discounts and surcharges `[mp301045]`.
11. Ad-control default cascades: outlet value Yes/No overrides; "per media type" inherits the media type flag `[mp301056]`.
12. Outlets requiring one order per insertion set `permite_orden_global = No`; default Yes `[mp301056]`.

**Duration pricing (seconds-based media)**

13. Base rate is quoted for `duracion_base` `[mp301045]`.
14. *Proportional*: `rate(d) = baseRate × d / baseDuration`.
15. *Respects factors*: `rate(d) = baseRate × factor(d)` where factor table (seconds 1–200) holds explicit factors; for any second without an entry the system falls back to proportional `[mp301521][mp302675]`. The base duration has factor 1. Example given: 1–15 s may all cost the same as 15 s.
16. *Does not respect factors*: rate must be entered per duration in the rate card; missing durations fall back to proportional `[mp302675]`.
17. Coefficient tables are resolved by criterion (outlet or supplier), optionally narrowed to client, publication type and media type; supplier-based criterion is a Dominican Republic option disabled by default `[mp301521]`. Suggested resolution order for a rebuild: most specific match (supplier+outlet+client+pubType+mediaType) → … → outlet-only → proportional.

**Press**

18. For modular press outlets, a cm adjustment factor converts modules to centimetres (manual or from a precomputed list) `[mp301056]`.
19. Publication type may impose the default measure (cm × columns for press, seconds for TV/radio) or leave it to the plan; per-outlet measure exceptions override `[mp301041]`.

**Dayparts & time**

20. A daypart set must cover all 7 days × 24 h without overlap; the same band name may appear on multiple rows (e.g., LATE Mon–Fri vs. Sat–Sun) and is reported as one band `[mp301084]`.
21. Programme ordering uses the media type's cut-off hour: times between 00:00 and the cut-off sort after 23:59 of the previous broadcast day `[mp301045]`. Formula: `sortKey = time < cutoff ? time + 24h : time`.

**Audience**

22. Target values: `universe = population × pct/100` or `pct = universe / population × 100` depending on entry mode `[mp301083]`.
23. Importing programmes: when an imported programme matches an existing one by similar name/time, user chooses (a) merge — average rating becomes the sum of both programmes, or (b) create a variant (suffix with emission-day abbreviation) `[mp301118]`.

**Surcharges, discounts, additional costs, fees**

24. Default surcharge value per (outlet, client, surcharge): fixed amount added to the item gross (`acumulado`) or % of item gross (`porcentaje`) `[mp306204]`. Applied only when the surcharge is ticked on the material used in the plan item; computed at plan time `[mp301204]`. Publication types may also carry default surcharges `[mp301041]`.
25. Discounts off the gross rate are labelled by the discount master; labels do not carry values `[mp305204]`.
26. Additional cost: applying it to a parent item creates a child item that inherits spot quantity and states; amount = parent amount × % or a fixed amount; per-client overrides; summed over flagged items; can be invoiced separately or with the plan, and partially per parent item `[mp309267]`.
27. Additional cost currency is fixed per cost record (one record per currency); display currency changes only convert visually using the plan-header FX rate `[mp309267]`.
28. Agency service: `fee = base × mediaPct` and `rebate = base × mediaRebatePct` (production analogues) with product-level overrides of client defaults; "apply to all" copies client % to all products `[mp306050]`.
29. Digital fee by publication type: client-specific % overrides default %; usable publication types restricted by buy type `[mp302927]`.
30. Hub revenue sharing: when enabled, agency-service income is split between hub and agency per % on the plan, defaulted from the product `[mp301062]`.

**Digital**

31. `itemCost = quantity × rate` where quantity is units, clicks or impressions per the calc type; fixed = rate `[mp302840]`.
32. Ad-serving cost = format quantity (normally impressions / 1000) × ad server cost for the tracking type; client price and supplier cost may differ, producing agency income `[mp302841][mp302843]`.
33. Taxonomy quarter tags: `Q = floor((month + 2) / 3)`, with or without "Q" prefix; year tags available as 4 or 2 digits `[mp302894]`.

**Payment due dates (outlet rule)** `[mp301056]`

34. *Supplier terms*: use supplier's payment condition at planning time.
35. *Month + N days* (30, 15, or custom): `due = lastDayOfMonth(airDate) + N`.
36. *Fortnight + N days* (15, 10, custom): if air date day ≤ 15 → `due = 15th + N`; else `due = lastDayOfMonth + N`.
37. *Per-spot days*: `due = airDate + N` for each spot.
38. *Invoice date + N*: `due = supplierInvoiceDate + N`.

**Tax**

39. Outlet VAT condition: 100% taxed, 50% taxed (VAT applied on half the base), or untaxed `[mp301056]`. `vat = base × (taxedShare) × vatRate`.
40. Tax jurisdiction (province/district) on the outlet drives local tax treatment.
41. VAT condition changes are propagated to existing plans via a retroactive process from an effective date `[mp301056]`.

**Ad verification**

42. Each verification code is OK or Deficiency; deficiencies specify origin (by quantity of contracted spots or by % for package deals) and whether rescheduling is allowed; one OK code is the configured closing-adjustment code `[mp301082]`.
43. Verification window: `dias_limite` from publication date on media types that control ads `[mp301045]`.

**OOH**

44. One order/reservation = one billboard type × one zone `[mp302805]`.
45. Rate card is mandatory to order (generic BASE or advertiser-specific); rate item ≠ face assignment `[mp302805]`.
46. Normal tariff: `gross = outings × rate × faces` `[mp302805]`.
47. Package tariff (P): `gross = entered rate`, ignoring faces, outings and dates `[mp302805]`.
48. CPM faces: one outing = 3 consecutive days; 2 outings = a full week (the type master describes split blocks such as Sun–Tue and Wed–Sat) `[mp302805][mp302808]`.
49. Discounts: up to 4 cumulative discounts reduce the invoice; up to 4 credit-note discounts are each issued as a separate credit note; all computed on the total amount `[mp302805]`. Recommended deterministic interpretation: `net = gross × Π(1 − dᵢ)` for cumulative; each credit-note discount `cnⱼ = gross × cⱼ` (confirm whether base is gross or post-cumulative net — see §11).
50. Bulk-allocation billboard types (e.g., CPM) decrement available quantity in a circuit (e.g., 400 faces) without addressing individual faces; individual types (e.g., mega-prints) require face-level assignment `[mp302808]`.
51. Multi-order flag on billboard type allows ordering blocks that straddle month end and billing them together or separately `[mp302808]`.
52. Orders spanning months are sliced per calendar month for billing `[mp302805]`.
53. Motif share %: the sum across motifs on an order should equal 100% of faces `[mp302805]`.
54. A face can only be assigned if its state kind is OK, needs-maintenance or repaired (not out-of-circuit) and it is free on the dates `[mp302806][mp302805]`.
55. Turning off the restriction to faces linked to the selected rate item requires access level 1 on the order module `[mp302805]`.
56. Supplier commission on an order can be settled by invoicing it or by receiving a credit note; percentage and status are tracked `[mp302805]`.
57. Foreign-currency orders require an FX rate to local currency `[mp302805]`.
58. Split billing (opening code) only if the JobNumber's billing client code is the wildcard `*` (billing client chosen on the order) `[mp302805]`.
59. Agreement type M blocks linking once billable amount is consumed; type C has no limit; agreements are single-currency; inactive or out-of-validity agreements cannot be linked; open-ended agreements stay active indefinitely `[mp301549]`.
60. Posting closed ⇒ no edits or added orders until reopened by the responsible role `[mp302856]`.
61. Investment statistics show agency commission per line alongside ordered amounts and share % `[mp301443]`.

---

## 6. Accounting impacts

**Media type ledger configuration** `[mp301045]` (accounts identified by an "observation code" on the chart of accounts):

| Purpose | Bridge-account mode | Result-account mode |
|---|---|---|
| Sales (normal) | obs. 01 (client investment bridge) | obs. 20–23 (21 client sales; 22 fee/honoraria) |
| Cost (normal) | obs. 02 (supplier investment bridge) | obs. 39 |
| Outlet rebates | obs. 23 | obs. 23 |
| Differences income / expense | obs. 23 | obs. 23 |
| Cost for "own advertising" jobs | obs. 36 | obs. 36 |

- Mode depends on special config "uses bridge account"; a further option separates taxed vs. untaxed income accounts (adds a second account tab).
- Prerequisite: bridge accounts 01, 02, 23 and result accounts 21/22, 39, 23 must exist before creating media types.

**Publication type additional-item accounts** `[mp301041]`: when "different accounts for additional costs" is enabled, sales/cost accounts for additional items are set per publication type; allowed codes 20 (agency service honoraria), 21 (client sales), 22 (monthly fee honoraria), 70 (balance-sheet account with client breakdown), IF (digital-services gross-income tax perception). If not set, media-type accounts apply. Balance-sheet accounts used as sales accounts are **excluded from the gross-income provision**.

**Publisher publication types** carry their own ledger account `[mp302671]`.

**OOH**: orders are invoiced per monthly slice; cumulative discounts reduce the invoice, credit-note discounts produce separate credit notes; the order listing is reconciled against the VAT sales sub-ledger `[mp302811]`. Prepaid agreements generate advance-sale invoices whose balance is consumed by later consumption invoices `[mp301549]`. Supplier commission may be invoiced or received as credit note.

**Hub mode**: billing matrix between hub, agency and client (who invoices space; who invoices agency service to whom; shared agency-service income %; "order-only" plans that do not create a receivable) `[mp301062]`.

---

## 7. Cross-module handoffs

| From → To | Handoff |
|---|---|
| Media masters → Rate cards/contracts | Outlet, programme/time block, publication type (own-rate flag), daypart, duration base & pricing mode, coefficients, currency |
| Media masters → Media planning | Allowed outlets/programmes, targets per client/programme, surcharges via materials, additional costs, fee %, digital formats/calc/buy types, funnels, platforms, ad servers, dynamic categories, restrictions |
| Planning → Insertion orders | Outlet default supplier, global-order flag, agency code at outlet, advertiser code, supplier–client codes, footnotes, modification reasons |
| Orders → Ad verification | Controls-ads flag, window days, audit codes, monitoring channel mapping, material interface codes/names for auto-matching |
| Orders → Supplier invoicing/payables | VAT condition, jurisdiction, due-date rule, retroactive VAT |
| Plans/orders → Client billing | Fee %, additional-cost children (separate or combined billing), attachments required by billing requirements |
| Media masters → Accounting | Media-type and publication-type accounts, gross-income provision exclusion |
| External providers ↔ Masters | Ratings/programme import, plan evaluation export/import, monitoring import, electronic orders (Chile), taxonomy export to ad servers/sites |
| Production module | Royalty contracts linked to materials; production fee %; footnotes for production estimates/POs |
| JobNumbers/Projects | Advertiser mandatory when enabled; hub agency filter by holder client; OOH orders inherit parties from JobNumber |
| OOH → Billing/Accounting | Monthly order slices, invoices, credit notes, advance-sale balances, salesperson commission (via salesperson assignment) |
| HR/Productivity | Equivalent-unit weights by employee category |

---

## 8. Configuration and country-specific behaviour

**Special configuration flags referenced**: is media hub; has advertisers; generates additional costs; different accounts for additional costs; uses digital/internet planning; uses agency service per item in digital media; uses basic suppliers; uses equivalent units; uses bridge account; separate taxed/untaxed income accounts; closing-adjustment audit code; duration coefficient by supplier (DR); user profile levels (1A for manual rates; level 1 for OOH face-restriction override).

| Country / client | Behaviour |
|---|---|
| Argentina | Agency register number (RAP) on agencies; tax id CUIT; digital-services gross-income tax perception account (IF); billboard municipal permit codes (Buenos Aires tax agency and works permit system) |
| Chile | Intermediary provider distributes TV programme grids daily and receives electronic orders; external provider must be set up before planning; daily grid import |
| Dominican Republic | Duration coefficients by supplier (+ outlet, client, publication & media type) |
| USA / Puerto Rico | Language master assigned to materials |
| Mexico (Televisa) | "Module buy" screen exists but is undocumented |
| Telefónica (client) | Supplier–client code cross-reference and client-specific outlet codes for orders/reports |
| Colombia etc. | Tax id label NIT |

---

## 9. Reports and KPIs

| Report | Content / KPI | Ref |
|---|---|---|
| Restriction listing | Clients covered by each restriction group/type/entity | mp302930 |
| Publication type listing | Publication types with assigned accounts | mp302005_tippub |
| Supplier–outlet assignment | Outlets per supplier; copy associations to another supplier | mp302933 |
| Order modification reasons | Outlets/clients causing most cancellations | mp309245 |
| Equivalent units | Workload/productivity per employee | mp302683 |
| OOH face listing | General / by start date / by end date / by client / by advertiser; occupancy & state; filter by type, zone, format, material, state, street | mp302810 |
| OOH orders & reservations listing | Orders, reservations, orders without motif, orders not invoiced; by party, salesperson, order/billing status; invoice numbers; discounts net vs credit-note; pivot export | mp302811 |
| OOH planning – occupied / available | Faces occupied vs. available per date by client; available by period/type/format/zone | mp302812 |
| Face state audit | State change history and timing; frequency of maintenance | mp302814 |
| Responsibles listing | Full / by type / by zone / by person | mp302816 |
| Agreement running account | Orders consuming each agreement; balance | mp301556 |
| Agreements listing | Agreements per client/advertiser with pending balance | mp301553 |
| OOH investment statistics | Ordered amount by holder/billing client, advertiser, product, salesperson, origin; share %; agency commission; approval status; charts | mp301443 |

Candidate KPIs: occupancy rate = occupied face-days / available face-days; unsold distressed inventory near date; mean time to repair; faces out of circuit; orders without motif ≤ N days before posting; unbilled orders; agreement burn rate; salesperson revenue and commission.

---

## 10. Agentic-skill implications

### 10.1 Atomic jobs (skills)

| Skill | Input | Output | Deterministic tool? |
|---|---|---|---|
| `media-master.upsert-outlet` | outlet payload | validated outlet | Validator: one default supplier, zone/type uniqueness, VAT enum, due-date rule |
| `media-master.clone-outlet-to-zones` | outlet id, zones | n outlets | Yes |
| `media-master.import-programme-grid` | provider file, market, dates | programme upserts + duplicate decisions | Parser + fuzzy matcher; human-in-loop for duplicates |
| `media-master.validate-daypart-set` | bands | coverage gaps/overlaps | **Yes** (7×24 coverage check) |
| `media-master.sort-broadcast-grid` | programmes, cutoff | ordered list | **Yes** |
| `rates.duration-price` | base rate, base duration, mode, factor table, target duration | rate | **Yes** |
| `rates.resolve-coefficient-table` | outlet, supplier, client, pubType, mediaType | table id | **Yes** |
| `plan.apply-surcharges` | item gross, material surcharges, defaults | surcharge lines | **Yes** |
| `plan.generate-additional-cost-children` | flagged items, cost config, client | child items | **Yes** |
| `plan.compute-agency-fee` | client, product, base, pub type | fee & rebate | **Yes** |
| `digital.compute-item-cost` / `digital.adserving-cost` | qty, rate, calc type | amount | **Yes** |
| `digital.render-taxonomy` | template, entity context, external codes | naming string / UTM | **Yes** (tag interpolation, `{L}` lowercase modifier) |
| `payables.compute-due-date` | rule, air date / invoice date | due date | **Yes** |
| `tax.vat-on-media` | base, outlet VAT condition, rate | VAT | **Yes** |
| `audience.target-values` | population / universe / pct | completed target | **Yes** |
| `external.map-codes` | provider, entity, client | code | Lookup tool |
| `ooh.check-availability` | type, zone, format, dates, street | free faces / free quantity | **Yes** (interval overlap on face assignments + state filter) |
| `ooh.create-reservation` / `ooh.confirm-order` | JobNumber, type, zone, items | reservation/order | Partially (validations) |
| `ooh.price-item` | tariff type, faces, outings, rate, discounts | gross, net, credit notes | **Yes** |
| `ooh.slice-by-month` | order dates & amount | monthly slices | **Yes** (proration rule must be set — see §11) |
| `ooh.assign-faces` | order, release options | assignment | Yes + permission check |
| `ooh.assign-motifs` | order, motifs, shares | link | Validator: shares sum 100% |
| `ooh.build-posting-batch` / `close` / `issue-sheet` | type, zone, date | batch, sheet | Yes; close requires role approval |
| `ooh.update-face-state` | face, new state, note | audit entry | Yes |
| `ooh.agreement-consume` | agreement, order amount | new balance or block | **Yes** |
| `ooh.reconcile-orders-vs-vat-ledger` | orders, sales ledger | breaks | **Yes** |

### 10.2 Controls to enforce in tools

- Referential: never hard-delete used masters; deactivate.
- Single default supplier per outlet; single media type per plan; one billboard type × zone per OOH order.
- Lock rules on dynamic categories once item is billed/closed/rejected.
- Permission gates: manual rates (top level), OOH face restriction override (level 1), posting reopen (responsible only), hub/fee % editing by profile.
- Mandatory attachments for billing requirements.
- Rate card mandatory before ordering OOH; motif mandatory before posting.
- Agreement cap and validity check before linking.
- Ledger accounts must exist with correct observation codes before media types can be used for postings.

### 10.3 Exceptions to surface to humans

Duplicate programme names on import; daypart gaps/overlaps; outlets missing default supplier or external code; VAT condition changes requiring retroactive run; faces with expired municipal permits still sellable; orders without motifs near posting date; faces out of circuit assigned to future orders; agreement balance vs. advance-sale balance mismatch; reservations stale (no progress) blocking inventory.

---

## 11. Gaps and ambiguities

1. **OOH rate cards** (`Tarifarios de Vía Pública`, `Ítems de Tarifario`, `Actualización Tarifarios de Medios`) are only menu entries; structure (per face, per circuit, per period, seasonality) is undocumented.
2. **Discount base**: "all discounted over the total amount" conflicts with "cumulative" — cascade vs. additive vs. credit-note base unknown.
3. **CPM outings**: 1 outing = 3 consecutive days but 2 outings = one week (7 days), and the type master mentions Sun–Tue / Wed–Sat blocks; exact calendar logic unclear.
4. **Monthly slicing proration**: whether amounts split by days, by outings, or by start month is not specified.
5. **Taxes on OOH orders** (VAT rate, municipal fees, permit costs), production/printing and installation costs are not described at all; no production-cost lines on OOH orders.
6. **Photo proof-of-posting**, removal orders, and maintenance work orders do not exist in the manual.
7. **Salesperson commission** calculation: assignment exists (advertiser × product type × billboard type) but no rate or computation is documented.
8. **Supplier commission** on OOH orders: who the "supplier" is in a seller-side context is unclear.
9. **`Ítems Ubicación de Vía Pública`** is "under construction"; `Factores Específicos`, `Visuales`, `Plazas de Medición de Audiencia`, `Revistas`, `Números de Revista`, `Tipos de Interfaz con Proveedores Externos`, `Conceptos de Agencia Cloud`, `Compra por módulos (Televisa)` are stubs.
10. Programme genre page text appears garbled (fiction vs. referential families mixed); only the master behaviour is reliable.
11. **50% taxed VAT** semantics (half the base or half the rate) is assumed.
12. Ad-verification "percentage origin" — threshold semantics not given.
13. Additional cost "internal/external" flag meaning is unclear (possibly whether it creates a supplier order).
14. Precedence among publication-type default surcharges, material surcharges and default surcharge values not specified.
15. Hub billing matrix options are listed but the resulting document flows (which invoices are generated) are not.
16. Duration coefficients: whether the factor applies to the base-duration rate or to proportional rate is implied (base) but not explicit; range limited to 200 s.
17. Equivalent-unit "entity type" list is assumed to be plans/orders/cancellations only.
18. Taxonomy `{L}` modifier is shown in examples (likely lowercase) but not defined.
19. Relationship between `Material` (generic, OOH measure "posters per circuit") and OOH `Motivo` (advertiser-level with image) is overlapping; it is unclear whether OOH orders can use generic materials.
20. Agreement "bonus amount" usage (free inventory value?) and how bonus consumption is recorded is not described.
