# battlepros-status: web pública y panel interno

Desde 2026-10-09 el bot (CT dockge, 192.0.2.243, `/opt/stacks/battlepros-status`)
sirve dos cosas separadas, cada una en su puerto:

| Parte | Puerto en el CT | Quién llega | URL |
|-------|-----------------|-------------|-----|
| Web pública (portada, servidores, normas, `/api/public/servers`, `/uploads`) | `3010` | Internet vía Traefik + Cloudflare | https://www.example.net |
| Panel de gestión (`/admin/`, `/api/*`, `/api/upload`) | `127.0.0.1:3011` | Solo Caddy del propio CT, tras Authelia | https://battlepros.home.arpa (LAN/VPN) |

En el puerto público `/admin` y `/api/*` (salvo `/api/public/*`) devuelven 404, y la
portada se sirve sin el botón «Panel admin».

## Web y panel (2026-10-09)

Los ficheros de la web pública y del panel están en
`ansible/roles/battlepros_status/files/web/` y el role los copia a
`/opt/stacks/battlepros-status/web`, montado en `/app/web` (ya no se usan los de la imagen).

- Web pública: una sola página (portada con datos en vivo, servidores, Discord, normas ES/EN).
  `servers.html` y `rules.html` redirigen a `/#servidores` y `/#normas`. Sin Three.js ni Bulma.
- Panel: resumen, estado en vivo de cada servidor, prueba de AMP explicada, alta/edición con
  recorte de carátula y la sección «Publicados desde AMP».

### Secciones de la web

`/api/public/servers` da `kind` (`minecraft`, `steam`, `other`) y `proxy` de cada servidor
(`describeAmp`). La web agrupa así:

1. **Minecraft**: todos los mundos, con el proxy (velocity, el único Minecraft en el 25565) como
   cabecera «Todos los mundos por la misma puerta» y su dirección general (`mc.example.net`).
   Velocity elige el mundo por el nombre con el que se entra (`[forced-hosts]` de `velocity.toml`):
   `expeditions.example.net` → david01, etc. El proxy no cuenta como servidor ni suma jugadores.
2. Una sección por juego con **2 o más servidores** (por la categoría del panel o el juego de AMP).
3. **Juegos de Steam**: el resto de juegos de Steam (`steam:<appid>`, imagen de steamstatic o
   enlace `steam://`).
4. **Otros juegos**: lo demás.

## Qué publica AMP

AMP ya sabe cómo se publica cada instancia (lo mismo que enseña su página Community
`https://amp.example.org/c/<8 primeros del ID>`). El bot lo lee de la lista de instancias
(`ADSModule/GetInstances`, una llamada por ciclo) con `describeAmp()` en `src/amp.js`:

| Dato | De dónde sale en AMP |
|------|----------------------|
| Dirección con puerto | `ApplicationEndpoints[].Endpoint` si hay `Core.AMP.AdvertisedAddress` |
| Botón «Conectar con Steam» | `ApplicationEndpoints[].Uri` cuando es `steam://connect/...` |
| Carátula | `DisplayImageSource` (`steam:<appid>` → `header.jpg` de Steam, `url:...`) |
| Juego | `ModuleDisplayName` (o `Minecraft` para `MinecraftModule`) |

- Servidor dado de alta en el panel: la dirección y la carátula del panel mandan; si están
  vacías se usan las de AMP. El mensaje de Discord también las usa (miniatura y dirección).
- Instancia con «Advertised Connection Address» que no está dada de alta: sale sola en la web
  (sin mensaje en Discord) y en el panel aparece en «Publicados desde AMP» con «Añadir al bot».
  Es la misma señal que usa `amp_publicar` para abrir router y DNS (ver `docs/amp-publicar.md`).
- El título del mensaje de Discord enlaza a la página Community de AMP
  (`AMP_COMMUNITY_URL/c/<id>`, conexión directa y copiar dirección) cuando la instancia tiene
  dirección anunciada; si no, a la web (sin ella AMP enseña la IP interna). La web pública no
  enlaza a AMP.
- Minecraft (módulo `Minecraft` en AMP): entran por velocity (25565), así que el bot usa la
  dirección anunciada sin puerto. La página de AMP enseña `ApplicationEndpoints[].Endpoint` tal
  cual: si lleva el puerto propio de la instancia (cerrado en el router), el mensaje de Discord
  enlaza a la web en vez de a AMP (`communityOk` en `describeAmp`). Se arregla en ADS dejando la
  dirección sin puerto o con `:25565`.

## Login del panel

Lo hace Authelia. Caddy (`forward_auth`) pasa `Remote-User` y el bot solo lo lee en el
puerto de gestión (`req.autheliaUser` en `src/index.js`); en el público se ignora. El
puerto 3011 está ligado a `127.0.0.1`, así que nadie de la LAN puede saltarse Caddy
enviando la cabecera a mano.

El login con Discord queda en el código pero sin uso: su redirect URI registrada
(`battlepros_discord_oauth_redirect_uri`) apunta a www.example.net, que ya no sirve
`/api/auth`.

## Desplegar

```sh
ansible-playbook playbooks/battlepros.yml   # compose + stack.env + bloque de Caddy
```

El código del bot (`files/src`, montado en `/app/src` sobre la imagen) y la web (`files/web`)
están versionados en el role desde 2026-10-09: el playbook los copia y reinicia el bot si cambia
el código. `data/` (SQLite y carátulas subidas) no se toca. En el servidor quedan las copias
anteriores a los cambios del 2026-10-09 (`src/*.bak-20261009*`).

Para volver al reparto anterior (panel en internet): restaurar `index.js` y `auth.js` desde esas
copias, quitar el puerto 3011 del compose y el bloque `battlepros.home.arpa` del Caddyfile.

## Comprobar

```sh
curl -s -o /dev/null -w '%{http_code}\n' https://www.example.net/admin/        # 404
curl -s -o /dev/null -w '%{http_code}\n' https://www.example.net/api/servers   # 404
curl -s -o /dev/null -w '%{http_code}\n' http://192.0.2.243:3011/               # sin conexión
curl -sk -o /dev/null -w '%{http_code}\n' https://battlepros.home.arpa/admin/      # 302 a auth.home.arpa
```
