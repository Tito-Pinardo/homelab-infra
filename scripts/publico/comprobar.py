#!/usr/bin/env python3
"""Control de fugas de la copia publica: bloquea si encuentra algo.

Busca en el arbol ya generado los patrones prohibidos de reglas.yml, IPv4
publicas fuera de la lista permitida y secretos (gitleaks). Sale con 1 y la
lista de hallazgos si hay alguno.

Uso: comprobar.py <carpeta> [--json fichero]
"""
import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

REGLAS = Path(__file__).with_name("reglas.yml")
# Octetos sin ceros a la izquierda: "1.25.08.08" de un SVG no es una IP.
OCTETO = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
IPV4 = re.compile(rf"(?<![\d.])({OCTETO}(?:\.{OCTETO}){{3}})(?![\d.])")


def main():
    ...


if __name__ == "__main__":
    sys.exit(main())
