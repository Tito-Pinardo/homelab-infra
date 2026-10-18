# Web personal titopinardogutierrez.com (CT 125)

> Cómo hacer cambios en la web (contenido, probar, CI en rojo, volver atrás,
> resumen semanal…): **wiki del repo de la web**, <https://git.home.arpa/tito/landing/wiki>.

Montado el 2026-10-04. Código de la web: `~/codeman-cases/testcase` (origen en
Forgejo `tito/landing` desde el 14-10; copia pública `Tito-Pinardo/landing` en GitHub);
plan y decisiones en su `docs/PLAN.md`.

## Qué es

Un binario de Rust (Axum) que sirve la web en español e inglés, guarda los
mensajes del formulario en PostgreSQL y avisa por Matrix. Las páginas se
renderizan al arrancar y Cloudflare las cachea: casi ninguna visita llega aquí.

```
Visitante ─► Cloudflare ─► Traefik (CT 209) ─► CT 125 :8080 (landing) ─► PostgreSQL (socket local)
                                                         └─► Matrix (aviso de contacto)
```

## Piezas

| Pieza | Dónde |
|---|---|
| CT 125 `landing`, 192.0.2.242, Debian 13, 2 vCPU, 1 GB, 8 GB, sin privilegios | `environments/homelab/lxc-landing.tf` |
| Rol (firewall, PostgreSQL, binario, systemd) | `ansible/roles/landing/` |
| Variables | `ansible/inventory/group_vars/landing/vars.yml` |
| Sal del hash de IP, Zabbix/Wazuh y (cuando existan) Matrix y Turnstile | `ansible/inventory/group_vars/landing/vault.yml` |
| Playbook | `ansible/playbooks/landing.yml` |

## Desplegar una versión nueva (CI/CD en Forgejo, desde el 14-10)

El origen del repo de la web es Forgejo (`ssh://git@192.0.2.235:2222/tito/landing.git`);
GitHub es la copia pública y solo la actualiza el despliegue. Basta con un push a `main`:

```
push a main ──► Forgejo ──► CI (CT 127, sin secretos): fmt, clippy, pruebas contra
                   │        PostgreSQL, build release, landing check, JS minificado
                   │        con node --check, pruebas del resumen y gitleaks
                   │
                   └──► si sale verde: desplegar (CT 123, runner landing-despliegue)
                          landing-desplegar <sha>
                          1. control de fugas de lo que aún no está en GitHub
                          2. cargo build --release + landing check
                          3. playbooks/landing.yml (master de infra-tf)
                          4. push de ese commit a GitHub
                          5. /healthz desde fuera
Element (sala CI/CD): ✅/❌ de cada ejecución por el webhook del repo
```

- **Workflow:** `.forgejo/workflows/ci.yml` del repo de la web (trabajos `comprobar` y
  `desplegar`). Lo que es de casa (rutas, remotos, patrones de fugas) vive aquí, en los
  scripts que instala `roles/forgejo/tasks/landing_cd_agent.yml`, no en el repo público.
- **Control de fugas** (`~/.local/bin/landing-fugas <rango>`): gitleaks, solo la identidad
  pública como autor y ni IPs ni nombres internos (`landing_fugas_patron` en
  `group_vars/agents`). Lo pasa el despliegue antes de tocar la web o GitHub, y el
  `pre-push` del checkout de trabajo llama al mismo script.
- **Si GitHub tiene commits que Forgejo no tiene**, el despliegue se para: no fuerza nada.
- **Necesita OpenBao desellado** (desde el 15-10): `landing.yml` abre el vault con
  `~/.vault-pass-infra-tf`, que pide la contraseña a OpenBao. Sellado, el despliegue falla
  en el playbook sin tocar el CT 125; tras desellar, relanzarlo (`landing-desplegar <sha>`).
- **Dos pushes seguidos:** el CI corre uno a uno; si al desplegar `main` ya va por otro
  commit, ese despliegue no hace nada y lo hace la ejecución del último.
