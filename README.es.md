# Una agencia pequeña, asistida por IA

Este paquete abierto agrega 28 skills operativas a tu asistente: onboarding, datos maestros, contratos y PO, presupuesto, planificación, compra, producción, activación, optimización, conciliación, proveedores, facturación, cobros/pagos, rebates, gastos, rentabilidad y cierre. Incluye seis calculadoras locales y un MCP local opcional. Licencia MIT.

Puedes empezar con documentos y CSV. No necesitas contratar todos los proveedores ni crear una infraestructura de agentes. Las skills usan el modelo de tu asistente; conectar una app es una acción separada y requiere tu autorización. El paquete no incluye una plataforma ERP alojada ni un runtime que ejecute controles por sí solo.

## Instalar

Desde el proyecto descargado, con Node 22 o superior:

```sh
node bin/agency-erp.mjs install --agent codex
# O para Claude Code:
node bin/agency-erp.mjs install --agent claude-code
node bin/agency-erp.mjs connect-plan --profile solo
node bin/agency-erp.mjs demo
```

Python 3 es necesario para las calculadoras, MCP local, bundles y evaluaciones. No se requieren dependencias externas para las herramientas locales. Agrega `--dry-run` para revisar destinos, `--global` para instalación personal o `--skill agency-production` para una sola skill. El instalador no sobrescribe archivos existentes.

Una vez publicado y accesible el repositorio, también podrás usar:

```sh
npx --package github:afelipeg/agentic-advertising-agency-erp agency-erp install --agent codex
npx skills add afelipeg/agentic-advertising-agency-erp --agent codex claude-code
```

La publicación en npm es un paso de lanzamiento separado; no asumas que el nombre ya está disponible allí.

## Claude.ai y GPT

Claude.ai admite skills personalizadas mediante una carga independiente. Genera el bundle con `node bin/agency-erp.mjs bundle --skill agency-production --out agency-production.zip`, súbelo en la sección de skills de Claude y actívalo. No basta con adjuntarlo como documento en una conversación. Después conecta las apps necesarias.

En ChatGPT usa los plugins/apps disponibles en su marketplace. Este paquete no figura automáticamente en esos marketplaces. El comando `export --host gpt --out agency-reference.md` genera una referencia para adaptar instrucciones en un Project/GPT o un constructor de skills/plugins compatible. Subir ese texto no instala MCP ni concede acceso a cuentas. Consulta [la guía por entorno](docs/web-assistant.md).

## Conectar lo mínimo

1. Pide a `agency-integrations` que revise tus apps ya habilitadas y los insumos del trabajo.
2. Usa primero esas apps. Si falta una capacidad, revisa MCP oficiales; después agregadores como Synter, Ryze, Supermetrics o Composio. Los archivos siguen siendo una opción válida.
3. Para producción considera Canva/Figma; para facturación y cobros Stripe/PayPal; para contabilidad Xero o tu sistema existente. Pagar proveedores necesita una capacidad de payout/banco comprobada. Un registro contable de pago no mueve dinero.
4. Autentícate en el flujo del proveedor. No pegues secretos ni claves en el chat. Comprueba empresa/cuenta, moneda, zona horaria, permisos y una consulta de prueba.
5. Empieza con borradores y consultas. Para gastar, contratar, emitir, enviar o borrar, revisa y aprueba la acción exacta. La emisión fiscal exige el proveedor y configuración del país; no se inventan tasas ni retenciones.

La [matriz detallada](docs/integrations.md) explica cada etapa, opciones y rutas sin conexión. No presupone que todas las apps estén disponibles en tu plan/país. No requiere que una persona sola tenga todos los departamentos: el agente prepara; el dueño humano revisa. Respeta las reglas documentadas de revisión independiente para gastos propios y cambios de beneficiario.

## Excel y cambios diarios

Todas las skills pueden correr con adjuntos en la UI. La CLI valida plantillas CSV/XLSX para planes, órdenes de radio/TV, emisiones, OOH, facturas y ratings. No se interpreta un archivo normalizado como aprobación ni como prueba de ejecución. La skill agency-plan-changes compara versiones y propaga sólo los cambios afectados, conservando compromisos y evidencias.

Lee [modo archivos](docs/file-mode.md), [medios offline](docs/offline-media.md) y [circuito completo](docs/operations-playbook.md). Incluyen ranking con/sin book, tarifarios, materiales, programación, control de emisión, compensaciones, procurement, facturación y cierre.

## Primer trabajo

“Usa agency-orchestrator. Aquí están mi brief, contrato y presupuesto. Revisa mis apps habilitadas, identifica lo que falta y prepara un plan de trabajo con borradores. Antes de gastar, enviar o borrar, presenta la acción para aprobación.”

Después puedes pedir una etapa concreta: verificar derechos creativos, conciliar una factura, preparar el cobro de un hito o revisar el margen del proyecto. El [workflow](docs/workflow.md) describe entradas, salidas y responsables.

Las instrucciones exigen controles, pero el host debe ejecutarlos: sandbox, aislamiento entre clientes, eliminación de PII antes del modelo, presupuesto compartido, trazas, checkpoints y aprobaciones verificadas. Si tu entorno no los implementa, usa el paquete para preparación y análisis con datos redactados. Las pruebas locales no demuestran que un modelo opere cuentas reales de forma segura.

Consulta [la validación del lanzamiento](docs/release-validation.md) para las pruebas ejecutadas y los límites de implementación y publicación.
