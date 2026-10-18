#!/usr/bin/env python3
"""
Publica el estado agregado del homelab para la web personal (CT 125,
docs/landing.md): servicios en marcha y disponibilidad de los ultimos 30
dias. Lo enseña la seccion "Ahora mismo" de titopinardogutierrez.com.

Solo agregados, nunca nombres, IPs ni puertos: la web es publica. El
estado por pieza usa los ids genericos del mapa de la web (plex, matrix...),
que ya son publicos; la correspondencia con los CT vive solo aqui.

Corre en el host Proxmox (root, cron cada 5 min, dos minutos despues de
sync_monitoring_snapshot.py) porque es el unico sitio que llega a Zabbix
(CT 130, API solo por loopback) y puede escribir en el CT 125 con
'pct push'. Asi el CT de la web no necesita credenciales ni red hacia nada.

- Servicios: contenedores LXC en marcha + contenedores Docker en marcha y
  sin healthcheck en rojo, leidos de la instantanea que ya genera
  sync_monitoring_snapshot.py (/tmp/monitoring_snapshot.json).
- Disponibilidad: cobertura de agent.ping en Zabbix (horas con datos /
  horas esperadas). La media de agent.ping no sirve: un agente activo
  caido no manda nada, asi que la media se queda siempre en 1. Se calcula
  una vez por hora y se guarda en cache.

Uso: python3 publish_landing_status.py
"""
import base64
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

SNAPSHOT = Path("/tmp/monitoring_snapshot.json")
SNAPSHOT_MAX_AGE = 15 * 60
ZABBIX_CTID = "130"
LANDING_CTID = "125"
DESTINO = "/opt/landing/estado/homelab.json"
CACHE = Path("/var/cache/publish_landing_status/uptime.json")
# Desde cuando esta caida cada pieza (para el modo incidente de la web).
DOWN_SINCE = Path("/var/cache/publish_landing_status/down_since.json")
CACHE_TTL = 3600

_UPTIME_SCRIPT = """
import sys, json, time
sys.path.insert(0, '/root/monitorizacion')
from zapi import API
a = API(); a.login()
items = a.call('item.get', {'output': ['itemid'], 'filter': {'key_': 'agent.ping'}, 'monitored': True})
ahora = int(time.time())
fin = ahora - ahora % 3600          # ultima hora completa (las tendencias son horarias)
inicio = fin - 30 * 86400
trends = a.call('trend.get', {'output': ['itemid', 'clock'], 'itemids': [i['itemid'] for i in items],
                             'time_from': inicio, 'time_till': fin - 1}) if items else []
horas = {}
for t in trends:
    horas.setdefault(t['itemid'], set()).add(int(t['clock']))
esperadas = cubiertas = 0
dias_esp = [0] * 30
dias_cub = [0] * 30
for h in horas.values():
    # Desde la primera hora con datos: un host nuevo no cuenta como caido
    # los dias anteriores a existir.
    primera = min(h)
    tramo = (fin - primera) // 3600
    esperadas += tramo
    cubiertas += min(len(h), tramo)
    for hora in range(primera, fin, 3600):
        d = (hora - inicio) // 86400
        dias_esp[d] += 1
        dias_cub[d] += hora in h
print(json.dumps({'esperadas': esperadas, 'cubiertas': cubiertas,
                  'dias': [round(100 * c / e, 2) if e else None for c, e in zip(dias_cub, dias_esp)]}))
"""


def pct_exec(ctid: str, script: str, timeout: int = 60) -> str:
    ...


def disponibilidad() -> tuple[float, list[float]]:
    """Disponibilidad a 30 dias y por dia (los dias sin hosts se omiten)."""
    ...


# Pieza del mapa de la web -> como saber si esta en marcha.
# ("ct", nombre) | ("docker", ct, [subcadenas]) | ("zfs",) | ("okd",) | ("host",)
PIEZAS = {
    "traefik": ("ct", "traefik"),
    "authelia": ("docker", "dockge", ["authelia"]),
    "dns": ("ct", "technitium"),
    "dnssync": ("ct", "dns-sync"),
    "landing": ("ct", "landing"),
    "postgres": ("ct", "landing"),
    "matrix": ("ct", "synapse"),
    "paperless": ("ct", "paperless"),
    "obsidian": ("docker", "dockge", ["obsidian"]),
    "n8n": ("docker", "n8n", ["n8n"]),
    "homepage": ("ct", "homepage"),
    "amp": ("ct", "amp"),
    "plex": ("ct", "plex"),
    "arr": ("docker", "dockge", ["sonarr", "radarr", "prowlarr", "bazarr"]),
    "tv": ("docker", "iptv", ["dispatcharr"]),
    "gpu": ("ct", "plex"),
    "hermes": ("ct", "ia-asistente"),
    "qdrant": ("ct", "qdrant"),
    "zabbix": ("ct", "zabbix"),
    "wazuh": ("ct", "wazuh"),
    "iac": ("ct", "agents"),
    "zfs": ("zfs",),
    "proxmox": ("host",),
    "okd": ("okd",),
}


def estado_piezas(snap: dict) -> dict:
    ...


DOCKER_CACHE = Path("/var/cache/publish_landing_status/docker.json")
DOCKER_CACHE_TTL = 2 * 3600


def servicios(snap: dict) -> tuple[int, int]:
    ...


def caidas_desde(nodos: dict, ahora: str) -> dict:
    """Para cada pieza caida, la hora en que se vio caida por primera vez.
    Se guarda entre pasadas; al volver a estar en marcha, se olvida."""
    ...


def main():
    ...


if __name__ == "__main__":
    main()
