"""PDFs adjuntos: texto local, acotado y sin seguir enlaces del mensaje."""
from email import policy
from email.parser import BytesParser
import hashlib
from pathlib import Path
import subprocess
import tempfile


def documents(raw):
    ...
