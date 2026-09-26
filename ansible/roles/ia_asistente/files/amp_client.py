"""Cliente de la API de AMP para consultar el estado de los servidores de juego.

- La sesion se reutiliza y solo se renueva si AMP la rechaza: no hago login
  en cada consulta.
- Hablo con el panel por la red interna, no por el dominio publico.
"""
import base64
import hmac
import os
import struct
import time

import requests

AMP_URL = "http://192.0.2.17:8080"
AMP_USERNAME = os.environ["AMP_USERNAME"]
AMP_PASSWORD = os.environ["AMP_PASSWORD"]
AMP_TOTP_SECRET = os.environ.get("AMP_TOTP_SECRET", "")

_session_id: str | None = None


def _totp(secret: str) -> str:
    """Genera el codigo TOTP actual para el inicio de sesion."""
    ...


def _login() -> str:
    """Inicia sesion en el panel de servidores de juego."""
    ...


def _call(endpoint: str, payload: dict | None = None) -> dict:
    """Llama a un endpoint del panel, reintentando el login si la sesion caduco."""
    ...


def get_instances() -> list[dict]:
    """Devuelve las instancias de servidores de juego con su estado y metricas."""
    ...
