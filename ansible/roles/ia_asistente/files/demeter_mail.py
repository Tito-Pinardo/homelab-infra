#!/usr/bin/env python3
"""Captura Gmail de solo lectura a una bandeja local, sin Qdrant ni avisos."""
import argparse
from datetime import date, timedelta
from email import policy
from email.parser import BytesParser
import fcntl
import hashlib
from html.parser import HTMLParser
import imaplib
import json
import os
from pathlib import Path
import re
import ssl

from demeter_review import Inbox
from demeter_store import Store, day


# Sintaxis Gmail por X-GM-RAW. Excluye enviados y borradores incluso en All Mail.
DEFAULT_QUERY = ('(category:purchases OR (from:stripe.com (subject:receipt OR subject:invoice)) OR '
                 '((from:amazon.es OR from:amazon.com OR from:amazon.co.uk OR from:amazon.de OR from:amazon.fr OR from:amazon.it) '
                 '(subject:pedido OR subject:pedidos OR subject:reembolso OR subject:devolucion OR subject:factura OR '
                 'subject:entrega OR subject:enviado OR subject:order OR subject:shipped OR subject:delivered OR subject:refund))) -in:sent -in:drafts')
# Remitentes que Gmail mete en la categoria "compras" pero que no venden
# nada: avisos de contenido de una suscripcion ya pagada. El 2026-09-23, 286
# de los 431 mensajes por revisar eran episodios nuevos de un creador de
# Patreon ("Perfect World Episodio 267"), y con ese ruido la bandeja era
# inabordable. Se excluyen en la propia consulta de Gmail para no llegar a
# descargarlos. La lista es configurable desde Ansible; los RECIBOS de
# Patreon (patreon.com a secas) siguen entrando.
REMITENTES_IGNORADOS = ('creator.patreon.com',)


def construir_consulta(base=None, ignorados=REMITENTES_IGNORADOS):
    ...


MAX_MESSAGE_BYTES = 10 * 1024 * 1024
MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
ACCOUNTS = (
    ('admin@example.org', 'IMAP_APP_PASSWORD_CORREO1'),
    ('admin@example.org', 'IMAP_APP_PASSWORD_CORREO2'),
)


class CaptureError(RuntimeError):
    """Solo códigos controlados, nunca texto de correo ni respuesta del servidor."""


class TextHTML(HTMLParser):
    def __init__(self):
        ...

    def handle_starttag(self, tag, attrs):
        ...

    def handle_endtag(self, tag):
        ...

    def handle_data(self, data):
        ...


def envelope(raw, account, gmail_id, received_on):
    ...


def quote(value):
    ...


def all_mail(imap):
    ...


def metadata(imap, uid):
    ...


def capture(imap, store, account, *, query=DEFAULT_QUERY, limit=100, since=None, reconcile=False):
    """Guardar cada mensaje/cuarentena y su cursor en una transacción.

    Fallo de red: detener cuenta sin saltar el UID. Mensaje ilegible: conservarlo
    en cuarentena y continuar. No modifica el estado de sync_correo/Hermes.
    """
    ...


def main():
    ...


if __name__ == '__main__':
    main()
