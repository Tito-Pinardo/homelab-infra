import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

MODULES = Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'
sys.path.insert(0, str(MODULES))
from demeter_extract import extract, money
from demeter_review import Inbox, StaleRevision
from demeter_store import MIGRATIONS, SCHEMA, Store


REF = '123-1234567-1234567'
REF2 = '456-1234567-1234567'
BODY = f'Gracias por tu pedido\nPedido: {REF}\nFecha del pedido: 21/09/2026\nTotal del pedido: 1.234,56 EUR'
PURCHASE = dict(merchant='amazon.es', reference=REF, purchased_on='2026-09-21', currency='EUR', total_minor=123456)
EVIDENCE = dict(merchant='amazon.es', reference=REF, purchased_on='21/09/2026', currency='EUR', total_minor='1.234,56 EUR')


class ExtractionTests(unittest.TestCase):
    def extract(self, body=BODY, subject='Confirmación del pedido', sender='Amazon <auto@amazon.es>'):
        ...

    def test_spanish_total_with_provenance(self):
        ...

    def test_currency_not_guessed_and_formats_strict(self):
        ...

    def test_missing_and_conflicting_totals_are_unknown(self):
        ...

    def test_multiple_orders_not_assigned_combined_total(self):
        ...

    def test_classification_and_malicious_text(self):
        ...

    def test_sender_spoof_and_forward_flagged(self):
        ...

    def test_invalid_date_not_replaced_by_email_date(self):
        ...

    def test_many_html_blank_lines_do_not_consume_adjacent_fields(self):
        ...


class ReviewTests(unittest.TestCase):
    def setUp(self):
        ...

    def tearDown(self):
        ...

    def ingest(self, **changes):
        ...

    def ready(self, **changes):
        ...

    def approve(self, candidate, **changes):
        ...

    def orders(self):
        ...

    # La papelera de Element (2026-09-23): lo que aprueba la automatica se
    # deshace con una reaccion, igual que los eventos del calendario.
    def test_la_papelera_deshace_una_aprobacion_automatica(self):
        ...

    def test_la_papelera_no_toca_lo_que_aprobo_una_persona(self):
        ...

    def test_la_papelera_solo_actua_sobre_compras_confirmadas(self):
        ...

    def test_un_pedido_que_respalda_otro_correo_no_se_borra(self):
        ...

    def test_ingestion_idempotent_with_content_conflict(self):
        ...

    def test_extraction_never_writes_ledger_and_survives_restart(self):
        ...

    def test_approval_audited_and_cannot_repeat(self):
        ...

    def test_reject_evidence_not_in_source(self):
        ...

    def test_error_and_explicit_retry(self):
        ...

    def test_cross_account_forward_requires_explicit_link(self):
        ...

    def test_discard_and_stale_review_from_other_connection(self):
        ...

    def test_reader_opens_current_schema_while_writer_is_active(self):
        ...

    def test_multiple_orders_reviewed_individually(self):
        ...

    def test_batch_failure_rolls_back_everything(self):
        ...

    def test_audit_failure_rolls_back_ledger_and_status(self):
        ...

    def test_publicity_can_be_discarded_without_spend(self):
        ...


class MigrationTests(unittest.TestCase):
    def test_legacy_database_preserved(self):
        ...

    def test_failed_migration_is_atomic(self):
        ...

    def test_newer_schema_rejected(self):
        ...

    def test_cli_synthetic_workflow_and_private_permissions(self):
        ...


if __name__ == '__main__':
    unittest.main()
