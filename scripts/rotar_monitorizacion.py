#!/usr/bin/env python3
"""Rota de golpe las credenciales de monitorizacion (PSK de Zabbix y clave del
agente de Wazuh) de todos los hosts, o de los que se pasen, y las guarda en
OpenBao. Para cuando se filtran (ver docs/secretos.md, "Si se filtra un secreto").

A diferencia de llamar a register_monitoring.py host a host, reinicia el
wazuh-manager UNA vez al final (tarda ~3 min cada vez). Paperless nunca entra.
Despues: ansible-playbook playbooks/monitoring.yml --limit '!paperless'

Uso: python3 scripts/rotar_monitorizacion.py [host ...]
"""
import re
import sys
from pathlib import Path

import yaml

import register_monitoring as rm

RAIZ = Path(__file__).resolve().parents[1]


def hosts_inventario():
    ...


def main():
    ...


if __name__ == "__main__":
    main()