- **A mano** (mismo resultado, mismo cerrojo): `landing-desplegar <sha de main>` en el CT 123.
  Relanzar solo el playbook vuelve a poner el último binario desplegado
  (`landing_binary_src` apunta a `~/.landing-cd/target/release/landing`).

El rol copia el binario, comprueba el contenido con `landing check`, reinicia
y no termina hasta que `/healthz` responde `ok` (que también comprueba la base
de datos). Las migraciones las aplica el propio binario al arrancar.

En este CT (agents) Ansible necesita `LC_ALL=C.UTF-8`; las colecciones están en
`ansible/requirements.yml` (el rol usa `community.postgresql`).

| Pieza del CI/CD | Dónde |
|---|---|
| Repo, webhook, `main` sin force push, registro del runner | `roles/forgejo/tasks/landing.yml` |
| Rust 1.99, PostgreSQL (solo socket), Node en el runner del CI | `roles/forgejo_runner/tasks/main.yml`, etiqueta `landing` |
| Runner `landing-despliegue` (servicio `forgejo-runner-landing`, usuario agent) | `roles/forgejo/tasks/landing_cd_root.yml` |
| `landing-desplegar`, `landing-fugas`, `~/.landing-cd/` | `roles/forgejo/tasks/landing_cd_agent.yml` |
| Todo lo anterior | `playbooks/forgejo.yml` (a mano, como el resto de Forgejo) |

## Seguridad

- **Firewall con `policy_in: DROP`**, el único del homelab: entra SSH (PC,
  agents, VPN), el 8080 **solo desde Traefik** e ICMP. Zabbix y Wazuh son
  agentes activos y no necesitan regla de entrada. Comprobado: desde agents
  el 8080 no responde; desde Traefik, sí.
- **PostgreSQL sin red** (`listen_addresses = ''`). El servicio entra por el
  socket con autenticación peer: no hay contraseña de base de datos. El rol
  `landing` de PostgreSQL no es superusuario, solo dueño de su base.
- **systemd endurecido** (`ProtectSystem=strict`, sin capacidades, filtro de
  syscalls, `MemoryDenyWriteExecute`, `MemoryMax=256M`).
- `TRUST_PROXY_HEADERS=true`: el binario usa `CF-Connecting-IP` para los
  límites de envío. Solo es seguro porque al 8080 únicamente llega Traefik.
- La IP de quien escribe no se guarda: solo un hash con sal (`vault`).
- Hardening y agentes de Zabbix y Wazuh como el resto de la flota.

## Publicación y avisos

- **Ruta pública** (04-10): `titopinardogutierrez-com` en `traefik_routes`
  hacia `http://192.0.2.242:8080`, sin `sec_headers` (el binario ya pone
  HSTS, CSP y el resto). Certificado de borde de Cloudflare; el de origen lo
  saca Traefik.
- **Avisos en Matrix**: usuario propio `@web:matrix.example.org` (sin
  admin, solo está en su sala) y sala sin cifrar «🌐 Web» dentro del Space
  «🏠 Casa». No uso el token de Hermes a propósito: este CT da a internet y,
  si alguien se colara, el token solo serviría para escribir en esa sala.
  Usuario, contraseña, token y sala están en el vault. Probado de extremo a
  extremo el 04-10 (aviso entregado con `event_id`; la fila de prueba se borró).

## Estado del homelab en "Ahora mismo"

`scripts/publish_landing_status.py`, en el host Proxmox
(`/root/infra-tf-scripts/`, copia manual como el resto de scripts del host),
cron `2-59/5` (dos minutos después de `sync_monitoring_snapshot.py`; copia del
crontab anterior en `/root/crontab.antes-landing-20261004`). Log en
`/var/log/publish_landing_status.log`.

