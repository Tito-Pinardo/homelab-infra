# Forgejo y CI de infra-tf (CT 126 y CT 127)

> Guía de uso para el día a día (cómo cambiar algo, leer el plan, qué es cada aviso,
> qué hacer si algo falla): **wiki del repo**, <https://git.home.arpa/tito/infra-tf/wiki>.
> Esto es el detalle técnico.

Montado el 2026-10-14. Forgejo es un servidor git con interfaz web
(`https://git.home.arpa`) y, desde ese mismo día, el **origen** de infra-tf:
cada push llega allí, pasa el CI y el resultado se avisa en Element, en la sala
de alertas.

```
checkout (CT 123, lucifer, Mac)
   │ hook post-commit: git push origin + git push backup
   ├──────────────────────────────► respaldo dns-sync (sigue igual)
   ▼
Forgejo (CT 126, origin) ──► runner (CT 127): terraform, ansible-lint, vaults, gitleaks, tflint, Trivy, copia pública
   │                    │ webhook al terminar
   │                    ▼
   │       ci-avisos (CT 126, loopback) ──► matrix-relay (CT 111, E2EE) ──► Element
   │ cron cada 5 min (fetch)
   ▼
repo central de antes /home/agent/infra-tf-sync.git (CT 123): solo lectura
```

El repo central de antes rechaza los pushes con un mensaje que explica cómo
cambiar el remoto, para que nadie empuje allí sin enterarse y se quede fuera
del CI.

Desde la noche del 14-10, `master` está protegida: los cambios entran por PR,
con el plan de lo que van a tocar antes de fusionar y el despliegue con un clic.
Eso está en [docs/despliegue.md](despliegue.md).

GitHub no cambia para infra-tf: nunca ha estado allí (solo la copia saneada
`homelab-infra`, con su propio proceso).

**La web personal** (`tito/landing`) también tiene su origen aquí desde el 14-10: su CI
corre en el mismo runner (etiqueta `landing`) y, si sale verde en `main`, un runner propio
del CT 123 la despliega y empuja ese commit a GitHub, que queda como copia pública.
Detalle en [docs/landing.md](landing.md).

## Piezas

| Pieza | Dónde |
|---|---|
| CT 126 `forgejo`, 192.0.2.235, 2 vCPU, 1 GB, 10 GB | `environments/homelab/lxc-forgejo.tf` |
| CT 127 `forgejo-runner`, 192.0.2.236, 2 vCPU, 2 GB, 16 GB | `environments/homelab/lxc-forgejo.tf` |
| Forgejo, repo, webhook, registro del runner, receptor de avisos | `ansible/roles/forgejo/` |
| Runner y herramientas del CI | `ansible/roles/forgejo_runner/` |
| Origin del CT 123, central de solo lectura y su cron | `ansible/roles/forgejo/tasks/central.yml` |
| Variables (versiones y sumas fijadas) | `ansible/inventory/group_vars/forgejo{,_runner}/vars.yml` |
| Contraseña del admin `tito` | `ansible/inventory/group_vars/forgejo/vault.yml` |
| Workflow del CI | `.forgejo/workflows/ci.yml` |
| Repo de la web, su webhook y su runner de despliegue | `ansible/roles/forgejo/tasks/landing.yml`, `landing_cd_*.yml` |
| Playbook (todo lo anterior + Caddy) | `ansible/playbooks/forgejo.yml` |

```sh
cd ~/infra-tf/ansible && ansible-playbook playbooks/forgejo.yml
```

Se lanza desde el CT 123: los plays de ese CT van con `connection: local`. El
despliegue por PR **no** lo lanza solo (reinicia Forgejo y el runner de
despliegue): sale como "a mano" en el plan. Solo la parte de Forgejo:

```sh
ansible-playbook playbooks/forgejo.yml --limit forgejo,localhost
```

`--check` no sirve con este playbook: varias tareas leen la salida de un
`command`, que en modo check no se ejecuta.

## Acceso

- Web: `https://git.home.arpa` (Caddy de dockge, solo LAN/WireGuard, Authelia 2FA
  y luego el login de Forgejo con `tito`).
- Puerto web directo (3000), sin Authelia: solo Caddy, el runner del CI (CT 127)
  y el runner de despliegue (CT 123).
- Git por SSH: `ssh://git@192.0.2.235:2222/tito/infra-tf.git`. Las claves de
  lucifer, el Mac y el usuario agent del CT 123 ya están dadas de alta
  (`forgejo_admin_ssh_keys` en `group_vars/forgejo/vars.yml`; la de agent la
  añade el playbook). Un equipo nuevo: añadir su clave ahí y relanzar.
- Cambiar un checkout viejo a Forgejo:

  ```sh
  git remote set-url origin ssh://git@192.0.2.235:2222/tito/infra-tf.git
  git fetch origin && git branch -u origin/master master
  ```

  Hecho el 14-10 en el CT 123 y en lucifer (allí también el remoto `sync`).
  Falta el Mac.

## Qué comprueba el CI

El runner del CT 127 atiende dos etiquetas (`forgejo_runner_labels`): `infra-tf` y
`landing`. Para la web tiene Rust (versión fijada, la misma del CT 123), PostgreSQL solo
por socket con un rol `runner` que puede crear bases (las pruebas crean una por prueba) y
Node; las compilaciones se guardan en `/var/lib/forgejo-runner/cargo-target` entre
ejecuciones. Con dos trabajos, el pico es ~1,3 GB en clippy (release ~1,1 GB, pruebas
~1,0 GB; medido el 14-10), dentro de sus 2 GB. La primera ejecución, sin caché,
tardó ~23 min; las siguientes reutilizan lo compilado.

