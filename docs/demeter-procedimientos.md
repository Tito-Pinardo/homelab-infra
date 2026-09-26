# Demeter

Demeter gestiona mis compras, entregas y gastos a partir del correo, con una
pagina privada y consultas desde Hermes. Todo el procesamiento es local.

## Piezas

| Pieza | Codigo |
|---|---|
| Registro de pedidos, entregas y devoluciones (SQLite) | `demeter_store.py` |
| Bandeja de revision de correos candidatos | `demeter_review.py` |
| Captura de correo por IMAP, en solo lectura | `demeter_mail.py` |
| Extraccion de datos (tiendas, Amazon, facturas, PDFs) | `demeter_extract.py`, `demeter_tiendas.py`, `demeter_amazon.py`, `demeter_invoices.py`, `demeter_documents.py` |
| Aprobacion automatica de lo que cumple los criterios | `demeter_automation.py` |
| Consultas (resumen, panel mensual, pedidos) | `demeter_queries.py`, `demeter_query_server.py` |
| Deshacer desde Element | `demeter_undo_server.py`, `demeter_client.py` |
| Pagina privada | `demeter_web.py`, `demeter_static/` |
| Copia de seguridad verificada | `demeter_backup.py` |
| Linea de comandos | `demeter_cli.py` |

Todo vive en `ansible/roles/ia_asistente/files/` y lo despliega el rol
`ia_asistente` (`playbooks/demeter.yml`).

## Principios

- El dinero se guarda en enteros, en la unidad minima de cada moneda.
- Nada se registra sin evidencia del correo original.
- Lo dudoso (remitente no autenticado, importes ambiguos, varios pedidos en un
  correo) pasa a revision y no se aprueba solo.
- Cada decision queda en un historial de auditoria.
- Lo que se aprueba solo se anuncia en Matrix y se puede deshacer reaccionando
  con la papelera.
- La pagina solo es accesible desde la red local, detras del proxy con
  autenticacion.
