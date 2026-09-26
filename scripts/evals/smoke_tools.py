#!/usr/bin/env python3
"""Comprueba que las herramientas de lectura de Hermes responden de verdad.

Se ejecuta en el CT del asistente, donde estan el codigo y las credenciales.
Nunca crea, edita ni borra nada. La bateria del modelo no detecta una
herramienta caida porque trabaja con resultados sinteticos.
"""
import json
import os
import sys
import time
from pathlib import Path

UNIT = Path('/etc/systemd/system/ia-bot.service')

# Herramientas de lectura con argumentos representativos. Las de escritura no
# se prueban aqui a proposito.
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
    """Carga las variables de entorno del servicio del bot."""
    ...


def problema(salida: str) -> str | None:
    """Indica si el resultado de una herramienta es un fallo."""
    ...


def main() -> int:
    """Punto de entrada: ejecuta cada herramienta una vez y comprueba que responde."""
    ...


if __name__ == '__main__':
    sys.exit(main())
