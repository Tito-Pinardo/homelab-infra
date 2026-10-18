import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'))
from demeter_store import Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        ...

    def tearDown(self):
        ...

    def purchase(self, **changes):
        ...

    def refund(self, order, **changes):
        ...

    def test_repeated_confirmation_and_shipping_do_not_double_spend(self):
        ...

    def test_conflict_rolls_back(self):
        ...

    def test_reused_message_does_not_create_another_order(self):
        ...

    def test_partial_refunds_deduplicated_and_dated(self):
        ...

    def test_over_refund_rolls_back_evidence(self):
        ...

    def test_accounts_and_currencies_are_separate(self):
        ...

    def test_wrong_account_cannot_attach_evidence(self):
        ...

    def test_invalid_amounts_and_dates(self):
        ...

    def test_persistence(self):
        ...


if __name__ == '__main__':
    unittest.main()
