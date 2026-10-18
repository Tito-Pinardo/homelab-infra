# Wazuh (CT 131, 192.0.2.241)

Manager, indexer y panel en un solo CT, version 4.14.7. El manager se
instalo a mano (no esta en Ansible); los agentes de los CT los gestiona
`roles/monitoring` (`playbooks/monitoring.yml`).

## Estado tras la revision del 2026-09-24

Lo que se comprobo y esta bien, para no repetirlo:

- API (55000) e indexer (9200/9300) solo en 127.0.0.1. Hacia fuera solo
  1514 (agentes, TLS con clave por agente) y 443 (panel).
- Registro de agentes (authd, 1515) desactivado: las altas se hacen con
  `scripts/register_monitoring.py`.
- Ninguna contrasena por defecto funciona (admin, kibanaserver, wazuh,
  wazuh-wui).
- Certificados validos hasta 2036.
- Disco al 34 %. `/var/ossec/queue/vd/feed` ocupa ~12 GB: es la base del
  detector de vulnerabilidades, tamano normal desde 4.8.
- Retencion: politica ISM `casa-30d` (alertas, monitoring y statistics).
- Integraciones: Matrix a partir de nivel 12; Discord a partir de nivel 7
  (era 3 hasta el 05-10-2026, ver abajo), repartido en tres canales por
  gravedad y deduplicado. Solo manda descripcion, equipo, nivel y regla,
  nunca el log. Correo a partir de nivel 10 (era 7).

## Cambios del 2026-09-24

| Problema | Arreglo | Donde |
|---|---|---|
| "Agent event queue is full" en plex todas las mananas 07:00-08:15 (190 avisos en 5 dias): el comskip del DVR de Plex escribe ~100k lineas al journal y el agente perdia eventos | Filtro journald que excluye `plexmediaserver.service` | `wazuh_journald_ignore_units` en `group_vars/plex_media`, plantilla `ossec.conf.j2` |
| La politica SCA `casa-esenciales.yml` solo existia (a mano) en proxmox, zabbix y wazuh; en los CT el SCA decia "File not found" | El role `monitoring` despliega la politica, su script y `*.remote_commands=0` | `roles/monitoring/files/`, `tasks/main.yml` |
| Con la politica ya activa, los 9 CT fallaban 3 controles que Proxmox ya cumplia: `sshd_config` 0644, `nullok` en PAM, MAC `umac-128` | `sshd_config` 0600, sin `nullok`, MACs solo SHA-2 | `roles/hardening` |
| ia-asistente (Hermes) y qdrant nunca habian pasado el hardening: SSH por defecto (6 intentos, reenvio abierto, MACs SHA-1) | `playbooks/hardening.yml` aplicado. Nadie usaba reenvio SSH (0 en 7 dias); Hermes, demeter-query y Qdrant siguen funcionando | `roles/hardening` |
| Regla 80710 "promiscuous mode" (nivel 10, ~50/dia) por las veth/tap/fwln/fwpr de cada CT, VM o contenedor Docker | Regla local 100005: nivel 3 solo para esas interfaces; `vmbr0` o una fisica siguen a 10. Probado con `wazuh-logtest` | `/var/ossec/etc/rules/local_rules.xml` en el manager, a mano (copia previa `.bak-20260924`) |
| ia-asistente y qdrant sin agentes | Registrados (Wazuh 028 y 027, mas Zabbix) e instalados con `monitoring.yml`; pasan los 14 controles de casa-esenciales | `register_monitoring.py`, vaults de ambos grupos |
| CT 118 (ia-asistente) sin firewall de Proxmox: SSH y Demeter (:8092) abiertos a toda la LAN | `118.fw`: SSH solo PC, agents, VPN y host (auditados 21 dias de logins); 8092 solo desde Caddy (dockge). La app ya exigia Caddy+secreto; esto es una segunda barrera | `/etc/pve/firewall/118.fw` en el host, a mano |
| CT 115 (qdrant): SSH abierto y gRPC :6334 abierto a toda la LAN (el 6333 si estaba cerrado) | SSH como el resto de CT; 6334 con las mismas IPs que 6333 (nadie lo usaba) | `/etc/pve/firewall/115.fw` |
| Agente 004 "scripts" huerfano (CT 105 ya no existe) y reglas 1514 para .8 y .137 (nada en esas IPs) | Agente borrado; reglas quitadas de `131.fw` | manager y host |
| Regla 100004 (CVE nginx paperless) a nivel 2: `log_alert_level` es 3, se descartaba | Subida a nivel 3 | `local_rules.xml` (copia `.bak-20260924-b`) |
| Indexer en amarillo: 18 replicas sin asignar (indices `.opendistro-ism-*`); con un solo nodo nunca se pueden asignar | `number_of_replicas: 0` en esos indices y `plugins.index_state_management.history.number_of_replicas: 0` persistente | API del indexer, a mano (no esta en Ansible) |
| (2026-10-06) El indexer era el que mas escribia en el RAID1 del host (md0, ~51 escrituras/s): translog con fsync en cada peticion | `index.translog.durability: async` y `sync_interval: 30s` en `wazuh-alerts-*`, `wazuh-monitoring-*`, `wazuh-statistics-*` y `wazuh-states-*` (estos tambien `refresh_interval: 30s`), en indices y plantillas (`casa-monitoring-tuning`, nueva `casa-states-tuning`). Queda en ~15 escrituras/s. Un corte de luz puede perder hasta 30 s de alertas en el indice (siguen en `alerts.json`) | API del indexer, a mano (copia previa en `/root/indexer-translog-20261006/` del CT) |

