from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'))
from demeter_backup import backup, verify
from demeter_store import Store, MIGRATIONS


class BackupTests(unittest.TestCase):
    def test_backup_restores_committed_data(self):
        ...

    def test_missing_database_does_not_create_empty_source(self):
        ...

    def test_rotation_keeps_other_files_and_latest_valid_snapshot(self):
        ...


if __name__ == '__main__':
    unittest.main()
