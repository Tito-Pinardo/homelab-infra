"""Evitar convertir ausencia de tareas programadas en ausencia de copias."""
import ast
from pathlib import Path
import json
import unittest

SOURCE = Path(__file__).resolve().parents[2] / "ansible/roles/ia_asistente/files/ia_tools.py"

class BackupEvidenceTests(unittest.TestCase):
    def result(self, snapshot):
        ...

    def test_missing_jobs_are_unknown(self):
        ...

    def test_no_jobs_does_not_rule_out_manual_copies(self):
        ...

    def test_existing_jobs_preserved(self):
        ...
