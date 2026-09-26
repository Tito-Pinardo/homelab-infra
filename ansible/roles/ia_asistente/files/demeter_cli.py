#!/usr/bin/env python3
"""Administración local de la bandeja; solo ficheros JSON, sin acceso al correo."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys

from demeter_review import Inbox
from demeter_store import Store
from demeter_extract import VERSION


def main():
    """Punto de entrada de la linea de comandos de Demeter."""
    ...


if __name__ == '__main__':
    try:
        main()
    except (ValueError, TypeError, OSError) as exc:
        print(f'Operación no completada: {exc}', file=sys.stderr)
        sys.exit(1)
