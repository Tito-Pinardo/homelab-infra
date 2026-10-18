"""
Cliente de la API REST de AMP para el tool de estado de servidores de juego.

Lecciones ya pagadas en produccion por battlepros-status (bot de Discord,
CT106/dockge, no relacionado con este repo) que se reutilizan aqui:
- NUNCA hacer login en cada consulta - genero un incidente real de "fuerza
  bruta" (miles de intentos/dia). La sesion se cachea en memoria del
  proceso y solo se renueva si AMP la rechaza.
- SIEMPRE contra la IP LAN (192.0.2.136:8080), NUNCA el dominio publico
  (amp.example.org via Traefik/Cloudflare) - mismo incidente de arriba.
- Cabecera "Accept: application/json" obligatoria, si no AMP devuelve un
  error "Invalid accept header value".

Identidad separada a proposito (decision mia, 2026-09-16): usuario
"bot_ia_status" con rol "bot-ia" (clonado de "bot-discord", mismo permiso
acotado de solo lectura) - NUNCA se reutiliza la cuenta del bot de Discord,
para no compartir blast radius/auditoria/rotacion entre ambos consumidores.
"""
import base64
import hmac
import os
import struct
import time

import requests

AMP_URL = "http://192.0.2.136:8080"
AMP_USERNAME = os.environ["AMP_USERNAME"]
AMP_PASSWORD = os.environ["AMP_PASSWORD"]
AMP_TOTP_SECRET = os.environ.get("AMP_TOTP_SECRET", "")

_session_id: str | None = None


def _totp(secret: str) -> str:
    """Generador TOTP (RFC 6238) sin dependencias de terceros - el secreto
    de AMP viene en base32, igual que cualquier app de 2FA estandar."""
    ...


def _login() -> str:
    ...


def _call(endpoint: str, payload: dict | None = None) -> dict:
    ...


def get_instances() -> list[dict]:
    """Devuelve una lista simplificada con estado + metricas en vivo. La
    propia respuesta de GetInstances YA trae CPU/RAM/jugadores activos por
    instancia (campo "Metrics") - no hace falta ninguna llamada extra por
    servidor."""
    ...
