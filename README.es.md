# ERP agéntico para agencias de publicidad

Skills abiertas para que tu asistente (las apps de Claude, ChatGPT o Gemini, o Claude Code, Codex y Gemini CLI) opere **todo el back office de una agencia**: JobNumbers, producción, planificación y compra de medios, control de avisos, facturas de proveedores, facturación a clientes, cobranzas, pagos, tesorería, impuestos, contabilidad, cierre mensual y rentabilidad.

La versión 0.2 se basa en una **ingeniería en reversa funcional de un ERP de agencias maduro de Latinoamérica**: se analizaron ~1,330 páginas públicas de su ayuda y se reescribieron como una [referencia funcional del ERP](docs/erp-reference/README.md) con procesos, ciclos de vida de documentos, reglas numeradas, impactos contables, handoffs entre módulos y comportamiento por país. Cada skill cita esas reglas.

**42 skills autocontenidas · 26 calculadoras deterministas de solo lectura (también como MCP local) · un solo `AGENCY.md` con la política de tu agencia que leen todas las skills y todos los agentes · referencia funcional del ERP · registro de MCP oficiales · 122 casos de comportamiento sintéticos · descargas listas para las apps de Claude y Gemini, paquete para ChatGPT/Gem, instalador npm/npx, marketplace de plugins de Claude Code y extensión de Gemini CLI.** Licencia MIT. No incluye credenciales, llaves ni suscripciones; no es un ERP alojado ni ejecuta pagos por sí solo.

> Proyecto independiente, sin afiliación con ningún proveedor de ERP. La referencia describe comportamiento funcional públicamente documentado con redacción propia; no redistribuye código, pantallas ni texto del manual.

## Empieza aquí (sin terminal)

### ¿Qué es esto, en simple?

Es un paquete gratuito que le enseña a **Claude, ChatGPT o Gemini** a operar la parte "invisible" de una agencia: todo lo que pasa desde que un cliente dice "sí" hasta que el dinero entra, se les paga a los medios y sabes cuánto ganaste. Presupuestos, planes de medios, órdenes a TV, radio y digital, revisar que los anuncios sí salieron, cruzar facturas, cobrar, pagar y cerrar el mes. Ahí es donde las agencias pierden margen sin darse cuenta.

Trae **42 skills**, una por cada paso, basadas en cómo funciona un ERP real de agencias en Latinoamérica. La regla de oro: **la IA prepara, revisa y calcula; una persona aprueba.** Nunca paga, factura ni envía nada por su cuenta.

### ¿Por qué skills y no prompts?

Un **prompt** es explicarle algo de palabra a alguien nuevo cada vez: depende de cómo lo digas ese día y cada quien lo explica distinto. Una **skill** es darle a ese colaborador su **manual de procedimientos con calculadora y formatos**, guardado en su escritorio:

- **Se activa sola cuando hace falta.** Pides "revisa esta factura del canal" y el asistente abre la skill correcta.
- **Siempre igual**, sin importar quién del equipo pregunte.
- **Los números no los inventa la IA:** cada skill trae calculadoras exactas para comisiones, descuentos, rebates y vencimientos.
- **Trae el contexto que un prompt no aguanta** (reglas del negocio, formatos, qué hacer cuando algo no cuadra) y solo lo lee cuando lo necesita.

### Instálalo en tu app

**Claude (claude.ai o app de escritorio)**

