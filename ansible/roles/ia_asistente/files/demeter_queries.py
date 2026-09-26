"""Consultas deterministas compartidas por la página y Hermes. Solo lectura."""
import json
import re
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from demeter_amazon import DOMAINS


def today():
    """Devuelve la fecha de hoy en hora local."""
    ...


def month_bounds(month=None):
    """Devuelve el mes y sus fechas de inicio y fin."""
    ...


def rows(db,sql,params=()):
    """Ejecuta una consulta y devuelve las filas como diccionarios."""
    ...


def coverage(db):
    """Devuelve la cobertura de la ultima captura de correo."""
    ...


def orders(db, *, month=None, q='', merchant='', status='', limit=100, offset=0):
    """Devuelve los pedidos filtrados y paginados."""
    ...


def dashboard(db, month=None):
    """Devuelve los datos del panel mensual."""
    ...


def query(db, args):
    """Resuelve una consulta de Demeter por accion."""
    ...
