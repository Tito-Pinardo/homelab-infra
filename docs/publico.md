# Copia pública (github.com/Tito-Pinardo/homelab-infra)

> Guía de uso: wiki del repo, página **Copia pública**. Esto es el detalle técnico.

Desde el 2026-10-15 la copia pública sale sola de este repo. Nunca se empuja
infra-tf a GitHub: lo que llega allí lo genera `scripts/publico/` y lo
aprueba una persona.

```
fusión en master ──► publico.yml (runner despliegue, CT 123)
                       generar.py  → lista blanca + saneado
                       comprobar.py → control de fugas ──✗──► ❌ en Element, no se propone
                       rama "propuesta" de tito/homelab-infra (Forgejo, privado)
                       ──► 🌐 en Element con el enlace al diff
Run workflow ──────► publico.yml: regenera, comprueba que es igual a la
                       propuesta, main ← propuesta y push a GitHub (sin force)
                       ──► 🚀 en Element
cada PR ───────────► ci.yml, trabajo "copia-publica": generar + comprobar
```

## Qué se publica

`scripts/publico/reglas.yml` (este fichero **no** se publica: tiene los
nombres, dominios e IPs reales):

- **`incluir`**: lista blanca. Un fichero nuevo que no encaje no se publica y
  sale en el aviso como «sin decidir»: hay que añadirlo a `incluir` o a
  `excluir`.
- **`excluir`**: gana sobre `incluir`. Fuera: descargas e IPTV (exposición
  legal), los vault, paquetes y scripts de terceros.
- **`binarios`**: los únicos binarios que se copian tal cual.
- **`fijos`** (`scripts/publico/fijos/`): ficheros propios de la copia (README,
  `.gitignore`...).

## Qué se cambia

- IPs: la red de casa pasa a `192.0.2.x`, la VPN a `198.51.100.x` y el resto a
  `203.0.113.x`. Se conserva el último número.
- Dominios a `example.org`/`example.net`. `.home.arpa` pasa a `.home.arpa`.
- Correos, nombres de cuentas de correo, IDs de Discord, IDs de salas de
  Matrix y claves SSH públicas: se cambian por marcadores.
- Listas de orígenes del firewall (`*_allowed_sources`, `*_origenes*`...): `[]`.
- Cada vault pasa a un `.example` con los nombres de sus variables y el valor
  `CAMBIAR`. Los nombres salen del propio vault, porque el runner tiene la
  contraseña; nunca se escribe un valor. Los vault con valores cifrados uno a
  uno (`!vault`) se leen sin descifrar. Sin contraseña (en el CI), los nombres
  se deducen de los `vars.yml`.
- Python (también las plantillas `.py.j2`): de cada función queda la firma y
  el docstring; el cuerpo y sus comentarios se cambian por `...`.

## El control de fugas

`comprobar.py` sobre el árbol ya generado:

- `prohibido`: IPs de casa y de la VPN, IP pública, dominios y correos
  reales, dominio interno, vault cifrados y claves privadas.
- **Estilo**: los comentarios van en primera persona. Bloquea el narrador
  en tercera persona («el usuario» seguido de un verbo de decisión, o una
  decisión atribuida «al usuario») y las atribuciones al asistente. No bloquea «el usuario agent» (cuentas del
  sistema) ni los textos que lee el modelo del asistente (`permitir`).
- Cualquier IPv4 pública fuera de `ips_permitidas` (DNS conocidos, rangos de
  documentación, privadas genéricas, multicast, Cloudflare).
- gitleaks sobre el árbol.

Si bloquea: corregir el fichero en infra-tf (o la regla, si es un falso
positivo) y fusionar otra vez. Probar en local:

```
python scripts/publico/generar.py HEAD /tmp/copia --informe /tmp/informe.json
python scripts/publico/comprobar.py /tmp/copia
```

## Publicar

Aviso «🌐 Copia pública lista para revisar» → abrir el enlace
(`git.home.arpa/tito/homelab-infra/compare/main...propuesta`) → si está bien,
**Actions → `publico.yml` → Run workflow** (rama master).

- Solo publica si la copia de la punta de master es **idéntica** a la
  propuesta. Si master cambió después, sale una propuesta nueva sola: hay que
  revisarla otra vez.
- La fusión la hace git y no Forgejo: así el autor es
  `Tito-Pinardo@users.noreply.github.com`, igual que en los commits públicos,
  y no la cuenta de Forgejo.
- `main` de tito/homelab-infra es exactamente lo publicado; no admite force
  push. Si algo ya publicado no debía estarlo, se borra con un commit nuevo,
  pero **sigue en la historia de GitHub**: hay que rotar lo filtrado.

## Piezas

| Pieza | Dónde |
|---|---|
| Reglas, generador, control, publicación | `scripts/publico/` |
| Workflows | `.forgejo/workflows/publico.yml`, trabajo `copia-publica` de `ci.yml` |
| Repo privado | `tito/homelab-infra` en Forgejo (`ansible/roles/forgejo/tasks/publico.yml`) |
| Clones de trabajo | `~/.infra-tf/publico/` en el CT 123 |
| Push a GitHub | clave SSH del usuario agent del CT 123 |