1. Descarga una o varias skills de la tabla de abajo. Para empezar: [agency-orchestrator](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-orchestrator.zip), [agency-client-billing](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-client-billing.zip) y [agency-cash-forecast](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-cash-forecast.zip). **No descomprimas el .zip.**
2. Entra a [claude.ai/customize/skills](https://claude.ai/customize/skills) (menú **Customize → Skills**).
3. Sube el .zip y activa la skill. Repite con cada una.
4. Abre un chat nuevo y pide algo de los ejemplos. Claude usa la skill solo.

> Requiere tener activada la ejecución de código. Disponible en los planes Free, Pro, Max, Team y Enterprise.

**Gemini (gemini.google.com o app)**

1. Descarga los mismos .zip de la tabla.
2. En Gemini abre **Configuración → Skills → Subir**, elige el .zip, revisa y toca **Crear**.
3. Úsala en cualquier chat.

> Por ahora funciona con cuentas personales de Google (no de trabajo o escuela) y con la Actividad activada. Si tu cuenta no lo permite, usa la opción "Gem" de abajo.

**ChatGPT (GPT o Proyecto)**

1. Descarga [assistant-instructions.txt](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/assistant-instructions.txt), [agency-erp-knowledge.md](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-erp-knowledge.md) y [agency_tools.py](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency_tools.py).
2. Crea un **GPT** (Explorar GPTs → Crear → Configurar) o un **Proyecto**.
3. Pega el contenido de `assistant-instructions.txt` en **Instrucciones**.
4. Sube `agency-erp-knowledge.md` y `agency_tools.py` en **Conocimiento** (o Archivos del proyecto).
5. Activa **Intérprete de código y análisis de datos** para que use las calculadoras. Guarda como "Solo yo".

**Gemini con Gem** (alternativa para cuentas de trabajo): crea un Gem, pega `assistant-instructions.txt` en las instrucciones y sube `agency-erp-knowledge.md` como conocimiento.

> Crear GPTs, Proyectos o Gems depende de tu plan. En estas opciones el asistente sigue las mismas reglas desde el archivo de conocimiento; la experiencia más completa son las skills en Claude o Gemini.

### Prueba con estos pedidos

- *"Abre una campaña nueva para el cliente Acme, producto Bebidas, y dime qué falta para arrancar."*
- *"Aquí está la factura del canal y el reporte de emisión. ¿Me están cobrando spots que no salieron?"*
- *"Con estas facturas por cobrar y por pagar, ¿cómo se ve mi caja las próximas 8 semanas?"*
- *"Calcula el rebate de este mes con la escala del contrato adjunto. Solo propónmelo."*

Puedes trabajar con Excel, PDF o CSV sin conectar nada. Conectar tus apps es opcional y siempre lo autorizas tú.

### Las 42 skills

<details>
<summary>Ver tabla con enlaces de descarga</summary>

| Etapa | Skill | Para qué | Descargar |
|---|---|---|---|
| Arranque | `agency-orchestrator` | Dirige el trabajo completo y te dice qué sigue | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-orchestrator.zip) |
|  | `agency-integrations` | Qué apps conectar en cada etapa | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-integrations.zip) |
|  | `agency-access-governance` | Permisos, aprobaciones y segregación de funciones | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-access-governance.zip) |
|  | `agency-master-data` | Clientes, proveedores, medios y cuentas | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-master-data.zip) |
| Clientes y contratos | `agency-onboarding` | Alta de cliente, marcas y brief | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-onboarding.zip) |
|  | `agency-job-lifecycle` | Abrir, mover y cerrar campañas (JobNumber) | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-job-lifecycle.zip) |
|  | `agency-contract-po` | Contratos y órdenes de compra del cliente | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-contract-po.zip) |
|  | `agency-budget-control` | Presupuesto disponible y límite de crédito | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-budget-control.zip) |
|  | `agency-fee-contracts` | Contratos de fee fijo o por horas | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-fee-contracts.zip) |
|  | `agency-billing-requirements` | Requisitos del cliente antes de facturar | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-billing-requirements.zip) |
| Trabajo y producción | `agency-tasks-timesheets` | Tareas y horas del equipo | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-tasks-timesheets.zip) |
|  | `agency-production-estimating` | Presupuestos de producción y cotizaciones | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-production-estimating.zip) |
|  | `agency-production` | Entregables, derechos y talento | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-production.zip) |
| Planificación de medios | `agency-media-ranking` | Ratings y ranking de programas | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-media-ranking.zip) |
|  | `agency-media-planning` | Plan de medios y aprobación del cliente | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-media-planning.zip) |
|  | `agency-tv-radio-planning` | Pautas de TV y radio | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-tv-radio-planning.zip) |
|  | `agency-ooh-planning` | Exterior, DOOH e impresos | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-ooh-planning.zip) |
|  | `agency-digital-planning` | Planes digitales, taxonomía y UTMs | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-digital-planning.zip) |
|  | `agency-plan-changes` | Cambios a planes ya aprobados | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-plan-changes.zip) |
| Compra de medios | `agency-rate-cards-contracts` | Tarifarios y contratos con medios | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-rate-cards-contracts.zip) |
|  | `agency-media-buying` | Órdenes de publicidad | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-media-buying.zip) |
|  | `agency-campaign-activation` | Lanzar campañas digitales (con aprobación) | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-campaign-activation.zip) |
|  | `agency-campaign-optimization` | Optimizar campañas en curso | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-campaign-optimization.zip) |
|  | `agency-transmission-control` | Verificar que los spots salieron al aire | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-transmission-control.zip) |
|  | `agency-ooh-inventory` | Inventario de espectaculares (si eres el medio) | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-ooh-inventory.zip) |
| Proveedores y pagos | `agency-delivery-reconciliation` | Factura del proveedor contra lo ordenado | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-delivery-reconciliation.zip) |
|  | `agency-payables` | Recepción y registro de facturas de proveedor | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-payables.zip) |
|  | `agency-payment-run` | Lista de pagos y órdenes de pago | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-payment-run.zip) |
|  | `agency-cash-settlement` | Bancos, depósitos y conciliación | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-cash-settlement.zip) |
|  | `agency-expenses` | Gastos, viáticos y caja chica | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-expenses.zip) |
| Facturación y cobranza | `agency-client-billing` | Facturas y notas al cliente | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-client-billing.zip) |
|  | `agency-collections` | Cobranza, anticipos y antigüedad de saldos | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-collections.zip) |
|  | `agency-rebates` | Overcomisiones y rebates de medios | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-rebates.zip) |
|  | `agency-tax-compliance` | CFDI, IVA y retenciones | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-tax-compliance.zip) |
| Contabilidad y cierre | `agency-general-ledger` | Catálogo de cuentas y pólizas | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-general-ledger.zip) |
|  | `agency-accruals-revaluation` | Provisiones y diferencia cambiaria | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-accruals-revaluation.zip) |
|  | `agency-fixed-assets` | Activo fijo y depreciación | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-fixed-assets.zip) |
|  | `agency-period-close` | Cierre mensual y anual | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-period-close.zip) |
| Rentabilidad | `agency-profitability` | Rentabilidad por campaña y cliente | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-profitability.zip) |
|  | `agency-revenue-budget` | Presupuesto de ingresos | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-revenue-budget.zip) |
|  | `agency-cash-forecast` | Flujo de caja proyectado | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-cash-forecast.zip) |
|  | `agency-management-reporting` | Reporte gerencial y KPIs | [Descargar](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-management-reporting.zip) |

