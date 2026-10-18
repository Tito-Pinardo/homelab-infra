# Deméter — Procedimientos de implementación

Fecha: 22-09-2026. Objetivo: gestionar compras, entregas, plazos y gasto detectado
desde una página privada y Hermes. Procesamiento de IA local.

## 1. Registro estructurado — implementado y desplegado

- [x] Crear módulo SQLite independiente de Qdrant, correo y calendario.
- [x] Registrar pedido por cuenta, comercio e identificador de pedido.
- [x] Conservar referencias al mensaje original por cuenta.
- [x] Calcular en unidades monetarias mínimas enteras, por moneda.
- [x] Registrar reembolsos parciales con identificador propio y fecha de recepción.
- [x] Rechazar contradicciones y excesos de reembolso sin dejar escrituras parciales.
- [x] Probar persistencia, duplicados, separación de cuentas y límites monetarios.

Código: `ansible/roles/ia_asistente/files/demeter_store.py`.
Validación: `python3 -m unittest discover -s scripts/evals -p 'test_demeter_store.py' -v`.
Base desplegada en CT118, con interfaz privada en https://demeter.home.arpa. La evidencia de envío/entrega
no constituye aún un modelo de paquetes o seguimiento. Un mensaje que afecte a varios
pedidos queda para revisión y permite confirmar cada pedido con su evidencia, atómicamente.
El consumidor deberá normalizar comercio y referencias antes de registrar datos.

## 2. Bandeja de extracción y revisión — base desplegada

- [x] Añadir migraciones versionadas antes de ampliar el esquema o desplegarlo.
- [x] Crear candidatos persistentes: pendiente, por revisar, validado, descartado, error y reintento.
- [x] Guardar procedencia, versión del extractor, campos desconocidos y evidencia de cada campo.
- [x] Revisión de varios pedidos y vinculación explícita de reenvíos entre cuentas; auditar datos corregidos al aprobar.
- [x] Parser conservador para texto de confirmaciones Amazon.es en español.
- [x] Recibos Stripe/Anthropic en inglés, decimales con punto o coma y prefijo EUR/€.
- [x] Extracción local de PDFs adjuntos, con referencia de factura preferida sobre recibo para deduplicar documentos.
- [x] Clasificar señales de compra, publicidad, envío, entrega, cancelación, devolución solicitada y reembolso emitido.
- [x] Dudas e importes ausentes van a revisión; no convertir desconocido en cero.
- [x] Pruebas sintéticas de clasificación, importes ambiguos, varios pedidos, reenvíos y errores parciales.
- [x] Validación real dirigida: nueve recibos de Anthropic completos, con dos PDFs cada uno; no se generaliza a cualquier comercio.
- [ ] Ampliar la validación de confirmaciones Amazon y otros comercios.
- [ ] Añadir extracción local por modelo como respaldo, con esquema validado y evaluación separada.
- [x] Incorporar avisos de envíos, entregas, cancelaciones y reembolsos al historial del pedido.
- [ ] Incorporar importes de reembolsos desde la web: actualmente los avisos no descuentan dinero.
- [ ] Modelar paquetes divididos y cambios de estado en la fase 4; no inferir entrega completa por un paquete.

Aceptación: cada importe confirmado tiene evidencia; publicidad no genera compras;
reprocesar no duplica pedidos ni reembolsos. La IA no ejecuta instrucciones del correo.

Implementación actual: `demeter_extract.py`, `demeter_review.py`, `demeter_cli.py` y
migraciones de `demeter_store.py`, bajo `ansible/roles/ia_asistente/files/`.
El extractor es determinista y funciona con el PC/modelo apagado. Las reglas incorporan
automáticamente compras completas, consistentes y autenticadas capturadas por IMAP.
Los casos ambiguos, los reenvíos y las importaciones manuales quedan por revisar.
Los estados explícitos de Amazon se incorporan sin sumar otro gasto.
No se autentica el remitente a partir del campo From. Un aviso de reembolso emitido
no acredita recepción bancaria. El importe y la fecha ausentes quedan desconocidos.

