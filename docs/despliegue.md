# Despliegue de infra-tf con PR (Forgejo)

> Guía de uso para el día a día (cómo cambiar algo, leer el plan, qué es cada aviso,
> qué hacer si algo falla): **wiki del repo**, <https://git.home.arpa/tito/infra-tf/wiki>.
> Esto es el detalle técnico.

Montado el 2026-10-14. Los cambios entran por PR, se ve **antes** qué van a
tocar, y se aplican al fusionar con un clic. Todo avisa en Element.

```
rama ──push──► PR en Forgejo ──► CI (CT 127, sin secretos)
                    │
                    └──► Plan del PR (CT 123): terraform plan + playbooks en --check
                         → comentario en el PR y resumen en Element. No cambia nada.
fusionar ──► master ──► Despliegue/plan (CT 123): plan guardado de esa punta
                         → resumen en Element: qué cambia, qué se recrea, qué es a mano
Run workflow ──► Despliegue/aplicar: aplica ESE plan y esos playbooks → Element
```

## Flujo de trabajo

```sh
git switch -c cambio-ip-landing      # master esta protegida (pre-commit lo para)
# ... editar ...
git commit -m "fix(landing): ..."    # el post-commit empuja la rama a Forgejo y al respaldo
```

1. En `https://git.home.arpa/tito/infra-tf` abrir el PR de la rama a `master`.
2. Esperar al CI (obligatorio para fusionar) y leer el **plan del PR** (comentario).
3. Fusionar. Sale solo el plan de despliegue de `master` (Element).
4. Aplicar: **Actions → `despliegue.yml` → Run workflow** (rama `master`; en la lista de Actions los workflows salen por nombre de fichero). Aviso en Element
   con el resultado.

## Cómo sé que no se modifica nada más

- **Terraform:** el resumen lista cada recurso que se crea (`+`), cambia (`~`),
  destruye (`-`) o **recrea** (`-/+`, marcado ⚠️). Lo que no sale no se toca.
  `aplicar` usa el fichero de plan guardado: si el estado cambió después del plan,
  Terraform se niega ("stale") en vez de aplicar otra cosa.
- **Ansible:** solo se lanzan los playbooks afectados por los ficheros cambiados
  desde lo último desplegado (rol → playbooks que lo usan, también por dentro;
  playbook cambiado → ese; `group_vars/<grupo>` → los playbooks de ese grupo,
  limitados a sus hosts). En el plan se pasan con `--check` y se listan las tareas
  que cambiarían. `--check` no es perfecto (las tareas `command`/`shell` no se
  simulan): si falla en check, el resumen lo marca.
- Si en un YAML solo cambian comentarios o líneas en blanco (como las anotaciones
  `# renovate:`), no cuenta: sale como nota "sin efecto".
- Sin `--diff` a propósito: las plantillas llevan secretos (`.env`) y acabarían en
  el log, el PR y Element.
- `aplicar` solo vale si el commit sigue siendo la punta de `master`, y solo aplica
  los playbooks del plan.

## Deriva nocturna

`.forgejo/workflows/deriva.yml`, cada día a las 05:15 UTC (y a mano con Run workflow):
`despliegue.py deriva` hace un `terraform plan` contra **lo último desplegado**
(no contra `master`), así que lo que salga es deriva de verdad: algo cambiado fuera
del repo. Avisa en Element con «⚠️ Deriva en Terraform» y la lista de recursos.
Aparte avisa «⏳ Pendiente de desplegar» si `master` tiene commits sin aplicar. Si
todo cuadra, no manda nada (el «correcto» de cada noche se calla en `ci-avisos`).
Solo Terraform: Ansible en `--check` daría falsos positivos cada noche.

Probado el 15-10 cambiando a mano la descripción del CT 127: lo detectó y avisó;
se dejó como estaba con un `apply -target` de ese recurso.

## Lo que nunca se lanza solo

`scripts/despliegue/playbooks.yml`: playbooks "a mano" (CT 123, Forgejo, host
Proxmox, paperless, mantenimiento, migraciones viejas) y hosts excluidos de toda
ejecución (`paperless`, `agents`). Salen en el resumen con el motivo. También se
avisa (sin lanzar nada) si cambian `group_vars/all`, `hosts.yml`, `ansible.cfg` o
`requirements.yml`, que afectan a todo.

## Piezas

| Pieza | Dónde |
|---|---|
| Script de plan/aplicar | `scripts/despliegue/despliegue.py` |
| Manuales y excluidos | `scripts/despliegue/playbooks.yml` |
| Workflows | `.forgejo/workflows/plan-pr.yml`, `despliegue.yml`, `deriva.yml`, `renovate.yml` ([renovate.md](renovate.md)) |
| Runner `despliegue` (CT 123, usuario agent, solo este repo) | `roles/forgejo/tasks/despliegue_root.yml` y `despliegue_agent.yml` |
| Protección de `master` | `roles/forgejo/tasks/main.yml` (`forgejo_checks_obligatorios`) |
| Hooks del repo | `githooks/pre-commit`, `githooks/post-commit` |

