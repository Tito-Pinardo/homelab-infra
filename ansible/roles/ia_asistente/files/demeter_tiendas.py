"""Reglas por comercio para los correos que no son ni Amazon ni factura Stripe.

Por que existe: el 2026-09-23 habia 431 mensajes por revisar y NINGUNO con
los datos completos, asi que revisarlos era teclear a mano cada importe. Los
tres remitentes con mas atasco (Loterias 35, poecurrency 24, AliExpress 16)
si traen el dato escrito en el correo; solo faltaba leerlo.

Cada regla mira unicamente el dominio que le toca y devuelve None si no lo
reconoce, igual que `demeter_invoices.extract_invoice`. Ninguna INVENTA un
dato: si el importe o la fecha no estan escritos, se dejan vacios y el motivo
correspondiente lo dice, que es justo lo que la pagina pide comprobar.
"""
import re
from email.utils import parseaddr

from demeter_invoices import invoice_money

# Meses de los resguardos de SELAE ("15 SEP 2026"), en castellano y por
# si acaso en ingles.
MESES = {m: i for i, m in enumerate(('ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO',
                                     'SEP', 'OCT', 'NOV', 'DIC'), 1)}
MESES.update({'JAN': 1, 'APR': 4, 'AUG': 8, 'DEC': 12})

# Un importe que ocupa la linea entera. Los correos de estos comercios ponen
# la etiqueta en una linea y la cifra en la siguiente, y asi se evita coger
# cifras sueltas de dentro de una frase ("tu saldo actual es: 0,00€").
# Ojo con \s: incluye el salto de linea y, en cuerpos con miles de espacios
# en blanco (AliExpress manda cientos de lineas vacias), `^\s*` retrocede de
# forma cuadratica y el extractor se queda colgado. Medido el 2026-09-23:
# 431 mensajes tardaban >2 min al 100% de CPU. Con [ \t]* son 2 segundos.
IMPORTE = re.compile(r'^[ \t]*((?:€|EUR|USD|GBP)[ \t]*\d[\d.,]*|\d[\d.,]*[ \t]*(?:€|EUR|USD|GBP))[ \t]*$', re.M)


def _dominio(sender):
    ...


def _de(sender, *dominios):
    ...


def _etiquetado(texto, etiqueta):
    """Importe que va tras una etiqueta, en su linea o en la siguiente.

    Devuelve (minor, moneda, cita literal) o None. La cita se guarda como
    evidencia para que en la pagina se vea de donde sale el numero.
    """
    ...


def _articulo(texto):
    """Nombre del producto, para que la lista no diga solo 'Comercio'."""
    ...


def _loterias(sender, subject, body, received_on):
    ...


def _aliexpress(sender, subject, body, received_on):
    ...


def _poecurrency(sender, subject, body, received_on):
    ...


REGLAS = (_loterias, _aliexpress, _poecurrency)


def extract_tienda(sender, subject, body, received_on=None):
    ...
