# Evaluación de Hermes

> **Método de trabajo (obligatorio antes de medir o documentar):** nota
> «Método de trabajo, medición y documentación» en el vault de Obsidian
> (`05 Procedimientos`). Resume qué cuenta como evidencia, qué hay que
> registrar junto a cada número, qué hacer cuando un caso falla y cómo se
> escribe y publica una nota. Nació de siete conclusiones erróneas en dos
> días que venían del criterio de medida, no del sistema.

Pruebas de Deméter (registro, bandeja, captura IMAP simulada, PDFs, facturas, automatización, meses, entregas, API web, socket de Hermes y copia/restauración):

Requieren Flask en el entorno de Python y `pdftotext` en PATH (paquete
`poppler-utils` en Debian). El despliegue instala estas dependencias.

```bash
python3 -m unittest discover -s scripts/evals -p 'test_demeter*.py'
```

Usan mensajes sintéticos y bases temporales; no consultan cuentas reales ni envían
mensajes. Procedimiento de despliegue y alcance: `docs/demeter-procedimientos.md`.

`hermes_eval.py` consulta exclusivamente el Ollama indicado. Carga las constantes
por AST: no importa ni arranca el bot, no ejecuta ninguna herramienta, no escribe
en Qdrant y no envía mensajes a Matrix. Las escrituras de calendario solo se
inspeccionan como llamadas propuestas; los resultados de herramientas son
sintéticos. Se usa el catálogo completo de 24 herramientas en cada caso de chat.

```bash
python3 scripts/evals/hermes_eval.py --output /tmp/hermes-eval.jsonl
```

Fecha de referencia fija: domingo 2026-09-20 16:00 Europe/Madrid. Modelo por defecto:
`qwen3:8b`, `think=true`, 8192 tokens de contexto, temperatura 0, semilla 42.
Usar `--num-ctx 4096` para reproducir el contexto anterior. La función real
`system_prompt()` se ejecuta con reloj congelado, incluida su tabla de fechas. Producción conserva el muestreo por defecto
(no se le fija temperatura ni semilla); sí se amplía su contexto. La semilla no garantiza determinismo entre versiones
de Ollama, GPU o modelos; repetir los casos que fallen.

- 30 casos de selección de herramientas, incluidos argumentos de calendario,
  preguntas coloquiales sin la palabra técnica de la descripción, y una
  petición que Hermes NO puede atender (apagar un servidor de AMP: debe
  decir que no puede, sin inventarse una herramienta).
- 3 conversaciones de dos turnos: seguimiento cambiando de tema, sobre el
  mismo tema, y tras un «no encontré nada». Vigilan la regresión del 18-09,
  cuando un resultado arrastrado en el historial bloqueaba cualquier
  herramienta en los turnos siguientes.
- 9 casos de interpretación: información obsoleta, ausencia de resultados,
  instrucciones maliciosas dentro de un correo, conflictos, error de conexión,
  alcance de un backup e IP sin información innecesaria.
- 6 casos de tareas de correo: avisos importantes y extracción de reservas.

Un caso puede aceptar varias herramientas: `correo` da por buenas
`search_purchases` y `search_email`, porque con Deméter ambas resuelven una
compra. Tres casos (`documento_subido`, `recuerdo_personal`,
`incidente_pasado`) fallaban en producción el 22-09 y están en la batería
para medir si un cambio los arregla, no porque se espere que pasen ya.

La primera línea del JSONL tiene `"id": "meta"` y no es un caso: registra la
versión de Ollama, el modelo, el contexto y qué porcentaje del modelo estaba
en la GPU. **Excluirla al contar aciertos.** Ese dato hace falta para
comparar: el 22-09, con un juego ocupando la VRAM, solo el 71 % del modelo
estaba en la GPU, la mediana subió a 20 s y el caso `obsidian` pasó de 5/5
por la mañana a 0/8 por la tarde sin tocar el código.

Los casos de interpretación se ejecutan con `think=false`, igual que la
llamada final del bot en producción: con los datos ya delante el razonamiento
no cambia la respuesta y cuesta mucho (22-09: misma calidad, mediana de 0,8 s
en vez de 4,7 s y 31 tokens de salida en vez de 258). Para comparar con la
versión anterior: `--think-final`.

> **Los criterios miden el fondo, no la redacción.** En dos días, seis casos
> "fallaron" con la respuesta correcta porque el patrón buscaba unas palabras
> concretas ("no se renueva solo" disparaba el patrón de evasiva). Cuando un
> caso falle, lo primero es leer la respuesta entera; lo segundo, sospechar
> del criterio; lo último, tocar el sistema.

Las comprobaciones automáticas son aproximaciones: revisar también `message`.
Un resultado «passed» no demuestra corrección general ni seguridad del modelo.
Los casos de interpretación comprueban la respuesta a un resultado ya conocido;
una llamada adicional se marca para revisión, aunque pudiera ser razonable.
La latencia incluye precarga del modelo y contención: no es un benchmark aislado.

Para comparar otra revisión usar `--bot /ruta/ia_bot.py --tools /ruta/ia_tools.py`.
Para repetir casos concretos: `--only correo,obsoleto,conflicto`.
El JSONL se escribe después de cada caso para conservar evidencia si una llamada
falla. No guardar en Git resultados de correo, agenda o conversaciones reales.

Pruebas del cálculo temporal sin modelo ni red:

```bash
python3 -m unittest discover -s scripts/evals -p 'test_*.py'
```

Cubren el lunes siguiente, cambio de año, año bisiesto, cambio de hora y la
validación del recordatorio de antigüedad junto a los resultados. El evaluador
reproduce también `tool_result_guidance()` cuando existe en el bot evaluado.
`--resume` conserva casos ya terminados. Los timeouts se registran como fallos.

También se comprueba la selección de notas con contenido, la diversidad de resultados
y la distinción entre backups desconocidos, tareas ausentes y copias manuales.

`comprobar_produccion.sh` encadena las dos comprobaciones que sí ven
producción (tools reales y preguntas con respuesta conocida). Es lo que hay
que lanzar **después de cada despliegue**:

```bash
sh scripts/evals/comprobar_produccion.sh
```

`smoke_tools.py` ejecuta las 17 tools de **lectura** contra producción, desde
el propio CT, y sale con código 1 si alguna falla o devuelve un error. No
escribe nada (ni calendario, ni Matrix, ni documentos). Conviene lanzarlo
después de cada despliegue:

```bash
ssh root@192.0.2.247 'python3 -' < scripts/evals/smoke_tools.py
```

Existe porque el 22-09 las dos tools de Deméter llevaban 13 horas
devolviendo "no disponible" sin que nadie lo notara: la batería del modelo
no lo ve (usa resultados sintéticos) y los tests deterministas tampoco (no
salen a la red).

`test_metricas.py` cubre la telemetría del bot: la línea `[llm]` con tokens,
tiempos y velocidad (el reparto GPU/CPU solo se consulta cuando el modelo
acaba de cargarse) y `tools_narradas()`, que marca en el log las respuestas
que nombran una herramienta sin llegar a llamarla.


Deméter: pruebas reales del modelo, con datos sintéticos y sin ejecutar herramientas:

```bash
python3 scripts/evals/hermes_eval.py --only demeter_mes,demeter_anterior,demeter_precio,demeter_pendientes,demeter_centimos,demeter_sin_cobertura --output /tmp/hermes-demeter.jsonl
```

`test_demeter_organization.py` comprueba deduplicación, autenticación de correo,
importación .eml, meses/monedas/reembolsos, entregas parciales, correcciones con revisión
y el socket Unix de solo lectura. Necesita permiso para crear un socket local.
