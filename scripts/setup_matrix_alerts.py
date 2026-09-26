#!/usr/bin/env python3
"""Configura las integraciones de Zabbix y Wazuh hacia Element para las
incidencias criticas, con el bot de alertas y su sala. Se orquesta con pct
exec a traves del host Proxmox, igual que register_monitoring.py.

Es idempotente: se puede volver a ejecutar sin duplicar nada.
"""
import base64
import subprocess
import sys
import yaml
from pathlib import Path

PROXMOX_HOST = "root@192.0.2.10"
ZABBIX_CTID = "130"
WAZUH_CTID = "131"
SCRIPTS_DIR = Path(__file__).resolve().parent
ANSIBLE_DIR = SCRIPTS_DIR.parent / "ansible"
VAULT_PASS_FILE = Path.home() / ".vault-pass-infra-tf"

ZABBIX_HOSTGROUP_CASA = "22"
ZABBIX_SEVERITY_HIGH = "4"  # High. Disaster=5 queda cubierto por el operador >=.
WAZUH_MIN_LEVEL = "12"


def ssh_pct_exec(ctid: str, script_text: str, interpreter: str = "bash") -> str:
    """Ejecuta un script dentro de un contenedor a traves del host Proxmox."""
    ...


def push_file(ctid: str, local_path: Path, remote_path: str, mode: str = "0755", owner: str = "root:root"):
    """Copia un fichero dentro de un contenedor con el modo y propietario indicados."""
    ...


def read_synapse_vault() -> dict:
    """Devuelve los secretos del vault de Synapse."""
    ...


def deploy_zabbix(secrets_json: str):
    """Despliega en Zabbix el envio de alertas a Matrix."""
    ...


def deploy_wazuh(secrets_json: str):
    """Despliega en Wazuh el envio de alertas a Matrix."""
    ...


def ensure_relay_secret() -> str:
    """Genera una vez el secreto compartido del relay de alertas y lo guarda en el vault."""
    ...


def main():
    """Punto de entrada: configura las alertas de Zabbix y Wazuh hacia Matrix."""
    ...


if __name__ == "__main__":
    main()
