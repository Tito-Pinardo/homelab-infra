from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'))
from demeter_extract import extract
from demeter_invoices import invoice_money


def receipt(amount='5.00', reference='1111-2222', when='September 20, 2026'):
    ...


class InvoiceTests(unittest.TestCase):
    def parse(self, body, subject='Your receipt from Anthropic Ireland, Limited #1111-2222'):
        ...

    def test_five_and_eighteen_euro_receipts(self):
        ...

    def test_invoice_pdf_reference_unifies_invoice_and_receipt(self):
        ...

    def test_ambiguous_totals_dates_and_partial_payment_need_review(self):
        ...

    def test_currencies_and_both_decimal_formats(self):
        ...

    def test_newsletter_and_spoofed_domain_are_not_invoices(self):
        ...


if __name__ == '__main__': unittest.main()
