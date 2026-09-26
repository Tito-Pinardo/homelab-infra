"""Evitar convertir ausencia de tareas programadas en ausencia de copias."""
import ast
from pathlib import Path
import json
import unittest

SOURCE = Path(__file__).resolve().parents[2] / "ansible/roles/ia_asistente/files/ia_tools.py"

class BackupEvidenceTests(unittest.TestCase):
    def result(self, snapshot):
        """Ejecuta el estado de copias con una instantanea de prueba."""
        ...

    def test_missing_jobs_are_unknown(self):
        """Comprueba que sin datos de trabajos el estado es desconocido."""
        ...

    def test_no_jobs_does_not_rule_out_manual_copies(self):
        """Comprueba que sin trabajos no se descartan copias manuales."""
        ...

    def test_existing_jobs_preserved(self):
        """Comprueba que se conservan los trabajos existentes."""
        ...
