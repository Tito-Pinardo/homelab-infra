#!/usr/bin/env python3
"""Registra un CT nuevo en Zabbix y Wazuh, genera sus credenciales y escribe
el vault correspondiente para que el rol monitoring instale los agentes.

Las APIs de Zabbix y Wazuh solo son accesibles desde dentro de sus CT, asi
que lo orquesto con pct exec a traves del host Proxmox.

Uso: python3 scripts/register_monitoring.py <nombre_ct> <ip_ct> [--zabbix-only]
"""
import base64
import secrets
import subprocess
import sys
from pathlib import Path

PROXMOX_HOST = "root@192.0.2.10"
ZABBIX_CTID = "130"
WAZUH_CTID = "131"
ANSIBLE_DIR = Path(__file__).resolve().parent.parent / "ansible"
VAULT_PASS_FILE = Path.home() / ".vault-pass-infra-tf"


def ssh_pct_exec(ctid: str, script_text: str, interpreter: str = "bash") -> str:
    """Ejecuta un script dentro de un contenedor a traves del host Proxmox."""
    ...


def register_zabbix(name: str, ip: str) -> str:
    """Da de alta o actualiza un host en Zabbix y devuelve su PSK."""
    ...


def ensure_firewall_rule(ctid: str, source_ip: str, port: str):
    """Asegura que el contenedor permite el trafico de monitorizacion."""
    ...


def register_wazuh(name: str, ip: str) -> str:
    """Registra el contenedor como agente de Wazuh, sustituyendo uno previo si existe."""
    ...


def write_vault(name: str, group_dir: str, zabbix_psk: str, wazuh_keys_line: str | None):
    """Guarda las credenciales de monitorizacion en el vault del grupo."""
    ...


def main():
    """Punto de entrada: registra un contenedor en Zabbix y Wazuh."""
    ...


if __name__ == "__main__":
    main()