Se conserva el original y cada extracción, error, reintento y decisión en una auditoría.
Una aprobación incluye los datos revisados y fragmentos literales para cada campo;
permite corregir la extracción antes de incorporar el pedido. Los pedidos registrados
permiten cambiar categoría y confirmar recepción/cancelación completas con auditoría.
Los importes ya contabilizados no tienen edición directa desde la interfaz. Una revisión obsoleta se rechaza por número de revisión.
Pedidos y aprobación se guardan juntos o se revierten juntos. Los reenvíos vinculados
conservan su procedencia en `candidate_orders`, sin duplicar el pedido original.

Esquema SQLite actual: versión 6. La base inicial sin versión se migra conservando
pedidos, evidencias y reembolsos; se rechazan bases de versiones futuras.

Validación local: **73 pruebas pasan** (registro, extracción, revisión,
captura, copias, PDFs, facturas y API web),
incluido flujo CLI completo con datos sintéticos, persistencia, migración de la base
anterior, rollback si falla una migración o la auditoría, conflicto de revisión entre
dos conexiones y permisos privados. Las pruebas de captura usan un servidor IMAP simulado;
la prueba real se documenta aparte. La interfaz también se probó con Chromium y datos
sintéticos: búsqueda, confirmación y resumen, móvil sin desbordamiento, scripts de
correo inertes, cero peticiones externas y cero errores JavaScript.

El entorno de pruebas requiere Flask y `pdftotext` (paquete `poppler-utils`).

```bash
python3 -m unittest discover -s scripts/evals -p 'test_demeter*.py' -v
```

### Uso local de la bandeja

Ejecutar desde el repositorio. El directorio de la BD debe pertenecer al usuario y ser
privado (0700); el CLI crea directorio y BD con permisos privados. Elegir una ruta fuera
del vault/Git, por ejemplo `~/.local/share/demeter-dev/queue.sqlite`.

```bash
python3 ansible/roles/ia_asistente/files/demeter_cli.py --db ~/.local/share/demeter-dev/queue.sqlite init
python3 ansible/roles/ia_asistente/files/demeter_cli.py --db ~/.local/share/demeter-dev/queue.sqlite ingest /ruta/privada/mensaje.json
python3 ansible/roles/ia_asistente/files/demeter_cli.py --db ~/.local/share/demeter-dev/queue.sqlite list --status pending
python3 ansible/roles/ia_asistente/files/demeter_cli.py --db ~/.local/share/demeter-dev/queue.sqlite process 1 --revision 0
python3 ansible/roles/ia_asistente/files/demeter_cli.py --db ~/.local/share/demeter-dev/queue.sqlite show 1
```

El sobre JSON de ingestión contiene `account`, `message_id`, `sender`, `subject`,
`body` y `received_on` (YYYY-MM-DD). Recibir un correo el día 22 no convierte ese día
en fecha de compra. Un Message-ID repetido con contenido diferente se rechaza sin
reemplazar el original; el futuro recolector deberá poner ese conflicto en cuarentena.

`approve ID --revision N --actor NOMBRE --reason MOTIVO --decisions ARCHIVO` recibe una
lista JSON. Cada entrada tiene `purchase` (merchant, reference, purchased_on, currency,
total_minor), `evidence` (los mismos campos con fragmentos literales del mensaje) y,
opcionalmente, `existing_order_id` para vincular un pedido existente. El revisor debe
comprobar que el fragmento respalda el valor: la comprobación literal no demuestra por
sí misma su interpretación correcta. El actor es trazabilidad local, no autenticación.

`discard ID --revision N --actor NOMBRE --reason MOTIVO` descarta; `retry ID --revision N
--actor NOMBRE` devuelve un error a pendiente. Consultar la revisión vigente con `show`.
`list` no imprime el cuerpo del correo; `show` sí, solo bajo petición explícita local.
Hay servicio de captura y página web de revisión; todavía no hay avisos de Deméter.

## 3. Captura de correo para compras

