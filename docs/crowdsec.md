# CrowdSec (en el CT 209, Traefik)

> Guía de uso: wiki del repo, página **CrowdSec**. Esto es el detalle técnico.

Montado el 2026-10-15. Detecta en el log de acceso de Traefik (y en el SSH del
CT) escaneos, búsqueda de ficheros sensibles, CVE conocidas y fuerza bruta, y
el plugin de Traefik bloquea esas IPs. Además recibe la **lista comunitaria**
de CrowdSec (IPs maliciosas vistas por otros) y comparte las que detecta aquí.

```
visitante ──► Cloudflare ──► Traefik (CT 209) ──► servicio
   escáner ───────────────────►│  │
                               │  └─ plugin crowdsec (bouncer, modo stream)
             log de acceso ────┘        ▲  decisiones cada 60 s
                    │                   │
                    ▼                   │
               CrowdSec (motor + LAPI 127.0.0.1:8080) ◄──► Central API (lista comunitaria)
                    │
         09:00 resumen ──► sala «CrowdSec» de Element
```

## La IP real con Cloudflare delante

Casi todo el tráfico entra por Cloudflare: sin más, Traefik vería IPs de
Cloudflare y CrowdSec bloquearía a Cloudflare (a todo el mundo).

- `traefik_ips_confiables` (rangos de <https://www.cloudflare.com/ips/>) en los
  dos entryPoints: Traefik se fía del `X-Forwarded-For` **solo** si la conexión
  viene de Cloudflare. Si una conexión directa trae esa cabecera, Traefik la
  quita y se ve la IP de origen.
- En el log, `ClientHost` es entonces la IP real y `ClientAddr` la de Cloudflare.
- Si alguien manda un `X-Forwarded-For` falso a través de Cloudflare, Cloudflare
  añade la IP real al final. El parser de CrowdSec coge **la última** de la
  cadena y el plugin hace lo mismo con `forwardedHeadersTrustedIPs`.
  Probado con `cscli explain`.
- Los servicios también reciben ahora la IP real (Synapse, Overseerr...).

Si Cloudflare cambia sus rangos, actualizar la lista (cambia muy poco).

## Solo mirar o bloquear

`crowdsec_bloquear` (`group_vars/traefik_prod/vars.yml`):

- **`true` desde el 18-10** (en vez del 22-10, a peticion de Tito, con 3 dias
  de datos): en 72 h habria bloqueado 7.875 peticiones de 143 IPs; las 71 con
  alguna respuesta 2xx eran escaneres de nubes (GCP, AWS, Azure) en paginas
  publicas, ninguna conocida.
- `false` (del 15-10 al 18-10): CrowdSec detecta y decide, pero
  el bouncer solo está en el router del dashboard (solo LAN, nunca bloquea),
  así que se puede comprobar que se carga y se conecta (`cscli bouncers list`,
  *last pull*). El resumen diario cuenta lo que **habría** bloqueado.
- `true`: el middleware `crowdsec@file` va en los entryPoints `web` y
  `websecure`, es decir, en todas las rutas. Se activa con un PR que cambie esa
  variable.

Nunca se bloquean: la LAN, la VPN (`crowdsec_ips_casa`, en el plugin) y la **IP
pública de casa**. Esta es dinámica: `ip-casa.timer` la consulta cada hora
(`whoami.cloudflare`) y la escribe como lista blanca de CrowdSec
(`/etc/crowdsec/parsers/s02-enrich/ip-casa.yaml`). Las IPs privadas ya las
excluye `crowdsecurity/whitelists`.

## Resumen diario (09:00)

`crowdsec-resumen.timer` cruza las alertas de 24 h y la lista comunitaria con el
log de acceso:

- detecciones propias (por escenario);
- cuántas IPs de la lista comunitaria vinieron;
- cuántas peticiones se bloquearon, o se habrían bloqueado;
- **⚠️ las IPs marcadas que recibieron respuestas 2xx**: son las candidatas a
  falso positivo (un amigo en battlepros, tú desde fuera...).

Antes de pasar a `true`, revisar esa última lista de toda la semana.

## Comandos (en el CT 209)

| Para | Comando |
|---|---|
| Ver decisiones activas propias | `cscli decisions list` |
| Desbloquear una IP | `cscli decisions delete --ip 203.0.113.5` |
| Bloquear a mano | `cscli decisions add --ip 203.0.113.5 --duration 24h` |
| Alertas recientes | `cscli alerts list --since 24h` |
| Qué lee y qué descarta | `cscli metrics show acquisition` |
| Por qué una línea dispara (o no) | `cscli explain --log '<línea>' --type traefik` |
| Estado del bouncer | `cscli bouncers list` |
| Lista comunitaria | `cscli capi status` |

## Piezas

| Pieza | Dónde |
|---|---|
| Motor, fuentes, colecciones, ip-casa, resumen | `ansible/roles/crowdsec/` |
| Rangos de Cloudflare, plugin, middleware, logrotate | `ansible/roles/traefik/` |
| Variables | `ansible/inventory/group_vars/traefik_prod/vars.yml` |
| Playbook | `traefik-prod.yml` (automático: crowdsec y después traefik) |

- Paquete: repositorio oficial (packagecloud, suite bookworm). Debian 13 trae la
  1.4, de 2023.
- Plugin: `maxlerebourg/crowdsec-bouncer-traefik-plugin`, versión fija
  (`traefik_crowdsec_plugin_version`) descargada a `/opt` y cargada como plugin
  local (`/etc/traefik/plugins-local`, `WorkingDirectory=/etc/traefik`): no
  descarga nada de plugins.traefik.io al arrancar.
- La clave del bouncer la genera `cscli` en el CT
  (`/etc/traefik/crowdsec-lapi.key`, 0600): no está en el repo ni en el vault.
  Si se borra, el playbook rehace el bouncer.
- Si CrowdSec se cae, el plugin sigue con las últimas decisiones que tenía (modo
  stream).

## Logs de Traefik

Antes no rotaban: el de acceso llegó a 570 MB. Ahora `logrotate` los rota cada
día, guarda 14 y los comprime. Traefik reabre el fichero con `USR1` y CrowdSec
sigue el nuevo solo.