- **Servicios**: CT en marcha + contenedores Docker en marcha y sin
  healthcheck en rojo, de la instantánea `/tmp/monitoring_snapshot.json`. Si
  tiene más de 15 min, no publica nada (la web oculta el dato a las 2 h). Si
  la parte de Docker llega vacía (host justo de I/O, visto el 04-10 durante
  el check mensual del RAID1), usa el último recuento bueno de menos de 2 h.
- **Disponibilidad 30 días**: cobertura de `agent.ping` en Zabbix (horas con
  datos / horas esperadas desde que existe cada host). La media de
  `agent.ping` no vale: un agente activo caído no manda datos y la media se
  queda en 1. Se recalcula cada hora (`/var/cache/publish_landing_status/`).
  Primera medida (04-10): 95,29 %.
- **Estado por pieza** (`nodes`): `up`, `down` u `off` para cada id del mapa de
  la web (la correspondencia pieza→CT/contenedor vive solo en el script).
  OpenShift sale `off` cuando sus VM están paradas a propósito.
- **Barras de 30 días** (`daily`): la misma consulta horaria de Zabbix, por día.
- Solo agregados. Se escribe con `pct push` a un `.tmp` y `mv`
  (`/opt/landing/estado/homelab.json`, 0644): el CT 125 no tiene credenciales
  ni red hacia Zabbix.

## Pendiente

- **Caché del HTML en Cloudflare** (opcional): Cloudflare no cachea HTML por
  defecto (`cf-cache-status: DYNAMIC`). Hace falta una Cache Rule en la zona
  (`/es/`, `/en/` → "Eligible for cache", respetando el Cache-Control del
  origen). Ningún token del vault tiene permiso de Cache Rules (403); o se crea
  a mano en el panel o se amplía un token con "Zone → Cache Rules → Edit".
- Turnstile (opcional): hoy frenan el spam el campo trampa y los límites.

## Resumen semanal de los lunes (2026-10-14)

`tools/digest/digest.py` del repo de la web (ver su `docs/digest.md`) corre en el CT 123
(agents) como `agent`, con `landing-digest.timer` cada 15 minutos. Lo instala
`playbooks/agents-digest.yml` (solo esas tareas del role `agents`, sin tocar los CLI ni
Codeman). Desde el propio CT, sin root, se lanza a través del hipervisor:

```bash
ansible-playbook playbooks/agents-digest.yml \
  -e ansible_connection=community.proxmox.proxmox_pct_remote -e ansible_host=192.0.2.2 -e ansible_user=root
```

- Clon propio: `~agent/.local/share/landing-digest/repo`, con origen en Forgejo; el servicio
  lo pone igual que `origin/main` antes de cada tick (ExecStartPre), así siempre corre el
  script último. Estado: `~agent/.local/state/landing-digest/<lunes>.json`.
- Entorno: `~agent/.config/landing-digest/digest.env` (0600), con el bot `@web` y la sala
  de los avisos de contacto de la web (secretos del vault de `landing`).
- Clave de Gemini: `~agent/.config/landing-digest/gemini.key` (0600), puesta a mano. No va
  en ningún entorno para que el CLI de Gemini no la use. Sin ella usa el Ollama de lucifer,
  que hoy NO deja pasar al CT 123 (ufw de lucifer solo admite .245 y .247).
- Solo publica si `@tito` responde «publicar» al borrador; al publicar hace commit + push
  del artículo a Forgejo y espera a que el CI/CD lo despliegue (la web responde con el
  artículo nuevo). Desde el 14-10 no lanza el playbook él mismo.
- Logs: `journalctl -u landing-digest.service`.

### Modo incidente (2026-10-14)

`publish_landing_status.py` publica ademas `down_since`: para cada pieza caida, la primera
vez que se vio caida (UTC, RFC 3339), guardado entre pasadas en
`/var/cache/publish_landing_status/down_since.json` y olvidado al volver. La web lo usa para
el aviso «caida desde las 14:10» del rack y de cada unidad. Copia anterior del script en el
host: `/root/infra-tf-scripts/publish_landing_status.py.antes-20261014`.

