# Renovate: PRs de versiones nuevas

> Guía de uso: wiki del repo, <https://git.home.arpa/tito/infra-tf/wiki>. Esto es el detalle técnico.

Montado el 2026-10-15. Cada lunes (05:45 UTC, y a mano con Actions →
`renovate.yml` → Run workflow) Renovate mira las versiones fijadas del repo y
abre un PR por cada una que tenga versión nueva. Cada PR pasa el CI y el plan
como cualquier otro: **nada cambia hasta que lo fusionas y apruebas el
despliegue**, igual que cuando subías el número a mano.

## Qué vigila

| Qué | Cómo |
|---|---|
| Versiones de `group_vars` (Forgejo, runner, Terraform, gitleaks, ansible-core, ansible-lint, OpenBao, Traefik, Element, Qdrant, Homepage) | Comentario `# renovate: datasource=… depName=…` justo encima de la variable |
| Imágenes con versión fijada en plantillas de roles (n8n…) | Regex sobre `image: x:1.2.3`. Las `:latest` no: esas las actualiza `update-containers.yml` |
| Provider de Proxmox | Lock file de Terraform (dentro del rango `~> 0.66`) |

Para vigilar una versión nueva, ponle encima el comentario, por ejemplo:

```yaml
# renovate: datasource=docker depName=qdrant/qdrant extractVersion=^v(?<version>.+)$
qdrant_version: "1.19.1"
```

Las fuentes son **imágenes Docker y PyPI**, no releases de GitHub: fuera de
GitHub, Renovate no consulta GitHub sin token, y las imágenes oficiales tienen
las mismas versiones.

**No vigila Ollama** a propósito: corre en lucifer y lo actualiza pacman;
`ollama_version` solo la lee Hefesto (poner a mano la de `pacman -Q ollama`).

**Hefesto** (`versiones_pinned.json` en el CT de ia-asistente) lleva las
versiones fijadas de varios servicios, pero solo se reescribe cuando se lanza
`ia-asistente.yml`: tras subir Traefik, Qdrant o Element, hasta el siguiente
cambio de ia-asistente Hefesto compara contra la versión anterior.

Los roles tienen que instalar la versión nueva de verdad: el 15-10 Qdrant y
Traefik (descarga a `/tmp` con `creates` fijo) y ansible-core del CT 123
(`state: present`) no lo hacían; un plan con «0 cambios» en una subida de
versión es la pista.

## Reglas (`renovate.json`)

- **Forgejo:** solo la rama LTS 15.x.
- **Major:** no abre PR sin tu aprobación en el issue «Renovate: actualizaciones
  pendientes» (marcar la casilla).
- **Postgres y Redis:** fuera; subir de major exige migrar datos.
- **Terraform** y **ansible-core** van agrupados: el CI y el CT 123 llevan la misma.
- Como mucho 5 PRs abiertos a la vez.

## Sumas SHA-256

Las descargas fijadas llevan su suma (`forgejo_sha256`, `ci_terraform_sha256`…).
Al subir la versión, `scripts/renovate/sumas.py` (postUpgradeTasks) pone la suma
nueva **sacada del fichero de sumas oficial de la release**; si la release no la
publica, falla y el PR no sale.

## Dónde corre

En el runner `despliegue` del CT 123 (el del CI sigue sin secretos), con su
propio Node 24 y Renovate en `~/.infra-tf/` (Node 22 del sistema es el de
Codeman). Usuario bot `renovate` de Forgejo, con escritura solo en infra-tf; su
token en `~/.infra-tf/renovate-token`. Lanzador: `scripts/renovate/ejecutar.sh`.
Todo lo instala `playbooks/forgejo.yml` (roles `forgejo`, tareas
`despliegue_agent.yml`); versiones en `group_vars/agents` (`renovate_*`).

Probar sin crear nada:

```sh
RENOVATE_DRY_RUN=full LOG_LEVEL=debug scripts/renovate/ejecutar.sh
```

## Tras fusionar un PR de Renovate

El plan dice qué se lanza. Ojo con los que tocan piezas «a mano»: Forgejo, el
runner, Terraform del CI o Renovate mismo se aplican con
`ansible-playbook playbooks/forgejo.yml`, y el Terraform/ansible-core del CT 123
con `agents.yml` (desde lucifer).
