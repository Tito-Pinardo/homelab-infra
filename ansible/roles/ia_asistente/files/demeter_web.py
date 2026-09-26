#!/usr/bin/env python3
"""Página privada de revisión detrás de Caddy/Authelia. Sin login alternativo."""
from datetime import date
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
from urllib.parse import urlsplit

from flask import Flask, abort, g, jsonify, request, send_from_directory, session

from demeter_extract import VERSION
from demeter_review import Inbox, StaleRevision
from demeter_store import Store
from demeter_queries import dashboard, orders, month_bounds
from demeter_automation import accept_event, CATEGORIES


def create_app(database, proxy_token, *, allowed_users=('usuario',), proxy_ips=('192.0.2.24',),
               origin='https://demeter.home.example'):
    """Crea la aplicacion web de Demeter: autenticacion detras del proxy, resumen, panel mensual, pedidos, importacion de correos, revision de candidatos, compras automaticas y remitentes."""
    ...


if __name__ == '__main__':
    from waitress import serve
    token = Path(os.environ.get('DEMETER_PROXY_TOKEN_FILE', '/etc/demeter-proxy-token')).read_text().strip()
    app = create_app(os.environ.get('DEMETER_DB', '/var/lib/demeter/queue.sqlite'), token)
    serve(app, host='192.0.2.27', port=8092, threads=4, max_request_body_size=11*1024*1024,
          channel_timeout=30, clear_untrusted_proxy_headers=True)