¿Las quieres todas de una vez? [agency-erp-all-skills.zip](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/agency-erp-all-skills.zip) trae los 42 .zip (este sí se descomprime; luego subes cada .zip por separado).

</details>

### Hazlo tuyo: AGENCY.md

Las skills saben cómo funciona el back office de una agencia. `AGENCY.md` les dice cómo lo maneja **tu** agencia: quién aprueba qué y hasta qué monto, tus monedas, tasas de impuestos, cuentas contables, tipos de job, plazos de pago y las apps que conectaste. Lo escribes una vez y todas las skills lo siguen.

1. Descarga [AGENCY.md](https://github.com/afelipeg/agentic-advertising-agency-erp/releases/latest/download/AGENCY.md). Trae valores de ejemplo de una agencia en México.
2. Cambia los valores dentro del bloque `json agency-policy` (puedes pedirle a Claude o a ChatGPT que te ayude a llenarlo). Que finanzas revise aprobaciones y tasas.
3. Súbelo junto con las skills: en Claude, en los **archivos de un Proyecto** (o adjúntalo al chat); en ChatGPT, en **Conocimiento** con los demás archivos; en un Gem de Gemini, como conocimiento.
4. Cuando algo cambie, edita el archivo y vuelve a subirlo. Lo cambias una vez y todas las skills lo aplican.

> AGENCY.md fija **parámetros, no permisos**: decide qué persona aprueba, nunca si una persona aprueba. Contraseñas, llaves de API y números de cuenta o tarjeta nunca van ahí.

### Lo que conviene saber

- Gratis y de código abierto (licencia MIT). No es un ERP en la nube ni guarda tus datos.
- No sustituye a tu contador: tasas de impuestos, tipos de cambio y políticas las pones tú, en `AGENCY.md`.
- Empieza en modo borrador; cuando confíes en el resultado, conecta tus herramientas.

---

## Para perfiles técnicos

### El circuito

JobNumber y maestros → contratos de fee, PO y crédito → presupuesto de producción y pauta → aprobación del cliente → órdenes y OC → emisión y control de avisos → facturas de proveedor → aprobado para facturar → factura y CFDI/CAE → cobranza → lista de pagos y libranza → tesorería y conciliación → provisiones, revaluación y cierre → rentabilidad y reporting. Ver el [circuito E2E](docs/erp-reference/e2e-circuit.md) con compuertas, identificadores, códigos de observación de cuentas y la matriz módulo → skill.

### Skills nuevas en 0.2

`agency-job-lifecycle` (JobNumber y cierre en dos pasos), `agency-tasks-timesheets`, `agency-revenue-budget`, `agency-rate-cards-contracts` (tarifarios y contratos de medios), `agency-digital-planning` (taxonomía y ajuste por factura de Google/Meta), `agency-ooh-inventory` (vía pública del lado del medio), `agency-payment-run` (lista de pagos, OP, retenciones, libranza), `agency-collections` (recibos, anticipos, aging, crédito), `agency-tax-compliance` (CFDI, CAE, libros de IVA, retenciones), `agency-general-ledger`, `agency-accruals-revaluation` (provisiones, WIP, diferencia de cambio, cierre de OT), `agency-fixed-assets`, `agency-management-reporting` y `agency-access-governance` (perfiles, poderes de aprobación, segregación de funciones). Las 28 skills anteriores se reescribieron sobre las reglas del ERP. Catálogo completo: [workflow](docs/workflow.md).

### Instalar desde la terminal

Node 22+ para el instalador; Python 3 (solo biblioteca estándar) para calculadoras, MCP local, bundles y evaluaciones.

```sh
# Plugin de Claude Code (skills + MCP de calculadoras)
claude plugin marketplace add afelipeg/agentic-advertising-agency-erp
claude plugin install agency-erp@afelipeg-agency-erp

# Instalación por proyecto
node bin/agency-erp.mjs install --agent codex          # .agents/skills
node bin/agency-erp.mjs install --agent claude-code    # .claude/skills
node bin/agency-erp.mjs install --agent gemini         # .gemini/skills

# Gemini CLI: todo el repo como extensión (skills + calculadoras)
gemini extensions install https://github.com/afelipeg/agentic-advertising-agency-erp
node bin/agency-erp.mjs connect-plan --profile agency
node bin/agency-erp.mjs demo

# Desde GitHub
npx --package github:afelipeg/agentic-advertising-agency-erp agency-erp install --agent codex
npx skills add afelipeg/agentic-advertising-agency-erp --agent codex claude-code
```

`--dry-run` revisa destinos, `--global` instala a nivel usuario y `--skill agency-payment-run` instala una sola. El instalador nunca sobrescribe carpetas existentes.

### Calculadoras

El dinero nunca lo calcula el modelo: escalas de overcomisión (fija, por valor, por tramo, marginal y escalonada, validadas con los ejemplos del manual), cascada de descuentos y fee, GRP/CPR/CPM, totales de presupuesto con líneas directas, liquidación de fee por horas, vencimientos con días hábiles, retenciones, revaluación cambiaria, aging, prorrateo exacto, cuotas, depreciación, validación de asientos, flujo de caja, matching de spots, exposición de crédito y verificación de facturas, y `approval_route`, que nombra a los aprobadores según los tramos de `AGENCY.md` (siempre exige una persona). Tasas de impuestos, tipos de cambio y políticas de la agencia siempre son insumos.

### Política de la agencia (AGENCY.md)

Un solo archivo de política para todas las skills y todos los agentes. Las skills lo buscan en este orden: un archivo que el usuario adjunte o nombre, `AGENCY.md` en la raíz del proyecto y luego `~/.agency-erp/AGENCY.md`. Solo el bloque `json agency-policy` es política: `approvals` (por acción y moneda, tramos de monto ascendentes con roles humanos), `currencies`, `roles`, `taxes`, `fx`, `jobs`, `commercial`, `collections`, `accounting` y `connectors`. Cada `SKILL.md` dice qué secciones aplica (se genera desde `contracts/workflows.json`).

```sh
node bin/agency-erp.mjs policy init --global   # escribe ~/.agency-erp/AGENCY.md con valores de ejemplo; nunca sobrescribe
node bin/agency-erp.mjs policy check           # ./AGENCY.md y luego ~/.agency-erp/AGENCY.md; sale con 1 si es inválido
```

En cada proyecto basta una línea en su `AGENTS.md` o `CLAUDE.md`: `Read ~/.agency-erp/AGENCY.md before using any agency-erp skill.` Cambias un umbral una vez y Claude Code, Codex y Gemini CLI lo aplican en todos los proyectos.

Precedencia: contrato de control → AGENCY.md → el pedido del usuario → valores de referencia (*confirm locally*). Todos los roles de un tramo aprueban (personas distintas, nunca quien preparó) y un tramo mayor conserva a los aprobadores del anterior. El validador rechaza todo lo que debilite controles: tramos sin aprobadores o con nombres de rol que apunten a software, un tramo mayor que quite aprobadores, `segregation_of_duties: false`, campos o conectores desconocidos, bloques de política ocultos o duplicados, frases para saltarse aprobaciones y cualquier cosa que parezca una credencial. Las revisiones de nombres y frases son de mejor esfuerzo; quien aprueba los cambios a AGENCY.md sigue siendo responsable. Un archivo inválido se ignora completo, nunca a medias. Guarda tu copia en un fork privado y cámbiala por pull request. Detalle en [docs/agency-policy.md](docs/agency-policy.md).

## Conectar lo mínimo

1. Pide a `agency-integrations` que revise tus apps ya habilitadas y los insumos del trabajo.
2. Usa primero esas apps. Si falta una capacidad, revisa MCP oficiales; después agregadores como Synter, Ryze, Supermetrics o Composio. Los archivos siguen siendo una opción válida.
3. Para producción considera Canva/Figma; para Meta el MCP oficial de Meta Ads; para redes sociales Zernio; para facturación y cobros Stripe/PayPal; para contabilidad Xero o el MCP oficial de QuickBooks (con escritura deshabilitada por defecto); para CFDI tu PAC autorizado; para tipos de cambio Banxico SIE; para investigación Monid con tope de gasto. Pagar proveedores necesita una capacidad de payout/banco comprobada. Un registro contable de pago no mueve dinero.
4. Autentícate en el flujo del proveedor. No pegues secretos ni claves en el chat. Comprueba empresa/cuenta, moneda, zona horaria, permisos y una consulta de prueba.
5. Empieza con borradores y consultas. Para gastar, contratar, emitir, enviar o borrar, revisa y aprueba la acción exacta. La emisión fiscal exige el proveedor y configuración del país; no se inventan tasas ni retenciones.

La [matriz detallada](docs/integrations.md) explica cada etapa, opciones y rutas sin conexión. No presupone que todas las apps estén disponibles en tu plan/país. No requiere que una persona sola tenga todos los departamentos: el agente prepara; el dueño humano revisa. Respeta las reglas documentadas de revisión independiente para gastos propios y cambios de beneficiario.

## Excel y cambios diarios

Todas las skills pueden correr con adjuntos en la UI. La CLI valida plantillas CSV/XLSX para planes, órdenes de radio/TV, emisiones, OOH, facturas y ratings. No se interpreta un archivo normalizado como aprobación ni como prueba de ejecución. La skill agency-plan-changes compara versiones y propaga sólo los cambios afectados, conservando compromisos y evidencias.

Lee [modo archivos](docs/file-mode.md), [medios offline](docs/offline-media.md) y [circuito completo](docs/operations-playbook.md). Incluyen ranking con/sin book, tarifarios, materiales, programación, control de emisión, compensaciones, procurement, facturación y cierre.

## Primer trabajo

“Usa agency-job-lifecycle para abrir un JobNumber del cliente ACM, producto 01, campaña nueva facturable a un solo cliente; luego pásalo a agency-media-planning.”

“Usa agency-payment-run para proponer la lista de pagos de esta semana con evidencia de cobro al cliente; no la apruebes ni la liberes.”

“Usa agency-orchestrator. Aquí están mi brief, contrato y presupuesto. Revisa mis apps habilitadas, identifica lo que falta y prepara un plan de trabajo con borradores. Antes de gastar, enviar o borrar, presenta la acción para aprobación.”

Después puedes pedir una etapa concreta: verificar derechos creativos, conciliar una factura, preparar el cobro de un hito o revisar el margen del proyecto. El [workflow](docs/workflow.md) describe entradas, salidas y responsables.

Las instrucciones exigen controles, pero el host debe ejecutarlos: sandbox, aislamiento entre clientes, eliminación de PII antes del modelo, presupuesto compartido, trazas, checkpoints y aprobaciones verificadas. Si tu entorno no los implementa, usa el paquete para preparación y análisis con datos redactados. Las pruebas locales no demuestran que un modelo opere cuentas reales de forma segura.

Consulta [la validación del lanzamiento](docs/release-validation.md) para las pruebas ejecutadas y los límites de implementación y publicación.

## Colaboradores

- **Andrés Felipe G. (Axiom Nexar)**: dueño y mantenedor.
- **Codex (OpenAI)**: construyó la versión 0.1, con el formato portable de skills, el instalador, el contrato de control, las calculadoras locales, el MCP stdio, el importador de archivos y el arnés de evaluación.
- **Claude (Anthropic)**: construyó la versión 0.2, con la ingeniería en reversa y la referencia funcional del ERP, 14 skills nuevas, la reescritura de las 28 existentes, 19 calculadoras nuevas, la actualización del registro de conectores y el empaquetado como plugin de Claude Code.

Las contribuciones son bienvenidas; ver [CONTRIBUTING.md](CONTRIBUTING.md).
