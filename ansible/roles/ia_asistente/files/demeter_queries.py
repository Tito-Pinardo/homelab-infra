"""Consultas deterministas compartidas por la página y Hermes. Solo lectura."""
import json
import re
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from demeter_amazon import DOMAINS


def today():
    ...


def month_bounds(month=None):
    ...


def rows(db,sql,params=()):
    ...


def coverage(db):
    ...


def orders(db, *, month=None, q='', merchant='', status='', limit=100, offset=0):
    ...


def dashboard(db, month=None):
    ...


def query(db, args):
    ...
