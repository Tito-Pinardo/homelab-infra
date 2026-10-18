#!/usr/bin/env python3
"""
Autorizacion INICIAL de Cronos (Google Calendar) - se ejecuta una sola vez
a mano. Pide un codigo de dispositivo a Google, lo muestra por pantalla, y
espera a que el usuario lo introduzca en su navegador (movil, PC, lo que
sea - este script nunca ve ni pide contrasenas de Google). Al confirmar,
guarda el refresh_token en disco para que cronos_client.py lo use siempre
a partir de ahora sin volver a pedir autorizacion.

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
    ...


if __name__ == "__main__":
    main()
