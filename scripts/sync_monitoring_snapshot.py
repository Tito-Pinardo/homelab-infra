#!/usr/bin/env python3
"""
Genera un snapshot semi-vivo de Zabbix/Wazuh y lo empuja al CT ia-asistente
para el tool get_server_health del asistente IA (ver runbook "Asistente IA -
Implementacion" en Obsidian).

Por que un snapshot por cron y no una consulta en vivo desde el bot: las
APIs de Zabbix (CT130) y Wazuh (CT131) solo son alcanzables por loopback
DENTRO de sus propios CT (cortafuegos intencional, ver register_monitoring.py)
- dar red directa desde ia-asistente rompería ese aislamiento a proposito.

Este script SI corre en el host Proxmox (root, via cron - el host no esta
gestionado por Ansible, paso manual documentado), que es el unico sitio con
acceso a todos los CT via 'pct exec'. Empuja el JSON resultante por SSH con
una clave de un solo proposito, forzada a 'cat > <ruta>' (ver
group_vars/ia_asistente/vars.yml y el role ia_asistente para la parte que
recibe el fichero).

Uso: python3 sync_monitoring_snapshot.py (pensado para cron cada 5-10 min)
"""
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

ZABBIX_CTID = "130"
WAZUH_CTID = "131"
IA_ASISTENTE_USER = "monitoring-push"
IA_ASISTENTE_HOST = "192.0.2.247"
SNAPSHOT_REMOTE_PATH = "/var/lib/monitoring-push/monitoring_snapshot.json"
PUSH_SSH_KEY = "/root/.ssh/id_ed25519_ia_asistente_push"
LOCAL_TMP = "/tmp/monitoring_snapshot.json"
# Estado de Docker entre ejecuciones: el ultimo digest publicado de cada
# imagen (consultar el registro en cada pasada de 5 min seria lento y
# gastaria el limite anonimo de Docker Hub) y los CT donde se vio Docker,
# para seguir listandolos si se paran.
DOCKER_CACHE_PATH = Path("/var/cache/sync_monitoring_snapshot/docker.json")
DOCKER_REMOTO_TTL = timedelta(hours=6)
# CT aislados: nunca se entra en ellos con pct exec (ni Docker ni apt).
# Paperless (119): documentos oficiales/confidenciales, fuera del alcance de
# los agentes IA y aislado por decision mia (2026-09-22, reiterada
# el 2026-09-24). Lo que Proxmox ve desde fuera (estado, CPU, RAM, via
# pvesh) si se sigue listando: no entra en el CT.
CT_AISLADOS = {119}


def pct_exec(ctid: str, script_text: str, interpreter: str = "python3", timeout: int = 60) -> str:
    """Mismo patron que ssh_pct_exec en register_monitoring.py, pero SIN el
    salto SSH externo - este script ya corre en el propio host Proxmox."""
    ...


def get_zabbix_problems() -> list[dict]:
    ...


def get_wazuh_agent_status() -> list[dict]:
    ...


def get_failed_logins() -> dict:
    """Nemesis (2026-09-18): recuento de intentos de login fallidos de HOY
    (grupo de regla de Wazuh que contenga "fail", cubre sshd/pam/etc a la
    vez sin mantener una lista de reglas a mano), agregado por agente -
    valida contra el archivo real de ayer (12 eventos en 3 hosts) antes de
    confiar en el patron de deteccion."""
    ...


def _pvesh(path: str) -> dict | list:
    ...


def get_proxmox_host_ip() -> str | None:
    ...


def get_proxmox_overview() -> dict:
    """Uso general del host (no problemas, solo totales) - pedido explicito
    del usuario (2026-09-17) tras ver que el asistente solo sabia hablar de
    discos ya en alarma, nunca de cuanto hay en total/libre."""
    ...


def get_ct_inventory() -> list[dict]:
    """Inventario de todos los CT (nombre, IP, estado, uso) - pedido
    explicito del usuario (2026-09-17): "si le pido info de un CT, incluso
    que IP tiene plex, me la de". La IP sale de net0 en la config (asignada
    estatica por Terraform), no de un agente invitado (no todos los CT lo
    tienen)."""
    ...


def get_apt_updates() -> list[dict]:
    """Hefesto (2026-09-18): recuento de paquetes apt pendientes por CT en
    marcha. Los CT que no usan apt (Alpine/apk) simplemente fallan el
    comando y se omiten sin romper el snapshot entero - mas simple que
    mantener aparte una lista de "cuales son Alpine"."""
    ...


def get_backup_jobs() -> list[dict]:
    """Tool "Mnemosine" del asistente (2026-09-17): jobs de vzdump configurados
    en el cluster (schedule/storage/CTs incluidos). Vacio es un resultado
    VALIDO y hay que dejarlo pasar tal cual - es precisamente el hallazgo que
    motivo esta funcion (no hay ningun vzdump programado en este Proxmox)."""
    ...


