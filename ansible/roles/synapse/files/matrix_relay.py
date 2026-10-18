#!/usr/bin/env python3
"""
Relay HTTP local -> Matrix con cifrado E2EE real.

Por que hace falta esto y no un simple curl como en las salas sin cifrar:
mandar un evento REALMENTE cifrado exige mantener un dispositivo Matrix con
sesiones Olm/Megolm establecidas - eso es estado que tiene que persistir
entre envios, no algo que un script de una sola ejecucion (como los de
Zabbix/Wazuh) pueda hacer por si solo. Este demonio hace de intermediario:
mantiene el cliente nio (con su "store" de claves en disco) vivo todo el
rato, y los scripts de Zabbix/Wazuh solo le hacen un POST local sencillo.

Escucha en todas las interfaces (Zabbix/Wazuh estan en otros CT) pero exige
un secreto compartido (RELAY_SHARED_SECRET) por cabecera - sin eso,
cualquiera en la LAN podria inyectar "alertas" falsas en la sala cifrada.
"""
import asyncio
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from nio import AsyncClient, LoginError

HOMESERVER = "http://localhost:8008"
STORE_PATH = "/var/lib/matrix-relay/store"
CREDS_PATH = "/var/lib/matrix-relay/credentials.json"
LISTEN_PORT = 8009
SHARED_SECRET = os.environ["RELAY_SHARED_SECRET"]

client: AsyncClient | None = None
loop: asyncio.AbstractEventLoop | None = None


async def ensure_ready():
    """Login (una vez, guardando credenciales) y sync inicial para que el
    cliente conozca las salas y sus dispositivos antes de mandar nada."""
    ...


async def send(room_id: str, body: str):
    ...


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        ...

    def log_message(self, fmt, *args):
        ...


def main():
    ...


if __name__ == "__main__":
    main()
