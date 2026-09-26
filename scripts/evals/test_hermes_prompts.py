"""Regresión del anclaje temporal sin cargar Matrix ni consultar Ollama."""
import ast
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BOT = Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files/ia_bot.py'

def load_prompt():
    """Carga la funcion que genera el prompt de sistema."""
    ...

class CalendarContextTests(unittest.TestCase):
    def test_relative_date_regression(self):
        """Comprueba las fechas de la semana en el prompt."""
        ...
    def test_year_boundary(self):
        """Comprueba las fechas al cambiar de ano."""
        ...
    def test_leap_year(self):
        """Comprueba las fechas en un ano bisiesto."""
        ...
    def test_dst_calendar_days(self):
        """Comprueba las fechas en el cambio de hora."""
        ...

class ToolFreshnessTests(unittest.TestCase):
    def guidance(self, value):
        """Carga y ejecuta la guia de resultados de herramientas."""
        ...
    def test_old_result(self):
        """Comprueba el aviso de datos antiguos."""
        ...
    def test_fresh_missing_and_untrusted_values(self):
        """Comprueba que no hay aviso con datos recientes, ausentes o no fiables."""
        ...

if __name__=='__main__': unittest.main()
