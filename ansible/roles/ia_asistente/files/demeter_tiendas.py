"""Reglas por comercio para los correos que no son de Amazon ni facturas.

Cada regla mira solo su dominio y devuelve None si no lo reconoce. Ninguna
inventa datos: si falta el importe o la fecha, el correo pasa a revision.
"""
import re
from email.utils import parseaddr

from demeter_invoices import invoice_money

# Meses de los resguardos de SELAE ("15 SEP 2026"), en castellano y por
# si acaso en ingles.
MESES = {m: i for i, m in enumerate(('ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO',
                                     'SEP', 'OCT', 'NOV', 'DIC'), 1)}
MESES.update({'JAN': 1, 'APR': 4, 'AUG': 8, 'DEC': 12})

# Un importe que ocupa la linea entera, para no coger cifras sueltas de una
# frase. Uso [ \t]* en vez de \s* para evitar un retroceso cuadratico en
# cuerpos con muchas lineas en blanco.
IMPORTE = re.compile(r'^[ \t]*((?:€|EUR|USD|GBP)[ \t]*\d[\d.,]*|\d[\d.,]*[ \t]*(?:€|EUR|USD|GBP))[ \t]*$', re.M)


def _dominio(sender):
    """Devuelve el dominio del remitente."""
    ...


def _de(sender, *dominios):
    """Indica si el remitente pertenece a alguno de los dominios dados."""
    ...


def _etiquetado(texto, etiqueta):
    """Devuelve el importe que acompana a una etiqueta del texto."""
    ...


def _articulo(texto):
    """Devuelve el nombre del producto comprado."""
    ...


def _loterias(sender, subject, body, received_on):
    """Extrae la compra de un correo de loterias, o None si no aplica."""
    ...


def _aliexpress(sender, subject, body, received_on):
    """Extrae la compra de un correo de AliExpress, o None si no aplica."""
    ...


def _poecurrency(sender, subject, body, received_on):
    """Extrae la compra de un correo de esa tienda, o None si no aplica."""
    ...


REGLAS = (_loterias, _aliexpress, _poecurrency)


def extract_tienda(sender, subject, body, received_on=None):
    """Extrae la compra de un correo aplicando las reglas de cada tienda conocida."""
    ...
