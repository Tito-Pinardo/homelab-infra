#!/usr/bin/env python3
"""
Configura las integraciones Zabbix->Element y Wazuh->Element para
incidencias criticas, usando el bot @alertas:matrix.example.org (creado
en Synapse) y la sala "Incidencias criticas" (IDs en el vault de
synapse_server). Mismo patron que register_monitoring.py: todo orquestado
via pct exec a traves del host Proxmox, porque las APIs de Zabbix/Wazuh
solo son alcanzables por loopback dentro de sus propios CT.

Idempotente: se puede re-ejecutar tras cambiar casa-matrix.py/custom-matrix
o el umbral de severidad, sin duplicar media types/actions/integrations.

Uso: python3 scripts/setup_matrix_alerts.py
"""
import base64
import subprocess
import sys
import yaml
from pathlib import Path

PROXMOX_HOST = "root@192.0.2.2"
ZABBIX_CTID = "130"
WAZUH_CTID = "131"
SCRIPTS_DIR = Path(__file__).resolve().parent
ANSIBLE_DIR = SCRIPTS_DIR.parent / "ansible"

ZABBIX_HOSTGROUP_CASA = "22"
ZABBIX_SEVERITY_HIGH = "4"  # High. Disaster=5 queda cubierto por el operador >=.
WAZUH_MIN_LEVEL = "12"


def ssh_pct_exec(ctid: str, script_text: str, interpreter: str = "bash", timeout: int = 60) -> str:
    ...


def push_file(ctid: str, local_path: Path, remote_path: str, mode: str = "0755", owner: str = "root:root"):
    ...


def read_synapse_vault() -> dict:
    """Secretos de synapse_server en OpenBao (docs/secretos.md)."""
    ...


def deploy_zabbix(secrets_json: str):
    ...


def deploy_wazuh(secrets_json: str):
    ...


def ensure_relay_secret() -> str:
    """Genera (una vez) el secreto compartido del relay E2EE y lo guarda en
    OpenBao (synapse_server), para que roles/synapse lo despliegue."""
    ...


def main():
    ...


if __name__ == "__main__":
    main()
