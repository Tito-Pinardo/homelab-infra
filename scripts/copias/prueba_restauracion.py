#!/usr/bin/env python3
"""Prueba semanal de restauracion de las copias de PBS (docs/copias.md).

Una copia que nunca se ha restaurado no se sabe si sirve. Cada semana:

- Restaura en un CT temporal (9000 + id, sin arrancarlo) la ultima copia de
  cada CT de un grupo. Los CT se reparten en 4 grupos de tamano parecido, asi
  que cada uno se prueba una vez al mes. Comprueba que el sistema esta y que
  los ficheros de /etc y /opt que no han cambiado desde la copia son
  identicos a los del CT en marcha. Despues borra el CT temporal.
- Saca de la ultima copia de cada dataset (Minecraft) los level.dat y
  comprueba que se pueden leer.

Avisa en Element: resumen en la sala CI/CD y fallos en Incidencias.

Corre en el runner de despliegue (CT 123) y se ejecuta a si mismo en el host
de Proxmox por SSH (--en-host). Uso: prueba_restauracion.py [--grupo N] [--ct ID...]
"""
import argparse
import datetime
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HOST = "root@192.0.2.2"
ALMACEN = "pbs-lb2"
GRUPOS = 4
VMID_TEMPORAL = 9000
# Paperless: fuera del alcance de los agentes (ver hosts.yml); no se monta.
EXCLUIDOS = {119}
DATASETS = ["minecraft"]
LIMITE_FICHEROS = 3000


# ------------------------------------------------------------ en el host

def h(*cmd, timeout=7200, check=True, env=None):
    ...


def ultima_copia(vmid):
    ...


def sha256(ruta):
    ...


def probar_ct(vmid):
    ...


def probar_dataset(nombre):
    ...


def en_host(cts):
    ...


# ------------------------------------------------------------ en el runner

def grupos(tamanos):
    """Reparte los CT en GRUPOS de tamano parecido (siempre igual para los mismos CT)."""
    ...


def avisar(texto, incidencia):
    ...


def main():
    ...


if __name__ == "__main__":
    sys.exit(main())
