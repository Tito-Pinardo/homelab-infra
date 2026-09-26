"""Recibos Stripe y facturas textuales; importes exactos y evidencia literal."""
import re
from datetime import date
from email.utils import parseaddr

MONTHS = {name.lower(): i for i, name in enumerate(
    ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'), 1)}
MONTHS.update({name[:3]: value for name, value in list(MONTHS.items())})
MONEY_TOKEN = r'(?:€|£|EUR|USD|GBP)\s*\d[\d.,]*(?:\s*(?:EUR|USD|GBP))?|\d[\d.,]*\s*(?:€|£|EUR|USD|GBP)'
DATE_TOKEN = r'(?:[A-Za-z]+ \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})'


def invoice_money(text):
    """Interpreta un importe de una factura."""
    ...


def invoice_date(value):
    """Interpreta la fecha de una factura."""
    ...


def extract_invoice(sender, subject, body):
    """Extrae los datos de una factura de suscripcion."""
    ...
