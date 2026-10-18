"""Automatización auditable. Solo reglas deterministas y correo autenticado."""
import json
import re
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr

from demeter_amazon import DOMAINS

CATEGORIES = ('Tecnología', 'Suscripciones e IA', 'Hogar', 'Alimentación', 'Transporte', 'Salud', 'Ocio', 'Otros')
FIELDS = ('merchant','reference','purchased_on','currency','total_minor')


# Comercios cuyas compras se aprueban solas si el correo esta autenticado
# (DMARC de Gmail) y trae los cinco datos con su cita literal. Loterias y
# poecurrency se añadieron el 2026-09-23 tras medir sobre el correo real:
# 29 y 9 compras autenticadas y completas. AliExpress NO esta: sus avisos no
# traen la fecha de compra, asi que siempre pasa por una persona.
AUTO_MERCHANTS = ('anthropic.com', 'openai.com', 'loteriasyapuestas.es', 'poecurrency.com')
OCIO = ('loteriasyapuestas.es', 'poecurrency.com')


def category(merchant):
    ...


def authenticated(inbox, row):
    ...


def annotate(inbox, row, order_ids, actor):
    ...


def accept_event(inbox, candidate_id, revision, *, actor, reason):
    ...


def automate(inbox, limit=500):
    ...
