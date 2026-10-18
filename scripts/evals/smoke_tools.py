#!/usr/bin/env python3
"""Comprueba que las tools de LECTURA de Hermes responden de verdad.

Se ejecuta EN el CT del asistente (192.0.2.247), donde estan el codigo y
las credenciales. Nunca crea, edita ni borra nada: no toca calendario,
Matrix ni documentos pendientes.

Por que existe: el 2026-09-22 las dos tools de Demeter llevaban 13 horas
devolviendo "no disponible" sin que nadie lo notara. La bateria del modelo
no lo ve (solo mira que tool ELIGE, con resultados sinteticos) y los tests
deterministas tampoco (no salen a la red). Esto si.

    ssh root@192.0.2.247 'python3 - ' < scripts/evals/smoke_tools.py

Sale con codigo 1 si alguna tool falla o devuelve un error, para poder
encadenarlo tras un despliegue.
"""
import json
import os
import sys
import time
from pathlib import Path

UNIT = Path('/etc/systemd/system/ia-bot.service')

# Tools de lectura y unos argumentos representativos. Las de escritura
# (crear/editar/borrar evento, indexar/descartar documento) no se prueban
# aqui a proposito.
CASOS = [
    ('get_server_health', {}),
    ('get_ct_info', {'nombre': 'plex'}),
    ('get_game_servers_status', {}),
    ('get_backup_status', {}),
    ('get_cert_status', {}),
    ('get_storage_health', {}),
    ('get_hefesto_status', {}),
    ('get_hipnos_status', {}),
    ('get_nemesis_status', {}),
    ('get_jano_status', {}),
    ('buscar_obsidian', {'query': 'homepage del homelab'}),
    ('buscar_conversaciones', {'query': 'gpu', 'dias_atras': 30}),
    ('buscar_documentos', {'query': 'apuntes'}),
    ('search_email', {'query': 'entradas'}),
    ('get_calendar_events', {'dias_adelante': 7}),
    ('get_expenses_summary', {}),
    ('get_pending_orders', {}),
]


def cargar_entorno():
    ...


def problema(salida: str) -> str | None:
    """Un resultado vacio o con 'error' es un fallo aunque no lance."""
    ...


def main() -> int:
    ...


if __name__ == '__main__':
    sys.exit(main())
