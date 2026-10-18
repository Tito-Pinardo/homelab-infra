from email.message import EmailMessage
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'))
from demeter_documents import documents


def simple_pdf():
    ...


def mime(data):
    ...


class DocumentTests(unittest.TestCase):
    def test_pdf_text_extracted_locally(self):
        ...

    def test_invalid_pdf_retained_as_failure_not_empty_success(self):
        ...

    def test_timeout_is_reported(self):
        ...


if __name__=='__main__':unittest.main()
