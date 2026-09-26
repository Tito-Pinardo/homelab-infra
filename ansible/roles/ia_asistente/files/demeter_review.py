"""Bandeja persistente y revisión explícita. No recibe IMAP ni publica avisos."""
import hashlib
import json

from demeter_extract import VERSION, extract
from demeter_documents import documents
from demeter_store import Store, required, day, amount


class StaleRevision(ValueError):
    pass


def encode(value):
    """Serializa un valor a JSON de forma estable."""
    ...


class Inbox:
    def __init__(self, store: Store):
        """Inicializa la bandeja de revision sobre un almacen."""
        ...

    def _audit(self, candidate_id, revision, actor, action, details):
        """Registra una accion en el historial de auditoria de un candidato."""
        ...

    def get(self, candidate_id):
        """Devuelve un candidato por su identificador."""
        ...

    @staticmethod
    def source(row):
        """Devuelve el texto completo de un candidato: remitente, asunto, cuerpo y documentos."""
        ...

    def _check(self, candidate_id, revision, statuses):
        """Comprueba que un candidato esta en la revision y estado esperados."""
        ...

    def ingest(self, *, account, message_id, sender, subject, body, received_on):
        """Da de alta un correo como candidato a compra."""
        ...

    def process(self, candidate_id, revision):
        """Procesa un candidato pendiente y decide si se aprueba solo o pasa a revision."""
        ...

    def reprocess(self, candidate_id, revision, *, actor, reason):
        """Vuelve a poner un candidato en cola para procesarlo de nuevo."""
        ...

    def retry(self, candidate_id, revision, *, actor):
        """Reintenta un candidato que fallo."""
        ...

    def discard(self, candidate_id, revision, *, actor, reason):
        """Descarta un candidato."""
        ...

    def undo_auto(self, candidate_id, *, actor, reason, revision=None):
        """Deshace una aprobacion automatica."""
        ...

    def confirm_auto(self, candidate_id, revision, *, actor, reason):
        """Confirma una aprobacion automatica."""
        ...

    def auto_pending(self):
        """Devuelve las aprobaciones automaticas sin confirmar."""
        ...

    def approve_purchase(self, candidate_id, revision, *, actor, purchase, evidence,
                         reason, existing_order_id=None):
        """Aprueba un candidato como una compra."""
        ...

    def approve_purchases(self, candidate_id, revision, *, actor, decisions, reason):
        """Aprueba uno o varios pedidos de un candidato, todos o ninguno."""
        ...

    def listing(self, status='review', limit=50):
        """Devuelve los candidatos de un estado."""
        ...
