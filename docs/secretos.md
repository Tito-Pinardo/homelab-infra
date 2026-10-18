# Secretos: de Ansible Vault a OpenBao

> Guía de uso: wiki del repo, página **Secretos**. Esto es el detalle técnico.

Desde el 2026-10-15 los secretos de Ansible pasan de los `vault.yml` cifrados
del repo a OpenBao (CT 128). Motivo: en git cada versión cifrada se queda para
siempre en la historia, y con la contraseña del vault (que llegó a filtrarse
el 15-10) se leen todas. En OpenBao el repo solo guarda **dónde** está cada
secreto.

```
inventory/secretos.yml          grupo -> NOMBRES de sus secretos (en git)
OpenBao infra-tf/grupos/<grupo> los VALORES (KV v2, con versiones y auditoría)
vars_plugins/bao_secretos.py    los carga como variables vault_* del grupo
```

Los roles no cambian: las variables se siguen llamando `vault_*`.

## Cómo carga los secretos

- En cada ejecución de Ansible, la primera vez que hace falta un grupo de
  `secretos.yml`, el plugin llama a `infra-tf-secreto grupos/<grupo> --json`
  (AppRole del CT 123, token de 15 min reutilizado; `roles/openbao`).
- Comprueba que estén **todos** los nombres de la lista; si falta alguno, o
  OpenBao está sellado o no responde, Ansible se para con el motivo. Mejor no
  desplegar que desplegar con secretos vacíos.
- Sin `infra-tf-secreto` (runner del CI, que no tiene secretos) solo avisa y
  no aporta variables: lint y `--syntax-check` no los necesitan.
- La política `despliegue` ya lee `infra-tf/data/*`: no hizo falta tocarla.

## Cambiar o añadir un secreto

- **Cambiar un valor:** `https://bao.home.arpa` → `infra-tf` → `grupos` →
  el grupo → *Create new version*. O `bao kv patch -mount=infra-tf
  grupos/<grupo> vault_x=...` con un token con la política admin. El
  siguiente despliegue lo aplica (el plan no lo enseña: el valor no está en
  git).
- **Añadir uno:** escribirlo en OpenBao **y** añadir su nombre en
  `inventory/secretos.yml` (por PR).
- La AppRole del despliegue solo lee. Escriben `tito` (web o token) y la
  AppRole `secretos` (scripts del CT 123).
- **Desde lucifer** no hay AppRole (está ligada a la IP del CT 123): los
  playbooks con secretos se lanzan desde el CT 123 o por PR.

## Si se filtra un secreto

Cambiar el valor, no limpiar la historia: hay clones y copias (PBS, lucifer,
`dns-sync`). Los cambios de valor en OpenBao no pasan por git, así que el
despliegue automático no los ve: hay que lanzar a mano el playbook del grupo.

| Tipo | Cómo |
|---|---|
| Tokens y claves de servicios externos | Generar uno nuevo en el servicio, ponerlo en OpenBao (*Create new version*), aplicar el playbook y, cuando funcione, revocar el viejo. |
| Cuentas Matrix de los bots | Cambiar la contraseña **sin cerrar sesiones** (`logout_devices: false`): el relay y Hermes guardan su sesión con claves E2EE y la perderían. Revocar solo los tokens filtrados (`/logout` con ese token). |
| PSK de Zabbix y clave de Wazuh | `scripts/rotar_monitorizacion.py` (todos los hosts, un solo reinicio del manager) y `playbooks/monitoring.yml --limit '!paperless'`. |
| Secreto del relay | Nuevo en `synapse_server` y luego `synapse.yml`, `forgejo.yml`, `traefik-prod.yml`, `pbs.yml` y `scripts/setup_matrix_alerts.py`. |
| Cuentas de AMP de los bots | Las resetea el admin desde AMP (las cuentas no pueden cambiarse a sí mismas). |

### Rotación del 18-10

La contraseña antigua del vault salió en la transcripción de una sesión del
15-10: con ella y la historia de git se abrían 53 secretos (nunca llegaron a
GitHub; comprobado valor a valor en toda la historia de `homelab-infra` y
`landing`).

- **Cambiados:** los 11 externos (Cloudflare x2, Gmail x2, Discord x2, GHCR,
  MikroTik x2, WireGuard de Proton, Google Calendar); las 3 cuentas Matrix
  (alertas, asistente, web) y sus tokens filtrados revocados; registration
  secret de Synapse; secreto del relay; clave de Qdrant; contraseña de admin
  de Forgejo; PSK de Zabbix y claves de Wazuh de 18 hosts.
- **Pendientes (los hace Tito):** las 3 cuentas de AMP (Hermes, amp-publicar,
  bot de battlepros: contraseña y TOTP) y Paperless (fuera de los agentes).
- **Sin cambiar a propósito (solo LAN y tras Authelia):** claves API de
  Radarr/Sonarr/Prowlarr, qBittorrent, gluetun, Dispatcharr, Codeman,
  htpasswd del dashboard de Traefik (no público), contraseña de la BD de
  Synapse (solo local) y la sal de las IP de la web.

## Migración

| Fase | Qué | Estado |
|---|---|---|
| 0 | Los 100 secretos de los 22 grupos copiados a OpenBao, releídos y comparados por huella | Hecha (15-10) |
| 1 | Plugin, `secretos.yml` y piloto `dns_sync` (sin `vault.yml`) | Hecha (15-10, PR #47) |
| 2 | El resto de grupos (21, 94 secretos), salvo Paperless; `scripts/secretos.py` para los scripts que leen o guardan secretos | Hecha (18-10) |
| 3a | AppRole `secretos` (política `secretos-escritura`: crear, cambiar y leer `infra-tf/grupos/*`, nada más; solo desde el CT 123, tokens de 15 min). `scripts/secretos.py` la usa si no hay `BAO_TOKEN` | Hecha (18-10, `scripts/openbao/configurar-secretos.sh`) |
| 3b | Paperless también (decisión de Tito, 18-10): ya no queda ningún `vault.yml`. Fuera `vault_password_file` de `ansible.cfg`, `~/.vault-pass-infra-tf`, la falsa del CI y `rekey-vault.py` | Hecha (18-10) |

Cada grupo se comprueba igual antes de quitar su `vault.yml`: las huellas
SHA-256 de todas sus variables `vault_*`, vistas por Ansible, iguales leyendo
del vault y de OpenBao; y el plan del playbook, sin cambios.

La contraseña del vault se queda en OpenBao (`infra-tf/ansible`) aunque ya no
se use: hace falta para leer los `vault.yml` de la historia de git
(`infra-tf-secreto ansible vault_password`). Los
secretos que estaban en esos ficheros conviene cambiarlos con el tiempo.

## Copias

OpenBao está en la copia diaria de PBS (CT 128). Para restaurar hace falta
además la clave de desbloqueo (gestor de contraseñas).
