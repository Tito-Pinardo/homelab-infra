"""Extractor conservador de texto Amazon.es, sin red ni ejecución de instrucciones.

Produce candidatos, nunca movimientos. Las coincidencias no autentican remitentes.
HTML/PDF deben convertirse en texto por el futuro recolector conservando su origen.
"""
import re
from datetime import datetime
from email.utils import parseaddr
from demeter_invoices import extract_invoice
from demeter_amazon import extract_amazon
from demeter_tiendas import extract_tienda

VERSION = 'purchases-tiendas-v6'
REFERENCE = re.compile(r'(?<!\d)\d{3}-\d{7}-\d{7}(?!\d)')
MONEY = re.compile(r'(?P<number>(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{2})?)\s*(?P<currency>EUR|€|USD|GBP)', re.I)
TOTAL = re.compile(r'^[ \t]*(?:total(?: del pedido)?|importe total)[ \t]*:[ \t]*(.*?)[ \t]*$', re.I | re.M)
DATE = re.compile(r'^[ \t]*fecha del pedido[ \t]*:[ \t]*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})[ \t]*$', re.I | re.M)


def money(text):
    """Interpreta un importe escrito en formato espanol."""
    ...


def extract(sender, subject, body, received_on=None):
    """Extrae los datos de compra de un correo."""
    ...
