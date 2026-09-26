"""Automatización auditable. Solo reglas deterministas y correo autenticado."""
import json
import re
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr

from demeter_amazon import DOMAINS

CATEGORIES = ('Tecnología', 'Suscripciones e IA', 'Hogar', 'Alimentación', 'Transporte', 'Salud', 'Ocio', 'Otros')
FIELDS = ('merchant','reference','purchased_on','currency','total_minor')


# Comercios cuyas compras se aprueban solas si el correo esta autenticado y
# trae todos los datos con su cita literal. Los comercios cuyos correos no
# traen la fecha de compra no estan: siempre pasan por revision.
AUTO_MERCHANTS = ('anthropic.com', 'openai.com', 'loteriasyapuestas.es', 'poecurrency.com')
OCIO = ('loteriasyapuestas.es', 'poecurrency.com')


def category(merchant):
    """Devuelve la categoria de gasto de un comercio."""
    ...


def authenticated(inbox, row):
    """Indica si el correo de un candidato esta autenticado por su remitente."""
    ...


def annotate(inbox, row, order_ids, actor):
    """Anade detalles y categoria a los pedidos aprobados."""
    ...


def accept_event(inbox, candidate_id, revision, *, actor, reason):
    """Acepta un candidato que es un evento y no una compra."""
    ...


def automate(inbox, limit=500):
    """Aprueba automaticamente los candidatos que cumplen los criterios y devuelve el recuento."""
    ...
