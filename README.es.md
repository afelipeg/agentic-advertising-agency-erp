# ERP agéntico para agencias de publicidad

Skills abiertas para que tu asistente (Claude Code, Codex, Claude.ai o un GPT/Project) opere **todo el back office de una agencia**: JobNumbers, producción, planificación y compra de medios, control de avisos, facturas de proveedores, facturación a clientes, cobranzas, pagos, tesorería, impuestos, contabilidad, cierre mensual y rentabilidad.

La versión 0.2 se basa en una **ingeniería en reversa funcional de un ERP de agencias maduro de Latinoamérica**: se analizaron ~1,330 páginas públicas de su ayuda y se reescribieron como una [referencia funcional del ERP](docs/erp-reference/README.md) con procesos, ciclos de vida de documentos, reglas numeradas, impactos contables, handoffs entre módulos y comportamiento por país. Cada skill cita esas reglas.

**42 skills autocontenidas · 25 calculadoras deterministas de solo lectura (también como MCP local) · referencia funcional del ERP · registro de MCP oficiales · 118 casos de comportamiento sintéticos · instalador npm/npx y marketplace de plugins de Claude Code.** Licencia MIT. No incluye credenciales, llaves ni suscripciones; no es un ERP alojado ni ejecuta pagos por sí solo.

> Proyecto independiente, sin afiliación con ningún proveedor de ERP. La referencia describe comportamiento funcional públicamente documentado con redacción propia; no redistribuye código, pantallas ni texto del manual.

## El circuito

JobNumber y maestros → contratos de fee, PO y crédito → presupuesto de producción y pauta → aprobación del cliente → órdenes y OC → emisión y control de avisos → facturas de proveedor → aprobado para facturar → factura y CFDI/CAE → cobranza → lista de pagos y libranza → tesorería y conciliación → provisiones, revaluación y cierre → rentabilidad y reporting. Ver el [circuito E2E](docs/erp-reference/e2e-circuit.md) con compuertas, identificadores, códigos de observación de cuentas y la matriz módulo → skill.

## Skills nuevas en 0.2

`agency-job-lifecycle` (JobNumber y cierre en dos pasos), `agency-tasks-timesheets`, `agency-revenue-budget`, `agency-rate-cards-contracts` (tarifarios y contratos de medios), `agency-digital-planning` (taxonomía y ajuste por factura de Google/Meta), `agency-ooh-inventory` (vía pública del lado del medio), `agency-payment-run` (lista de pagos, OP, retenciones, libranza), `agency-collections` (recibos, anticipos, aging, crédito), `agency-tax-compliance` (CFDI, CAE, libros de IVA, retenciones), `agency-general-ledger`, `agency-accruals-revaluation` (provisiones, WIP, diferencia de cambio, cierre de OT), `agency-fixed-assets`, `agency-management-reporting` y `agency-access-governance` (perfiles, poderes de aprobación, segregación de funciones). Las 28 skills anteriores se reescribieron sobre las reglas del ERP. Catálogo completo: [workflow](docs/workflow.md).

## Instalar

Node 22+ para el instalador; Python 3 (solo biblioteca estándar) para calculadoras, MCP local, bundles y evaluaciones.

```sh
# Plugin de Claude Code (skills + MCP de calculadoras)
claude plugin marketplace add afelipeg/agentic-advertising-agency-erp
claude plugin install agency-erp@afelipeg-agency-erp

# Instalación por proyecto
node bin/agency-erp.mjs install --agent codex          # .agents/skills
node bin/agency-erp.mjs install --agent claude-code    # .claude/skills
node bin/agency-erp.mjs connect-plan --profile agency
node bin/agency-erp.mjs demo

# Desde GitHub
npx --package github:afelipeg/agentic-advertising-agency-erp agency-erp install --agent codex
npx skills add afelipeg/agentic-advertising-agency-erp --agent codex claude-code
```

`--dry-run` revisa destinos, `--global` instala a nivel usuario y `--skill agency-payment-run` instala una sola. El instalador nunca sobrescribe carpetas existentes.

## Calculadoras

El dinero nunca lo calcula el modelo: escalas de overcomisión (fija, por valor, por tramo, marginal y escalonada, validadas con los ejemplos del manual), cascada de descuentos y fee, GRP/CPR/CPM, totales de presupuesto con líneas directas, liquidación de fee por horas, vencimientos con días hábiles, retenciones, revaluación cambiaria, aging, prorrateo exacto, cuotas, depreciación, validación de asientos, flujo de caja, matching de spots, exposición de crédito y verificación de facturas. Tasas de impuestos, tipos de cambio y políticas de la agencia siempre son insumos.

## Claude.ai y GPT

Claude.ai admite skills personalizadas: `node bin/agency-erp.mjs bundle --skill agency-client-billing --out agency-client-billing.zip`, súbelo en la sección de skills y actívalo. En ChatGPT usa las apps disponibles; `export --host gpt --out agency-reference.md` genera una referencia (circuito, contrato de control, skills y registro) para adaptar en un Project/GPT. Subir ese texto no instala MCP ni concede acceso a cuentas. Consulta [la guía por entorno](docs/web-assistant.md).

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
