"""Regresión del anclaje temporal sin cargar Matrix ni consultar Ollama."""
import ast
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BOT = Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files/ia_bot.py'

def load_prompt():
    ...

class CalendarContextTests(unittest.TestCase):
    def test_relative_date_regression(self):
        ...
    def test_year_boundary(self):
        ...
    def test_leap_year(self):
        ...
    def test_dst_calendar_days(self):
        ...

class ToolFreshnessTests(unittest.TestCase):
    def guidance(self, value):
        ...
    def test_old_result(self):
        ...
    def test_fresh_missing_and_untrusted_values(self):
        ...

if __name__=='__main__': unittest.main()
