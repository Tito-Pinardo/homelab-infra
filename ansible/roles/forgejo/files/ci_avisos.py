#!/usr/bin/env python3
"""
Avisos del CI de Forgejo en Element (sala de alertas, cifrada).

Forgejo manda un webhook al terminar cada ejecucion de Actions (correcta,
fallida o que vuelve a estar bien tras un fallo). Este servicio lo recibe en
loopback, comprueba la firma y se lo pasa al relay E2EE del CT de Synapse,
el mismo que usan Zabbix y Wazuh. Asi el secreto del relay vive aqui y no
en el runner, que no guarda nada.
"""
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

LISTEN = ("127.0.0.1", int(os.environ.get("CI_AVISOS_PORT", "9010")))
RELAY_URL = os.environ["RELAY_URL"]
RELAY_SECRET = os.environ["RELAY_SECRET"]
ROOM_ID = os.environ["ROOM_ID"]
WEBHOOK_SECRET = open("/etc/forgejo/webhook_secret").read().strip().encode()

ICONOS = {"success": "✅", "failure": "❌", "recover": "🔁"}
NOMBRES = {"ci.yml": "CI", "despliegue.yml": "Despliegue", "plan-pr.yml": "Plan del PR",
           "deriva.yml": "Deriva nocturna", "renovate.yml": "Renovate"}
# Estos mandan su propio resumen (despliegue.py): de ellos solo se avisa si
# fallan, para no repetir.
# Renovate: lo que importa son sus PRs (cada uno con CI y plan).
CON_RESUMEN_PROPIO = {"despliegue.yml", "plan-pr.yml", "deriva.yml", "renovate.yml"}
TEXTOS = {"success": "correcto", "failure": "FALLO", "recover": "vuelve a estar bien"}


def mensaje(evento: str, datos: dict) -> str:
    """Texto del aviso a partir del payload del webhook."""
    ...


def enviar(texto: str) -> None:
    """POST al relay E2EE, con reintentos cortos (igual que casa-matrix.py)."""
    ...


class Receptor(BaseHTTPRequestHandler):
    def do_POST(self):
        ...

    def log_message(self, formato, *args):
        ...


if __name__ == "__main__":
    HTTPServer(LISTEN, Receptor).serve_forever()