El filtro journald solo sabe *incluir*, asi que las unidades se excluyen
con un lookahead negativo de PCRE2. Se probo con dos unidades de prueba:
la de la lista no llego al manager y la otra si.

## Cambios del 2026-10-05: menos ruido en los avisos

Medido antes (7 dias): Discord recibia todo desde nivel 3, unas 9.500
alertas (2.000-2.900/dia). El 98 % era rutina: sesiones PAM 5501/5502
(6.219), SSH correcto 5715 (1.776), auditd SELinux 80730 (774), Docker
86003 (394).

| Cambio | Antes | Despues | Donde |
|---|---|---|---|
| Integracion `custom-discord` | nivel >= 3 | nivel >= 7 (~106/semana) | `ossec.conf` del manager, a mano (copia `ossec.conf.bak-20261005`) |
| `email_alert_level` | 7 | 10 (~15/semana) | idem |

Zabbix (por API, estado previo en `~/auditoria-casa/avisos-20261005/` de
agents): el trigger de load average estaba en 10 CT, pero en LXC
`/proc/loadavg` es el del host (lxcfs sin `--enable-loadavg`) dividido entre
las 2 CPU del CT, asi que con el host cargado saltaban todos a la vez (82 %
de los 178 avisos de la semana, y cada uno por correo y Discord). Ahora:
trigger de load solo en `proxmox`; host fantasma `scripts` (CT 105)
desactivado; accion de correo desde gravedad Alta (Discord sigue desde
Media y Element desde Alta).

Se pierde en Discord: autenticaciones fallidas (2501) y fallos de servicio
(40704), ambos nivel 5; siguen en el panel y Hermes (Nemesis) resume los
accesos fallidos. Nota en Obsidian: `05 Procedimientos/Avisos de Zabbix y
Wazuh - menos ruido 2026-10-05`.

## Comprobar

```sh
# en el CT de wazuh
C=/etc/wazuh-indexer/certs
curl -sk --cert $C/admin.pem --key $C/admin-key.pem https://127.0.0.1:9200/_cluster/health
/var/ossec/bin/agent_control -l

# en cualquier CT: los controles de la politica, uno a uno
/usr/local/sbin/casa-seguridad-check.py ssh_macs   # PASS / FAIL
```

Copias de los `.fw` anteriores en `/root/pve-fw-backup/` del host.

## Pendiente

Nada abierto de esta revision.
