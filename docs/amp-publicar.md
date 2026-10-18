# Publicar servidores de AMP (router + Cloudflare)

Activo desde 2026-10-09. Rol `amp_publicar`, desplegado en el CT dns-sync (192.0.2.249)
con `playbooks/dns-sync.yml`.

## Qué hace

Cada minuto pregunta a AMP qué instancias están encendidas (cuenta de solo lectura
`bot_ia_status`, la misma que usa el asistente) y:

- **Encendida** (AppState 10/20/50): crea en el MikroTik una regla `dst-nat` por cada
  puerto de juego hacia 192.0.2.136, con comentario `amp-auto:<instancia>`, y el
  CNAME gris `<nombre>.example.net` → `example.net` con el mismo comentario.
- **Apagada** (no corre, o AppState 0/100/200) durante más de 3 minutos
  (`amp_publicar_espera_cierre`): borra esas reglas y ese CNAME. El margen evita
  borrar el DNS en cada reinicio. Estado en `/var/lib/amp-publicar.json`.
- **Estados de paso** (reiniciando, actualizando, instalando…): no toca nada.
- **AMP no responde:** no cambia nada.

Puertos de juego = los que declara la instancia en `GenericModule.App.Ports`, salvo
los que contienen `rcon|api|admin|control|telnet|allocs|sftp` en el nombre
(`amp_publicar_puertos_excluir`). SFTP nunca entra (es otro campo).

Los Minecraft no abren puertos: entran todos por el 25565 de velocity01, que tiene
reglas fijas con protección anti fuerza bruta y está en `amp_publicar_ignorar`.
Se gestiona su subdominio y, desde el 15-10, también su sitio en Velocity y en
MiniMOTD (abajo).

Nunca toca reglas NAT ni registros DNS sin el comentario `amp-auto:`, con una
excepción: un CNAME gris al apex con el mismo nombre que una instancia lo adopta
(le pone el comentario) al encenderla, o lo borra si la instancia está apagada.

Se niega a abrir (y lo deja en el log) un puerto que coincida con un servicio del
router (`/ip service`) o con una regla `dst-nat` manual.

## Nombre de cada servidor

1. **Advertised Connection Address** de la instancia, si es `algo.example.net`.
   Se pone desde el **panel principal** (ADS) → ajustes de la instancia, no desde
   dentro de la instancia. Guardarlo reinicia la instancia. AMP lo devuelve en
   `DeploymentArgs["Core.AMP.AdvertisedAddress"]`.
   No usar el «Default Advertised Connection Address» de ADS con `example.net`:
   el apex está en naranja (Cloudflare) y los juegos no conectarían.
2. Si no, `amp_publicar_nombres` en `group_vars/dns_sync/vars.yml`.
3. Sin nombre: solo se abren puertos.

«Configure for Traefik» de ADS no sirve aquí: publica el panel web de cada
instancia por HTTP con etiquetas de Docker (Traefik en el mismo Docker), no los
puertos de juego.

## Velocity y MiniMOTD (servidores de Minecraft nuevos)

Con `amp_publicar_velocity_activo`, en cada pasada y para cada instancia de
Minecraft (salvo el propio velocity01) con dirección anunciada
`<nombre>.example.net`:

- **`velocity.toml`**: `<nombre> = "192.0.2.136:<puerto>"` en `[servers]`
  (antes de `try`) y `"<nombre>.example.net" = ["<nombre>"]` en
  `[forced-hosts]`. El puerto es el de la instancia
  (`MinecraftModule.Minecraft.PortNumber`); si cambia, se actualiza.
- **MiniMOTD** (`plugins/minimotd-velocity`): si no hay
  `extra-configs/<nombre>.conf`, lo crea desde
  `roles/amp_publicar/files/minimotd-servidor.conf` (nombre en grande,
  jugadores conectados) con el icono estándar `icons/estandar.png` (bloque de
  hierba, 64×64); y añade `"<nombre>.example.net:25565"=<nombre>` a
  `virtual-host-configs` de `plugin_settings.conf`. **Lo que ya existe no se
  toca**: el MOTD y el icono de cada servidor se pueden personalizar a mano.
