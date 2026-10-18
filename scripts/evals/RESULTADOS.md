# Evaluación del asistente — 20–21 septiembre 2026

- Modelo local qwen3:8b, contexto anterior 4096; nuevo 8192.
- Batería anterior: 28/31. Candidato completo: 31/31 según criterios automáticos.
- La revisión manual encontró una antigüedad inventada pese a ese resultado;
  tras corregir el prompt, los tres casos dirigidos afectados pasaron.
- No se repitió toda la batería después de cada ajuste: no se atribuye el 31/31
  a la revisión final ni se interpreta como precisión general.
- 14 herramientas de lectura devolvieron resultados reales; voz Piper/Whisper correcta.
- Seguimiento Plex/Homepage y dos filtros de agenda verificados.
- 13 pruebas deterministas finales pasan; escrituras de calendario simuladas.
- Mediana observada: 11,04 s antes y 14,23 s en el candidato, con carga compartida.

Se reparó la sincronización desde Obsidian en 192.0.2.243 a Qdrant
(colección obsidian_vault), conservando correo como colección independiente.
Se verificó la identidad SSH, instaló rsync y limitó la clave del conector a
lectura del vault desde CT118. La primera sincronización revisó 150 notas y
actualizó cuatro. La recuperación ahora descarta encabezados vacíos y limita
la repetición de fragmentos de una nota. Homepage aparece entre los primeros
resultados con contenido útil.

La herramienta de backups distingue campo ausente, ausencia de tareas
programadas y existencia de otras copias que no puede verificar. El propietario
aclara el 21-09-2026 que actualmente no dispone de backups de ningún tipo;
una réplica Git no representa una recuperación validada del homelab.

Informe completo en Obsidian:
`05 Procedimientos/Hermes - Evaluacion y mejora del prompt 2026-09-20.md`.
Evidencias privadas fuera de Git: `/home/lucifer/auditoria-casa/ia-eval-20260920/`.
