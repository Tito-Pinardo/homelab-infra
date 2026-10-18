from email.message import EmailMessage
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'))
from demeter_mail import (CaptureError, DEFAULT_QUERY, MAX_MESSAGE_BYTES, all_mail, capture,
                          construir_consulta, envelope)
from demeter_extract import extract
from demeter_store import Store


def message(identifier='one', *, html=False, body=None):
    ...


class FakeIMAP:
    def __init__(self, messages=None, validity=b'1'):
        ...

    def list(self):
        ...

    def select(self, mailbox, readonly=False):
        ...

    def response(self, key):
        ...

    def uid(self, command, uid, query):
        ...


class CaptureTests(unittest.TestCase):
    def setUp(self):
        ...

    def tearDown(self):
        ...

    def run_capture(self, imap, **changes):
        ...

    def count(self, table):
        ...

    def test_readonly_all_mail_peek_and_no_side_effects(self):
        ...

    def test_incremental_and_batch_resume(self):
        ...

    def test_network_failure_does_not_skip_uid(self):
        ...

    def test_uidvalidity_reset_preserves_deduplication(self):
        ...

    def test_new_query_reuses_captures(self):
        ...

    def test_late_category_detected_without_redownloading_known_messages(self):
        ...

    def test_conflicting_message_is_preserved_in_quarantine(self):
        ...

    def test_oversize_is_visible_and_not_downloaded(self):
        ...

    def test_database_failure_rolls_back_candidate_and_cursor(self):
        ...

    def test_html_and_missing_message_id(self):
        ...

    def test_html_table_keeps_total_label_with_its_value(self):
        ...


class ConsultaTests(unittest.TestCase):
    """Lo que NO se captura importa tanto como lo que sí.

    Gmail clasifica en "compras" los avisos de episodios de una suscripción
    ya pagada: 286 de los 431 mensajes atascados el 2026-09-23. Excluirlos en
    la captura evita que el atasco se vuelva a formar solo.
    """

    def test_excluye_los_remitentes_de_ruido_sin_tocar_el_resto(self):
        ...

    def test_se_puede_pedir_la_consulta_completa_o_una_propia(self):
        ...


if __name__ == '__main__':
    unittest.main()
