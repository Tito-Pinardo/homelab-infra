#!/usr/bin/env python3
"""Autorizacion inicial de Cronos (Google Calendar). Se ejecuta una sola vez a
mano: pide un codigo de dispositivo, lo muestra y espera a que lo confirme
desde un navegador. Despues guarda el token para cronos_client.py.

Uso: python3 cronos_authorize.py
"""
import json
import os
import sys
import time

import requests

CLIENT_ID = os.environ["GOOGLE_CALENDAR_CLIENT_ID"]
CLIENT_SECRET = os.environ["GOOGLE_CALENDAR_CLIENT_SECRET"]
SCOPE = "https://www.googleapis.com/auth/calendar"
TOKEN_PATH = "/var/lib/ia-bot/cronos_token.json"


def main():
    """Autoriza el acceso a Google Calendar mediante el flujo de dispositivo y guarda el token."""
    ...


if __name__ == "__main__":
    main()