- [x] Añadir recolector específico de compras, sin cambiar el filtro Principal de Hermes.
- [x] Buscar recibos y pedidos fuera de Principal; documentar carpetas y cuentas cubiertas.
- [x] Usar lectura IMAP sin marcar mensajes como leídos y cursor propio por cuenta/carpeta/UIDVALIDITY.
- [x] Persistir el candidato o la cuarentena antes de avanzar el cursor; reintentar fallos sin saltar mensajes.
- [x] Primera carga desde 180 días atrás, conservando después el historial ya incorporado.
- [x] Carga histórica sin disparar avisos ni creación retroactiva de eventos en Cronos.
- [x] Extraer con reglas sin depender del PC; los casos que requieran modelo quedan para revisión.

Aceptación: recuperar mensajes tras reinicio y fallo parcial; repetir carga sin efectos duplicados.
Los checkpoints actuales de `sync_correo.py` no se reutilizan ni se borran.

`demeter_mail.py` descubre la carpeta Gmail con atributo `\\All`, la abre con
`readonly=True` y obtiene los mensajes con `BODY.PEEK[]`. Incluye archivados;
excluye enviados, borradores, spam y papelera. Usa las dos cuentas ya configuradas
en Hermes, con credenciales aprovisionadas desde Ansible Vault, sin exponerlas en logs.
La consulta combina `category:purchases` con mensajes de Amazon.es cuyo asunto contenga
pedido/pedidos/reembolso/devolucion/factura/entrega. No es una garantía de cobertura completa.

El servicio usa `--reconcile`: vuelve a buscar coincidencias del intervalo inicial y
solo descarga UIDs aún no capturados. Así recoge categorías asignadas con retraso.
La fecha inicial queda fija en el cursor; cambiar de consulta genera un cursor nuevo
sin duplicar capturas. UIDVALIDITY distinto reinicia el rastreo y deduplica candidatos.
Las capturas y el avance de cursor se confirman juntos. Un fallo de red detiene esa
cuenta sin saltar el UID; la otra cuenta puede continuar. Solo hay una ejecución de
captura simultánea por BD, mediante bloqueo local.

Se guarda el MIME original en la BD privada, incluido cualquier adjunto. Se
extrae cuerpo de texto o HTML sin ejecutar scripts y texto de PDFs adjuntos mediante
pdftotext local: hasta 8 PDFs, 5 MiB por PDF, 10 páginas y 10 segundos por documento.
No se siguen enlaces a facturas remotas; PDF sin texto queda señalado para revisión/OCR. Los
mensajes ilegibles o contradictorios se conservan en `mail_captures` como cuarentena.
Mensajes mayores de 10 MiB no se descargan: quedan identificados por cuenta/carpeta/
UIDVALIDITY/UID y Gmail ID para recuperación posterior. La cuarentena no se reintenta
automáticamente; requiere diagnóstico y recuperación explícita.

