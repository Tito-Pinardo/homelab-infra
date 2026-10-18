"""Regresión de automatización, meses y paquetes parciales con mensajes sintéticos."""
import io
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
import threading
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'ansible/roles/ia_asistente/files'))
from demeter_store import Store
from demeter_review import Inbox
from demeter_extract import extract
from demeter_automation import automate, accept_event
from demeter_queries import dashboard, orders, query
from demeter_query_server import Server, Handler
from demeter_web import create_app

REF='123-1234567-1234567'
BODY=f'Gracias por tu pedido\nPedido {REF}\nFecha del pedido: 20/09/2026\nTotal del pedido: 24,90 EUR\nProducto: Teclado de prueba\nEntrega prevista: 24/09/2026'
TOKEN='only-test-token'*4
ORIGIN='https://demeter.home.arpa'

class OrganizationTests(unittest.TestCase):
    def setUp(self):
        ...
        ...
    def candidate(self,subject='Confirmación del pedido',body=BODY,number=1,auth=True,day='2026-09-20'):
        ...
    def test_automatic_purchase_and_repeat_do_not_duplicate(self):
        ...
    def test_untrusted_and_conflicting_stay_in_review(self):
        ...
    def test_dmarc_other_domain_not_accepted(self):
        ...
    def test_partial_delivery_and_event_without_purchase(self):
        ...
    def test_months_refunds_categories_currency_and_search(self):
        ...
    def test_unknown_dates_and_multiorder_not_automatic(self):
        ...
    def test_english_format_and_negated_delivery(self):
        ...
    def test_readonly_query_during_uncommitted_capture(self):
        ...

    def test_socket_can_query_but_not_write(self):
        ...

class OrganizationWebTests(unittest.TestCase):
    candidate = OrganizationTests.candidate
    tearDown = OrganizationTests.tearDown
    def request(self,path,method='get',headers=None,**kw):
        ...
    def setUp(self):
        ...
    def test_edit_category_receipt_and_stale_revision(self):
        ...
    def test_eml_import_idempotent_and_not_automatically_trusted(self):
        ...
    def test_import_csrf_and_invalid_files(self):
        ...

if __name__=='__main__':unittest.main()