En el CT 123, `~/.infra-tf/` (0700):

| Fichero | Qué |
|---|---|
| `estado/homelab.tfstate` | El estado de Terraform, compartido con el checkout de trabajo (mismo bloqueo) |
| `openbao/` | Acceso de solo lectura a OpenBao (desde el 15-10 las credenciales de Terraform y la contraseña del vault viven allí: [openbao.md](openbao.md)) |
| `arbol/` | Checkout propio del despliegue (no el de trabajo) |
| `planes/<sha>/` | Plan guardado y resumen de cada punta de `master`; `planes/pr-*` los de los PR |
| `ultimo-desplegado` | Último commit aplicado: base para elegir playbooks |
| `matrix.env`, `forgejo-token` | Avisos a Element y comentarios en los PR |

El estado salió del checkout el 14-10 (`backend "local" {}` con la ruta en el
init). En un checkout nuevo del CT 123:

```sh
terraform -chdir=environments/homelab init -backend-config=path=/home/agent/.infra-tf/estado/homelab.tfstate
# y para plan/apply a mano, "tf" en vez de "terraform" (credenciales de OpenBao)
```

Copia del estado anterior a la migración: `~/.infra-tf/copias/`.

## Seguridad

El runner `despliegue` ejecuta lo que diga el workflow como `agent` en el CT 123,
que puede tocar todo el homelab. Por eso solo está registrado para este repo, y
solo pueden empujar las claves de lucifer, el Mac y el CT 123, que ya entran como
root por SSH en todo: no da más acceso del que ya hay. El runner del CI (CT 127)
sigue sin secretos.

## Problemas

- **"master ya no es X":** se fusionó otra cosa después del plan. Esperar a su plan
  y aplicar ese.
- **"Saved plan is stale":** alguien aplicó Terraform a mano después del plan. Hacer
  un push a master (o relanzar el plan) y aplicar el nuevo.
- **Nada que desplegar:** si el plan sale vacío, se marca como desplegado solo.
- Aplicar a mano sigue funcionando como siempre desde `~/infra-tf` (mismo estado y
  bloqueo). Si se hace, el siguiente plan lo verá y no repetirá nada.

## RAM y disco de los CT, en caliente

El proveedor de Terraform (bpg/proxmox) **reinicia el contenedor** al cambiar
la memoria, aunque Proxmox la aplica en caliente en un LXC. El 18-10 eso
devolvió AMP de 64 a 42 GB con un reinicio y el OOM killer mató el panel.
Por eso todos los `lxc-*.tf` tienen `memory` en `ignore_changes`: Terraform la
usa al crear el CT y luego no la toca.

- **Cambiar la RAM:** en Proxmox, CT → *Resources* → *Memory* → *Edit*, o
  `pct set <id> -memory <MB>` en el host. Se aplica al momento, sin reiniciar.
  Después, el mismo valor en `dedicated` del `.tf` (por PR), como registro.
- **Ampliar el disco:** con Terraform (`size` del `disk` en el `.tf`) ya se
  hace en caliente (`pct resize`), sin reiniciar. También en la web: CT →
  *Resources* → *Root Disk* → *Volume Action* → *Resize*. Encoger no se puede:
  Terraform recrearía el CT.
- Otros cambios que sí reinician el CT con Terraform: consola, variables de
  entorno, nombre, DNS, `idmap`, puntos de montaje y opciones de montaje del
  disco. Revisar el plan antes de aprobar.

## Actualizaciones sin terminal (actualizar.yml)

**Actions → `actualizar.yml` → Run workflow**, con tres campos:

| Campo | Valores |
|---|---|
| que | `paquetes` (`update-all.yml`: apt/apk, sin reiniciar), `contenedores` (`update-containers.yml`: baja imágenes y recrea solo lo que cambió), `todo` |
| equipos | `todos` o una lista: `dockge,plex` |
| stacks | solo contenedores: `seerr,tautulli` (vacío = todos los del equipo) |

Corre en el runner de despliegue (CT 123) con `scripts/despliegue/actualizar.py`:
lanza el playbook con `--limit <equipos>:!paperless` (Paperless nunca entra) y
manda a la sala CI/CD de Element el resumen: equipos con cambios, los que
necesitan reiniciar (no se reinician solos), contenedores recreados y fallos.
Log completo en `~/.infra-tf/actualizaciones/` del CT 123. Los valores del
formulario llegan por variables de entorno, nunca pegados en el comando.
