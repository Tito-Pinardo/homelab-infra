#!/usr/bin/env python3
"""
Registra un CT nuevo en Zabbix y Wazuh (genera credenciales frescas) y
escribe el vault de Ansible correspondiente, listo para que el role
"monitoring" instale los agentes.

Por que este script y no un role de Ansible normal para el registro: las
APIs de Zabbix y Wazuh solo son alcanzables por loopback DENTRO de sus
propios CT (130 y 131) - no hay ruta de red desde el PC ni desde Ansible
hacia ellas (confirmado 2026-09-16, cortafuegos/hardening intencional).
Este script orquesta todo via 'pct exec' a traves del host Proxmox
(192.0.2.2), que si tiene acceso a todos los CT.

Uso:
    python3 scripts/register_monitoring.py <nombre_ct> <ip_ct> [--zabbix-only]

--zabbix-only: no registra en Wazuh - usar en hosts sin soporte (ej. Alpine/
musl, Wazuh no tiene paquete nativo ahi).

Ejemplo:
    python3 scripts/register_monitoring.py traefik 192.0.2.6
    python3 scripts/register_monitoring.py dns-sync 192.0.2.249 --zabbix-only

Requiere: acceso SSH root a 192.0.2.2 (el propio host Proxmox), y la
la AppRole "secretos" de OpenBao en el CT 123 (para guardar el resultado en
infra-tf/grupos/<grupo>; docs/secretos.md).

Ojo: necesita PyYAML, que el python3 del sistema del CT agents no trae. Sin
el, registra en Zabbix/Wazuh y luego falla al escribir el vault (las claves
se pierden; se puede repetir, da de baja el registro anterior). Usar el
python de Ansible (visto 2026-09-24):
    ~/.local/share/pipx/venvs/ansible-core/bin/python scripts/register_monitoring.py ...
"""
import base64
import secrets
import subprocess
import sys
from pathlib import Path

PROXMOX_HOST = "root@192.0.2.2"
ZABBIX_CTID = "130"
WAZUH_CTID = "131"
ANSIBLE_DIR = Path(__file__).resolve().parent.parent / "ansible"


def ssh_pct_exec(ctid: str, script_text: str, interpreter: str = "bash") -> str:
    """Ejecuta un script dentro de un CT via pct exec, a traves del host Proxmox.

    El script viaja en base64 y se decodifica al otro lado antes de
    ejecutarlo - evita CUALQUIER problema de escapado de comillas/saltos de
    linea al atravesar tres capas de shell (local -> ssh -> pct exec).
    """
    ...


def register_zabbix(name: str, ip: str) -> str:
    """Crea (o actualiza si ya existe) el host en Zabbix con PSK nueva. Devuelve la PSK."""
    ...


def ensure_firewall_rule(ctid: str, source_ip: str, port: str):
    """Añade (si no existe ya) la regla de firewall Proxmox que permite a
    source_ip llegar a ese puerto del CT dado. Sin esto, un CT nuevo se
    registra bien en Zabbix/Wazuh pero se queda "sin datos" para siempre -
    bug real repetido dos veces (2026-09-16) por olvidarlo a mano."""
    ...


def register_wazuh(name: str, ip: str) -> str:
    """Da de baja un agente previo con ese nombre (si existe) y registra uno nuevo.
    Devuelve la linea completa de client.keys ('id name ip key')."""
    ...


def write_vault(name: str, group_dir: str, zabbix_psk: str, wazuh_keys_line: str | None):
    """Guarda en OpenBao (infra-tf/grupos/<grupo>) las credenciales de
    monitorizacion del grupo (docs/secretos.md). wazuh_keys_line=None (host
    sin Wazuh, ej. Alpine/musl) - no escribe esa clave."""
    ...


def main():
    ...


if __name__ == "__main__":
    main()