- Si cambia algo: copia de `velocity.toml` en `/var/lib/amp-publicar/` (las 20
  últimas), `velocity reload` y `minimotd reload` por la consola de velocity01.
  Sin reiniciar el proxy: nadie se desconecta.

Las entradas que ya había y coinciden se adoptan. Al borrar una instancia se
quitan sus líneas (solo de las que gestiona el script,
`/var/lib/amp-publicar/velocity.json`), salvo si el servidor está en `try` de
`[servers]` (Velocity no cargaría): sale un aviso en el log. Apagar una
instancia no quita nada (su DNS sí).

Ficheros y consola por la API de AMP con una cuenta propia
(`vault_amp_publicar_velocity_*`) con permisos **solo** en velocity01: gestor de
ficheros y enviar a la consola. La cuenta de solo lectura no puede (lo
deniega con `Core.AppManagement.SendConsoleInput`).

Activo desde el 15-10 (cuenta `velocity-sync` de AMP). La primera pasada creó
el MOTD de `smp`, que no tenía. Ojo con la API de ficheros de AMP: leer un
fichero que no existe no da error (devuelve vacío), así que «existe» se mira
en el listado de la carpeta; la raíz del gestor es la carpeta de Velocity
(`velocity.toml`, no `Minecraft/velocity.toml`).

Crear un servidor nuevo, entonces: crearlo en AMP con su puerto, poner su
*Advertised Connection Address* `<nombre>.example.net` (ADS → ajustes de la
instancia) y encenderlo. En un minuto tiene DNS, sitio en Velocity y MOTD.

## Credenciales

- MikroTik: usuario `amp-nat`, grupo `amp-nat` (`read,write,api,rest-api`; sin
  `api` el REST responde «not allowed (9)»), solo desde 192.0.2.249. Contraseña en
  `vault_amp_publicar_mikrotik_password`. La huella SHA-256 del certificado
  `www-ssl` está fijada en `amp_publicar_mikrotik_fingerprint`; si se regenera el
  certificado el script deja de funcionar hasta actualizarla.
- Cloudflare: el token de `dns_sync` (llega a las 3 zonas).
- AMP: `vault_amp_publicar_amp_*` (copia de la cuenta de `ia_asistente`).

## Operar

```sh
# en dns-sync
amp-publicar.py --dry-run      # dice qué haría
tail /var/log/amp-publicar.log # solo escribe cuando cambia algo o hay avisos
```

Apagar la automatización: `amp_publicar_activo: false` y reaplicar el playbook
(quita el cron). Para dejarlo todo cerrado, borrar en el router las reglas
`amp-auto:` y en Cloudflare los registros con ese comentario.

## Limitaciones

- Si alguien busca el nombre mientras el servidor está apagado, su resolutor puede
  recordar que no existe durante el TTL negativo de la zona (minutos) aunque se
  encienda después.
- Dos instancias con el mismo puerto: la segunda que arranque se queda sin abrir
  (aviso en el log).

## Verificación 2026-10-09

- V Rising (creado ese día): 9876/udp y 9877/udp abiertos y `vrising.example.net`
  tomado del Advertised Connection Address; llegan paquetes desde fuera.
- Satisfactory, ciclo completo: al encenderlo, en menos de un minuto, 7777 tcp/udp,
  8888 tcp y `satis.example.net` (HealthCheck por la IP pública: `healthy`); al
  apagarlo, a los 3 minutos, reglas y CNAME borrados y puertos cerrados.
  Probado desde la LAN a través de la IP pública (hairpin), no desde fuera.
- Satisfactory no arrancaba por la licencia de AMP (`NoMatchingMachineId`, no se
  encendía desde la migración CT108 → CT121); se reactivó desde el panel con la
  clave. Otras instancias paradas desde entonces pueden tener el mismo problema.