Para infra-tf, trabajos separados, para que un fallo no esconda los demás:

| Trabajo | Qué | Notas |
|---|---|---|
| terraform | `fmt -check` y `validate` de cada entorno | `init -backend=false`: sin state ni credenciales |
| ansible | `ansible-lint` | Solo fallan los avisos nuevos: los que había el 14-10 están en `ansible/.ansible-lint-ignore`. Al arreglar uno, quitar su línea |
| secretos | vaults cifrados y `gitleaks` de todo el historial | `.gitleaksignore` lleva los avisos revisados a mano |
| seguridad | `tflint` (reglas recomendadas) y Trivy: errores de configuración en Terraform y Dockerfiles y dependencias vulnerables | Falla con HIGH o CRITICAL. Lo aceptado va en `.trivyignore` (un ID por línea, con un comentario del motivo). Trivy fijado a una versión de al menos 14 días (Renovate espera ese tiempo: en marzo de 2026 se publicó una versión comprometida) |
| copia-publica | genera la copia de GitHub y pasa el control de fugas | Ver [publico.md](publico.md) |

El runner **no tiene secretos**: ni la clave de la API de Proxmox, ni el
tfstate, ni la contraseña del vault. Para que las herramientas arranquen hay
dos ficheros falsos a propósito (`~/.vault-pass-infra-tf` y `~/.ssh/id_ed25519`
del usuario `runner`) que no abren nada. El CI nunca aplica cambios.

## Avisos en Element

Webhook de cada repo (infra-tf y landing) (eventos `action_run_success`, `action_run_failure`,
`action_run_recover`) → `ci-avisos` (`127.0.0.1:9010`, comprueba la firma) →
`matrix-relay` del CT 111 → sala **CI/CD**, cifrado. Los avisos del despliegue
(plan, aplicar, deriva) van a la misma sala; el de OpenBao sellado, a **Incidencias**
(`ROOM_INCIDENCIAS` en `~/.infra-tf/matrix.env`). El aviso de fallo sale en
cuanto falla el primer trabajo, aunque los otros sigan corriendo.

```
❌ **CI de tito/infra-tf: FALLO**
master · 50acb76 · feat(ci): CI de infra-tf en Forgejo y avisos en Element
Duración: 7 s
https://git.home.arpa/tito/infra-tf/actions/runs/1
```

Entregas y respuestas: Forgejo → repo → Ajustes → Webhooks. Log del receptor:
`journalctl -u ci-avisos` en el CT 126.

## Copia de seguridad

Desde el 15-10, en la copia diaria de PBS con el resto de CT (cifrada, 02:30):
[copias.md](copias.md). La tarea suelta `forgejo-diaria` a `lb2-copias` se
retiró. El runner también entra, aunque no guarda nada (se recrea con el
playbook).

## Problemas conocidos y comprobaciones

- **Central de solo lectura:** el cron del usuario agent (CT 123) deja su
  resultado en `~/.cache/forgejo-mirror.log`; si pone `FALLO`, se repite solo a
  los 5 minutos. El central solo lo usa quien aún no haya cambiado el remoto.
- **Trabajos que se quedan en espera:** el runner solo busca trabajo nuevo
  cuando cambia la versión de tareas del servidor. Si se le cambian las
  etiquetas con trabajos ya en cola, reiniciarlo (`systemctl restart
  forgejo-runner` en el CT 127). Pasó en la primera instalación.
- **Deriva de Terraform (resuelta 14-10):** el plan completo queria quitar el `startup order=1`
  del CT 120 (lo puso `playbooks/pve-dns.yml`). Por eso estos CT se crearon con
  `-target`. Ya esta en `lxc-technitium.tf` y el plan completo sale limpio.
- **Acceso de agents:** los CT 126/127 tienen la clave del CT 123 puesta a mano
  por `pct exec` (lo mismo que hace `playbooks/agents-access.yml`, que se lanza
  desde lucifer).
- Zabbix y Wazuh: los dos CT registrados (`scripts/register_monitoring.py`) y con
  agentes (`playbooks/monitoring.yml`) desde el 14-10.

## Actualizar

Cambiar `forgejo_version`/`forgejo_sha256` (o los del runner y las
herramientas) en `group_vars` y relanzar el playbook. Cada versión queda en su
propio fichero y un enlace apunta a la que está en uso: volver atrás es poner
la anterior.

## Deshacer

Primero devolver el origen al repo central (si no, se pierde lo que solo
esté en Forgejo): quitar `hooks/pre-receive` y el cron del central, hacer un
último `git fetch` desde Forgejo y volver a poner `origin` en cada checkout al
central (`/home/agent/infra-tf-sync.git` en el CT 123; `ssh://agent@192.0.2.237/home/agent/infra-tf-sync.git`
desde fuera). Luego:

```sh
cd ~/infra-tf/environments/homelab
terraform destroy -target=proxmox_virtual_environment_container.forgejo \
                  -target=proxmox_virtual_environment_container.forgejo_runner
```

Y quitar: el bloque `git.home.arpa` del Caddyfile (relanzar `caddy_recargar`),
y el remoto `forgejo` del repo central. Las copias del CT en PBS caducan solas
con la poda.