# Se ejecuta DENTRO de cada CT (python3 ya esta en todos: lo exige Ansible).
# REFS es la lista de imagenes cuyo digest publicado hay que consultar; vacia
# en la pasada normal, que solo lee el estado local.
_DOCKER_CT_SCRIPT = r"""
import hashlib, json, shutil, subprocess, sys
REFS = json.loads(%r)

def run(*args, timeout=30):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)

if not shutil.which("docker"):
    print(json.dumps({"docker": False}))
    sys.exit()
r = run("docker", "ps", "-aq")
if r.returncode != 0:
    print(json.dumps({"docker": True, "error": r.stderr.strip()[:300]}))
    sys.exit()
contenedores = []
ids = r.stdout.split()
if ids:
    inspeccion = json.loads(run("docker", "inspect", *ids).stdout)
    imagenes = {}
    for img_id in {c["Image"] for c in inspeccion}:
        ri = run("docker", "image", "inspect", "--format", "{{json .RepoDigests}}", img_id)
        # "repo@sha256:..." -> "sha256:..."; vacio en imagenes construidas en
        # local, que ademas pueden devolver una salida en blanco (CT 114)
        try:
            digests = json.loads(ri.stdout.strip() or "null") or []
        except ValueError:
            digests = []
        imagenes[img_id] = [d.split("@", 1)[1] for d in digests if "@" in d]
    for c in inspeccion:
        etiquetas = c["Config"].get("Labels") or {}
        estado = c["State"]
        contenedores.append({
            "nombre": c["Name"].lstrip("/"),
            "proyecto": etiquetas.get("com.docker.compose.project"),
            "estado": estado["Status"],
            "salud": (estado.get("Health") or {}).get("Status"),
            "codigo_salida": estado.get("ExitCode"),
            "reinicios": c.get("RestartCount", 0),
            "politica": (c["HostConfig"].get("RestartPolicy") or {}).get("Name") or "no",
            "imagen": c["Config"]["Image"],
            "digests_locales": imagenes[c["Image"]],
        })
remotos = {}
for ref in REFS:
    try:
        # --raw: solo el manifiesto raiz (una peticion), y su sha256 ES el
        # digest. Con --format se bajaban tambien los de cada arquitectura:
        # mas lento y fallaba con bazarr en ghcr.io (23-09).
        rr = subprocess.run(["docker", "buildx", "imagetools", "inspect", "--raw", ref],
                            capture_output=True, timeout=45)
        if rr.returncode == 0 and rr.stdout:
            remotos[ref] = {"digest": "sha256:" + hashlib.sha256(rr.stdout).hexdigest()}
        else:
            remotos[ref] = {"error": rr.stderr.decode(errors="replace").strip()[:200]}
    except Exception as e:
        remotos[ref] = {"error": str(e)[:200]}
print(json.dumps({"docker": True, "contenedores": contenedores, "remotos": remotos}))
"""


def _docker_en_ct(vmid: str, refs: list[str] | None = None) -> dict:
    ...


def get_docker_status() -> list[dict]:
    """Hipnos/Hefesto/Pitia (2026-09-23): contenedores Docker de cada CT
    (estado, healthcheck, reinicios) y si su imagen tiene una version
    publicada mas nueva. Sustituye a Dockge como "que esta caido o
    desactualizado" - el CT 122 ya no lo tiene y Ansible es quien despliega.

    "Hay actualizacion" = el digest que publica el registro para la etiqueta
    del compose (p. ej. radarr:latest) no es ninguno de los digests de la
    imagen con la que corre el contenedor. Cubre tambien una imagen ya
    descargada pero con el contenedor sin recrear. Las imagenes construidas
    en local (puppeteer-api) no tienen digest de registro: quedan sin
    comprobar (actualizacion = None)."""
    ...


def _zpool_list() -> list[dict]:
    ...


def _zpool_scrub_info(pool: str) -> str | None:
    ...


def get_zfs_health() -> list[dict]:
    """Tool "Atlas" del asistente (2026-09-17): estado real de los pools ZFS
    (raiz5, games) - capacidad, salud, ultimo scrub. Complementa el
    almacenamiento generico de get_proxmox_overview (ese es por storage de
    Proxmox, este es a nivel de pool ZFS con salud/errores reales)."""
    ...


def get_smart_summary() -> list[dict]:
    """Salud SMART basica (PASSED/FAILED) por disco fisico - defensivo a
    proposito: algunos discos (JBOD USB NetApp, ver Obsidian "Layout fisico
    discos") no responden bien a smartctl generico, y un fallo aqui NUNCA
    debe tumbar el resto del snapshot."""
    ...


def _seguro(fn, por_defecto):
    """Docker es lo ultimo que se anadio y lo que mas depende de la red (los
    registros): si falla, el resto del snapshot debe seguir llegando."""
    ...


def main():
    ...


if __name__ == "__main__":
    main()
