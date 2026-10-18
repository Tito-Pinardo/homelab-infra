"""Leer y guardar secretos de un grupo de Ansible en OpenBao (docs/secretos.md).

Los valores viven en OpenBao (infra-tf/grupos/<grupo>) y sus nombres en
ansible/inventory/secretos.yml. Leer usa infra-tf-secreto (AppRole del
CT 123, solo lectura). Guardar usa BAO_TOKEN si lo hay o, si no, la AppRole
"secretos" (solo escritura en infra-tf/grupos/*).
"""
import json
import os
import subprocess
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
MANIFIESTO = RAIZ / "ansible" / "inventory" / "secretos.yml"
AYUDANTE = str(Path.home() / ".local/bin/infra-tf-secreto")
ENTORNO = {"BAO_ADDR": "https://192.0.2.234:8200",
           "BAO_CACERT": str(Path.home() / ".infra-tf/openbao/ca.pem"), "LC_ALL": "C.UTF-8"}


def leer(grupo: str) -> dict:
    """Todos los secretos del grupo ({} si aun no tiene)."""
    ...


def token_escritura() -> str:
    """Token de 15 min de la AppRole "secretos" (solo infra-tf/grupos/*, solo
    desde el CT 123; scripts/openbao/configurar-secretos.sh)."""
    ...


def guardar(grupo: str, datos: dict) -> None:
    """Crea o actualiza esos secretos del grupo y anade sus nombres a secretos.yml."""
    ...