Documentación técnica contrastada: [extensiones IMAP de Gmail](https://developers.google.com/workspace/gmail/imap/imap-extensions)
y [operadores de búsqueda de Gmail](https://support.google.com/mail/answer/7190?hl=es).

## 4. Página privada — revisión desplegada

- [x] API y página con acceso autenticado mediante la infraestructura existente.
- [x] Resumen mensual, por revisar, confirmados, descartados y búsqueda por comercio/asunto/referencia.
- [x] Amazon: historial de estados y fechas previstas explícitas, sin consulta en vivo.
- [ ] Gestión de importes de reembolsos desde la interfaz.
- [ ] Modelo separado de artículos y paquetes: un pedido puede tener varias entregas.
- [x] Ver correo y texto de PDFs, corregir campos con evidencia, confirmar/descartar y conservar historial.
- [x] Mostrar última captura y distinguir gasto confirmado de mensajes pendientes; el resumen no es saldo bancario.
- [x] Mostrar fecha prevista solo si aparece explícitamente y con año en el correo.
- [x] Proteger operaciones de escritura contra CSRF y comprobar autorización en la API.

Aceptación: usable desde móvil; correcciones persisten; acceso anónimo rechazado;
mostrar estado conocido por correo, sin prometer seguimiento en vivo.

Acceso: **https://demeter.home.arpa**, solo LAN y Authelia (usuario `tito`, política
vigente de dos factores). Sin registro DNS público ni ruta en Traefik. Caddy rechaza
orígenes fuera de 192.0.2.0/24 y también el proxy público .6 y la entrada del router .1.
La API en .247:8092 exige origen .243, secreto de proxy y usuario permitido; no acepta
cabeceras de identidad por sí solas. Caddy elimina las cabeceras de identidad entrantes
antes de preguntar a Authelia. El secreto vive fuera de Git y no se envía al navegador.

Las escrituras requieren sesión firmada, token CSRF y Origin exacto. Cookies Secure,
HttpOnly y SameSite=Strict; contenido sin caché, CSP sin scripts externos ni inline.
El correo y los PDFs se representan como texto inerte. Confirmar pide una casilla de
comprobación; los datos corregidos confirmados aparecen tanto en detalle como en lista.
Una revisión obsoleta devuelve 409 para impedir que dos pestañas pisen sus cambios.

Reconocimiento probado de Anthropic: recibos de 5 € y 18 €, fechas, referencia de
factura y fuentes de cada campo. En la fase del 21-09 nueve recibos reales quedaron
completos y por revisar. La ampliación del 22-09 permite incorporarlos con reglas
automáticas si superan autenticación y comprobaciones. Se detectan importes/monedas contradictorios y pagos
parciales como dudas. El prefijo `$` sin moneda explícita no se convierte en USD.

Pruebas de acceso: anónimo y cabeceras falsas en Caddy → login Authelia; backend sin
secreto, usuario no permitido o escritura sin CSRF → 403; acceso desde el host del proxy
público → 403; acceso autorizado desde el proxy → 200. La prueba desde .6 verifica esa
vía de entrada, no es un escaneo desde Internet. Certificado interno validado en las pruebas.

## 5. Consultas desde Hermes

- [x] Herramientas de consulta de compras, resumen monetario y pedidos pendientes.
- [x] Consultar SQL para totales completos; correo semántico solo como evidencia complementaria.
- [x] Resultados con periodo, moneda, cobertura y fuente; desconocido nunca equivale a cero.
- [x] Seis evaluaciones con qwen3:8b y catálogo completo: mes actual/anterior, precio, pendientes, céntimos y cobertura incompleta.
- [ ] Ampliar evaluación de conversaciones largas y seguimientos ambiguos.

Aceptación: las cifras del bot coinciden con la página y la consulta determinista.

## 6. Agenda y avisos

- [ ] Recordatorios configurables de entregas, vencimientos y devoluciones.
- [ ] Integración con Cronos mediante identificador estable y actualización idempotente.
- [ ] Detectar cambios de fecha, cancelaciones y conflictos; permitir deshacer.
- [ ] Activar avisos de Deméter desde el propio proceso autorizado de Matrix.

Aceptación: un hecho produce como máximo un aviso por versión; ningún aviso histórico
inesperado. No abrir un segundo cliente sobre el almacén E2EE del bot en marcha.

## 7. Presupuestos y suscripciones

- [ ] Categorías editables y presupuesto mensual por moneda.
- [ ] Detectar recurrencias como propuestas revisables; separar cobro previsto y recibido.
- [ ] Importación opcional de CSV bancario con deduplicación y conciliación con compras.

Aceptación: compra y movimiento bancario conciliados no duplican gasto; nunca presentar
el correo como saldo bancario. No incluye pagos automáticos ni operaciones bancarias.

## 8. Despliegue y recuperación

- [x] Rol Ansible, usuario de servicio, directorio privado 0700 y umask 0077.
- [x] Guardar BD fuera del vault y de Git; logs sin cuerpos de correo ni credenciales.
- [x] Copia consistente de SQLite y restauración comprobada antes de cargar datos reales.
- [x] Desplegar primero importación controlada sin avisos; comprobar muestra y ausencia de gastos automáticos.
- [ ] Activar captura incremental, página, consultas y avisos por separado.
- [ ] Documentar versión, migraciones, salud del proceso y procedimiento de reversión.

La preparación operativa de esta fase precede a cualquier activación en producción.
Las notas vigentes indican que no existe todavía un sistema general de backups.
La copia nueva de Deméter es local al mismo CT y no protege frente a pérdida del host.

### Operación de Deméter

- CT118: `192.0.2.247`, código `/opt/demeter/`, usuario `demeter`.
- BD `/var/lib/demeter/queue.sqlite`, directorio 0700, fichero 0600.
- Credenciales `/etc/demeter.env`, root:root 0600, leídas por systemd.
- `demeter-capture.service`: captura limitada por cuenta, extracción y automatización de casos completos.
- `demeter-query.service`: socket Unix `/run/demeter-query/query.sock`, grupo ia-bot, consultas SQLite de solo lectura; sin puerto TCP.
- `demeter-web.service`: Flask + Waitress, escucha .247:8092, admite únicamente proxy autenticado.
- `demeter-capture.timer`: activo, cada 15 minutos, máximo 100 mensajes por cuenta y pasada.
- `demeter-backup.timer`: diario a las 04:15, con recuperación de ejecuciones perdidas.
- `/var/lib/demeter/backups/`: últimas 14 copias SQLite; cada copia se restaura en
  un fichero temporal y pasa integrity_check y foreign_key_check antes de rotar.

```bash
cd ~/infra-tf/ansible
ansible-playbook playbooks/demeter.yml -e 'ansible_ssh_common_args="-F /dev/null"'
```

El playbook dedicado no ejecuta el rol completo de Hermes. Instala su cliente de
Deméter, herramientas y prompt; reinicia ia-bot únicamente cuando cambian esos archivos. Antes de migrar una base
existente genera y verifica una copia. No necesita instalar sudo: usa runuser desde root.
Las unidades se validaron con systemd-analyze verify.

El mismo playbook provisiona el sitio de Caddy en el host `dockge`, valida antes de
recargar y no reinicia el stack ARR. La importación de `/config/demeter/*.caddy` debe
estar después del snippet `protected`, como está en la plantilla. Credencial backend
`/etc/demeter-proxy-token` (root:demeter 0640) y configuración de proxy bajo
`/opt/stacks/arr/proxy/caddy_config/demeter/` (directorio 0700, secreto 0600).
El rol ARR conserva la importación, para no perder la página en futuros despliegues.

Reextraer candidatos de una versión anterior sin confirmar compras:

```bash
runuser -u demeter -- python3 /opt/demeter/demeter_cli.py --db /var/lib/demeter/queue.sqlite refresh --query Anthropic --actor operador --limit 100
```

La operación conserva los originales y las extracciones previas en auditoría; excluye
confirmados y descartados. La referencia canónica de la factura reúne recibo y PDF.
La captura habitual ahora incluye recibos/facturas de Stripe aunque Gmail no les haya
asignado la categoría Compras. No se aplicó el modelo de IA: este reconocimiento es local
y determinista. Sigue pendiente ampliar formatos, OCR y casos de otros comercios.

Estado anonimizado en el CT (sin asuntos, cuerpos ni importes):

```bash
runuser -u demeter -- python3 /opt/demeter/demeter_cli.py --db /var/lib/demeter/queue.sqlite stats
systemctl status demeter-capture.timer demeter-backup.timer
journalctl -u demeter-capture.service -n 10 --no-pager
```

La configuración persistente está en `inventory/group_vars/ia_asistente/vars.yml`:
`demeter_capture_enabled: true` y `demeter_capture_limit: 100`.

Para detener la captura: `systemctl disable --now demeter-capture.timer` y
`systemctl stop demeter-capture.service`. Esto no afecta a Hermes ni a sync-correo.
Para revertir una migración, detener también backup.service, conservar aparte la BD
actual, restaurar una copia verificada con propietario demeter y modo 0600 y reinstalar
la versión de código correspondiente. No restaurar archivos SQLite mientras un proceso
los tiene abiertos; no cambiar los checkpoints ni el almacén E2EE de Hermes.

Primera prueba real (21-09-2026): 10 mensajes capturados, 0 en cuarentena, 10 candidatos
por revisar y 0 pedidos contabilizados; segunda cuenta sin coincidencias en esa consulta.
La muestra inicial era 4 anuncios y 6 desconocidos según el parser, con 0 importes
extraídos. Se acotó la consulta Amazon antes de activar la carga general. Esto confirma
captura y aislamiento, no precisión de extracción. Hermes mantuvo PID 292862 y su fecha
de arranque; ia-bot y sync-correo siguieron activos. La copia posterior a la muestra se
restauró y comprobó durante el siguiente despliegue.

Una prueba de recuentos detectó que Gmail interpretaba las llaves anidadas de la
consulta de forma más amplia de lo previsto (421 coincidencias). Se sustituyeron por
paréntesis y OR explícitos; recuento comprobado de la consulta final: 403 en la primera
cuenta al realizar esa prueba. Los diez mensajes adicionales de la prueba intermedia
se conservan por revisar: no se borraron ni se contabilizaron. La búsqueda final es:

```text
(category:purchases OR (from:stripe.com (subject:receipt OR subject:invoice)) OR (from:amazon.es (subject:pedido OR subject:pedidos OR subject:reembolso OR subject:devolucion OR subject:factura OR subject:entrega))) -in:sent -in:drafts
```

Captura y copia periódicas habilitadas tras las pruebas. La carga histórica continúa
por lotes; los recuentos del servicio no significan compras confirmadas. Los datos
reales permanecen en la BD del CT; Obsidian y Git contienen solo código y documentación.

Durante el primer lote de 100 apareció `database is locked` al consultar estadísticas:
el constructor abría una transacción de escritura incluso si el esquema estaba al día.
Se corrigió para solicitarla solo al migrar y se añadió una prueba de lector concurrente
con escritor activo. También se limitaron los espacios de las expresiones multilínea
para evitar recorrer repetidamente saltos de línea de HTML, y se preservó la etiqueta
Total junto a su importe en celdas de tabla. En ese cierre: `amazon-es-text-v2`;
extractor actual tras ampliar facturas: `purchases-invoices-v3`.
Las extracciones anteriores conservan su versión y no se presentan como reprocesadas.

Comprobación histórica anterior a la ampliación de facturas: 120 mensajes capturados, 120 por revisar, 0 cuarentenas,
0 pedidos y 0 importes extraídos en ese lote. Clasificación acumulada: 8 anuncios y
112 desconocidos. Quedaban 286 coincidencias de la consulta final por capturar en
la primera cuenta según la última pasada. La captura general funciona, pero este lote
no demuestra extracción útil: hace falta ampliar formatos/comercios y validar
confirmaciones Amazon antes de confiar en automatismos monetarios. Las estadísticas
ya se consultan sin la transacción de escritura innecesaria. Ambos timers activos;
última ejecución de captura finalizada con Result=success y ExecMainStatus=0.

## Fuentes revisadas

- Obsidian: `04 Proyectos/Asistente IA + base semantica.md`.
- Obsidian: `05 Procedimientos/Asistente IA - Implementacion.md`.
- Obsidian: `05 Procedimientos/Hermes - Evaluacion y mejora del prompt 2026-09-20.md`.
- Código de `sync_correo.py`, `ia_tools.py` y tareas Ansible del bot.

Este documento describe avance real y trabajo pendiente; no implica que las funciones
pendientes estén activadas. No se han importado compras reales en la primera fase.


## Ampliación del 22-09-2026: meses, Amazon y Hermes

### Decisiones del usuario

Cuenta Amazon **personal**. Sin scraper, navegador automatizado, cookies ni acceso de
la IA a la sesión de Amazon. Fuentes: IMAP de solo lectura y archivos .eml elegidos
por el usuario. No se ejecutan compras, cancelaciones, devoluciones ni mensajes a Amazon.
La recepción/cancelación en Deméter solo anota la confirmación del usuario en el registro.
Sin APIs externas de IA. Jev descartado: la documentación de TypeSafe describe una API
alojada y no se encontró una distribución local oficial. Hermes usa Ollama local.

### Página

- Resumen por mes con totales separados por moneda, categorías, comercios e historial.
- Lista de gastos por producto/comercio/referencia, filtro mensual o historial completo.
- Patrones de compras repetidas en varios meses, sin afirmar que exista suscripción activa.
- Amazon y entregas: agrupa avisos por cuenta/comercio/referencia. Un aviso de entrega
  puede ser parcial; solo la confirmación manual cierra la recepción de todo el pedido.
- Pedidos con solo correo de envío conservan importe desconocido; no generan gasto.
- Importación .eml hasta 10 MiB, original y PDF guardados localmente, con deduplicación
  por mensaje y cuenta. Siempre queda para revisión; una cabecera de autenticación
  dentro de un archivo subido no autoriza incorporación automática.
- Sin conexión en vivo a Amazon. La consulta controlada de los últimos 180 días encontró
  dos correos de seguridad y **ninguna compra de Amazon** en las cuentas conectadas.
  No confundir ausencia de cobertura con ausencia de pedidos pendientes.

### Automatización y cálculo

`demeter_automation.py` incorpora una compra solo con una referencia, campos completos,
fragmentos literales, ausencia de contradicciones, comercio reconocido y autenticación
DMARC de Gmail alineada con el remitente en el MIME capturado. Los recibos Stripe
admitidos deben ser de Anthropic/OpenAI y declarar Amount paid. No se usa un LLM para
calcular dinero ni decidir escrituras. Cada incorporación guarda actor `auto:rules-v1`.
Posibles duplicados entre cuentas y datos contradictorios siguen por revisar.

Los avisos logísticos se guardan en `order_events` sin duplicar el gasto. Un reembolso
notificado no se considera dinero recibido ni se descuenta automáticamente. El registro
monetario conserva el soporte previo de reembolsos auditables; falta su formulario web.

`capture_runs` registra éxito, cola restante y hora incluso cuando no hay correos nuevos.
Las respuestas muestran cobertura incompleta ante errores, cola o más de 30 minutos sin
sincronización. Los importes pendientes de revisión no están incluidos.

### Hermes

- `get_expenses_summary(month?)`: mes YYYY-MM o actual en Europe/Madrid.
- `search_purchases(query, month?)`: descripción/comercio/referencia; importe total del
  pedido, no precio unitario de todos los productos citados en el correo.
- `get_pending_orders(query?)`: estados y fechas de los correos, sin asegurar entrega
  en tiempo real. Los pedidos antiguos sin evidencia no se declaran retrasados.

Las tres herramientas llaman `demeter_client.py`, que solo abre un socket Unix local.
El servidor abre SQLite con `mode=ro` y `query_only=ON`. El proceso Hermes no puede leer
la BD privada, correo MIME o secreto del proxy a través de esta integración, ni dispone
de operaciones de escritura. La web mantiene los controles de Authelia y LAN previos.

### Comprobaciones

73 pruebas de Deméter; 6 pruebas del contexto temporal de Hermes; 6 evaluaciones del
modelo local. Chromium con datos ficticios: navegación mensual, categorías, búsqueda,
Amazon, recepción manual, importar .eml e incorporar evento; móvil sin desbordamiento,
sin errores JavaScript ni peticiones externas de la página. No se enviaron mensajes a Matrix.

Fuentes contrastadas sobre conectores:
[Amazon SP-API para vendedores](https://sell.amazon.com/developers),
[Amazon Business Reporting](https://docs.business.amazon.com/docs/reporting-api-v1-reference-1),
[TypeSafe Jev: API remota](https://docs.typesafe.ai/introduction/quickstart).
