"""Bandeja persistente y revisión explícita. No recibe IMAP ni publica avisos."""
import hashlib
import json

from demeter_extract import VERSION, extract
from demeter_documents import documents
from demeter_store import Store, required, day, amount


class StaleRevision(ValueError):
    pass


def encode(value):
    ...


class Inbox:
    def __init__(self, store: Store):
        ...

    def _audit(self, candidate_id, revision, actor, action, details):
        ...

    def get(self, candidate_id):
        ...

    @staticmethod
    def source(row):
        ...

    def _check(self, candidate_id, revision, statuses):
        ...

    def ingest(self, *, account, message_id, sender, subject, body, received_on):
        ...

    def process(self, candidate_id, revision):
        ...

    def reprocess(self, candidate_id, revision, *, actor, reason):
        ...

    def retry(self, candidate_id, revision, *, actor):
        ...

    def discard(self, candidate_id, revision, *, actor, reason):
        ...

    def undo_auto(self, candidate_id, *, actor, reason, revision=None):
        """Deshace una aprobacion AUTOMATICA: la papelera de Element.

        Mismo contrato que el calendario desde el 2026-09-17: lo que se crea
        solo, se deshace con un gesto. Por eso solo actua si la ultima
        aprobacion la hizo un actor `auto:`; una compra que confirmo una
        persona no se toca desde el chat.

        Quita la evidencia de ESTE correo. El pedido solo se borra si ya nada
        lo respalda: si otro correo lo sostiene, tiene reembolsos o alguien
        lo edito en la pagina, se conserva y se dice, porque borrarlo seria
        perder datos que no vienen de este mensaje. El correo queda
        descartado y la auditoria guarda la decision entera.
        """
        ...

    def confirm_auto(self, candidate_id, revision, *, actor, reason):
        """Visto bueno de una persona a lo que aprobo la automatica.

        No cambia importes ni estado: la compra ya cuenta. Solo deja
        constancia de que alguien la ha mirado, para que salga de la lista
        de "aprobadas solas" de la pagina.
        """
        ...

    def auto_pending(self):
        """Compras que aprobo la automatica y nadie ha confirmado todavia."""
        ...

    def approve_purchase(self, candidate_id, revision, *, actor, purchase, evidence,
                         reason, existing_order_id=None):
        ...

    def approve_purchases(self, candidate_id, revision, *, actor, decisions, reason):
        """Confirma uno o varios pedidos revisados, todos o ninguno.

        Cada decisión incluye purchase y evidence por campo; opcionalmente
        existing_order_id para un reenvío entre cuentas. No la llama el extractor.
        """
        ...

    def listing(self, status='review', limit=50):
        ...
